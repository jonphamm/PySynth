# PySynth — How We Built It

A walk-through of every tool used and every step taken to ship PySynth, the Python tutor app, from a local Streamlit prototype to a fully deployed PWA with push notifications on iOS.

Audience: someone curious about full-stack web apps who hasn't built one before. The goal isn't that you re-type every line — it's that you understand the moving pieces and roughly the order they go in.

---

## What PySynth is

A daily Python practice agent. You answer a few quiz questions, write a small piece of code, and an LLM grades it and explains what could be better. Streaks, sessions, and review history live in a database. There's an iOS push notification each evening if you haven't logged a session that day.

**Live:**
- Frontend: https://py-synth.vercel.app
- Backend API: https://pysynth.onrender.com

---

## The full tech stack

### Frontend (what the user sees in their browser)
| Tool | What it is | Why we used it |
|---|---|---|
| **Next.js 16** | A React-based framework for building websites and apps | Best-in-class developer experience; deploys to Vercel in one click |
| **React** | Library for building UI as composable components | The de facto standard for modern web UIs |
| **TypeScript** | JavaScript with type checking added | Catches whole classes of bugs before you run the code |
| **Tailwind CSS v4** | Utility-first CSS — write `class="px-4 text-red-500"` instead of writing CSS files | Fast styling without context-switching to a separate file |
| **Framer Motion** | Animation library for React | Smooth page transitions and micro-interactions |
| **Geist Sans + Fira Code** | Fonts (the latter is monospace, for code blocks) | Modern look, free, easy to load via Next.js |

### Backend (the server the frontend talks to)
| Tool | What it is | Why we used it |
|---|---|---|
| **Python 3.11+** | The programming language | Wide ecosystem; matches what Jon is learning |
| **FastAPI** | Modern Python framework for building APIs | Async-first, auto-generates API docs, great error messages |
| **Uvicorn** | An "ASGI server" — the thing that actually runs your FastAPI app | Required to serve a FastAPI app in production |
| **SQLAlchemy 2.0 (async)** | An ORM — lets you write database queries in Python instead of raw SQL | The standard for Python DB access |
| **Alembic** | Database migration tool — versions your DB schema in Git, just like code | So you can change tables safely over time |
| **asyncpg** | Async Postgres driver | Fast, modern, plays well with SQLAlchemy async |
| **pywebpush + py_vapid** | Libraries for sending Web Push notifications | The standard way to push notifications to a browser/PWA |
| **Pillow (PIL)** | Python imaging library | Generated the PWA icons from a source PNG |

### Database
| Tool | What it is | Why we used it |
|---|---|---|
| **PostgreSQL** | A battle-tested open-source relational database | The pragmatic default in 2026 |
| **Neon** | A cloud-hosted Postgres provider with a free tier | No credit card needed; auto-pauses when idle to save money |

### Hosting / Infrastructure
| Tool | What it is | Why we used it |
|---|---|---|
| **Vercel** | Hosting platform optimized for Next.js | Push to GitHub → auto-deploys. Free tier covers personal apps |
| **Render** | Cloud platform for running web services from a Docker image | Card-free signup; free tier; runs the backend |
| **GitHub** | Where the code lives | Plus GitHub Actions for the daily cron job |
| **GitHub Actions** | Runs scripts on a schedule (cron) directly from your repo | Free, no extra service to manage. Triggers the daily push reminder |
| **Docker** | Packages your app + dependencies into a portable container | Render runs the backend from a Docker image we define |

### Third-party APIs (the actual "AI" behind the tutor)
| Provider | Role | Free tier? |
|---|---|---|
| **Google Gemini** | Primary LLM | Yes |
| **Groq** | Fallback #1 (very fast inference) | Yes |
| **Cerebras** | Fallback #2 | Yes |
| **OpenRouter** | Fallback #3 (aggregates many models) | Yes |

We chain them: if Gemini is rate-limited, we try Groq, then Cerebras, then OpenRouter. This is what `shared/llm.py` does.

### Dev tools (what you'd install on your machine)
| Tool | What it is |
|---|---|
| **Git** | Version control (tracks every change you make) |
| **VS Code** | Code editor |
| **Node.js + npm** | Runs the JavaScript/TypeScript side |
| **Python venv** | Isolates Python dependencies per project |
| **Claude Code** | The AI agent (me) that helped build it |

---

## How it all fits together

```
                 ┌─────────────────────────────────┐
                 │  User's browser / iPhone PWA    │
                 │  (Next.js frontend on Vercel)   │
                 └──────────────┬──────────────────┘
                                │   HTTPS + X-User-Id header
                                ▼
                 ┌─────────────────────────────────┐
                 │  FastAPI backend on Render      │
                 │  (Python, in a Docker image)    │
                 └──────┬──────────────────┬───────┘
                        │                  │
                        ▼                  ▼
              ┌─────────────────┐  ┌──────────────────┐
              │  Postgres on    │  │  LLM providers:  │
              │  Neon           │  │  Gemini/Groq/... │
              └─────────────────┘  └──────────────────┘

                     GitHub Actions cron (00:00 UTC)
                                │
                                ▼
                        POST /push/send-daily
                                │
                                ▼
                     Apple Push Notification Service
                                │
                                ▼
                            iPhone 📱
```

