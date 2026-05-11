---
name: python-monthly
description: Generate a monthly Python-learning review covering the last calendar month of progress.md rows, milestones, and recommended adjustments. Use when the user says "monthly python review", "monthly review", or similar.
---

Read [`Workflows/python-tutor-monthly.md`](../../../Workflows/python-tutor-monthly.md) and follow its steps faithfully.

For autonomous execution against a clean recent log, prefer delegating to the `progress-analyst` subagent via the Agent tool with `subagent_type: "progress-analyst"` — it runs with a restricted tool set and writes its report directly to `Output/reviews/`.
