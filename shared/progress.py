"""Progress + exercise persistence. Async SQLAlchemy against Postgres.

Phase 6a port of the former filesystem implementation. Every function reads
or writes rows scoped by `user_id`. The static learning plan still lives on
disk (`PLAN_PATH`) — only user-generated data moved to the DB."""

from __future__ import annotations

import re
from datetime import date as Date
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import Exercise, Session as SessionRow

from .config import PLAN_PATH, load_text


ANGLES = {
    "A": "Sysadmin / day job (email-marketing ops, AD, log parsing, CSV diffs, vendor APIs)",
    "B": "Cybersecurity (audit scripts, security flags, log analysis, port checks, IOC parsing)",
    "C": "AI agents (Claude API clients, prompt templates, message dicts, structured output)",
}


def _chapter_sort_key(chapter: str) -> tuple[int, int]:
    """Sort chapters numerically by (part, chapter). Tolerates 'Ch' or 'Chapter'."""
    m = re.search(r"Part\s+(\d+)\s*/\s*Ch(?:apter)?\s+(\d+)", chapter, re.IGNORECASE)
    return (int(m.group(1)), int(m.group(2))) if m else (99, 99)


def _format_row(s: SessionRow) -> str:
    """Render a session as the pipe-delimited markdown row the LLM is used to seeing.

    The prompt context (get_current_position) has historically embedded recent
    rows in this exact shape, and several prompts in `shared/prompts.py` reason
    about Daily / Daily (extra) row prefixes. Keep the format stable so the LLM
    behavior doesn't shift."""
    angle_suffix = f" (Angle {s.angle})" if s.angle else ""
    return (
        f"| {s.date.isoformat()} | {s.type} | {s.chapter} | {s.concept} | "
        f"{s.quiz_score} | {s.exercise_verdict} | "
        f"{s.apply_summary}{angle_suffix} | {s.feeling} |"
    )


async def pick_next_angle(user_id: UUID, db: AsyncSession) -> str:
    """Pick A/B/C based on the user's last 3 Daily / Daily (extra) sessions.

    Reads the `angle` column directly — much cleaner than the old regex-extract
    from apply_summary. Returns the first letter not in the recent set, or
    falls back to the *least* recently used letter (oldest in the window) if
    all three appeared."""
    stmt = (
        select(SessionRow.angle)
        .where(SessionRow.user_id == user_id, SessionRow.type.like("Daily%"))
        .order_by(desc(SessionRow.date), desc(SessionRow.created_at))
        .limit(3)
    )
    result = await db.execute(stmt)
    used = [row[0].upper() for row in result if row[0]]  # newest -> oldest
    for candidate in ("A", "B", "C"):
        if candidate not in used:
            return candidate
    return used[-1] if used else "A"  # oldest of the last 3 = least recently used


async def list_done_chapters(user_id: UUID, db: AsyncSession) -> list[dict]:
    """Return distinct chapters the user has done a Daily / Daily (extra) on,
    sorted by (part, chapter). Each entry: {chapter, last_date}."""
    stmt = (
        select(SessionRow.chapter, func.max(SessionRow.date).label("last_date"))
        .where(SessionRow.user_id == user_id, SessionRow.type.like("Daily%"))
        .group_by(SessionRow.chapter)
    )
    result = await db.execute(stmt)
    rows = [
        {"chapter": chapter, "last_date": last_date.isoformat()}
        for chapter, last_date in result
        if chapter
    ]
    return sorted(rows, key=lambda r: _chapter_sort_key(r["chapter"]))


async def find_today_daily_row(user_id: UUID, db: AsyncSession) -> dict | None:
    """Return `{'chapter': str, 'concept': str}` if today already has a Daily
    row for this user, else None. Picks the most recent if multiple."""
    stmt = (
        select(SessionRow.chapter, SessionRow.concept)
        .where(
            SessionRow.user_id == user_id,
            SessionRow.date == Date.today(),
            SessionRow.type.like("Daily%"),
        )
        .order_by(desc(SessionRow.created_at))
        .limit(1)
    )
    result = await db.execute(stmt)
    row = result.first()
    if row is None:
        return None
    return {"chapter": row[0], "concept": row[1]}


async def get_current_position(user_id: UUID, db: AsyncSession) -> str:
    """Snapshot of recent sessions + learning plan, embedded in the system prompt.

    Returns the last 5 sessions formatted as pipe-delimited rows (same shape
    as the historical `Output/progress.md` table) followed by the full static
    learning plan text from disk."""
    stmt = (
        select(SessionRow)
        .where(SessionRow.user_id == user_id)
        .order_by(desc(SessionRow.date), desc(SessionRow.created_at))
        .limit(5)
    )
    result = await db.execute(stmt)
    recent = list(result.scalars())
    recent.reverse()  # oldest-first in the rendered context, matching the old log
    last_rows = "\n".join(_format_row(s) for s in recent) if recent else "(no sessions yet)"
    plan = load_text(PLAN_PATH)
    return f"Recent sessions (last 5):\n{last_rows}\n\nLearning plan:\n{plan}"


async def log_session(
    user_id: UUID,
    db: AsyncSession,
    *,
    date_: Date,
    type_: str,
    chapter: str,
    concept: str,
    quiz_score: str,
    exercise_verdict: str,
    apply_summary: str,
    angle: str,
    feeling: str,
    exercise_text: str,
    code: str,
) -> dict[str, UUID]:
    """Insert one Session row and its matching Exercise row in a single
    transaction. Returns the new IDs for the response."""
    session_row = SessionRow(
        user_id=user_id,
        date=date_,
        type=type_,
        chapter=chapter,
        concept=concept,
        quiz_score=quiz_score,
        exercise_verdict=exercise_verdict,
        apply_summary=apply_summary,
        angle=angle,
        feeling=feeling,
    )
    db.add(session_row)
    await db.flush()  # populates session_row.id without committing

    exercise_row = Exercise(
        session_id=session_row.id,
        exercise_text=exercise_text,
        code=code,
    )
    db.add(exercise_row)
    await db.commit()

    return {"session_id": session_row.id, "exercise_id": exercise_row.id}
