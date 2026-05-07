"""
Python Tutor — Stage 2 (2026-05-07, UX revision)

Streamlit web app implementing the full python-tutor-daily recipe as a
multi-stage wizard:
  start → concept+quiz → graded → exercise → graded → apply-at-work → wrap → done

Run:  streamlit run tutor.py
"""

import os
import re
from datetime import date
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def _import_gemini():
    from google import genai
    return genai


def _import_groq():
    from groq import Groq
    return Groq


# ---------------- Config ----------------

WORKSPACE = Path(__file__).parent
RECIPE_PATH = WORKSPACE / "Workflows" / "python-tutor-daily.md"
PROGRESS_PATH = WORKSPACE / "Output" / "progress.md"
PLAN_PATH = WORKSPACE / "Resources" / "python-learning-plan.md"
EXERCISES_DIR = WORKSPACE / "Output" / "exercises"

GEMINI_MODEL = "gemini-2.5-flash"
GROQ_MODEL = "llama-3.3-70b-versatile"

ANGLES = {
    "A": "Sysadmin / day job (email-marketing ops, AD, log parsing, CSV diffs, vendor APIs)",
    "B": "Cybersecurity (audit scripts, security flags, log analysis, port checks, IOC parsing)",
    "C": "AI agents (Claude API clients, prompt templates, message dicts, structured output)",
}


# ---------------- LLM helpers ----------------

def call_gemini(system_prompt: str, user_message: str) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    genai = _import_gemini()
    client = genai.Client(api_key=api_key)
    full_prompt = f"{system_prompt}\n\n---\n\n{user_message}"
    response = client.models.generate_content(model=GEMINI_MODEL, contents=full_prompt)
    return response.text


def call_groq(system_prompt: str, user_message: str) -> str:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set")
    Groq = _import_groq()
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )
    return response.choices[0].message.content


def call_llm(system_prompt: str, user_message: str) -> tuple[str, str]:
    try:
        return call_gemini(system_prompt, user_message), "Gemini"
    except Exception as gemini_error:
        st.warning(f"Gemini failed: {gemini_error}. Falling back to Groq.")
        return call_groq(system_prompt, user_message), "Groq"


# ---------------- State helpers ----------------

def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def get_current_position() -> str:
    progress = load_text(PROGRESS_PATH)
    plan = load_text(PLAN_PATH)
    rows = [line for line in progress.splitlines() if line.startswith("| 2026-")]
    last_rows = "\n".join(rows[-5:]) if rows else "(no sessions yet)"
    return f"Recent sessions (last 5):\n{last_rows}\n\nLearning plan:\n{plan}"


def build_system_prompt() -> str:
    recipe = load_text(RECIPE_PATH)
    state = get_current_position()
    return f"{recipe}\n\n---\n\n# Current state — read this before generating today's session\n\n{state}\n"


def pick_next_angle() -> str:
    rows = [l for l in load_text(PROGRESS_PATH).splitlines() if l.startswith("| 2026-")]
    daily_rows = [r for r in rows if "Daily" in r.split("|")[2]]
    last_3 = daily_rows[-3:] if daily_rows else []
    used = []
    for row in last_3:
        m = re.search(r"\(Angle\s+([ABC])\)", row, re.IGNORECASE)
        if m:
            used.append(m.group(1).upper())
    for candidate in ["A", "B", "C"]:
        if candidate not in used:
            return candidate
    return used[0] if used else "A"


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


def append_progress_row(row: str) -> None:
    PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PROGRESS_PATH.open("a", encoding="utf-8") as f:
        f.write(row)


# ---------------- Parsing ----------------

