"""
Python Tutor — Streamlit UI.

Multi-stage wizard implementing the python-tutor-daily recipe:
  start → concept+quiz → graded → exercise → graded → apply-at-work → wrap → done

Shared LLM / validation / progress logic lives in `shared/` and is also used
by the FastAPI backend that powers PySynth.

Run:  streamlit run tutor.py
"""

import math
import random
import re
import textwrap
from datetime import date
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from shared.chapters import next_chapter, quote_of_the_day
from shared.config import load_text
from shared.llm import call_llm, call_llm_json
from shared.progress import (
    PROGRESS_PATH,
    append_progress_row,
    append_solution,
    pick_next_angle,
    write_exercise_file,
)
from shared.prompts import (
    build_system_prompt,
    exercise_user_message,
    grade_user_message,
    review_user_message,
    start_user_message,
)
from shared.validators import (
    render_exercise_markdown,
    validate_exercise_data,
    validate_session_data,
)


# ---------------- Streamlit UI ----------------

st.set_page_config(page_title="Python Tutor", page_icon="🐍", layout="centered")

# Theme-agnostic injection: Inter font + animation keyframes.
# Idempotent — runs once per page load, not per rerun.
components.html(
    """
    <script>
    (function() {
      try {
        const PARENT = window.parent;
        const doc = PARENT.document;
        if (doc.querySelector('#tutor-fx-marker')) return;
        const marker = doc.createElement('div');
        marker.id = 'tutor-fx-marker';
        marker.style.display = 'none';
        doc.body.appendChild(marker);

        const fontLink = doc.createElement('link');
        fontLink.rel = 'stylesheet';
        fontLink.href = 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap';
        doc.head.appendChild(fontLink);

        const styleEl = doc.createElement('style');
        styleEl.textContent = `
          [data-testid="stToolbar"], footer { display: none !important; }
          @keyframes daystartHorizon {
            0% { height: 0; opacity: 0; }
            40% { height: 60vh; opacity: 0.65; }
            100% { height: 60vh; opacity: 0.0; }
          }
          @keyframes daystartParticle {
            0% { transform: translate(-50%, -50%) scale(0.2); opacity: 1; }
            100% { transform: translate(calc(-50% + var(--dx)), calc(-50% + var(--dy))) scale(1); opacity: 0; }
          }
          @keyframes daystartArc {
            0% { transform: translate(-50%, -50%) scale(0.2); opacity: 0; }
            40% { transform: translate(-50%, -50%) scale(1.1); opacity: 1; }
            70% { transform: translate(-50%, -50%) scale(0.95); opacity: 0.9; }
            100% { transform: translate(-50%, -50%) scale(1); opacity: 0; }
          }
          @keyframes daystartFlash {
            0% { transform: translate(-50%, -50%) scale(0); opacity: 0; }
            45% { transform: translate(-50%, -50%) scale(1.6); opacity: 0.9; }
            100% { transform: translate(-50%, -50%) scale(2); opacity: 0; }
          }
          @keyframes daystartLabel {
            0% { transform: translate(-50%, calc(-50% + 12px)); opacity: 0; }
            30% { transform: translate(-50%, -50%); opacity: 1; }
            85% { transform: translate(-50%, -50%); opacity: 1; }
            100% { transform: translate(-50%, calc(-50% - 12px)); opacity: 0; }
          }
          @keyframes daystartFade {
            0% { opacity: 1; }
            85% { opacity: 1; }
            100% { opacity: 0; pointer-events: none; }
          }
          @keyframes topbarShimmer {
            0% { background-position: 0% 0; }
            100% { background-position: 200% 0; }
          }
          @keyframes auroraDriftA {
            0%   { transform: translate(-15vw, -15vh) scale(1); }
            50%  { transform: translate(40vw, 25vh) scale(1.15); }
            100% { transform: translate(-15vw, -15vh) scale(1); }
          }
          @keyframes auroraDriftB {
            0%   { transform: translate(35vw, 35vh) scale(1); }
            50%  { transform: translate(-20vw, -10vh) scale(1.1); }
            100% { transform: translate(35vw, 35vh) scale(1); }
          }
        `;
        doc.head.appendChild(styleEl);
      } catch (err) {
        console.warn('Tutor FX injection failed:', err);
      }
    })();
    </script>
    """,
    height=0,
)

