# Workflow: Python Tutor — Weekly Review

**When to run:** Sundays (manual or scheduled). the user says "weekly python review" or this is invoked by the weekly routine.

**Goal:** Synthesize the past week of Python sessions, identify strengths/weaknesses, update next week's focus in the learning plan, and append a "Week of …" section to progress.md.

---

## Steps

### 1. Read inputs

- `Output/progress.md` — pull the **last 7 days** of daily session rows
- `Resources/python-learning-plan.md` — current weekly goal and where the user expected to be by today
- `Output/exercises/` — glance at this week's exercise files for any patterns (e.g., recurring syntax mistakes, code style trends)

### 2. Synthesize the week

Compute and reason about:

- **Sessions completed** this week vs. planned (e.g., 4/5)
- **Topics covered** — list them from the progress rows
- **Quiz performance** — average score; flag any topic with a low score (<3/5)
- **Coding exercise outcomes** — count of pass / partial / struggled
- **Drift from plan** — did the user finish the weekly goal (typically: 1 MOOC Part)? If not, by how much?

### 3. Identify strongest and weakest topics

- **Strongest** — highest quiz scores + clean exercises
- **Weakest** — lowest quiz scores or struggled exercises
- If a weak topic is foundational (e.g., for-loops, function definition), call it out explicitly — these need re-coverage before moving on.

### 4. Propose next week's focus

Update `Resources/python-learning-plan.md`:
- Set the **next weekly goal** (typically: next MOOC Part, but slow down if this week was rough)
- If any weak topics need re-coverage, schedule **1–2 review days** in next week's plan
- Update the user's **current position** if he completed the previous Part

### 5. Append weekly summary to progress.md

Below the daily session table, add a section like:

```markdown
---

### Week of YYYY-MM-DD (week starting Monday)

- **Sessions:** 4/5 completed
- **Topics covered:** dictionaries, list comprehensions, file reading, exception basics
- **Average quiz score:** 4.2 / 5
- **Strongest:** list comprehensions (5/5, clean exercise)
- **Weakest:** exceptions — re-cover Mon next week
- **Plan progress:** completed Part 4. **On pace.**
- **Next week focus:** Part 5 (dictionaries advanced + small-data analysis), with Mon = exceptions review.
```

### 6. Brief sign-off to the user

Show the user the summary section you just wrote (paste it back in chat) and confirm next week's plan with him. Use `AskUserQuestion` if any aspect of next week's focus is genuinely ambiguous (e.g., "skip Part 6 for now and prioritize a mini-project?"). Otherwise, keep it short.

---

## Anti-patterns

- Don't grade the week harshly if the user missed a day or two — life happens. Acknowledge, adjust, move on.
- Don't propose a complete plan rewrite based on one bad week. Adjust at the margins.
- Don't bury the weekly summary deep in the file — it goes right after the most recent daily rows, with `---` separators above and below.
