"""One-time importer: filesystem progress.md + exercise .py files -> Postgres.

Idempotent: re-running is a no-op once the dev user row exists. Use this
once after bringing up a fresh Neon branch so your historical sessions
(Ch 1-5 etc.) are visible in the new SQL-backed app.

Usage from `c:\\dev\\pysynth`:
    python -m backend.migrations.import_legacy
"""

from __future__ import annotations

import asyncio
import re
import sys
from datetime import date as Date
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from backend.db import DEV_USER_ID, Exercise, Session as SessionRow, User, get_engine, get_sessionmaker
from shared.config import WORKSPACE


PROGRESS_PATH = WORKSPACE / "Output" / "progress.md"
EXERCISES_DIR = WORKSPACE / "Output" / "exercises"

EXERCISE_SPLIT_MARKER = "# ---- your solution will be appended here after review ----"
ANGLE_REGEX = re.compile(r"\(Angle\s+([ABC])\)", re.IGNORECASE)


def _split_row(line: str) -> list[str]:
    """Split a markdown table row into trimmed cells, dropping the empty
    pre-leading-pipe and post-trailing-pipe slots."""
    cells = [c.strip() for c in line.split("|")]
    if cells and cells[0] == "":
        cells = cells[1:]
    if cells and cells[-1] == "":
        cells = cells[:-1]
    return cells


def _parse_exercise_file(path: Path) -> tuple[str, str]:
    """Return (exercise_text, code). The on-disk format is::

        \"\"\"
        <exercise prompt>
        \"\"\"

        # ---- your solution will be appended here after review ----

        <code, optional>

    Tolerates missing prefix/suffix gracefully."""
    if not path.exists():
        return ("", "")
    raw = path.read_text(encoding="utf-8")
    if EXERCISE_SPLIT_MARKER in raw:
        prefix, code = raw.split(EXERCISE_SPLIT_MARKER, 1)
        code = code.strip("\n").rstrip()
    else:
        prefix, code = raw, ""
    # Strip the surrounding triple-quoted docstring from prefix
    prefix = prefix.strip()
    if prefix.startswith('"""'):
        prefix = prefix[3:]
    # Find the closing """ that ends the docstring (anywhere in the remainder)
    closing = prefix.find('"""')
    if closing != -1:
        prefix = prefix[:closing]
    return (prefix.strip(), code.strip())


def _parse_progress_rows(text: str) -> list[dict]:
    """Yield one dict per Daily / Daily (extra) row in the progress markdown."""
    rows: list[dict] = []
    for line in text.splitlines():
        if not line.startswith("| 2026-"):
            continue
        cells = _split_row(line)
        # Expected cells after split:
        # [date, type, chapter, concept, quiz_score, exercise_verdict,
        #  apply_summary, feeling]
        if len(cells) < 5 or "Daily" not in cells[1]:
            continue
        # Pad to 8 in case feeling cell was empty (split('|') keeps it as '')
        while len(cells) < 8:
            cells.append("")
        date_str, type_, chapter, concept, quiz_score, verdict, apply_summary, feeling = cells[:8]

        # Extract Angle X from the apply_summary, then strip the suffix so the
        # DB stores the clean text. pick_next_angle reads from the angle
        # column directly, not by re-parsing the summary.
        m = ANGLE_REGEX.search(apply_summary)
        angle = m.group(1).upper() if m else "A"
        clean_summary = ANGLE_REGEX.sub("", apply_summary).rstrip(" ,").strip()

        rows.append(
            {
                "date": Date.fromisoformat(date_str),
                "type": type_,
                "chapter": chapter,
                "concept": concept,
                "quiz_score": quiz_score or "—",
                "exercise_verdict": verdict or "pass",
                "apply_summary": clean_summary,
                "angle": angle,
                "feeling": feeling,
            }
        )
    return rows


async def main() -> None:
    if not PROGRESS_PATH.exists():
        print(f"No legacy progress file at {PROGRESS_PATH} — nothing to import.")
        return

    SessionMaker = get_sessionmaker()
    async with SessionMaker() as db:
        # Idempotency gate: bail early if the dev user already exists.
        existing = await db.execute(select(User).where(User.id == DEV_USER_ID))
        if existing.scalar_one_or_none() is not None:
            print(f"Dev user {DEV_USER_ID} already exists — skipping import.")
            return

        # Insert the dev user. ON CONFLICT DO NOTHING in case of a race.
        stmt = insert(User).values(id=DEV_USER_ID).on_conflict_do_nothing(index_elements=["id"])
        await db.execute(stmt)

        rows = _parse_progress_rows(PROGRESS_PATH.read_text(encoding="utf-8"))
        if not rows:
            print(f"No Daily rows found in {PROGRESS_PATH}.")
            await db.commit()
            return

        for row in rows:
            session_row = SessionRow(
                user_id=DEV_USER_ID,
                date=row["date"],
                type=row["type"],
                chapter=row["chapter"],
                concept=row["concept"],
                quiz_score=row["quiz_score"],
                exercise_verdict=row["exercise_verdict"],
                apply_summary=row["apply_summary"],
                angle=row["angle"],
                feeling=row["feeling"],
            )
            db.add(session_row)
            await db.flush()

            exercise_path = EXERCISES_DIR / f"{row['date'].isoformat()}.py"
            exercise_text, code = _parse_exercise_file(exercise_path)
            db.add(
                Exercise(
                    session_id=session_row.id,
                    exercise_text=exercise_text,
                    code=code,
                )
            )

        await db.commit()
        print(f"Imported {len(rows)} sessions under dev user {DEV_USER_ID}.")

    engine = get_engine()
    await engine.dispose()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()) or 0)
