# PySynth

A daily Python tutor for the [Helsinki MOOC.fi 2026](https://programming-26.mooc.fi/) curriculum, with side-tracks for cybersecurity and AI-agent topics.

The agent reads your progress from a markdown log, generates a concept review + quiz + coding exercise + apply-at-work suggestion, grades your answers, and appends the session to your progress log. It rotates the "apply-at-work" suggestion across three angles (sysadmin, cybersecurity, AI agents) so each career direction gets exposure.

## Stack

PySynth is a monorepo with three top-level Python/JS surfaces sharing one logic core:

- [shared/](shared/) — chapters, prompts, LLM fan-out, progress log IO. The single source of truth for tutoring logic.
- [backend/](backend/) — **FastAPI** wrapping `shared/`, serves JSON to the frontend.
- [frontend/](frontend/) — **Next.js 16** (React 19, Tailwind 4, Webpack), the daily-driver UI.

LLM providers (tried in order, first success wins):
1. **Google Gemini 2.5 Flash** — free tier
2. **Groq Llama 3.3 70B** — fallback
3. **Cerebras Qwen 3 235B** — second fallback

## Setup

```powershell
# 1. Clone
git clone https://github.com/jonphamm/pysynth.git
cd pysynth

# 2. Python env (backend + shared)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt

# 3. Node deps (frontend)
cd frontend
npm install
cd ..

# 4. API keys
Copy-Item .env.example .env
# edit .env and paste at least GEMINI_API_KEY
```

Free API keys:
- Gemini: <https://aistudio.google.com/apikey>
- Groq: <https://console.groq.com/keys>
- Cerebras: <https://cloud.cerebras.ai/platform/api-keys>

## Run

Two terminals.

**Terminal 1 — backend (FastAPI on :8000):**

```powershell
cd C:\dev\pysynth
.\.venv\Scripts\Activate.ps1
uvicorn backend.app:app --port 8000 --reload
```

**Terminal 2 — frontend (Next.js on :3000):**

```powershell
cd C:\dev\pysynth\frontend
npm run dev
```

Open <http://localhost:3000>.

> **Windows note:** the frontend uses Webpack (`next dev --webpack`) rather than Turbopack to sidestep AppLocker's `.dll` blocking on locked-down corporate machines.

## How a session flows

1. Click **Start today's session** — backend reads [Output/progress.md](Output/progress.md) to see where you left off, picks today's chapter from the learning plan.
2. Read the concept review. Answer 4 quiz questions (3 anchor + 1 stretch).
3. Submit answers, get graded with explanations focused on the stretch question.
4. The next stage shows an exercise; write your solution in the editor and submit.
5. Get a code review focused on correctness + one idiomatic improvement.
6. Read an apply-at-work suggestion — rotated across three angles (sysadmin / cybersecurity / AI agents) by Python code, not the LLM.
7. Drop an optional 1-word feeling note. Session logged to `progress.md`.
8. Click **Start another session** to land on the next chapter.

## Customization

- [Workflows/python-tutor-daily.md](Workflows/python-tutor-daily.md) — loaded at runtime as the agent's system prompt. Edit this plain-English recipe to change tutor behavior; no code changes required.
- [Resources/python-learning-plan.md](Resources/python-learning-plan.md) — your MOOC position. Created on first run.
- [Resources/supplementary-resources.md](Resources/supplementary-resources.md) — external resources (Automate the Boring Stuff, Anthropic Cookbook, PicoCTF, etc.) the tutor pulls from.

## Privacy / per-user state

Personal data is gitignored — every user keeps their own local state:

- `.env` — your API keys
- `Output/progress.md` — your daily session log
- `Output/exercises/` — your code submissions
- `Resources/python-learning-plan.md` — your current chapter
- `Resources/personal-context.md` — optional personal context for the tutor

Friends can clone the repo and run their own copy without seeing each other's data.

## Roadmap

- [x] Stage 1 — concept + 1 stretch question, end-to-end stack validation
- [x] Stage 2 — full daily session (concept + 4 quiz Qs + exercise + apply-at-work + log)
- [x] Stage 3 — Streamlit prototype on Streamlit Community Cloud
- [x] Stage 4 — extract `shared/`, FastAPI backend, Next.js frontend, monorepo migration
- [x] Stage 5 — retire the Streamlit prototype; PySynth is the only client
- [ ] Stage 6 — deploy backend + frontend somewhere reachable from a phone