def parse_session_content(text: str) -> dict:
    """Pull Topic / Concept review / Quiz sections out of LLM output for richer rendering."""
    result = {
        "topic_header": "",
        "concept_text": "",
        "questions": [],
        "raw": text,
    }
    topic_match = re.search(r"#\s*Topic\s*\n+(.*?)(?=\n#\s)", text, re.DOTALL)
    if topic_match:
        result["topic_header"] = topic_match.group(1).strip()
    concept_match = re.search(r"#\s*Concept review\s*\n+(.*?)(?=\n#\s*Quiz)", text, re.DOTALL)
    if concept_match:
        result["concept_text"] = concept_match.group(1).strip()
    quiz_match = re.search(r"#\s*Quiz\s*\n+(.*)", text, re.DOTALL)
    quiz_text = quiz_match.group(1) if quiz_match else ""
    blocks = re.split(r"(?=\*\*Q\d+\.\*\*)", quiz_text)
    blocks = [b.strip() for b in blocks if b.strip().startswith("**Q")]
    for block in blocks[:4]:
        result["questions"].append(parse_question_block(block))
    return result


def parse_question_block(block: str) -> dict:
    """Determine question type, extract options + hidden correct-answer letter for MC."""
    is_mc = bool(re.search(r"\*\(Multiple choice\)\*|\*\(What does this print\?\)\*", block))
    if not is_mc:
        return {"type": "free", "text": block.strip(), "options": [], "correct_letter": None}
    correct_match = re.search(r"\*\*Correct:\*\*\s*([a-dA-D])", block)
    correct_letter = correct_match.group(1).lower() if correct_match else None
    cleaned = re.sub(r"\*\*Correct:\*\*\s*[a-dA-D]\s*", "", block).strip()
    options = []
    question_lines = []
    for line in cleaned.splitlines():
        if re.match(r"^\s*[a-dA-D][\)\.]", line):
            options.append(line.strip())
        else:
            question_lines.append(line)
    return {
        "type": "mc",
        "text": "\n".join(question_lines).strip(),
        "options": options,
        "correct_letter": correct_letter,
    }


def picked_letter(option_string: str) -> str | None:
    if not option_string:
        return None
    m = re.match(r"^\s*([a-dA-D])[\)\.]", option_string)
    return m.group(1).lower() if m else None


# ---------------- Streamlit UI ----------------

st.set_page_config(page_title="Python Tutor", page_icon="🐍", layout="centered")
st.title("🐍 Python Tutor")
st.caption("Daily session · Gemini + Groq · MOOC.fi 2026")

