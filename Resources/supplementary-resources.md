# Supplementary Resources — Beyond the MOOC

*Generated 2026-05-05.*

The MOOC.fi 2026 course is the **spine** of Jon's learning. These resources layer in problems, examples, and angles for his two career destinations — **cybersecurity** and **AI agents**. The tutor pulls from them once Jon has the prerequisite Python from the MOOC. Each entry notes when it becomes in-scope.

## Cybersecurity track

**Now (Parts 1–3) — flavor only.** No outside resource yet; security shows up via worked examples (log lines, audit headers, status banners).

**Part 4+ (lists, strings):**
- **Automate the Boring Stuff with Python** — Al Sweigart. Free at https://automatetheboringstuff.com/ . Beginner-friendly practical scripting. Use Ch 7 (regex), Ch 9 (file I/O), Ch 14 (CSV/JSON).

**Part 5+ (functions):**
- **PicoCTF** — https://picoctf.org/ . Free CTF challenges with a beginner track. Many easier challenges use small Python scripts — perfect applied practice.

**Part 7+ (files, exceptions, modules):**
- **TryHackMe — Python for Cybersecurity path** — https://tryhackme.com/ . Some content paid; free rooms still solid.

**Part 8+ (OOP, intermediate):**
- **Black Hat Python (2nd ed)** — Justin Seitz / Tim Arnold. Classic. Sockets, packet manipulation, simple offensive tooling. Defer until Jon is comfortable with classes.

## AI-agent track

**Now (Parts 1–3) — flavor only.** Security/sysadmin analogies for now; AI agent code requires functions and dicts (Part 5+).

**Part 5+ (functions, dicts):**
- **Anthropic Claude API docs** — https://docs.anthropic.com . Most relevant given Jon already uses Claude Code. Start with Quickstart + Messages API.
- **Anthropic "Building Effective Agents" guide** — https://www.anthropic.com/research/building-effective-agents . Code-light essay on agent design patterns.

**Part 7+ (files, exceptions):**
- **Real Python — Anthropic SDK / agent articles** — https://realpython.com . Search for current Claude/agent tutorials.

**Part 8+ (OOP, libraries):**
- **Pydantic docs** — https://docs.pydantic.dev/ . Structured validation; essential for serious agent work.
- **Anthropic Cookbook** — https://github.com/anthropics/anthropic-cookbook . Working examples for tool use, structured output, prompt caching, agents.

## How the tutor uses these

- **Concept review** — once a track is in scope, the worked example may come from there instead of a generic MOOC example.
- **Mini quiz** — one of the 3–5 questions may use a security or AI context.
- **Coding exercise** — Parts 1–4: MOOC-style with security/AI flavor. Part 5+: pull directly from these sources when a better fit exists.
- **Apply-at-work** — three rotating angles now: **(A)** sysadmin/day-job, **(B)** cybersecurity, **(C)** AI agents. The tutor checks `progress.md` so the same angle isn't picked twice in a row.

## Updating this file

Add a resource when:
- Jon mentions interest in a specific subarea (reverse engineering, prompt engineering, etc.)
- A new MOOC concept opens a door to a useful supplementary text
- A previously-deferred resource becomes accessible (Jon hits the prerequisite Part)

Remove resources that prove too advanced, low-quality, or outdated.
