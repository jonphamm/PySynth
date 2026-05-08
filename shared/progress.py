"""Progress log + exercise file IO. Angle rotation logic."""

import re
from pathlib import Path

from .config import EXERCISES_DIR, CANONICAL_PROGRESS_PATH, load_text, progress_path

ANGLES = {
    "A": "Sysadmin / day job (email-marketing ops, AD, log parsing, CSV diffs, vendor APIs)",
    "B": "Cybersecurity (audit scripts, security flags, log analysis, port checks, IOC parsing)",
    "C": "AI agents (Claude API clients, prompt templates, message dicts, structured output)",
}


def _daily_rows(text: str) -> list[str]:
    rows = [line for line in text.splitlines() if line.startswith("| 2026-")]
    return [r for r in rows if "Daily" in r.split("|")[2]]


def pick_next_angle() -> str:
    """Pick A/B/C based on the last 3 Daily rows in the active progress log.

    "Active" = canonical for Streamlit, dev log for backend (when PYSYNTH_DEV is
    set). Both apps consult the same selection rule but against their own log.
    """
    text = load_text(progress_path())
    last_3 = _daily_rows(text)[-3:]
    used = []
    for row in last_3:
        m = re.search(r"\(Angle\s+([ABC])\)", row, re.IGNORECASE)
        if m:
            used.append(m.group(1).upper())
    for candidate in ["A", "B", "C"]:
        if candidate not in used:
            return candidate
    return used[0] if used else "A"


def get_current_position() -> str:
    """Snapshot of recent sessions + learning plan, embedded in the system prompt."""
    from .config import PLAN_PATH

    progress = load_text(progress_path())
    plan = load_text(PLAN_PATH)
    rows = [line for line in progress.splitlines() if line.startswith("| 2026-")]
    last_rows = "\n".join(rows[-5:]) if rows else "(no sessions yet)"
    return f"Recent sessions (last 5):\n{last_rows}\n\nLearning plan:\n{plan}"


def write_exercise_file(date_str: str, exercise_text: str) -> Path:
    EXERCISES_DIR.mkdir(parents=True, exist_ok=True)
    path = EXERCISES_DIR / f"{date_str}.py"
    safe_text = exercise_text.replace('"""', "'''")
    content = (
        f'"""\n{safe_text.strip()}\n"""\n\n'
        f"# ---- your solution will be appended here after review ----\n"
    )
    path.write_text(content, encoding="utf-8")
    return path


def append_solution(path: Path, code: str) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(f"\n{code}\n")


def append_progress_row(row: str, *, target: Path | None = None) -> Path:
    """Append a row to the progress log. Defaults to the active log per env.

    Streamlit calls this without `target`, hitting the canonical log via
    `progress_path()`. Backend can override to write directly to a specific
    path for testing.
    """
    dest = target if target is not None else progress_path()
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("a", encoding="utf-8") as f:
        f.write(row)
    return dest


# Streamlit imports this constant directly so it always hits the canonical log
# regardless of PYSYNTH_DEV.
PROGRESS_PATH = CANONICAL_PROGRESS_PATH
