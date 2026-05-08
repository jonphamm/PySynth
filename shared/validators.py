"""LLM-output coercion: turn loose JSON into the strict shapes the UI consumes."""


def _str_list(value):
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item is not None and str(item).strip()]


def validate_session_data(d: dict) -> dict:
    """Coerce LLM JSON into the expected session shape with sensible defaults."""
    topic = d.get("topic") or {}
    review = d.get("concept_review") or {}
    questions = d.get("questions") or []
    valid_qs = []
    for q in questions[:4]:
        if not isinstance(q, dict):
            continue
        qtype = q.get("type", "free")
        if qtype not in ("mc", "free"):
            qtype = "free"
        cleaned = {
            "type": qtype,
            "subtype": q.get("subtype", ""),
            "text": q.get("text", "(missing question)"),
        }
        if qtype == "mc":
            opts = q.get("options") or []
            cleaned["options"] = [str(o) for o in opts if o is not None]
            ci = q.get("correct_index")
            if isinstance(ci, int) and 0 <= ci < len(cleaned["options"]):
                cleaned["correct_index"] = ci
            else:
                cleaned["correct_index"] = None
            if q.get("code"):
                cleaned["code"] = str(q["code"])
            if not cleaned["options"]:
                cleaned = {"type": "free", "subtype": cleaned["subtype"], "text": cleaned["text"]}
        valid_qs.append(cleaned)

    syntax_forms = []
    for sf in (review.get("syntax_forms") or []):
        if not isinstance(sf, dict):
            continue
        syntax_forms.append({
            "label": str(sf.get("label", "")),
            "code": str(sf.get("code", "")),
        })

    return {
        "topic": {
            "chapter": topic.get("chapter", ""),
            "concept": topic.get("concept", ""),
        },
        "concept_review": {
            "definition": review.get("definition", ""),
            "how_it_works": _str_list(review.get("how_it_works")),
            "syntax_forms": syntax_forms,
            "worked_example_code": review.get("worked_example_code", ""),
            "worked_example_walkthrough": _str_list(review.get("worked_example_walkthrough")),
            "common_patterns": _str_list(review.get("common_patterns")),
            "analogy": review.get("analogy", ""),
            "gotcha": review.get("gotcha", ""),
            "when_to_use": review.get("when_to_use", ""),
        },
        "questions": valid_qs,
    }


def validate_exercise_data(d: dict) -> dict:
    ex = d.get("exercise") or {}
    aw = d.get("apply_at_work") or {}
    constraints = ex.get("constraints") or []
    return {
        "exercise": {
            "topic": ex.get("topic", ""),
            "task": ex.get("task", ""),
            "expected_output": ex.get("expected_output", ""),
            "constraints": [str(c) for c in constraints],
        },
        "apply_at_work": {
            "angle": aw.get("angle", ""),
            "text": aw.get("text", ""),
        },
    }


def render_exercise_markdown(ex: dict) -> str:
    """Render an exercise dict to display markdown + file docstring text."""
    parts = []
    if ex.get("topic"):
        parts.append(f"**Topic:** {ex['topic']}\n")
    if ex.get("task"):
        parts.append(f"**Task:**\n\n{ex['task']}\n")
    if ex.get("expected_output"):
        parts.append(f"**Expected output:**\n```\n{ex['expected_output']}\n```\n")
    if ex.get("constraints"):
        parts.append("**Constraints:**\n" + "\n".join(f"- {c}" for c in ex["constraints"]) + "\n")
    parts.append("**How to submit:**\nPaste your solution into the text box on this page.")
    return "\n".join(parts)
