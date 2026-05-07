# Python Tutor Agent

A Streamlit web app that runs daily Python tutoring sessions using Google Gemini (with Groq fallback). Built around the [Helsinki MOOC.fi 2026](https://programming-26.mooc.fi/) curriculum, with side-tracks for cybersecurity and AI-agent topics.

The agent reads your progress from a markdown log, generates a concept review + quiz + coding exercise + apply-at-work suggestion, grades your answers, and appends the session to your progress log. It rotates the "apply-at-work" suggestion across three angles (sysadmin, cybersecurity, AI agents) so each career direction gets exposure.

## Stack

- **Streamlit** — Python web framework, mobile-friendly UI
- **Google Gemini 2.5 Flash** — primary LLM (free tier: 15 req/min, 1500/day)
- **Groq Llama 3.3 70B** — fallback LLM (also free tier)
- **python-dotenv** — local secrets loading

## Setup

```powershell
# 1. Clone the repo
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>

# 2. Create a virtual environment and install deps
python -m venv .venv
.\.venv\Scripts\Activate.ps1     # Windows PowerShell
# source .venv/bin/activate      # macOS/Linux
pip install -r requirements.txt

# 3. Get free API keys
#    Gemini: https://aistudio.google.com/apikey
#    Groq:   https://console.groq.com/keys

# 4. Copy the env template and fill in your keys
Copy-Item .env.example .env
# then edit .env to paste your keys

# 5. Run
python -m streamlit run tutor.py
# opens http://localhost:8501
```

## How a session flows

1. Click **Start today's session** — agent reads `Output/progress.md` to see where you left off, picks today's chapter from the learning plan.
2. Read the concept review. Answer 4 quiz questions (3 anchor + 1 stretch). Multiple-choice questions show ✓/✗ feedback the moment you pick.
3. Submit answers, get graded with explanations focused on the stretch question.
4. Open the auto-generated exercise at `Output/exercises/YYYY-MM-DD.py`, write your solution in the text box, submit.
5. Get a code review focused on correctness + one idiomatic improvement.
6. Read an apply-at-work suggestion — rotated across three angles (sysadmin / cybersecurity / AI agents) by Python code, not the LLM.
7. Drop an optional 1-word feeling note. Session logged to `progress.md`.

## Customization

- **`Workflows/python-tutor-daily.md`** is loaded at runtime as the agent's system prompt. Edit this plain-English recipe to change how the tutor behaves — no code changes required.
- **`Resources/python-learning-plan.md`** tracks your MOOC position. Created on first run.
- **`Resources/supplementary-resources.md`** lists external resources (Automate the Boring Stuff, Anthropic Cookbook, PicoCTF, etc.) the tutor pulls from as you progress through the MOOC.

## Privacy / per-user state

Personal data is gitignored — every user keeps their own local state:

- `.env` — your API keys
- `Output/progress.md` — your daily session log
- `Output/exercises/` — your code submissions
- `Resources/python-learning-plan.md` — your current chapter

Friends can clone the repo and run their own copy without seeing each other's data.

## Roadmap

- ✅ Stage 1 — concept + 1 stretch question, end-to-end stack validation
- ✅ Stage 2 — full daily session (concept + 4 quiz Qs + exercise + apply-at-work + log)
- ⏳ Stage 3 — deploy to Streamlit Community Cloud for phone-accessible URL
- ⏳ Stage 4+ — refactor into functions/classes/modules as Python skills grow; the codebase is itself a learning artifact
