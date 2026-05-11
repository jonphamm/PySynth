"""Filesystem paths, env loading, and small text helpers."""

from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

WORKSPACE = Path(__file__).resolve().parent.parent
RECIPE_PATH = WORKSPACE / "Workflows" / "python-tutor-daily.md"
PLAN_PATH = WORKSPACE / "Resources" / "python-learning-plan.md"
EXERCISES_DIR = WORKSPACE / "Output" / "exercises"

CANONICAL_PROGRESS_PATH = WORKSPACE / "Output" / "progress.md"

GEMINI_MODEL = "gemini-2.5-flash"
GROQ_MODEL = "llama-3.3-70b-versatile"
CEREBRAS_MODEL = "qwen-3-235b-a22b-instruct-2507"
OPENROUTER_MODEL = "openai/gpt-oss-120b:free"


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""
