"""FastAPI backend serving the PySynth Next.js frontend.

Reuses everything in `shared/` (chapters, prompts, LLM fan-out, progress
log IO) so tutoring logic lives in exactly one place.

Run (from `C:\\dev\\pysynth`):
    pip install -r backend/requirements.txt
    uvicorn backend.app:app --reload --port 8000
"""

from datetime import date
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from shared.llm import call_llm_json
from shared.progress import (
    append_progress_row,
    append_solution,
    find_today_daily_row,
    list_done_chapters,
    pick_next_angle,
    write_exercise_file,
)
from shared.prompts import (
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    exercise_path: str
    progress_path: str


# ---------------- Helpers ----------------

def _fail(detail: str, status: int = 502) -> HTTPException:
    return HTTPException(status_code=status, detail=detail)


def _safe_score(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


# ---------------- Endpoints ----------------

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/chapters/done")
def chapters_done() -> dict[str, Any]:
    return {"chapters": list_done_chapters()}


@app.post("/session/start")
def session_start(req: StartRequest = StartRequest()) -> dict[str, Any]:
    if req.pin_to_chapter:
        user_msg = start_user_message(pin_chapter=req.pin_to_chapter)
    else:
        today_row = find_today_daily_row()
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
    try:
        data, _provider = call_llm_json(build_system_prompt(), user_msg)
    except Exception as exc:
        raise _fail(f"LLM call failed: {exc}") from exc
    return {"kind": "session", **validate_session_data(data)}


@app.post("/session/grade", response_model=GradeResponse)
def session_grade(req: GradeRequest) -> GradeResponse:
    user_msg = grade_user_message(req.questions, req.answers, req.picked_indexes)
    try:
        data, _provider = call_llm_json(build_system_prompt(), user_msg)
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
def session_exercise(req: ExerciseRequest) -> ExerciseResponse:
    angle = pick_next_angle()
    user_msg = exercise_user_message(angle)
    try:
        data, _provider = call_llm_json(build_system_prompt(), user_msg)
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
def session_review(req: ReviewRequest) -> ReviewResponse:
    if not req.code.strip():
        raise _fail("code is empty", status=400)
    exercise_text = render_exercise_markdown(req.exercise)
    user_msg = review_user_message(exercise_text, req.code)
    try:
        data, _provider = call_llm_json(build_system_prompt(), user_msg)
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


@app.post("/session/log", response_model=LogResponse)
def session_log(req: LogRequest) -> LogResponse:
    today_str = date.today().isoformat()

    exercise_path = write_exercise_file(today_str, req.exercise_text or "(no exercise text)")
    if req.code.strip():
        append_solution(exercise_path, req.code)

    apply_summary = req.apply_summary[:120] if req.apply_summary else ""
    row = (
        f"| {today_str} | {req.type} | {req.chapter or '?'} | {req.topic or '?'} | "
        f"{req.quiz_score or '—'} | {req.exercise_verdict or 'pass'} | "
        f"{apply_summary} (Angle {req.angle}) | {req.feeling} |\n"
    )
    progress_dest = append_progress_row(row)
    return LogResponse(
        ok=True,
        exercise_path=str(exercise_path),
        progress_path=str(progress_dest),
    )
