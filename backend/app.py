"""FastAPI backend serving the PySynth Next.js frontend.

Phase 6a: all user data lives in Postgres via SQLAlchemy (see `backend/db.py`
and `shared/progress.py`). The static recipe + learning plan files are still
read from disk by `shared/prompts.py`.

Run (from `C:\\dev\\pysynth`):
    pip install -r backend/requirements.txt
    uvicorn backend.app:app --reload --port 8000
"""

import asyncio
import os
from datetime import date
from typing import Any, Literal
from uuid import UUID

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import and_, delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import PushSubscription, Session as SessionRow, User, get_session
from shared.push import PushConfigError, PushExpired, Subscription, send_push
from shared.llm import call_llm, call_llm_json
from shared.progress import (
    find_today_daily_row,
    list_done_chapters,
    log_session,
    pick_next_angle,
)
from shared.prompts import (
    ask_user_message,
    build_system_prompt,
    exercise_user_message,
    grade_user_message,
    review_user_message,
    start_user_message,
)
from shared.validators import (
    render_exercise_markdown,
    validate_exercise_data,
    validate_session_data,
)


app = FastAPI(title="PySynth Backend", version="0.1.0")

_allowed_origins = [
    o.strip()
    for o in os.environ.get("ALLOWED_ORIGIN", "http://localhost:3000").split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Phase 6b: each browser sends a UUID it minted in localStorage. We validate
# the header, upsert the User row (creating it on first sight, bumping
# last_seen_at on returning visits), and hand the UUID to the endpoint.
async def get_user_id(
    x_user_id: str = Header(..., alias="X-User-Id"),
    db: AsyncSession = Depends(get_session),
) -> UUID:
    try:
        uid = UUID(x_user_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid X-User-Id header")
    stmt = (
        insert(User)
        .values(id=uid)
        .on_conflict_do_update(
            index_elements=["id"],
            set_={"last_seen_at": func.now()},
        )
    )
    await db.execute(stmt)
    await db.commit()
    return uid


# ---------------- Pydantic models ----------------

class StartRequest(BaseModel):
    intent: Literal["advance", "review"] | None = None
    pin_to_chapter: str | None = None


class GradeRequest(BaseModel):
    questions: list[dict[str, Any]]
    answers: list[str]
    picked_indexes: list[int | None] = Field(default_factory=list)


class GradeResponse(BaseModel):
    grade_markdown: str
    score_correct: float
    score_total: int


class ExerciseRequest(BaseModel):
    topic: dict[str, Any] = Field(default_factory=dict)
    concept: str = ""


class ExerciseResponse(BaseModel):
    exercise: dict[str, Any]
    apply_at_work: dict[str, Any]
    angle: str
    exercise_text: str


class ReviewRequest(BaseModel):
    exercise: dict[str, Any]
    code: str


class ReviewResponse(BaseModel):
    review_markdown: str
    verdict: str
    reference_solution: str = ""


class ChatTurn(BaseModel):
    role: Literal["user", "mentor"]
    text: str


class AskRequest(BaseModel):
    question: str
    chapter: str = ""
    concept: str = ""
    stage: str = "concept"
    history: list[ChatTurn] = Field(default_factory=list)


class AskResponse(BaseModel):
    answer: str
    provider: str


class LogRequest(BaseModel):
    chapter: str = ""
    topic: str = ""
    quiz_score: str = "—"
    exercise_verdict: str = "pass"
    apply_summary: str = ""
    angle: str = "A"
    feeling: str = ""
    code: str = ""
    exercise_text: str = ""
    type: str = "Daily"


class LogResponse(BaseModel):
    ok: bool
    session_id: UUID
    exercise_id: UUID


# ---------------- Helpers ----------------

def _fail(detail: str, status: int = 502) -> HTTPException:
    return HTTPException(status_code=status, detail=detail)


def _safe_score(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _looks_degraded(data: dict[str, Any]) -> str | None:
    """Cheap content-quality check on a validated session payload.

    Catches the failure mode where a free-tier LLM emits structurally-valid
    JSON whose string values are nonsense (e.g. brace-spam loops inside
    definition) or whose required arrays are empty. Returns a one-line
    reason string if degraded; otherwise None.
    """
    review = data.get("concept_review") or {}
    if len(review.get("how_it_works") or []) < 2:
        return "how_it_works has fewer than 2 entries"
    if len(review.get("syntax_forms") or []) < 1:
        return "syntax_forms is empty"
    if not (review.get("worked_example_code") or "").strip():
        return "worked_example_code is empty"
    definition = review.get("definition") or ""
    for ch in set(definition):
        if not ch.isspace() and ch * 13 in definition:
            return f"definition contains a run of {ch!r}*13+ (model degenerated)"
    if len(data.get("questions") or []) < 3:
        return "fewer than 3 quiz questions"
    return None


# In-memory cache for today's /session/start responses. Keyed by
# (user_id, date, intent, pin_to_chapter) so a refresh on the same calendar
# day with the same arguments serves the cached session instead of burning
# an LLM call. Date in the key implicitly expires entries at midnight.
# Restart the backend to clear.
_session_cache: dict[tuple[str, str, str | None, str | None], dict[str, Any]] = {}


# ---------------- Endpoints ----------------

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/chapters/done")
async def chapters_done(
    user_id: UUID = Depends(get_user_id),
    db: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    return {"chapters": await list_done_chapters(user_id, db)}


@app.post("/session/start")
async def session_start(
    req: StartRequest = StartRequest(),
    user_id: UUID = Depends(get_user_id),
    db: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    if req.pin_to_chapter:
        user_msg = start_user_message(pin_chapter=req.pin_to_chapter)
    else:
        today_row = await find_today_daily_row(user_id, db)
        if today_row and req.intent is None:
            return {
                "kind": "needs_intent",
                "today_chapter": today_row["chapter"],
                "today_concept": today_row["concept"],
            }
        if today_row and req.intent in ("advance", "review"):
            user_msg = start_user_message(
                same_day_intent=req.intent,
                same_day_chapter=today_row["chapter"],
                same_day_concept=today_row["concept"],
            )
        else:
            user_msg = start_user_message()

    cache_key = (str(user_id), date.today().isoformat(), req.intent, req.pin_to_chapter)
    cached = _session_cache.get(cache_key)
    if cached is not None:
        return {"kind": "session", **cached}

    try:
        sys_prompt = await build_system_prompt(user_id, db)
        data, _provider = call_llm_json(sys_prompt, user_msg)
    except Exception as exc:
        raise _fail(f"LLM call failed: {exc}") from exc
    validated = validate_session_data(data)
    reason = _looks_degraded(validated)
    if reason:
        raise _fail(f"LLM returned a degraded session ({reason}); please retry")
    _session_cache[cache_key] = validated
    return {"kind": "session", **validated}


@app.post("/session/grade", response_model=GradeResponse)
async def session_grade(
    req: GradeRequest,
    user_id: UUID = Depends(get_user_id),
    db: AsyncSession = Depends(get_session),
) -> GradeResponse:
    user_msg = grade_user_message(req.questions, req.answers, req.picked_indexes)
    try:
        sys_prompt = await build_system_prompt(user_id, db)
        data, _provider = call_llm_json(sys_prompt, user_msg)
    except Exception as exc:
        raise _fail(f"LLM call failed: {exc}") from exc

    md = data.get("grade_markdown") or ""
    if not md:
        raise _fail("LLM returned no grade_markdown")
    correct = _safe_score(data.get("score_correct"))
    total_raw = data.get("score_total")
    try:
        total = int(total_raw) if total_raw is not None else len(req.questions)
    except (TypeError, ValueError):
        total = len(req.questions)
    return GradeResponse(grade_markdown=md, score_correct=correct, score_total=total)


@app.post("/session/exercise", response_model=ExerciseResponse)
async def session_exercise(
    req: ExerciseRequest,
    user_id: UUID = Depends(get_user_id),
    db: AsyncSession = Depends(get_session),
) -> ExerciseResponse:
    angle = await pick_next_angle(user_id, db)
    user_msg = exercise_user_message(angle)
    try:
        sys_prompt = await build_system_prompt(user_id, db)
        data, _provider = call_llm_json(sys_prompt, user_msg)
    except Exception as exc:
        raise _fail(f"LLM call failed: {exc}") from exc

    coerced = validate_exercise_data(data)
    exercise_text = render_exercise_markdown(coerced["exercise"])
    return ExerciseResponse(
        exercise=coerced["exercise"],
        apply_at_work=coerced["apply_at_work"],
        angle=angle,
        exercise_text=exercise_text,
    )


@app.post("/session/review", response_model=ReviewResponse)
async def session_review(
    req: ReviewRequest,
    user_id: UUID = Depends(get_user_id),
    db: AsyncSession = Depends(get_session),
) -> ReviewResponse:
    if not req.code.strip():
        raise _fail("code is empty", status=400)
    exercise_text = render_exercise_markdown(req.exercise)
    user_msg = review_user_message(exercise_text, req.code)
    try:
        sys_prompt = await build_system_prompt(user_id, db)
        data, _provider = call_llm_json(sys_prompt, user_msg)
    except Exception as exc:
        raise _fail(f"LLM call failed: {exc}") from exc

    md = data.get("review_markdown") or ""
    verdict = (data.get("verdict") or "").strip().lower()
    if verdict not in ("pass", "close", "miss"):
        verdict = "close"
    if not md:
        raise _fail("LLM returned no review_markdown")
    reference = data.get("reference_solution")
    if reference is None or verdict == "pass":
        reference = ""
    return ReviewResponse(
        review_markdown=md, verdict=verdict, reference_solution=str(reference)
    )


@app.post("/session/ask", response_model=AskResponse)
async def session_ask(
    req: AskRequest,
    user_id: UUID = Depends(get_user_id),
    db: AsyncSession = Depends(get_session),
) -> AskResponse:
    if not req.question.strip():
        raise _fail("question is empty", status=400)
    user_msg = ask_user_message(
        question=req.question,
        chapter=req.chapter,
        concept=req.concept,
        stage=req.stage,
        history=[t.model_dump() for t in req.history[-10:]],
    )
    try:
        sys_prompt = await build_system_prompt(user_id, db)
        text, provider = call_llm(sys_prompt, user_msg)
    except Exception as exc:
        raise _fail(f"LLM call failed: {exc}") from exc
    return AskResponse(answer=text.strip(), provider=provider)


@app.post("/session/log", response_model=LogResponse)
async def session_log(
    req: LogRequest,
    user_id: UUID = Depends(get_user_id),
    db: AsyncSession = Depends(get_session),
) -> LogResponse:
    result = await log_session(
        user_id,
        db,
        date_=date.today(),
        type_=req.type,
        chapter=req.chapter or "?",
        concept=req.topic or "?",
        quiz_score=req.quiz_score or "—",
        exercise_verdict=req.exercise_verdict or "pass",
        apply_summary=req.apply_summary,
        angle=req.angle,
        feeling=req.feeling,
        exercise_text=req.exercise_text or "(no exercise text)",
        code=req.code,
    )
    return LogResponse(
        ok=True,
        session_id=result["session_id"],
        exercise_id=result["exercise_id"],
    )


# ---------------- Push notifications ----------------

class PushKeys(BaseModel):
    p256dh: str
    auth: str


class PushSubscribeRequest(BaseModel):
    endpoint: str
    keys: PushKeys


class PushUnsubscribeRequest(BaseModel):
    endpoint: str


async def require_cron_secret(
    authorization: str = Header(..., alias="Authorization"),
) -> None:
    """Auth for the daily cron — separate from the X-User-Id browser flow."""
    secret = os.environ.get("CRON_SECRET", "")
    if not secret or authorization != f"Bearer {secret}":
        raise HTTPException(status_code=401, detail="invalid cron auth")


@app.post("/push/subscribe")
async def push_subscribe(
    req: PushSubscribeRequest,
    user_id: UUID = Depends(get_user_id),
    db: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    """Store (or refresh) this browser's push subscription for this user."""
    stmt = (
        insert(PushSubscription)
        .values(
            user_id=user_id,
            endpoint=req.endpoint,
            p256dh=req.keys.p256dh,
            auth=req.keys.auth,
        )
        .on_conflict_do_update(
            index_elements=["endpoint"],
            set_={
                "user_id": user_id,
                "p256dh": req.keys.p256dh,
                "auth": req.keys.auth,
            },
        )
    )
    await db.execute(stmt)
    await db.commit()
    return {"ok": True}


@app.post("/push/unsubscribe")
async def push_unsubscribe(
    req: PushUnsubscribeRequest,
    user_id: UUID = Depends(get_user_id),
    db: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    await db.execute(
        delete(PushSubscription).where(
            PushSubscription.user_id == user_id,
            PushSubscription.endpoint == req.endpoint,
        )
    )
    await db.commit()
    return {"ok": True}


async def _send_to_subs(
    subs: list[PushSubscription],
    db: AsyncSession,
    title: str,
    body: str,
) -> dict[str, int]:
    """Push `title`/`body` to each subscription. Collects expired (410)
    subscriptions and deletes them in one batch at the end."""
    sent = 0
    expired_ids: list[UUID] = []
    other_failures: list[str] = []
    for s in subs:
        sub = Subscription(endpoint=s.endpoint, p256dh=s.p256dh, auth=s.auth)
        try:
            await asyncio.to_thread(send_push, sub, title, body, "/")
            sent += 1
        except PushExpired as exc:
            expired_ids.append(s.id)
            print(f"[push] expired sub {s.id}: {exc}", flush=True)
        except PushConfigError:
            # Misconfiguration — fail the whole run so the cron logs it loudly
            raise
        except Exception as exc:
            # Log instead of silent-fail so we can see real failures (VAPID
            # signature issues, network errors, etc.)
            other_failures.append(f"{type(exc).__name__}: {exc}")
            print(f"[push] send failed sub {s.id}: {type(exc).__name__}: {exc}", flush=True)

    print(
        f"[push] result: subs={len(subs)} sent={sent} "
        f"expired={len(expired_ids)} other_failures={len(other_failures)}",
        flush=True,
    )

    if expired_ids:
        await db.execute(
            delete(PushSubscription).where(PushSubscription.id.in_(expired_ids))
        )
        await db.commit()

    return {"sent": sent, "expired_removed": len(expired_ids)}


@app.post("/push/send-daily")
async def push_send_daily(
    db: AsyncSession = Depends(get_session),
    _: None = Depends(require_cron_secret),
) -> dict[str, int]:
    """Cron entrypoint — push to every subscribed user who has NOT logged a
    session today. Date check uses server-local (UTC) `date.today()`; late
    ET-evening sessions can land on the next UTC date, which would cause a
    spurious reminder the morning after. Acceptable for v1; see plan.

    Uses a LEFT JOIN + IS NULL rather than NOT EXISTS — the latter version
    silently returned no rows under SQLAlchemy 2.0 because the correlated
    subquery wasn't matching the outer push_subscriptions row in practice."""
    today = date.today()
    stmt = (
        select(PushSubscription)
        .outerjoin(
            SessionRow,
            and_(
                SessionRow.user_id == PushSubscription.user_id,
                SessionRow.date == today,
            ),
        )
        .where(SessionRow.id.is_(None))
    )
    subs = list((await db.execute(stmt)).scalars().all())
    return await _send_to_subs(
        subs, db, "PySynth", "Time for today's Python session."
    )


