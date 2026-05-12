"""Filesystem paths, env loading, and small text helpers."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

WORKSPACE = Path(__file__).resolve().parent.parent
RECIPE_PATH = WORKSPACE / "Workflows" / "python-tutor-daily.md"
PLAN_PATH = WORKSPACE / "Resources" / "python-learning-plan.md"

GEMINI_MODEL = "gemini-2.5-flash"
GROQ_MODEL = "llama-3.3-70b-versatile"
CEREBRAS_MODEL = "qwen-3-235b-a22b-instruct-2507"
OPENROUTER_MODEL = "qwen/qwen3-next-80b-a3b-instruct:free"


def _normalize_db_url(url: str) -> str:
    """Translate a stock Postgres URL into one the asyncpg driver accepts.

    Neon and most providers hand out `postgresql://...?sslmode=require`.
    SQLAlchemy needs the dialect prefix (`postgresql+asyncpg://`) and asyncpg
    uses `ssl=` instead of `sslmode=`."""
    if not url:
        return url
    if url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]
    return url.replace("sslmode=", "ssl=")


DATABASE_URL = _normalize_db_url(os.environ.get("DATABASE_URL", ""))


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""
