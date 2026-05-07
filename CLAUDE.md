# Project Context

This is my AI agent workspace. I use it for research, learning, creating AI agents, and productivity workflows.

# About Me

I'm a Python learner working through the Python Programming MOOC 2026, with career interests in cybersecurity and AI agents. Day job is sysadmin / IT operations. Still a beginner with Python.

# Rules

- Always ask clarifying questions before starting a complex task.
- Show your plan and steps before executing.
- Keep reports and summaries concise, bullet points over paragraphs.
- Save all output files to the output folder.
- Cite sources when doing research.

# Workflow Triggers

When I ask you to run a workflow, **read the matching file in `Workflows/` first** and follow its steps faithfully — don't improvise. The recipes encode decisions from prior sessions (length caps, difficulty calibration, supplementary tracks, etc.).

| When I say… | Read and follow |
|---|---|
| "run the research workflow on X" / "research X" / "research X for me" | `Workflows/research-topic.md` |
| "run the python tutor" / "today's python session" / "let's do python" | `Workflows/python-tutor-daily.md` |
| "weekly python review" / "weekly review" | `Workflows/python-tutor-weekly.md` |
| "monthly python review" / "monthly review" | `Workflows/python-tutor-monthly.md` |

The python-tutor daily workflow also reads `Resources/python-learning-plan.md` and `Resources/supplementary-resources.md` as part of step 1 — don't skip those. Logging today's session row to `Output/progress.md` is mandatory; the weekly/monthly workflows depend on it.

If my phrasing is close but not exact, match the closest workflow and confirm with me before starting.

# Project Structure

- Workflows/ Workflow instruction files (plain English recipes the agent follows)
- Output/ Finished deliverables (reports, drafts, analysis)
- Resources/ Reference docs and templates