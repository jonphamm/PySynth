---
name: python-weekly
description: Generate a weekly Python-learning review from the last 7 days of progress.md rows. Use when the user says "weekly python review", "weekly review", or similar.
---

Read [`Workflows/python-tutor-weekly.md`](../../../Workflows/python-tutor-weekly.md) and follow its steps faithfully.

For autonomous execution against a clean recent log, prefer delegating to the `progress-analyst` subagent via the Agent tool with `subagent_type: "progress-analyst"` — it runs with a restricted tool set and writes its report directly to `Output/reviews/`.