DEFAULTS = {
    "stage": "start",
    "angle": None,
    "session_data": None,
    "user_answers": ["", "", "", ""],
    "quiz_grade": None,
    "exercise_data": None,
    "exercise_text": None,
    "exercise_path": None,
    "apply_at_work": None,
    "user_code": "",
    "code_review": None,
    "feeling": "",
    "provider": None,
    "completion_played": False,
    "theme_mode": "dark",
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


def reset_session() -> None:
    for k in list(st.session_state.keys()):
        del st.session_state[k]


def reset_button() -> None:
    if st.button("Reset session", help="Discard progress and start over"):
        reset_session()
        st.rerun()


# -------- Theme + ambient background --------

DARK_TOKENS = """
    --tutor-bg: #0a0a0a;
    --tutor-surface: #161616;
    --tutor-surface-2: #1c1c1c;
    --tutor-card: #141414;
    --tutor-text: #f5f5f5;
    --tutor-text-dim: #9aa0a6;
    --tutor-border: rgba(255,107,53,0.18);
    --tutor-border-soft: rgba(255,107,53,0.12);
    --tutor-accent: #ff6b35;
    --tutor-accent-2: #ffae42;
    --tutor-accent-deep: #e8431f;
    --tutor-track-bg: rgba(255,255,255,0.06);
    --tutor-blob-opacity: 0.18;
    --tutor-quote: #d8d8d8;
    --tutor-quote-attr: #9aa0a6;
    --tutor-row-border: rgba(255,255,255,0.05);
    --tutor-card-shadow: 0 12px 40px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,0.04);
    --tutor-topbar-bg: linear-gradient(180deg, rgba(10,10,10,0.92) 0%, rgba(10,10,10,0.0) 100%);
    --tutor-topbar-blur: blur(8px);
    --tutor-completion-particle: #ff6b35;
    --tutor-completion-label: #fff;
"""

LIGHT_TOKENS = """
    --tutor-bg: #faf8f4;
    --tutor-surface: #ffffff;
    --tutor-surface-2: #f5f3ee;
    --tutor-card: #ffffff;
    --tutor-text: #1a1a1a;
    --tutor-text-dim: #6b7280;
    --tutor-border: rgba(232,67,31,0.22);
    --tutor-border-soft: rgba(232,67,31,0.12);
    --tutor-accent: #e8431f;
    --tutor-accent-2: #ff6b35;
    --tutor-accent-deep: #c0301a;
    --tutor-track-bg: rgba(0,0,0,0.06);
    --tutor-blob-opacity: 0.32;
    --tutor-quote: #4a4a4a;
    --tutor-quote-attr: #6b7280;
    --tutor-row-border: rgba(0,0,0,0.06);
    --tutor-card-shadow: 0 12px 40px rgba(232,67,31,0.10), inset 0 1px 0 rgba(255,255,255,0.7);
    --tutor-topbar-bg: linear-gradient(180deg, rgba(250,248,244,0.92) 0%, rgba(250,248,244,0.0) 100%);
    --tutor-topbar-blur: blur(8px);
    --tutor-completion-particle: #e8431f;
    --tutor-completion-label: #1a1a1a;
"""


def render_theme_css() -> None:
    """Emit theme-dependent CSS variables, component styles, and the two ambient
    background blobs. Re-runs on every Streamlit rerun so theme toggles apply cleanly."""
    mode = st.session_state.get("theme_mode", "dark")
    tokens = LIGHT_TOKENS if mode == "light" else DARK_TOKENS
    template = textwrap.dedent("""
        <style>
        :root { __TOKENS__ }
        [data-testid="stApp"], [data-testid="stApp"] * {
            font-family: 'Inter', -apple-system, "Segoe UI Variable", "Segoe UI", system-ui, sans-serif !important;
        }
        [data-testid="stApp"] {
            background: var(--tutor-bg) !important;
            color: var(--tutor-text) !important;
        }
        [data-testid="stAppViewContainer"], [data-testid="stMain"], section.main {
            background: transparent !important;
        }
        [data-testid="stHeader"] { background: transparent !important; }
        h1, h2, h3, h4, h5 { color: var(--tutor-text) !important; letter-spacing: -0.01em !important; }
        p, span, label, li { color: var(--tutor-text); }
        /* Primary buttons */
        div[data-testid="stButton"] > button[kind="primary"] {
            background: linear-gradient(135deg, var(--tutor-accent-2) 0%, var(--tutor-accent-deep) 100%) !important;
            color: #fff !important;
            border: none !important;
            border-radius: 14px !important;
            padding: 0.75em 1.5em !important;
            font-weight: 700 !important;
            letter-spacing: 0.3px !important;
            box-shadow: 0 6px 20px rgba(255,107,53,0.28) !important;
            transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease !important;
        }
        div[data-testid="stButton"] > button[kind="primary"]:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 10px 28px rgba(255,107,53,0.42) !important;
            filter: brightness(1.08) !important;
        }
        div[data-testid="stButton"] > button[kind="primary"]:active {
            transform: translateY(0) scale(0.98) !important;
        }
        /* Secondary buttons */
        div[data-testid="stButton"] > button:not([kind="primary"]) {
            background: var(--tutor-surface) !important;
            color: var(--tutor-text) !important;
            border: 1px solid var(--tutor-border) !important;
            border-radius: 12px !important;
            font-weight: 500 !important;
            transition: border-color 0.15s ease, background 0.15s ease !important;
        }
        div[data-testid="stButton"] > button:not([kind="primary"]):hover {
            border-color: var(--tutor-accent) !important;
            background: var(--tutor-surface-2) !important;
        }
        /* Radio options as pills */
        div[data-testid="stRadio"] [role="radiogroup"] label {
            background: var(--tutor-surface) !important;
            border: 1px solid var(--tutor-border-soft) !important;
            border-radius: 12px !important;
            padding: 0.7em 1em !important;
            margin: 0.4em 0 !important;
            transition: border-color 0.15s ease, background 0.15s ease !important;
        }
        div[data-testid="stRadio"] [role="radiogroup"] label:hover {
            border-color: var(--tutor-accent) !important;
            background: var(--tutor-surface-2) !important;
        }
        /* Code blocks */
        [data-testid="stCodeBlock"] pre,
        [data-testid="stCode"] pre {
            background: var(--tutor-surface) !important;
            border: 1px solid var(--tutor-border-soft) !important;
            border-radius: 12px !important;
            color: var(--tutor-text) !important;
        }
        /* Inputs / textareas */
        [data-baseweb="input"] input,
        [data-baseweb="textarea"] textarea {
            background: var(--tutor-surface) !important;
            border-color: var(--tutor-border) !important;
            color: var(--tutor-text) !important;
            border-radius: 12px !important;
        }
        [data-baseweb="input"]:focus-within,
        [data-baseweb="textarea"]:focus-within {
            border-color: var(--tutor-accent) !important;
        }
        [data-testid="stAlert"] { border-radius: 12px !important; }
        /* Aurora background blobs */
        .tutor-aurora {
            position: fixed;
            z-index: 0;
            pointer-events: none;
            border-radius: 50%;
            filter: blur(80px);
            opacity: var(--tutor-blob-opacity);
            will-change: transform;
        }
        .tutor-aurora-a {
            width: 70vw; height: 70vw;
            max-width: 1100px; max-height: 1100px;
            top: -20vh; left: -20vw;
            background: radial-gradient(circle, var(--tutor-accent) 0%, var(--tutor-accent) 25%, rgba(255,107,53,0) 70%);
            animation: auroraDriftA 65s ease-in-out infinite;
        }
        .tutor-aurora-b {
            width: 55vw; height: 55vw;
            max-width: 900px; max-height: 900px;
            bottom: -15vh; right: -15vw;
            background: radial-gradient(circle, var(--tutor-accent-2) 0%, var(--tutor-accent-2) 25%, rgba(255,174,66,0) 70%);
            animation: auroraDriftB 80s ease-in-out infinite;
        }
        /* Make sure Streamlit content sits above the blobs */
        [data-testid="stAppViewContainer"] section.main { position: relative; z-index: 1; }
        /* Theme-toggle: fixed top-right circular icon button (renders as first horizontal block) */
        section.main div[data-testid="stHorizontalBlock"]:first-of-type {
            position: fixed !important;
            top: 14px;
            right: 18px;
            z-index: 9501;
            width: auto !important;
            margin: 0 !important;
            gap: 0 !important;
        }
        section.main div[data-testid="stHorizontalBlock"]:first-of-type,
        section.main div[data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="column"] {
            background: transparent !important;
        }
        section.main div[data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="column"]:not(:last-child) {
            display: none !important;
        }
        /* Loading spinner: warm-orange ring, theme-aware caption */
        [data-testid="stSpinner"] > div::before,
        [data-testid="stSpinner"] i,
        .stSpinner > div::before {
            border-top-color: var(--tutor-accent) !important;
            border-right-color: var(--tutor-accent) !important;
        }
        [data-testid="stSpinner"] svg { color: var(--tutor-accent) !important; fill: var(--tutor-accent) !important; }
        [data-testid="stSpinner"] > div { color: var(--tutor-text) !important; }
        section.main div[data-testid="stHorizontalBlock"]:first-of-type div[data-testid="stButton"] > button {
            padding: 0 !important;
            min-height: unset !important;
            height: 2.4em !important;
            width: 2.4em !important;
            font-size: 1.1em !important;
            line-height: 1 !important;
            border-radius: 50% !important;
            background: var(--tutor-surface) !important;
            border: 1px solid var(--tutor-border-soft) !important;
            color: var(--tutor-text) !important;
            font-weight: 500 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.20) !important;
        }
        section.main div[data-testid="stHorizontalBlock"]:first-of-type div[data-testid="stButton"] > button:hover {
            border-color: var(--tutor-accent) !important;
            background: var(--tutor-surface-2) !important;
        }
        </style>
        <div class="tutor-aurora tutor-aurora-a"></div>
        <div class="tutor-aurora tutor-aurora-b"></div>
    """)
    st.markdown(template.replace("__TOKENS__", tokens), unsafe_allow_html=True)


def render_theme_toggle() -> None:
    """Top-right sun/moon button that flips between dark and light mode."""
    is_dark = st.session_state.get("theme_mode", "dark") == "dark"
    icon = "🌙" if is_dark else "☀️"
    target = "light" if is_dark else "dark"
    cols = st.columns([14, 1])
    with cols[1]:
        if st.button(icon, key="theme_toggle", help=f"Toggle theme — switch to {target} mode"):
            st.session_state.theme_mode = target
            st.rerun()


# -------- Progress bar + completion animation --------

PROGRESS_TOTAL = 6


def progress_done() -> int:
    """How many of today's six milestones the user has completed."""
    done = 0
    answers = st.session_state.get("user_answers") or []
    for a in answers[:4]:
        if isinstance(a, str) and a.strip():
            done += 1
    if (st.session_state.get("user_code") or "").strip():
        done += 1
    if st.session_state.get("stage") == "done":
        done += 1
    return min(done, PROGRESS_TOTAL)


def render_topbar() -> None:
    """Sticky-top daily progress bar. Hidden on `start` and `done` stages."""
    stage = st.session_state.get("stage")
    if stage in ("start", "done"):
        return
    done = progress_done()
    pct = round(done / PROGRESS_TOTAL * 100)
    st.markdown(
        textwrap.dedent(f"""
        <style>
        .tutor-topbar-wrap {{
            position: fixed;
            top: 0; left: 0; right: 0;
            z-index: 9000;
            padding: 14px 22px 10px 22px;
            background: var(--tutor-topbar-bg);
            backdrop-filter: var(--tutor-topbar-blur);
            -webkit-backdrop-filter: var(--tutor-topbar-blur);
            display: flex;
            align-items: center;
            gap: 14px;
        }}
        .tutor-topbar-track {{
            flex: 1;
            height: 4px;
            background: var(--tutor-track-bg);
            border-radius: 999px;
            overflow: hidden;
            position: relative;
        }}
        .tutor-topbar-fill {{
            position: absolute;
            inset: 0;
            border-radius: 999px;
            background:
                linear-gradient(90deg, var(--tutor-accent) 0%, var(--tutor-accent-2) 50%, var(--tutor-accent) 100%);
            background-size: 200% 100%;
            animation: topbarShimmer 2.6s linear infinite;
            transform-origin: left center;
            transform: scaleX({done / PROGRESS_TOTAL});
            transition: transform 600ms cubic-bezier(0.2, 0.8, 0.2, 1);
            box-shadow: 0 0 18px rgba(255,107,53,0.55);
        }}
        .tutor-topbar-count {{
            font-size: 0.78em;
            font-weight: 600;
            letter-spacing: 1px;
            color: var(--tutor-text-dim);
            min-width: 48px;
            text-align: right;
        }}
        .tutor-topbar-label {{
            font-size: 0.72em;
            font-weight: 700;
            letter-spacing: 2.5px;
            color: var(--tutor-accent);
            text-transform: uppercase;
        }}
        [data-testid="stAppViewContainer"] section.main > div.block-container {{
            padding-top: 4.2rem !important;
        }}
        </style>
        <div class="tutor-topbar-wrap">
          <span class="tutor-topbar-label">Today</span>
          <div class="tutor-topbar-track"><div class="tutor-topbar-fill"></div></div>
          <span class="tutor-topbar-count">{pct}%</span>
        </div>
        """),
        unsafe_allow_html=True,
    )


def play_completion_animation() -> None:
    """Full-screen 'Daystart Sequence' on the done stage. Plays once per session."""
    if st.session_state.get("completion_played"):
        return
    st.session_state.completion_played = True

    particles = []
    rng = random.Random("completion")
    for i in range(24):
        angle = (i / 24) * 2 * math.pi + (rng.random() - 0.5) * 0.4
        dist = 180 + rng.random() * 220
        dx = round(math.cos(angle) * dist, 1)
        dy = round(math.sin(angle) * dist, 1)
        delay = round(rng.random() * 0.25, 3)
        size = 4 + rng.random() * 6
        particles.append(
            f'<div style="position:absolute;left:50%;top:50%;width:{size:.1f}px;height:{size:.1f}px;'
            f'border-radius:50%;background:var(--tutor-completion-particle);'
            f'box-shadow:0 0 14px var(--tutor-completion-particle);filter:blur(0.5px);'
            f'transform:translate(-50%,-50%);'
            f'animation:daystartParticle 1.4s {0.6 + delay:.3f}s cubic-bezier(0.15,0.7,0.2,1) forwards;'
            f'--dx:{dx}px;--dy:{dy}px;"></div>'
        )

    overlay_html = f"""
    <div id="daystart-overlay" style="
        position: fixed; inset: 0; z-index: 99999; pointer-events: none;
        background: radial-gradient(ellipse at center, rgba(0,0,0,0) 30%, rgba(255,107,53,0.18) 100%);
        animation: daystartFade 2.8s ease-out forwards;
        overflow: hidden;
    ">
      <div style="
          position: absolute; left: 0; right: 0; top: 50%;
          height: 60vh; transform: translateY(-50%);
          background: linear-gradient(180deg, rgba(255,107,53,0) 0%, rgba(255,107,53,0.55) 50%, rgba(255,107,53,0) 100%);
          filter: blur(6px);
          animation: daystartHorizon 2.2s ease-out forwards;
      "></div>
      <div style="
          position: absolute; left: 50%; top: 50%;
          width: 70vw; height: 70vw; max-width: 720px; max-height: 720px;
          border-radius: 50%;
          background: radial-gradient(circle at center, rgba(255,174,66,0.55) 0%, rgba(255,107,53,0.15) 35%, rgba(255,107,53,0) 70%);
          transform: translate(-50%, -50%) scale(0);
          animation: daystartFlash 1.6s 0.8s ease-out forwards;
          filter: blur(2px);
      "></div>
      <div style="
          position: absolute; left: 50%; top: 50%;
          width: 80vw; height: 18vw; max-width: 900px; max-height: 200px;
          border-radius: 100%;
          border-top: 3px solid var(--tutor-accent);
          box-shadow: 0 -10px 60px rgba(255,107,53,0.6), inset 0 4px 20px rgba(255,174,66,0.4);
          transform: translate(-50%, -50%) scale(0.2);
          animation: daystartArc 2.0s 0.5s cubic-bezier(0.2,0.8,0.2,1) forwards;
      "></div>
      {''.join(particles)}
      <div style="
          position: absolute; left: 50%; top: 50%;
          transform: translate(-50%, calc(-50% + 12px));
          font-family: 'Inter', system-ui, sans-serif;
          font-weight: 800;
          letter-spacing: 12px;
          font-size: clamp(28px, 5vw, 56px);
          color: var(--tutor-completion-label);
          text-shadow: 0 0 20px rgba(255,107,53,0.7), 0 0 40px rgba(255,107,53,0.4);
          opacity: 0;
          animation: daystartLabel 2.2s 1.4s ease-out forwards;
          white-space: nowrap;
      ">DAY COMPLETE</div>
    </div>
    """
    st.markdown(overlay_html, unsafe_allow_html=True)


# -------- Stage handlers --------

def stage_start() -> None:
    progress = load_text(PROGRESS_PATH)
    rows = [line for line in progress.splitlines() if line.startswith("| 2026-")]
    daily_rows = [r for r in rows if "Daily" in r.split("|")[2]]
    sessions_count = len(daily_rows)
    last_chapter_raw = "—"
    if daily_rows:
        cells = [c.strip() for c in daily_rows[-1].split("|")]
        if len(cells) > 3 and cells[3]:
            last_chapter_raw = cells[3]
    formatted_chapter = next_chapter(last_chapter_raw)
    quote_text, quote_attr = quote_of_the_day()
    next_angle = pick_next_angle()

    st.markdown(
        """
        <style>
        .landing-wrap { text-align: center; padding: 2.6em 0 1em 0; position: relative; z-index: 2; }
        .landing-visor {
            margin: 0 auto 1.4em auto;
            width: 240px;
            height: 28px;
            border-radius: 50%;
            background: radial-gradient(ellipse at center,
                var(--tutor-accent-2) 0%,
                var(--tutor-accent) 22%,
                rgba(255,107,53,0.45) 50%,
                rgba(255,107,53,0) 75%);
            filter: blur(0.6px);
            box-shadow:
                0 0 60px rgba(255,107,53,0.55),
                0 0 120px rgba(255,107,53,0.35);
            position: relative;
        }
        .landing-visor::before {
            content: "";
            position: absolute;
            left: 50%; top: 50%;
            width: 75%; height: 1.5px;
            transform: translate(-50%, -50%);
            background: linear-gradient(90deg,
                rgba(255,255,255,0) 0%,
                rgba(255,255,255,0.95) 50%,
                rgba(255,255,255,0) 100%);
            box-shadow: 0 0 14px rgba(255,255,255,0.85);
        }
        .landing-title {
            font-size: clamp(40px, 6.5vw, 68px);
            font-weight: 800;
            letter-spacing: -0.02em;
            color: var(--tutor-text);
            margin: 0 0 0.25em 0;
            text-shadow: 0 0 30px rgba(255,107,53,0.25);
        }
        .landing-subtitle {
            color: var(--tutor-text-dim);
            font-size: 0.78em;
            font-weight: 600;
            letter-spacing: 3px;
            text-transform: uppercase;
            margin: 0 0 2.2em 0;
        }
        .stats-card {
            background: var(--tutor-card);
            border: 1px solid var(--tutor-border-soft);
            border-radius: 18px;
            padding: 1.4em 1.6em 1.6em 1.6em;
            margin: 0 auto 2em auto;
            max-width: 520px;
            box-shadow: var(--tutor-card-shadow);
            text-align: left;
            position: relative;
            z-index: 2;
        }
        .stat-row {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            padding: 0.85em 0;
            border-bottom: 1px solid var(--tutor-row-border);
        }
        .stat-row:last-of-type { border-bottom: none; }
        .stat-label {
            color: var(--tutor-text-dim);
            font-size: 0.72em;
            font-weight: 600;
            letter-spacing: 2.5px;
            text-transform: uppercase;
        }
        .stat-value {
            color: var(--tutor-text);
            font-weight: 600;
            font-size: 1em;
            text-align: right;
            max-width: 65%;
        }
        .stat-value-num {
            color: var(--tutor-accent);
            font-weight: 700;
            font-size: 1.5em;
            text-shadow: 0 0 18px rgba(255,107,53,0.45);
        }
        .stat-quote {
            margin-top: 1.2em;
            padding-top: 1.1em;
            border-top: 1px solid var(--tutor-border-soft);
            color: var(--tutor-quote);
            font-style: italic;
            text-align: center;
            line-height: 1.55;
            font-size: 0.95em;
        }
        .stat-quote-attr {
            display: block;
            color: var(--tutor-quote-attr);
            font-size: 0.72em;
            margin-top: 0.7em;
            letter-spacing: 1.5px;
            font-style: normal;
        }
        </style>
        <div class="landing-wrap">
          <div class="landing-visor"></div>
          <h1 class="landing-title">Python Tutor</h1>
          <p class="landing-subtitle">MOOC.fi 2026 · Daily Session</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="stats-card">
          <div class="stat-row">
            <span class="stat-label">Sessions</span>
            <span class="stat-value-num">{sessions_count}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Up next</span>
            <span class="stat-value">{formatted_chapter}</span>
          </div>
          <div class="stat-quote">"{quote_text}"<span class="stat-quote-attr">— {quote_attr}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Start Today's Session", type="primary", use_container_width=True):
        st.session_state.angle = next_angle
        with st.spinner("Generating today's session…"):
            data, provider = call_llm_json(build_system_prompt(), start_user_message())
            st.session_state.session_data = validate_session_data(data)
            st.session_state.provider = provider
            st.session_state.stage = "concept_quiz"
        st.rerun()


def stage_concept_quiz() -> None:
    data = st.session_state.session_data or {}

    # Topic
    topic = data.get("topic") or {}
    if topic.get("chapter") or topic.get("concept"):
        st.subheader("📚 Topic")
        if topic.get("chapter"):
            st.markdown(f"**Chapter:** {topic['chapter']}")
        if topic.get("concept"):
            st.markdown(f"**Concept:** {topic['concept']}")

    # Concept review
    review = data.get("concept_review") or {}
    if any(review.values()):
        st.subheader("💡 Concept review")

        if review.get("definition"):
            st.markdown(f"**Definition** — {review['definition']}")

        if review.get("how_it_works"):
            st.markdown("**How it works**")
            for bullet in review["how_it_works"]:
                st.markdown(f"- {bullet}")

        if review.get("syntax_forms"):
            st.markdown("**Syntax forms**")
            for form in review["syntax_forms"]:
                label = form.get("label", "").strip()
                code = form.get("code", "").strip()
                if label:
                    st.markdown(f"*{label}*")
                if code:
                    st.code(code, language="python")

        if review.get("worked_example_code"):
            st.markdown("**Worked example**")
            st.code(review["worked_example_code"], language="python")
            if review.get("worked_example_walkthrough"):
                for step in review["worked_example_walkthrough"]:
                    st.markdown(f"- {step}")

        if review.get("common_patterns"):
            st.markdown("**Common patterns**")
            for pattern in review["common_patterns"]:
                st.markdown(f"- {pattern}")

        if review.get("when_to_use"):
            st.markdown(f"**When to use it** — {review['when_to_use']}")

        if review.get("analogy"):
            st.markdown(f"**Analogy** — {review['analogy']}")

        if review.get("gotcha"):
            st.markdown(f"**Watch out for** — {review['gotcha']}")

    # Quiz
    questions = data.get("questions") or []
    if questions:
        st.subheader("❓ Quiz")
    answers = []
    picked_indexes = []
    for i, q in enumerate(questions):
        st.markdown("---")
        st.markdown(f"**Question {i + 1}**")
        st.markdown(q.get("text", ""))
        if q.get("code"):
            st.code(q["code"], language="python")

        if q["type"] == "mc" and q.get("options"):
            options = q["options"]
            ans = st.radio(
                "Choose one:",
                options=options,
                index=None,
                key=f"answer_{i}",
            )
            picked_idx = options.index(ans) if ans in options else None
            picked_indexes.append(picked_idx)
            correct_idx = q.get("correct_index")
            if picked_idx is not None and correct_idx is not None:
                if picked_idx == correct_idx:
                    st.success("✓ Correct!")
                else:
                    st.error(f"✗ Wrong. Correct answer: **{options[correct_idx]}**")
            answers.append(ans or "")
        else:
            ans = st.text_area(
                "Your answer:",
                value=st.session_state.user_answers[i] if i < len(st.session_state.user_answers) else "",
                height=120,
                key=f"answer_{i}",
            )
            picked_indexes.append(None)
            answers.append(ans or "")

    st.markdown("---")
    col1, col2 = st.columns([1, 4])
    with col1:
        all_answered = all(a and a.strip() for a in answers) if questions else False
        submit = st.button("Submit answers", type="primary", disabled=not all_answered)
    with col2:
        reset_button()

    if submit:
        # Pad to length 4 so the grading prompt never IndexErrors on a partial parse.
        padded = list(answers) + [""] * (4 - len(answers))
        st.session_state.user_answers = padded[:4]
        with st.spinner("Grading…"):
            user_message = grade_user_message(questions, padded[:4], picked_indexes)
            response, provider = call_llm(build_system_prompt(), user_message)
            st.session_state.quiz_grade = response
            st.session_state.provider = provider
            st.session_state.stage = "graded_quiz"
        st.rerun()


def stage_graded_quiz() -> None:
    st.subheader("📝 Grade")
    st.markdown(st.session_state.quiz_grade)
    st.markdown("---")
    if st.button("Continue to coding exercise", type="primary"):
        with st.spinner("Preparing your coding exercise…"):
            angle = st.session_state.angle
            user_message = exercise_user_message(angle)
            data, provider = call_llm_json(build_system_prompt(), user_message)
            ex_data = validate_exercise_data(data)
            today_str = date.today().isoformat()
            exercise_md = render_exercise_markdown(ex_data["exercise"])
            st.session_state.exercise_data = ex_data
            st.session_state.exercise_text = exercise_md
            st.session_state.apply_at_work = ex_data["apply_at_work"].get("text", "")
            st.session_state.exercise_path = str(write_exercise_file(today_str, exercise_md))
            st.session_state.provider = provider
            st.session_state.stage = "exercise"
        st.rerun()
    reset_button()


def stage_exercise() -> None:
    st.subheader("⚙️ Coding exercise")
    st.markdown(st.session_state.exercise_text)
    st.markdown("---")
    st.subheader("Your solution")
    code = st.text_area(
        "Paste your Python code:",
        value=st.session_state.user_code,
        height=240,
        key="code_input",
    )
    col1, col2 = st.columns([1, 4])
    with col1:
        submit = st.button("Submit code", type="primary", disabled=not code.strip())
    with col2:
        reset_button()
    if submit:
        st.session_state.user_code = code
        if st.session_state.exercise_path:
            append_solution(Path(st.session_state.exercise_path), code)
        with st.spinner("Reviewing your code…"):
            user_message = review_user_message(st.session_state.exercise_text, code)
            response, provider = call_llm(build_system_prompt(), user_message)
            st.session_state.code_review = response
            st.session_state.provider = provider
            st.session_state.stage = "graded_exercise"
        st.rerun()


def stage_graded_exercise() -> None:
    st.subheader("🔍 Code review")
    st.markdown(st.session_state.code_review)
    st.markdown("---")
    if st.button("Continue to apply-at-work", type="primary"):
        st.session_state.stage = "apply_at_work"
        st.rerun()
    reset_button()


def stage_apply_at_work() -> None:
    st.subheader("💼 Apply at work")
    st.markdown(st.session_state.apply_at_work)
    st.markdown("---")
    if st.button("Wrap up the session", type="primary"):
        st.session_state.stage = "wrap"
        st.rerun()
    reset_button()


def stage_wrap() -> None:
    st.subheader("🏁 Wrap up")
    st.write(
        "Optional 1-word feeling note (e.g. `clicked`, `smooth`, `rough`, "
        "`productive`, `confused` — leave blank to skip)."
    )
    feeling = st.text_input("Feeling:", value=st.session_state.feeling, max_chars=20)
    col1, col2 = st.columns([1, 4])
    with col1:
        log = st.button("Log session", type="primary")
    with col2:
        reset_button()
    if log:
        st.session_state.feeling = feeling.strip()
        today_str = date.today().isoformat()
        chapter, topic = "?", "?"
        sd = st.session_state.session_data or {}
        topic_d = sd.get("topic") or {}
        chapter = topic_d.get("chapter") or "?"
        topic = topic_d.get("concept") or "?"
        score = "—"
        if st.session_state.quiz_grade:
            sm = re.search(r"(\d+(?:\.\d+)?)\s*/\s*4", st.session_state.quiz_grade)
            if sm:
                score = f"{sm.group(1)}/4"
        apply_summary = ""
        if st.session_state.apply_at_work:
            words = re.sub(r"[\*\#\n]", " ", st.session_state.apply_at_work).split()
            apply_summary = " ".join(words[:10]) + ("..." if len(words) > 10 else "")
        row = (
            f"| {today_str} | Daily | {chapter} | {topic} | {score} | pass | "
            f"{apply_summary} (Angle {st.session_state.angle}) | {st.session_state.feeling} |\n"
        )
        append_progress_row(row)
        st.session_state.stage = "done"
        st.rerun()


def stage_done() -> None:
    play_completion_animation()
    st.markdown(
        """
        <div style="text-align:center; padding: 2.5em 0 1em 0; position: relative; z-index: 2;">
          <div style="font-size: 0.78em; font-weight: 700; letter-spacing: 4px; color: var(--tutor-accent); text-transform: uppercase;">Session complete</div>
          <h1 style="font-size: clamp(36px, 5vw, 56px); font-weight: 800; color: var(--tutor-text); margin: 0.4em 0 0.6em 0; letter-spacing: -0.02em;">Nice work today.</h1>
          <p style="color: var(--tutor-text-dim); max-width: 480px; margin: 0 auto 2em auto; line-height: 1.6;">
            Your progress is saved. Tomorrow's session picks up where you left off.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Start another session", type="primary", use_container_width=True):
            reset_session()
            st.rerun()


STAGE_HANDLERS = {
    "start": stage_start,
    "concept_quiz": stage_concept_quiz,
    "graded_quiz": stage_graded_quiz,
    "exercise": stage_exercise,
    "graded_exercise": stage_graded_exercise,
    "apply_at_work": stage_apply_at_work,
    "wrap": stage_wrap,
    "done": stage_done,
}

render_theme_css()
render_theme_toggle()
render_topbar()
STAGE_HANDLERS[st.session_state.stage]()