---

## How to recreate this app (the path we actually walked)

### Phase 0 — Local prototype (you can skip this)
We started in Streamlit (a quick Python UI framework). It got the idea working but its CSS overrides became painful. We rewrote it from scratch in Next.js + FastAPI. **Lesson: prototypes are throwaway by design — that's fine.**

### Phase 1 — Set up the project skeleton

1. **Make a folder, init git, create a GitHub repo.**
   ```
   mkdir pysynth
   cd pysynth
   git init
   ```
2. **Scaffold the frontend** with Next.js (one command creates the whole React + TS + Tailwind setup):
   ```
   npx create-next-app@latest frontend --typescript --tailwind --app
   ```
3. **Scaffold the backend** as a plain Python folder with a virtual environment:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   mkdir backend
   pip install fastapi uvicorn sqlalchemy asyncpg alembic
   ```
4. **Write a "hello world" FastAPI app** in `backend/app.py` and run it: `uvicorn backend.app:app --reload`. Visit `http://localhost:8000/docs` to see the auto-generated API docs.

### Phase 2 — Get the core flow working locally

5. **Define your data model** (in `backend/db.py`): users, sessions, messages, etc., using SQLAlchemy classes.
6. **Set up Alembic** so schema changes can be versioned: `alembic init backend/migrations`. Every time you change a table, run `alembic revision --autogenerate -m "what changed"` and then `alembic upgrade head`.
7. **Build the API endpoints**: `/session/start`, `/session/log`, etc., in `backend/app.py`.
8. **Wire up the LLM calls** in `shared/llm.py` — call Gemini's API with the user's question + the system prompt, return the response.
9. **Build the frontend UI** — pages, components, an API client (`frontend/src/lib/api.ts`) that calls the backend.
10. **Iterate** until the full flow works locally: start a session, answer questions, get graded, see history.

### Phase 3 — Add anonymous identity

The simplest possible "who are you" without making users sign up:
- On first visit, the browser generates a UUID v4 and stores it in `localStorage`.
- Every API request sends `X-User-Id: <that-uuid>` as a header.
- The backend has a FastAPI **dependency** (`get_user_id`) that reads the header and looks up/creates the user row.

That's it — no passwords, no email, no OAuth. Good enough for v1. Cross-device sync (claiming the same UUID on a phone after starting on desktop) is deferred for later.

### Phase 4 — Deploy

This is where most personal projects die. Each piece deploys differently:

11. **Neon (database):** Create a Neon account, create a project, copy the `DATABASE_URL`. That's the entire setup.
12. **Render (backend):**
    - Create a `Dockerfile` in `backend/` describing how to build the image.
    - Push to GitHub.
    - In Render, create a Web Service from your repo, point at the Dockerfile.
    - Add env vars: `DATABASE_URL`, `GEMINI_API_KEY`, etc.
    - Render builds the image, deploys it, gives you a `*.onrender.com` URL.
13. **Vercel (frontend):**
    - Connect your GitHub repo in Vercel.
    - Set the "root directory" to `frontend/` (since the repo has both backend and frontend).
    - Vercel auto-detects Next.js and deploys on every push.
    - Add `NEXT_PUBLIC_API_BASE_URL` env var pointing at your Render URL.
14. **CORS:** The backend has to allow the frontend's domain. Set `ALLOWED_ORIGIN=https://py-synth.vercel.app` as a Render env var; the backend reads it and configures FastAPI CORS.

At this point the app is live on the internet. 🎉

### Phase 5 — Make it a PWA (Progressive Web App)

A PWA is a website that can be "installed" to a phone's home screen and feels app-like. Steps:

15. **Add a manifest** (`frontend/src/app/manifest.ts`) — tells iOS/Android the app's name, colors, icons.
16. **Add a service worker** (`frontend/public/sw.js`) — a background script the browser keeps alive. It handles push notification events.
17. **Generate icons** at various sizes (192×192, 512×512, 180×180 for Apple) and put them in `frontend/public/`.
18. **Set the right `<head>` tags** in `frontend/src/app/layout.tsx`: `apple-touch-icon`, `theme-color`, `viewport-fit=cover`.

Test by opening the site in Safari on iPhone → Share → Add to Home Screen. The app icon appears, opening it gives a full-screen app shell with no browser chrome.

### Phase 6 — Add iOS daily push reminders

The hardest part. Apple gates Web Push behind PWA installation, and the developer experience is full of subtle traps.

19. **Generate a VAPID keypair** (Voluntary Application Server Identification — proves to the browser that the push is from your server). Use a script with the `cryptography` Python library to generate a P-256 EC keypair.
    - **The single trickiest gotcha:** Don't paste a multi-line PEM key into a cloud env-var textbox. The cloud platform (Render, Vercel, etc.) silently mangles the whitespace. Store the raw 32-byte private key as a **single-line base64url string** instead. Lesson burned-in over ~45 minutes of debugging an opaque `ASN.1 parsing error`.
