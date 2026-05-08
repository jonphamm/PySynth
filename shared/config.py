"""Filesystem paths, env loading, and small text helpers."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

WORKSPACE = Path(__file__).resolve().parent.parent
RECIPE_PATH = WORKSPACE / "Workflows" / "python-tutor-daily.md"
PLAN_PATH = WORKSPACE / "Resources" / "python-learning-plan.md"
EXERCISES_DIR = WORKSPACE / "Output" / "exercises"

CANONICAL_PROGRESS_PATH = WORKSPACE / "Output" / "progress.md"
PYSYNTH_PROGRESS_PATH = WORKSPACE / "Output" / "progress-pysynth.md"

GEMINI_MODEL = "gemini-2.5-flash"
GROQ_MODEL = "llama-3.3-70b-versatile"
CEREBRAS_MODEL = "qwen-3-235b-a22b-instruct-2507"


def progress_path() -> Path:
    """Return the progress log path, honouring the PYSYNTH_DEV env flag.

    Backend sets PYSYNTH_DEV=1 during Stage 4.1 so PySynth sessions write to
    `Output/progress-pysynth.md` and don't clobber Streamlit's canonical log.
    Streamlit code reads CANONICAL_PROGRESS_PATH directly and is unaffected.
    """
    if os.environ.get("PYSYNTH_DEV"):
        return PYSYNTH_PROGRESS_PATH
    return CANONICAL_PROGRESS_PATH


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""
