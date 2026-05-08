"""MOOC chapter map, next-chapter logic, daily quote pool, chapter formatting."""

import random
import re
from datetime import date


QUOTES = [
    ("The expert in anything was once a beginner.", "Helen Hayes"),
    ("Programs must be written for people to read, and only incidentally for machines to execute.", "Harold Abelson"),
    ("First, solve the problem. Then, write the code.", "John Johnson"),
    ("Code is read more often than it is written.", "Guido van Rossum"),
    ("It always seems impossible until it's done.", "Nelson Mandela"),
    ("Make it work, make it right, make it fast.", "Kent Beck"),
    ("Simple is better than complex. Complex is better than complicated.", "The Zen of Python"),
    ("Talk is cheap. Show me the code.", "Linus Torvalds"),
    ("Computers are good at following instructions, but not at reading your mind.", "Donald Knuth"),
    ("The only way to learn a new programming language is by writing programs in it.", "Brian Kernighan"),
    ("The most damaging phrase in the language is 'we've always done it this way.'", "Grace Hopper"),
    ("Security is a process, not a product.", "Bruce Schneier"),
    ("There is no patch for human stupidity.", "Kevin Mitnick"),
    ("The future is already here — it's just not very evenly distributed.", "William Gibson"),
    ("Programming isn't about what you know; it's about what you can figure out.", "Chris Pine"),
    ("Quality is not an act, it is a habit.", "Aristotle"),
]


# Known MOOC.fi 2026 chapter titles. Extend as new chapters are reached;
# missing entries render as "Part X: Chapter Y" without a title.
MOOC_CHAPTERS = {
    (1, 1): "Getting Started",
    (1, 2): "Information from the User",
    (1, 3): "More about Variables",
    (1, 4): "Arithmetic Operations",
}

# Last chapter number per part. Empty until a part's bounds are confirmed
# from progress.md reality.
PART_LAST_CHAPTER: dict[int, int] = {}


def format_chapter(raw: str) -> str:
    """Convert 'Part X / Ch Y — Title' to 'Part X: Chapter Y - Title'."""
    if not raw:
        return raw
    out = raw.replace(" / Ch ", ": Chapter ")
    out = out.replace(" / Chapter ", ": Chapter ")
    out = out.replace(" — ", " - ")
    return out


def next_chapter(last_raw: str) -> str:
    """Given the most recent chapter cell from progress.md, render today's
    'Part X: Chapter Y - Title' for the landing's Up next slot."""
    bootstrap = "Part 1: Chapter 1 - Getting Started"
    if not last_raw or last_raw == "—":
        return bootstrap
    m = re.search(r"Part\s+(\d+)\s*/\s*Ch(?:apter)?\s+(\d+)", last_raw, re.IGNORECASE)
    if not m:
        return bootstrap
    part, ch = int(m.group(1)), int(m.group(2))
    next_part, next_ch = part, ch + 1
    last_in_part = PART_LAST_CHAPTER.get(part)
    if last_in_part is not None and next_ch > last_in_part:
        next_part, next_ch = part + 1, 1
    title = MOOC_CHAPTERS.get((next_part, next_ch))
    if title:
        return f"Part {next_part}: Chapter {next_ch} - {title}"
    return f"Part {next_part}: Chapter {next_ch}"


def quote_of_the_day() -> tuple[str, str]:
    """Return (text, attribution) — deterministic per calendar day."""
    rng = random.Random(date.today().isoformat())
    return rng.choice(QUOTES)
