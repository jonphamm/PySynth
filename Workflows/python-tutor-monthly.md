# Workflow: Python Tutor — Monthly Review

**When to run:** Last weekday of each month (manual or scheduled). the user says "monthly python review" or this is invoked by the monthly routine.

**Goal:** Deeper synthesis than the weekly. Test retention from earlier in the month, propose a month-end mini-project tying recent concepts to your day-job work, and update the learning plan with next month's targets.

---

## Steps

### 1. Read inputs

- `Output/progress.md` — full month of daily rows + 4 weekly summaries
- `Resources/python-learning-plan.md` — monthly milestone target and current position
- `Output/exercises/` — scan all exercise files from this month for patterns

### 2. Compute monthly stats

- **Sessions completed** this month (target: 20 daily + 4 weekly = 24)
- **MOOC Parts completed** vs. planned (typical target: 4 Parts/month)
- **Estimated hours logged** (rough estimate: ~25 min/daily session × count + ~15 min/weekly review × 4)
- **Quiz performance trend** — compare week 1 average vs. week 4 average
- **Topic coverage** — list every concept covered in the month

### 3. Retention check

Pick **3 random concepts** from the **first half of the month** (the ones longest since covered) and run a 1-question quiz on each:
- 1 multiple choice
- 1 "what does this print?"
- 1 short answer

Present all three at once. Grade. If the user misses 2/3, schedule a review week before continuing forward in the MOOC.

### 4. Propose the month-end project

Suggest **one** mini-project that:
- Combines **2–3 concepts** the user learned this month
- Has a clear application to your **sysadmin / day-job work** (e.g. email marketing, IT ops)
- Is doable in 2–4 hours total
- Has a defined "done" condition (an output file, a working script, etc.)

Examples (pick one that fits the month's concepts):
- Bounce-log analyzer: parse a week of SMTP logs, group failures by domain, output a top-10 CSV.
- AD-stale-user reporter: read a CSV of users + last login, flag users inactive >90 days, write a report file.
- Subscriber diff tool: take two CSV exports, compute adds/removes/changes between them.
- Email-syntax validator: read a list of emails from a file, validate each, output two files (valid / invalid) with reasons.

Present the project with: **Goal**, **Inputs**, **Outputs**, **Concepts used**, **Stretch goals** (1–2 optional extras for if he finishes early).

Save the project spec to `Output/exercises/project-YYYY-MM.md` (note: `.md`, not `.py` — this is a spec, not a script).

### 5. Update the learning plan for next month

In `Resources/python-learning-plan.md`:
- Update the user's current MOOC position
- Set **next month's milestone** (typically: next 4 Parts + one project)
- If retention check showed weakness, build review days into the first week
- Note any career-relevant detours (e.g., "the user expressed interest in subprocess management — slot a side-quest mid-month")

### 6. Append monthly summary to progress.md

Below the most recent weekly summary, add:

```markdown
---

## Month of YYYY-MM

- **Sessions:** 22 / 24 planned
- **Hours logged (est):** ~10
- **MOOC Parts completed:** 4 (Parts 4–7)
- **Quiz trend:** Week 1 avg 3.8 → Week 4 avg 4.5 (improving)
- **Strongest:** list comprehensions, file I/O
- **Weakest at month-end:** error handling — needs review week
- **Retention check:** 3/3 — solid retention
- **Month-end project:** Bounce-log analyzer (spec at `Output/exercises/project-2026-05.md`)
- **Next month focus:** Parts 8–11 (functions deep dive, modules, basic OOP)
```

### 7. Sign-off

Acknowledge the month. Be honest but encouraging. If the user completed the project, celebrate it briefly. If he didn't get to it yet, carry it forward to next month with a smaller scope if needed.

---

## Anti-patterns

- Don't propose a project that needs frameworks/libraries the user hasn't seen yet (Flask, pandas, requests) unless the MOOC has covered them.
- Don't make the retention check punitive — its job is to spot real gaps, not to grade the user.
- Don't pile up incomplete projects month-over-month. If a project rolls over twice, scope it down or replace it.
- Don't change the monthly milestone structure if it's working — consistency is what makes long-term tracking valuable.