DEFAULTS = {
    "stage": "start",
    "angle": None,
    "concept_quiz_text": None,
    "parsed": None,
    "user_answers": ["", "", "", ""],
    "quiz_grade": None,
    "exercise_text": None,
    "exercise_path": None,
    "apply_at_work": None,
    "user_code": "",
    "code_review": None,
    "feeling": "",
    "provider": None,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


def reset_session() -> None:
    for k in list(st.session_state.keys()):
        del st.session_state[k]


def reset_button() -> None:
    if st.button("Reset session", help="Discard progress and start over"):
        reset_session()
        st.rerun()


# -------- Stage handlers --------

def stage_start() -> None:
    st.write(
        "Click below to start today's full session — concept review + quiz + "
        "coding exercise + apply-at-work + progress log."
    )
    if st.button("Start today's session", type="primary"):
        st.session_state.angle = pick_next_angle()
        with st.spinner(f"Picked Angle {st.session_state.angle} for apply-at-work. Generating today's content..."):
            user_message = (
                "Generate today's session content in this EXACT markdown format. Use bolded sub-labels and "
                "the **Correct:** marker for MC questions exactly as shown.\n\n"
                "# Topic\n"
                "Chapter: [Part X / Chapter Y — Chapter Title]\n"
                "Concept: [granular concept name, e.g. 'arithmetic operators']\n\n"
                "# Concept review\n"
                "**Definition:** [1–2 sentence plain-English definition]\n\n"
                "**Worked example:**\n"
                "```python\n"
                "[3–10 lines of code, sysadmin/security flavored where natural]\n"
                "```\n\n"
                "**Sysadmin / security analogy:** [1–2 sentences]\n\n"
                "**Common gotcha:** [1–2 sentences about a common beginner mistake]\n\n"
                "# Quiz\n"
                "Generate exactly 4 questions per the recipe's anchor + stretch rule.\n\n"
                "**Q1.** *(Multiple choice)*\n"
                "[Question text]\n"
                "a) [option]\n"
                "b) [option]\n"
                "c) [option]\n"
                "d) [option]\n"
                "**Correct:** [single letter a/b/c/d]\n\n"
                "**Q2.** *(What does this print?)*\n"
                "[Optional setup sentence]\n"
                "```python\n"
                "[3–6 line code snippet]\n"
                "```\n"
                "a) [output]\n"
                "b) [output]\n"
                "c) [output]\n"
                "d) [output]\n"
                "**Correct:** [single letter a/b/c/d]\n\n"
                "**Q3.** *(Short answer)*\n"
                "[Question that needs a one-sentence answer]\n\n"
                "**Q4.** *(Stretch — conceptual)*\n"
                "[Why/when/which question for Parts 1–2 calibration]\n\n"
                "Do NOT include the coding exercise or apply-at-work — those come in a later step."
            )
            response, provider = call_llm(build_system_prompt(), user_message)
            st.session_state.concept_quiz_text = response
            st.session_state.parsed = parse_session_content(response)
            st.session_state.provider = provider
            st.session_state.stage = "concept_quiz"
        st.rerun()


def stage_concept_quiz() -> None:
    parsed = st.session_state.parsed or {}
    st.success(f"Concept + quiz generated by **{st.session_state.provider}**")

    # Topic
    if parsed.get("topic_header"):
        st.subheader("📚 Topic")
        st.markdown(parsed["topic_header"])
    # Concept review
    if parsed.get("concept_text"):
        st.subheader("💡 Concept review")
        st.markdown(parsed["concept_text"])
    # Fallback for unparsed output
    if not parsed.get("topic_header") and not parsed.get("concept_text"):
        st.warning("Could not parse session structure — showing raw output:")
        st.markdown(st.session_state.concept_quiz_text)

    # Quiz
    questions = parsed.get("questions", [])
    if questions:
        st.subheader("❓ Quiz")
    answers = []
    for i, q in enumerate(questions):
        st.markdown("---")
        st.markdown(f"**Question {i + 1}**")
        st.markdown(q["text"])
        if q["type"] == "mc":
            ans = st.radio(
                "Choose one:",
                options=q["options"],
                index=None,
                key=f"answer_{i}",
            )
            # Instant feedback when user picks
            if ans and q.get("correct_letter"):
                if picked_letter(ans) == q["correct_letter"]:
                    st.success("✓ Correct!")
                else:
                    correct_full = next(
                        (o for o in q["options"] if (picked_letter(o) or "") == q["correct_letter"]),
                        f"option {q['correct_letter']}",
                    )
                    st.error(f"✗ Wrong. Correct answer: **{correct_full}**")
        else:
            ans = st.text_area(
                "Your answer:",
                value=st.session_state.user_answers[i] if i < len(st.session_state.user_answers) else "",
                height=120,
                key=f"answer_{i}",
            )
        answers.append(ans if ans else "")

    st.markdown("---")
    col1, col2 = st.columns([1, 4])
    with col1:
        all_answered = all(a and a.strip() for a in answers) if questions else False
        submit = st.button("Submit answers", type="primary", disabled=not all_answered)
    with col2:
        reset_button()

    if submit:
        st.session_state.user_answers = answers
        with st.spinner("Grading..."):
            user_message = (
                f"Earlier you generated:\n\n{st.session_state.concept_quiz_text}\n\n"
                f"---\n\nJon's answers:\nQ1: {answers[0]}\nQ2: {answers[1]}\n"
                f"Q3: {answers[2]}\nQ4: {answers[3]}\n\n"
                f"---\n\nFor Q1 and Q2, the answer is the FULL option text (e.g., 'c) Floor division').\n\n"
                f"Grade per the recipe. Use this EXACT format with bolded labels:\n\n"
                f"**Summary:** [overall score, e.g. '3.5 / 4'] — [1-line takeaway]\n\n"
                f"**Q1 — ✓/✗:** [your answer / correct / 1-line why if wrong]\n\n"
                f"**Q2 — ✓/✗:** [same format]\n\n"
                f"**Q3 — ✓/partial/✗:** [brief assessment]\n\n"
                f"**Q4 (stretch) — ✓/partial/✗:** [explain THOROUGHLY — that's where real learning lives]\n\n"
                f"Encourage idiomatic improvement; don't be harsh. Total response under 350 words."
            )
            response, provider = call_llm(build_system_prompt(), user_message)
            st.session_state.quiz_grade = response
            st.session_state.provider = provider
            st.session_state.stage = "graded_quiz"
        st.rerun()


def stage_graded_quiz() -> None:
    st.success(f"Graded by **{st.session_state.provider}**")
    st.subheader("📝 Grade")
    st.markdown(st.session_state.quiz_grade)
    st.markdown("---")
    if st.button("Continue to coding exercise", type="primary"):
        with st.spinner("Generating exercise + apply-at-work..."):
            angle = st.session_state.angle
            user_message = (
                "Generate two things in this EXACT markdown format with bolded sub-labels:\n\n"
                "# Coding exercise\n"
                "**Topic:** [chapter / concept]\n\n"
                "**Task:**\n"
                "[Clear instructions, 1–3 short paragraphs.]\n\n"
                "**Expected output:**\n"
                "```\n"
                "[Literal expected output, line by line]\n"
                "```\n\n"
                "**Constraints:**\n"
                "- [bullet]\n"
                "- [bullet]\n"
                "- [bullet]\n\n"
                "**How to submit:**\n"
                "Paste your solution into the text box on this page.\n\n"
                f"# Apply-at-work — Angle {angle}\n"
                f"[2–3 sentences. Concrete idea using today's concept, framed for **Angle {angle}**: "
                f"{ANGLES[angle]}. Don't stray into the other angles.]\n\n"
                f"The assigned angle is **{angle}** — use ONLY that for the apply-at-work."
            )
            response, provider = call_llm(build_system_prompt(), user_message)
            parts = re.split(r"^# Apply-at-work.*$", response, maxsplit=1, flags=re.MULTILINE)
            if len(parts) == 2:
                exercise = parts[0].replace("# Coding exercise", "", 1).strip()
                apply_text = parts[1].strip()
            else:
                exercise = response
                apply_text = "(apply-at-work suggestion not parsed cleanly)"
            today_str = date.today().isoformat()
            st.session_state.exercise_text = exercise
            st.session_state.apply_at_work = apply_text
            st.session_state.exercise_path = str(write_exercise_file(today_str, exercise))
            st.session_state.provider = provider
            st.session_state.stage = "exercise"
        st.rerun()
    reset_button()


def stage_exercise() -> None:
    st.success(f"Exercise generated by **{st.session_state.provider}**")
    st.subheader("⚙️ Coding exercise")
    st.markdown(st.session_state.exercise_text)
    st.info(f"Saved to: `{st.session_state.exercise_path}`")
    st.markdown("---")
    st.subheader("Your solution")
    code = st.text_area(
        "Paste your Python code:",
        value=st.session_state.user_code,
        height=240,
        key="code_input",
    )
    col1, col2 = st.columns([1, 4])
    with col1:
        submit = st.button("Submit code", type="primary", disabled=not code.strip())
    with col2:
        reset_button()
    if submit:
        st.session_state.user_code = code
        if st.session_state.exercise_path:
            append_solution(Path(st.session_state.exercise_path), code)
        with st.spinner("Reviewing your code..."):
            user_message = (
                f"Exercise was:\n\n{st.session_state.exercise_text}\n\n"
                f"---\n\nJon's solution:\n```python\n{code}\n```\n\n"
                f"---\n\nReview per the recipe. Use this EXACT format with bolded labels:\n\n"
                f"**Verdict:** ✓ pass / partial / needs fix\n\n"
                f"**Correctness:** [does the output match the spec? are constraints met?]\n\n"
                f"**Idiomatic improvement:** [ONE concrete improvement — something that actually makes the code better, not stylistic nitpicking]\n\n"
                f"**Pattern check:** [if you spot a recurring pattern from past sessions like 'what' comments instead of 'why', flag it; otherwise '—']\n\n"
                f"Don't be harsh; encourage idiomatic improvement. Keep response under 250 words."
            )
            response, provider = call_llm(build_system_prompt(), user_message)
            st.session_state.code_review = response
            st.session_state.provider = provider
            st.session_state.stage = "graded_exercise"
        st.rerun()


def stage_graded_exercise() -> None:
    st.success(f"Code review by **{st.session_state.provider}**")
    st.subheader("🔍 Code review")
    st.markdown(st.session_state.code_review)
    st.markdown("---")
    if st.button("Continue to apply-at-work", type="primary"):
        st.session_state.stage = "apply_at_work"
        st.rerun()
    reset_button()


def stage_apply_at_work() -> None:
    st.subheader(f"💼 Apply-at-work — Angle {st.session_state.angle}")
    st.markdown(st.session_state.apply_at_work)
    st.markdown("---")
    if st.button("Wrap up the session", type="primary"):
        st.session_state.stage = "wrap"
        st.rerun()
    reset_button()


def stage_wrap() -> None:
    st.subheader("🏁 Wrap up")
    st.write(
        "Optional 1-word feeling note (e.g. `clicked`, `smooth`, `rough`, "
        "`productive`, `confused` — leave blank to skip)."
    )
    feeling = st.text_input("Feeling:", value=st.session_state.feeling, max_chars=20)
    col1, col2 = st.columns([1, 4])
    with col1:
        log = st.button("Log session", type="primary")
    with col2:
        reset_button()
    if log:
        st.session_state.feeling = feeling.strip()
        today_str = date.today().isoformat()
        chapter, topic = "?", "?"
        if st.session_state.concept_quiz_text:
            cm = re.search(r"Chapter:\s*(.+)", st.session_state.concept_quiz_text)
            cn = re.search(r"Concept:\s*(.+)", st.session_state.concept_quiz_text)
            if cm:
                chapter = cm.group(1).strip()
            if cn:
                topic = cn.group(1).strip()
        score = "—"
        if st.session_state.quiz_grade:
            sm = re.search(r"(\d+(?:\.\d+)?)\s*/\s*4", st.session_state.quiz_grade)
            if sm:
                score = f"{sm.group(1)}/4"
        apply_summary = ""
        if st.session_state.apply_at_work:
            words = re.sub(r"[\*\#\n]", " ", st.session_state.apply_at_work).split()
            apply_summary = " ".join(words[:10]) + ("..." if len(words) > 10 else "")
        row = (
            f"| {today_str} | Daily | {chapter} | {topic} | {score} | pass | "
            f"{apply_summary} (Angle {st.session_state.angle}) | {st.session_state.feeling} |\n"
        )
        append_progress_row(row)
        st.session_state.stage = "done"
        st.rerun()


def stage_done() -> None:
    st.success("Session logged.")
    st.markdown(
        f"- Row appended to `Output/progress.md` ✓\n"
        f"- Exercise saved to `{st.session_state.exercise_path}` ✓\n"
        f"- Apply-at-work angle: **{st.session_state.angle}**\n\n"
        f"Tomorrow's run picks up at the next chapter automatically."
    )
    if st.button("Start another session"):
        reset_session()
        st.rerun()


STAGE_HANDLERS = {
    "start": stage_start,
    "concept_quiz": stage_concept_quiz,
    "graded_quiz": stage_graded_quiz,
    "exercise": stage_exercise,
    "graded_exercise": stage_graded_exercise,
    "apply_at_work": stage_apply_at_work,
    "wrap": stage_wrap,
    "done": stage_done,
}

STAGE_HANDLERS[st.session_state.stage]()
