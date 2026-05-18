"""System prompt + user-message builders used by the FastAPI backend."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from .config import RECIPE_PATH, load_text
from .progress import ANGLES, get_current_position


async def build_system_prompt(user_id: UUID, db: AsyncSession) -> str:
    recipe = load_text(RECIPE_PATH)
    state = await get_current_position(user_id, db)
    return f"{recipe}\n\n---\n\n# Current state — read this before generating today's session\n\n{state}\n"


def start_user_message(
    *,
    same_day_intent: str | None = None,
    same_day_chapter: str | None = None,
    same_day_concept: str | None = None,
    pin_chapter: str | None = None,
    auto_pin_chapter: str | None = None,
) -> str:
    """Prompt that asks for today's concept review + 4 quiz questions as JSON.

    Four optional override modes:
    - `pin_chapter`: explicit chapter pin — user clicked a past chapter in
      the sidebar. Generates a session on that exact chapter. Takes
      precedence over `same_day_intent` and `auto_pin_chapter` (callers
      should not set both).
    - `same_day_intent` + chapter/concept: same-day review or advance,
      triggered by the SameDayModal when today's session is already logged.
      Takes precedence over `auto_pin_chapter`.
    - `auto_pin_chapter`: server-side deterministic next-chapter pin for
      the default daily-advance flow. Computed by `compute_next_chapter()`
      in shared.progress from the user's done-chapters list against the
      learning plan. Applies only in the default branch (no pin, no
      same-day intent). When provided, the LLM is locked to that exact
      chapter label and may only pick the granular concept. When None,
      the default branch falls back to the LLM picking from the plan
      (intentional fallback for users past Part 1).

    With no overrides, the prompt asks the LLM to follow the recipe's normal
    next-uncovered-chapter logic.
    """
    override = ""
    if pin_chapter:
        override = (
            "OVERRIDE — explicit chapter pin (review of a past chapter):\n"
            f'The user has explicitly chosen to revisit the chapter "{pin_chapter}".\n'
            "Generate today's session on THIS chapter regardless of recent progress.md\n"
            "rows or the learning plan's auto-advance flow. Treat it as a review of\n"
            "already-covered material: scan the recent rows for prior takes on this\n"
            "chapter and either regenerate the same sub-concept with fresh examples\n"
            "and questions, or pick a complementary sub-concept WITHIN the same\n"
            "chapter. Do NOT advance to a different chapter, and do NOT drift to an\n"
            "unrelated sub-concept.\n\n"
            "---\n\n"
        )
    elif same_day_intent and same_day_chapter and same_day_concept:
        if same_day_intent == "review":
            override = (
                "OVERRIDE — same-day review request:\n"
                f'The user has already completed today\'s session on chapter "{same_day_chapter}" /\n'
                f'concept "{same_day_concept}". They explicitly chose to REVIEW the same chapter from\n'
                "a different angle. Generate the session for the SAME chapter AND the SAME\n"
                "granular concept. Use a different worked_example_code, different syntax_forms\n"
                "examples, and entirely new questions. Do NOT advance to a different chapter or\n"
                "sub-concept.\n\n"
                "---\n\n"
            )
        elif same_day_intent == "advance":
            override = (
                "OVERRIDE — same-day advance request:\n"
                f'The user has already completed today\'s session on chapter "{same_day_chapter}" /\n'
                f'concept "{same_day_concept}", but has explicitly chosen to ADVANCE past it and\n'
                "start the NEXT chapter today (an extra session). Treat today's completed row\n"
                "as part of the \"already covered\" history. Do NOT repeat that chapter or\n"
                "concept. Pick the next uncovered chapter from the learning plan — typically\n"
                "the chapter immediately after the one named above. The recipe's \"stop and\n"
                "ask\" rule for same-day sessions has already been resolved by the user's choice;\n"
                "proceed with generating the next chapter's session.\n\n"
                "---\n\n"
            )
    elif auto_pin_chapter:
        override = (
            "OVERRIDE — server-computed next chapter (daily advance):\n"
            "The user is starting today's session with no explicit review choice.\n"
            "The next chapter has been determined server-side from the user's\n"
            "done-chapters list and the learning plan. Set `topic.chapter` to EXACTLY:\n"
            f'    "{auto_pin_chapter}"\n'
            "Use that string verbatim — same Part number, same Chapter number, same\n"
            "title, same punctuation. You MAY pick the granular `concept` within this\n"
            "chapter as usual, but you MUST NOT change the chapter, MUST NOT drift to\n"
            "a different chapter number, and MUST NOT improvise a different title.\n"
            "Do NOT repeat the most recent chapter, even if its quiz score was low or\n"
            "its exercise verdict was 'needs fix' or 'close'. A single weak session\n"
            "does not trigger an auto-review day. The recipe's \"interleave a review\n"
            "day for weakness every 3-4 sessions\" rule is paused here -- review days\n"
            "are user-initiated only:\n"
            "  - same-day re-runs come through the SameDayModal (different override),\n"
            "  - past-chapter revisits come through the past-chapters sidebar pin.\n\n"
            "---\n\n"
        )
    else:
        override = (
            "DEFAULT MODE — daily advance:\n"
            "The user is starting today's session with no explicit review choice.\n"
            "Pick the NEXT uncovered chapter from the learning plan — the chapter\n"
            "after the most recent Daily / Daily (extra) row in progress.md. Do NOT\n"
            "repeat the most recent chapter, even if its quiz score was low or its\n"
            "exercise verdict was 'needs fix' or 'close'. A single weak session does\n"
            "not trigger an auto-review day. The recipe's \"interleave a review day\n"
            "for weakness every 3-4 sessions\" rule is paused here -- review days are\n"
            "user-initiated only:\n"
            "  - same-day re-runs come through the SameDayModal (different override),\n"
            "  - past-chapter revisits come through the past-chapters sidebar pin.\n"
            "Treat the user as having completed the most recent chapter regardless of\n"
            "its score, and advance one chapter further in the learning plan.\n\n"
            "---\n\n"
        )
    return override + (
        "Generate today's session content as a JSON object with EXACTLY this shape "
        "(no markdown, no extra commentary — just the JSON):\n\n"
        "{\n"
        '  "topic": {\n'
        '    "chapter": "Part X / Chapter Y — Chapter Title",\n'
        '    "concept": "granular concept name, e.g. arithmetic operators"\n'
        "  },\n"
        '  "concept_review": {\n'
        '    "definition": "2–4 sentence plain-English definition; name key terminology (operators, keywords, return types).",\n'
        '    "how_it_works": [\n'
        '      "4–6 short bullets on what Python does at runtime — evaluation order, types involved, side effects, scope. Each bullet ≤ 18 words."\n'
        "    ],\n"
        '    "syntax_forms": [\n'
        '      {"label": "name of form", "code": "1–3 line snippet"}\n'
        "    ],\n"
        '    "worked_example_code": "5–12 lines of Python, sysadmin/security flavored where natural; inline comments only when WHY is non-obvious",\n'
        '    "worked_example_walkthrough": [\n'
        '      "Numbered or bulleted trace: what each non-trivial line does, what variables hold, what gets printed."\n'
        "    ],\n"
        '    "common_patterns": [\n'
        '      "2–4 bullets showing real-world shapes the user will encounter."\n'
        "    ],\n"
        '    "analogy": "1–2 sentences relating the concept to a sysadmin / security scenario",\n'
        '    "gotcha": "1–2 sentences on a common mistake — and how to avoid it",\n'
        '    "when_to_use": "1–2 sentences contrasting this concept with the alternatives. This is the bridge to the stretch question."\n'
        "  },\n"
        '  "questions": [\n'
        '    {"type": "mc", "subtype": "multiple_choice", "text": "<question>",\n'
        '     "options": ["<opt0>", "<opt1>", "<opt2>", "<opt3>"], "correct_index": <0-3>},\n'
        '    {"type": "mc", "subtype": "what_does_this_print", "text": "What does this print?",\n'
        '     "code": "<3–6 line python snippet>",\n'
        '     "options": ["<opt0>", "<opt1>", "<opt2>", "<opt3>"], "correct_index": <0-3>},\n'
        '    {"type": "free", "subtype": "short_answer", "text": "<question needing a one-sentence answer>"},\n'
        '    {"type": "free", "subtype": "stretch_conceptual", "text": "<why/when/which question for Parts 1–2 calibration>"}\n'
        "  ]\n"
        "}\n\n"
        "Rules:\n"
        "- Write the chapter cell exactly as \"Part X / Chapter Y — Title\" — always spell out \"Chapter\", never abbreviate to \"Ch\".\n"
        "- The concept_review must be substantive enough that the user can answer all 4 questions and write the coding exercise from it alone. Aim for ~450–700 words across all review fields combined.\n"
        "- `how_it_works`, `syntax_forms`, `worked_example_walkthrough`, and `common_patterns` are REQUIRED arrays — never null, never strings.\n"
        "- `syntax_forms` typically has 2–4 entries showing the different ways the concept can appear in code.\n"
        "- Exactly 4 questions per the recipe's anchor + stretch rule.\n"
        "- Option strings should be the answer text only (e.g. \"//\" or \"7\"), NOT prefixed with a/b/c/d.\n"
        "- correct_index is a 0-based integer.\n"
        "- All code values (worked_example_code and each syntax_forms.code) are raw code bodies — do NOT wrap them in ``` fences.\n"
        "- Code values MUST use raw ASCII Python operators ONLY: `>=` not `≥`, `<=` not `≤`, `!=` not `≠`, `*` not `×`, `/` not `÷`, `-` not `−` (or any other dash). Python's parser rejects Unicode math symbols — students will copy these examples and hit SyntaxError. This applies to worked_example_code, every syntax_forms.code, and any code embedded in quiz questions.\n"
        "- Do NOT include the coding exercise or apply-at-work in this response — those come later.\n"
        "\n"
        "Inline-markdown formatting — REQUIRED, the UI depends on this for visual hierarchy:\n"
        "\n"
        "1) **Wrap every Python identifier in inline code.** Anywhere you mention a function name, keyword, operator, variable, literal, type, or short expression — in any field — wrap it in single backticks: `` `print()` ``, `` `#` ``, `` `name` ``, `` `=` ``, `` `int` ``, `` `True` ``, `` `5 + 3` ``. Do NOT leave bare identifiers like `print` or `total_seconds` without backticks. Code chips render as cyan-tinted IDE-style pills; their density is what gives the page its IDE feel.\n"
        "\n"
        "2) **Every bullet in `how_it_works`, `worked_example_walkthrough`, and `common_patterns` MUST start with a bold leading phrase that names the subtopic.** Two patterns:\n"
        "   - When the subtopic IS a Python identifier, NEST inline code INSIDE the bold (markdown nesting is bold-outside-code-inside): `` **`print()`:** evaluates the expression and outputs the result `` — this renders as a bright-white code chip with cyan glow, the page's strongest visual element.\n"
        "   - When the subtopic is a plain phrase, use bold without code: `**Operator precedence:** ** binds tighter than * and /.`\n"
        "   Never write `` `**print()**` `` (code wrapping bold) — markdown won't render that. Always `` **`print()`** `` (bold wrapping code).\n"
        "\n"
        "3) **When the chapter covers two or more sub-concepts** (e.g. `print()` AND comments), assign at least one bullet per sub-concept and lead each with the corresponding bold-code phrase, so the UI renders visual section breaks within the bullet list.\n"
        "\n"
        "4) `definition`, `analogy`, `gotcha`, `when_to_use`, and `questions[].text` are short paragraphs — same rule (1) applies (every identifier in backticks). They MAY also use `**bold**` to emphasize a key term, but bold is optional in paragraphs; mandatory in bullet leading phrases.\n"
        "\n"
        "Concrete example bullet (target this shape):\n"
        "    `` **`print()`:** When called, Python evaluates each argument left-to-right, converts it to a string with `str()`, joins them with the `sep` separator (default `' '`), and writes the result to `stdout` followed by `end` (default `'\\n'`). ``"
    )


def grade_user_message(
    questions: list[dict],
    answers: list[str],
    picked_indexes: list[int | None],
) -> str:
    """Prompt that grades the 4 quiz answers. Returns a JSON-wrapped response
    `{"grade_markdown": "...", "score_correct": int, "score_total": int}`.
    """
    padded = list(answers) + [""] * (4 - len(answers))
    padded = padded[:4]
    qa_lines = []
    for i, q in enumerate(questions):
        qa_lines.append(f"Q{i + 1} ({q.get('subtype') or q['type']}): {q.get('text', '')}")
        if q.get("code"):
            qa_lines.append(f"```python\n{q['code']}\n```")
        if q.get("options"):
            for j, opt in enumerate(q["options"]):
                marker = " ← correct" if j == q.get("correct_index") else ""
                qa_lines.append(f"  {chr(97 + j)}) {opt}{marker}")
        user_pick = padded[i] if i < len(padded) else ""
        if q.get("options") and i < len(picked_indexes) and picked_indexes[i] is not None:
            user_pick = f"{chr(97 + picked_indexes[i])}) {user_pick}"
        qa_lines.append(f"User answer: {user_pick}")
        qa_lines.append("")

    markdown_format = (
        "Use this EXACT format with bolded labels:\n\n"
        "**Summary:** [overall score, e.g. '3.5 / 4'] — [1-line takeaway]\n\n"
        "**Q1 — ✓/✗:** [your answer / correct / 1-line why if wrong]\n\n"
        "**Q2 — ✓/✗:** [same format]\n\n"
        "**Q3 — ✓/partial/✗:** [brief assessment]\n\n"
        "**Q4 (stretch) — ✓/partial/✗:** [explain THOROUGHLY — that's where real learning lives]\n\n"
        "Encourage idiomatic improvement; don't be harsh. Total response under 350 words."
    )
    return (
        "Grade the user's quiz answers per the recipe.\n\n"
        "Quiz + answers:\n"
        f"{chr(10).join(qa_lines)}\n"
        "---\n\n"
        "Return a JSON object with EXACTLY this shape (no extra commentary):\n\n"
        "{\n"
        '  "grade_markdown": "<the full graded response, formatted as markdown — see format below>",\n'
        '  "score_correct": <number, e.g. 3 or 3.5>,\n'
        '  "score_total": <integer, the count of questions, typically 4>\n'
        "}\n\n"
        "The grade_markdown field MUST follow this exact shape (the markdown lives inside the JSON string):\n\n"
        + markdown_format
    )


def exercise_user_message(angle: str, *, chapter: str = "", concept: str = "") -> str:
    """Prompt that produces the coding exercise + apply-at-work paragraph (JSON mode).

    When `chapter` and `concept` are both provided, prepends a strong pin override
    so the exercise stays locked to the current session's topic instead of drifting
    to whichever chapter the LLM would infer from progress.md.
    """
    override = ""
    if chapter and concept:
        override = (
            "OVERRIDE — exercise chapter pin (active session):\n"
            f'The user is currently working through chapter "{chapter}" / concept "{concept}"\n'
            "in their active session. This coding exercise MUST be for THAT chapter and\n"
            "THAT concept. Set `exercise.topic` to exactly:\n"
            f'    "{chapter} / {concept}"\n'
            "Do NOT drift to a different chapter or concept regardless of what\n"
            "progress.md, recent rows, or any \"next chapter\" inference would suggest.\n"
            "The task must exercise the pinned concept, not an adjacent one.\n\n"
            "---\n\n"
        )
    return override + (
        "Generate the coding exercise and apply-at-work as a JSON object with EXACTLY this shape "
        "(no markdown, no extra commentary — just the JSON):\n\n"
        "{\n"
        '  "exercise": {\n'
        '    "topic": "chapter / concept",\n'
        '    "task": "1–3 short paragraphs of clear instructions",\n'
        '    "expected_output": "literal expected output, line by line (newlines preserved)",\n'
        '    "constraints": ["bullet 1", "bullet 2", "bullet 3"]\n'
        "  },\n"
        '  "apply_at_work": {\n'
        f'    "angle": "{angle}",\n'
        '    "text": "2–3 sentences with a concrete idea using today\'s concept"\n'
        "  }\n"
        "}\n\n"
        f"The assigned angle is **{angle}**: {ANGLES[angle]}. "
        f"Use ONLY that angle — don't stray into the other angles.\n"
        "Constraints array should have 2–4 short items.\n"
        "\n"
        "Inline-markdown formatting (the UI renders these):\n"
        "- `exercise.task` MAY use `**bold**` to emphasize key requirements and `` `inline code` `` for variable names, function calls, operators, or short expressions (e.g. `` `print()` ``, `` `name` ``, `` `+` ``). Inline code renders as a cyan-tinted code chip.\n"
        "- Each entry in `exercise.constraints` MAY use the same `**bold**` and `` `inline code` `` formatting.\n"
        "- `apply_at_work.text` is a short paragraph — also MAY use `**bold**` and `` `inline code` `` sparingly."
    )


def ask_user_message(
    *,
    question: str,
    chapter: str,
    concept: str,
    stage: str,
    history: list[dict],
) -> str:
    """Prompt for the free-form mentor chat alongside the session.

    `history` is a list of `{"role": "user"|"mentor", "text": "..."}` dicts.
    Caller should pass only the recent turns (last 5 pairs is plenty); we
    interleave them as User: / Mentor: lines so the LLM has context for the
    current question.
    """
    turns: list[str] = []
    for msg in history[-10:]:
        role = msg.get("role")
        text = (msg.get("text") or "").strip()
        if not text:
            continue
        speaker = "User" if role == "user" else "Mentor"
        turns.append(f"{speaker}: {text}")
    convo = "\n\n".join(turns)
    if convo:
        convo = f"Conversation so far:\n\n{convo}\n\n"

    return (
        "TUTOR-CHAT MODE\n"
        "The student is in a free-form chat alongside their daily session, not a graded\n"
        "stage. Answer the most recent question briefly and helpfully.\n\n"
        "CURRENT SESSION CONTEXT\n"
        f'- Chapter: "{chapter or "unknown"}"\n'
        f'- Concept: "{concept or "unknown"}"\n'
        f'- Stage: {stage} (concept | quiz | editor | grade | done)\n\n'
        "RULES\n"
        "- Short answer: 3-6 sentences max unless the user explicitly asks 'explain more'.\n"
        "- Markdown is fine. Inline code in backticks. Fenced ```python blocks for multi-line code.\n"
        "- ASCII operators only (`>=`, `<=`, `!=`, `*`, `/`). No Unicode math symbols.\n"
        "- DO NOT reveal the answer to the current quiz question or solve the current coding exercise. Hint, don't solve.\n"
        "- Off-topic questions (not about Python or this concept): one-line redirect back to the topic.\n"
        "- If the user asks 'how would I use this at work?', vary the angle across sysadmin / cybersecurity / AI agents.\n\n"
        "---\n\n"
        f"{convo}"
        f"User: {question.strip()}\n\n"
        "Mentor:"
    )


def review_user_message(exercise_text: str, code: str) -> str:
    """Prompt that reviews the user's submitted code. Returns a JSON-wrapped
    response `{"review_markdown": "...", "verdict": "pass"|"close"|"miss",
    "reference_solution": "..."}`.
    """
    markdown_format = (
        "Use this EXACT format with bolded labels:\n\n"
        "**Verdict:** ✓ pass / partial / needs fix\n\n"
        "**Correctness:** [does the output match the spec? are constraints met?]\n\n"
        "**Idiomatic improvement:** [ONE concrete improvement — something that actually makes the code better, not stylistic nitpicking]\n\n"
        "**Pattern check:** [if you spot a recurring pattern from past sessions like 'what' comments instead of 'why', flag it; otherwise '—']\n\n"
        "Don't be harsh; encourage idiomatic improvement. Keep response under 250 words."
    )
    return (
        f"Exercise was:\n\n{exercise_text}\n\n"
        f"---\n\nUser's solution:\n```python\n{code}\n```\n\n"
        f"---\n\nReview per the recipe. "
    ) + (
        "Return a JSON object with EXACTLY this shape (no extra commentary):\n\n"
        "{\n"
        '  "review_markdown": "<the full review formatted as markdown — see format below>",\n'
        '  "verdict": "pass" | "close" | "miss",\n'
        '  "reference_solution": "<full clean idiomatic Python solution to the exercise, OR empty string if verdict is pass>"\n'
        "}\n\n"
        '"verdict" maps from the **Verdict:** line: "pass" if ✓, "close" if partial, "miss" if needs fix.\n\n'
        '"reference_solution":\n'
        "- When verdict is `close` or `miss`: provide a complete, runnable solution that uses ONLY the Python features the user has been taught up to and including their current MOOC chapter. Consult the recent sessions + learning plan in the system prompt to determine that chapter. The reference is for direct comparison against the user's submission — if it uses syntax the user hasn't seen yet, the comparison fails its job and creates a false ceiling. When in doubt, use the simpler approach. Repetition and verbosity are fine. **Never reach forward into a feature that hasn't been introduced** — no comprehensions, no f-strings, no slicing, no library imports beyond what the chapter covered, no functions/loops/conditionals unless the chapter unlocked them.\n"
        "- Concrete scope guide for the early chapters (where this matters most):\n"
        "    * **Part 1 Ch 1** (`print()` + comments): only `print(...)` calls, string literals, integer literals, and `#` comments. No variables. No `input()`. No f-strings. No operators.\n"
        "    * **Part 1 Ch 2** (input + type conversion): adds `input(...)`, `int(...)`, `str(...)`, `float(...)`. Still no `if`/`while`/`for`/functions.\n"
        "    * **Part 1 Ch 3** (variables): adds variable assignment. Still no control flow.\n"
        "    * **Part 1 Ch 4** (arithmetic): adds `+ - * / // % **`. Still no control flow.\n"
        "    * **Part 2** (booleans, if/else, while): unlocks `if`/`elif`/`else`/`while`. Still no `for`, no functions.\n"
        "    * **Part 3** (functions, lists, for): unlocks `def`, lists, `for`.\n"
        "    * **Part 4+**: infer from the learning plan and recent sessions.\n"
        "- When verdict is `pass`: return an empty string.\n"
        "- Raw code only — do NOT wrap in markdown ``` fences inside the JSON value. The frontend renders this through a Python syntax highlighter.\n\n"
        "The review_markdown field MUST follow this exact shape (the markdown lives inside the JSON string):\n\n"
        + markdown_format
    )
