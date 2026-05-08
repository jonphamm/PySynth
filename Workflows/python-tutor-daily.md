# Workflow: Python Tutor — Daily Session

**When to run:** the user says "run the python tutor", "let's do today's python session", or this is invoked by the daily scheduled routine.

**Goal:** A focused ~20-minute Python learning session aligned to the [Helsinki MOOC.fi 2026](https://programming-26.mooc.fi/) course, with concept review → quiz → coding exercise → real-world application, logged to `Output/progress.md`.

---

## Steps

### 1. Where-am-I check

Read these files first:
- `Output/progress.md` — last 5 session rows (most recent at the bottom)
- `Resources/python-learning-plan.md` — current MOOC chapter, weekly goal, monthly target

Then assess:
- **What did the user cover yesterday?** (and the day before)
- **Is he on track with the weekly goal?** Behind / on pace / ahead?
- **Did we finish a chapter recently?** If so, today should start a new one.

If `Resources/python-learning-plan.md` does **not** exist yet, jump to step 2 (bootstrap), otherwise skip step 2.

If today's date already appears in `progress.md` as a daily session, **stop and ask** the user if he wants to (a) skip, (b) do a different concept, or (c) extend yesterday's exercise.

### 2. First-time bootstrap (only if learning plan doesn't exist)

Use `AskUserQuestion` to ask the user:
- Which MOOC.fi 2026 **Part** is he currently on? (Parts 1–14)
- Within that Part, which **chapter** was the last one he completed?
- How many **days per week** does he want to study? (default suggestion: 5, Mon–Fri)

Then create `Resources/python-learning-plan.md` with:
- A map of all 14 Parts of MOOC.fi 2026 (with chapter titles — if you don't have this from memory, fetch the course outline from `https://programming-26.mooc.fi/` first)
- His current position
- A **weekly goal** (typically: complete 1 Part per week, but adjust based on Part difficulty)
- A **monthly milestone** (typically: complete 4 Parts + one mini-project applying recent concepts to his sysadmin work)

### 3. Pick today's topic

From the learning plan, pick the next concept the user hasn't covered yet. Prefer:
- The next chapter inside his current Part
- If a Part just finished, start the next Part with its first concept
- If quiz scores in `progress.md` show weakness in a recent topic, **interleave a review day** every 3–4 sessions

Then check `Resources/supplementary-resources.md` to see which **cybersecurity** and **AI-agent** resources are now in scope for the user's current Part. Use those to **flavor** today's session (steps 4–7). The MOOC stays the spine — supplementary tracks add angle and applied practice, they don't replace the chapter.

State the topic clearly to the user: *"Today's topic: [concept] from MOOC Part X, Chapter Y."* If a supplementary resource is the source of today's example or exercise, name it.

### 4. Concept review (~7 min)

Explain the concept in plain English with enough depth that the user can answer all 4 quiz questions and write the coding exercise from this section alone — no outside docs needed. Aim for ~450–700 words across these eight sub-sections:

- **Definition** — 2–4 sentences. Name key terminology (operators, keywords, return types).
- **How it works** — 4–6 short bullets on what Python does at runtime: evaluation order, types involved, side effects, scope. Each bullet ≤ 18 words.
- **Syntax forms** — 2–4 entries. For each, a short label and a 1–3 line snippet showing that form. Covers the variations the user will see in MC questions.
- **Worked example** — 5–12 lines of Python with inline comments only where the WHY is non-obvious. When a supplementary track is in scope, prefer **cybersecurity** (log lines, audit headers, user records) or **AI agents** (API calls, structured prompts, message dicts) flavor over a generic one. A clean MOOC-style example beats a contrived security/AI one.
- **Worked example walkthrough** — bulleted/numbered trace: what each non-trivial line does, what variables hold, what gets printed.
- **Common patterns** — 2–4 bullets showing real-world shapes the user will encounter (e.g. "guard with `if key in d` before access", "iterate with `.items()` to get pairs").
- **When to use it** — 1–2 sentences contrasting this concept with the alternatives the user already knows. This is the bridge to the stretch question.
- **Analogy** — 1–2 sentences relating to a sysadmin or security scenario where it fits naturally (dictionaries → DNS lookup tables, list comprehensions → filtered log lines). Don't force it if awkward.
- **Watch out for** — 1–2 sentences on a common beginner mistake and how to avoid it.

The user is a beginner but a sharp one — be substantive, but don't over-explain.

### 5. Mini quiz (3–4 questions): anchor + stretch rule

Every quiz must contain **2–3 anchor questions + exactly 1 stretch question.**

**Anchor questions (2–3)** — at the chapter's natural level:
- Multiple-choice recall ("Which of these is a valid dictionary key?")
- "What does this print?" on a 3–6 line snippet
- Short-answer (one sentence)

**Stretch question (1, always)** — deeper than recall, **calibrated to the user's current MOOC Part:**

| the user is on… | Stretch style |
|---|---|
| **Parts 1–2** | Conceptual: why / when / which is right (e.g., "why use comments — when to avoid"). Tests misconceptions, not syntax. |
| **Parts 3–4** | Trace/predict on a 5–8 line snippet that composes multiple concepts (loop + condition, list + slicing). |
| **Part 5+** | "Fix the bug" / "what's wrong here" on realistic code. |
| **Part 7+** | Scenario pulled from a supplementary source (Automate the Boring Stuff, Anthropic Cookbook, PicoCTF). Cite the source. |

When supplementary tracks are in scope, the stretch may also use a **cybersecurity or AI-agent context** (log lines, API-stub calls). Rotate the angle the user hasn't seen recently.

Style after MOOC.fi questions. Present all questions at once, then wait for the user's answers. After he answers:
- Grade each one
- For misses, explain *why* the right answer is right — don't just state it
- **The stretch is the most important to explain thoroughly** — that's where real learning lives. Today's Q4 (comments why-vs-what) is the model.

### 6. Coding mini-exercise

Give the user **one** small task. **Style scales with the user's current MOOC Part:**

| the user is on… | Exercise style |
|---|---|
| **Parts 1–4** | Spec-driven: clear inputs, expected exact output. Flavor with security/AI context where natural (e.g., audit-script header instead of Hello World). |
| **Part 5+** | Real-data scenario: given a CSV / log file / messages payload, write something that does X. Inputs are realistic, output may be open-ended. |
| **Part 7+** | Pull at least one exercise per week directly from a supplementary source (*Automate the Boring Stuff*, Anthropic Cookbook, PicoCTF). Cite the source in the docstring. |

Requirements regardless of style:
- Clear inputs and expected outputs (or expected behavior for open-ended tasks)
- Solvable in 5–15 minutes
- Uses today's concept as the main idea

Save the **prompt** to `Output/exercises/YYYY-MM-DD.py` as a top docstring. Wait for the user's solution. When he submits:
- Run it mentally (or with `python` via Bash if needed)
- Check correctness against the spec
- Note one **idiomatic Python improvement** (not stylistic nitpicking — something that actually makes the code better)
- Append his final solution to the same file under the docstring

### 7. Apply-at-work / career-track suggestion

One concrete idea for using today's concept. **Rotate across three angles** session-to-session — check `progress.md`'s last 3 rows so you don't pick the same angle twice in a row.

**Angle A — Sysadmin / day job:**
- Strings/files: parse SMTP bounce logs, group failures by domain
- Dicts/lists: build a lookup of which mailing lists a contact appears in
- Loops/conditionals: cleanup script for stale AD users
- Functions: reusable helper to validate email syntax
- File I/O: diff two CSV exports of subscribers
- Exceptions: wrap a flaky vendor API call with retries
- Regex: extract message-IDs from server logs

**Angle B — Cybersecurity (the user's career destination):**
- print/comments: header for an audit script, status banner for a recon tool
- variables/arithmetic: simple password-entropy calc, port-range generator
- conditionals: flag suspicious login times, bucket events by severity
- loops: brute-force a tiny demo CTF challenge, scan a list of IPs
- strings: parse `/etc/passwd`-style records, redact PII from log dumps
- files: tail a syslog file, hash a directory of binaries with `hashlib`
- functions: reusable IOC checker, simple subnet calculator
- regex: extract emails, IPs, or hashes from a forensic dump
- exceptions: defensive parsing of malformed log lines

**Angle C — AI agents (the user's other career destination):**
- print/comments: log lines from a Claude API client, structured-output debug print
- variables: store a system prompt, an API key (with reminder to use env vars later)
- conditionals: route a request based on intent classification
- loops: iterate over a batch of prompts, retry failed completions
- strings: prompt template formatting, parsing model output
- dicts: shape a `messages=[{...}]` payload for the Anthropic API
- files: load a JSON dataset to feed an agent
- functions: a reusable `ask_claude(prompt) -> str` wrapper
- exceptions: handle rate-limit and retry errors

Suggest **one** idea from one angle, briefly (2–3 sentences). State which angle (A / B / C) so the rotation is trackable. Not a full design — just enough to spark an idea.

### 8. Append to progress.md

Add one row to the table in `Output/progress.md`:

```
| YYYY-MM-DD | Daily | Part X / Chapter Y | <topic> | <quiz score, e.g. 4/5> | <pass/partial/struggled> | <work-apply idea, ≤10 words> | <optional 1-word note from the user> |
```

Ask the user for the optional 1-word "feeling" note (e.g., "smooth", "stuck", "fun") before writing the row. Keep it optional — if he doesn't provide one, leave that cell blank.

### 9. Wrap

Brief sign-off: 1 sentence on what's next session (next chapter / a review day). No long summary — the progress.md row is the record.

---

## Anti-patterns

- Don't lecture. Concept review is **5 min**, not a textbook chapter.
- Don't give the answer to the coding exercise unless the user asks or is genuinely stuck (>10 min, no progress).
- Don't skip the where-am-I check — it's the whole reason daily sessions stay coherent over weeks.
- Don't pile on quiz questions. 5 max. Quality over quantity.
- Don't grade the exercise harshly. Encourage idiomatic improvement, not perfection.