20. **Backend:**
    - Add a `push_subscriptions` table (Alembic migration).
    - Add `/push/subscribe`, `/push/unsubscribe`, `/push/send-daily` endpoints.
    - `/push/send-daily` requires a `CRON_SECRET` Bearer token (so only our cron, not anyone on the internet, can trigger it).
    - Send pushes via `pywebpush`.
21. **Frontend:**
    - In `lib/push.ts`, helpers to register the service worker, request notification permission, subscribe via the browser's PushManager API, and POST the subscription to the backend.
    - A `NotificationsToggle` component in the sidebar. State machine: not iOS / not installed / permission denied / ready-to-enable / enabled.
22. **Cron:** A GitHub Actions workflow (`.github/workflows/daily-reminder.yml`) runs daily at 00:00 UTC and calls `/push/send-daily` with the bearer token. Free, no extra service needed.

### Phase 7 — Polish

- Safe-area-inset CSS so the iPhone notch / Dynamic Island doesn't cover the header.
- Custom PWA icon artwork (Python logo + a "by: JP" watermark) generated by a Python script from a source PNG.
- Connection pool tuning so Neon's idle-connection drops don't 502 the app.

---

## Lessons learned (the bugs that ate the most time)

1. **Web Push private keys → single-line base64url, never PEM in cloud env vars.** Render's env-var UI mangles multi-line whitespace silently. Also: `py_vapid.Vapid.from_string()` doesn't actually parse PEM — it base64url-decodes the whole input. Both pushed us to single-line base64url.
2. **iOS Safari hides the Notification API in regular tabs.** It only exists inside an installed PWA. So we can't feature-detect "does this browser support push?" — we have to UA-detect iOS, then check standalone mode, then show the install prompt or the toggle.
3. **`~exists(...)` correlated subqueries silently return 0 rows in SQLAlchemy 2.0 async.** Don't fight it — rewrite as `LEFT JOIN ... WHERE other_table.id IS NULL`. Much more reliable.
4. **Neon free tier drops idle DB connections.** Use SQLAlchemy's `pool_pre_ping=True` + `pool_recycle=300` so reconnects are transparent.
5. **Don't run `npm` in a folder synced by Google Drive / OneDrive.** `node_modules` has tens of thousands of files; the sync client + npm fight each other. Keep dev work on a non-synced drive.
6. **Render free tier sleeps after 15 min idle**, with a ~30s cold start. Acceptable for personal use; a $7/mo paid tier or an external uptime ping would fix it.
7. **iOS aggressively caches PWA icons.** Updating an icon requires deleting the home-screen PWA and re-installing. Plan for that during icon iteration.

---

## What we explicitly chose not to build (yet)

These are good "phase 2" projects if you want to extend it:

- **Cross-device identity (sync code / QR).** Today, your phone and laptop are two separate users. A "scan this QR to claim that UUID on this device" flow would fix it.
- **Configurable reminder time.** Cron fires at one time for everyone (00:00 UTC). Per-user reminder time + timezone is a small but meaningful feature.
- **Streak-aware reminder copy.** "You're on day 5, don't break it" reads better than "Time for today's session."
- **Custom domain.** `py-synth.vercel.app` is fine but a real domain looks more polished.
- **Date-semantics fix.** The backend uses UTC `date.today()` to decide "did you study today" — late-night sessions in eastern time can land on the next UTC day. Accept a `local_date` from the frontend to fix.

---

## Glossary (terms that come up a lot)

- **API** — Application Programming Interface. The set of URLs your backend exposes for the frontend to call.
- **ASGI** — Async Server Gateway Interface. The "protocol" between Uvicorn and FastAPI.
- **Cron** — A scheduled job. "Cron fires at midnight" means "the scheduler runs this script at midnight."
- **CORS** — Cross-Origin Resource Sharing. Browser security feature; the backend has to explicitly allow the frontend's domain to call it.
- **Docker image** — A snapshot of your app + its dependencies + a tiny OS, packaged so it runs the same anywhere.
- **Env var (environment variable)** — A configuration value set outside the code (like API keys). Never commit them to Git.
- **ORM** — Object-Relational Mapper. Lets you write `user = User(name="Jon")` in Python instead of `INSERT INTO users (name) VALUES ('Jon')` in SQL.
- **PWA** — Progressive Web App. A website that can be installed to a phone's home screen and feels app-like.
- **Service worker** — A background JavaScript file the browser keeps running even when your tab is closed. Required for push notifications and offline support.
- **VAPID** — Voluntary Application Server Identification. The keypair that proves to the browser that a push notification came from your server.

---

## Final tip for the friend

Don't try to do all of this at once. The path that worked:
1. Get a "hello world" frontend talking to a "hello world" backend on your laptop.
2. Add one feature end-to-end (backend route + frontend page + database table).
3. Deploy that one feature to the internet.
4. Repeat.

If a step takes more than a day, the step is too big — break it down further. And when something fails opaquely (like our VAPID key disaster), the bug is almost always in the layer you trust most. Question that layer first.
