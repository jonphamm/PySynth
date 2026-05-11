"""Multi-provider LLM client. Gemini → Groq → Cerebras → OpenRouter chain. JSON + text modes."""

import json
import os
import sys
import time

from .config import CEREBRAS_MODEL, GEMINI_MODEL, GROQ_MODEL, OPENROUTER_MODEL

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Error-message hints that indicate a transient (server-side or short-window)
# failure worth retrying on the SAME provider before falling through to the
# next one. Daily-quota exhaustion is excluded on purpose — retrying won't help
# until the day rolls over.
_TRANSIENT_ERROR_HINTS = (
    "queue_exceeded",        # Cerebras: shared capacity is saturated
    "tokens per minute",     # Groq: per-minute token rate limit (TPM)
    "requests per minute",   # Groq: per-minute request rate limit (RPM)
)


def _is_transient(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(hint in msg for hint in _TRANSIENT_ERROR_HINTS)


def _strict_json_loads(text: str) -> dict:
    """Parse JSON from an LLM response, tolerating markdown fences and
    surrounding prose. Some free-tier models drop ```json fences or a
    reasoning preamble around an otherwise-clean JSON object even when
    asked for json_object mode. Raises ValueError with a preview snippet
    if nothing parses."""
    if not text:
        raise ValueError("LLM returned empty response")
    s = text.strip()

    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else ""
        if s.rstrip().endswith("```"):
            s = s.rstrip()[:-3]
        s = s.strip()

    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass

    first = s.find("{")
    last = s.rfind("}")
    if first >= 0 and last > first:
        try:
            return json.loads(s[first:last + 1])
        except json.JSONDecodeError as exc:
            preview = s[first:first + 200]
            raise ValueError(
                f"LLM returned malformed JSON ({exc.msg} at char {exc.pos}). "
                f"Preview: {preview}..."
            ) from exc

    raise ValueError(f"LLM response had no JSON object: {s[:200]}...")


def _call_with_retry(fn, system_prompt, user_message, *, max_retries=2):
    """Invoke a provider, retrying on transient errors with short backoff."""
    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            return fn(system_prompt, user_message)
        except Exception as exc:
            last_exc = exc
            if not _is_transient(exc) or attempt == max_retries:
                raise
            wait = 2.0 * (attempt + 1)
            print(
                f"[llm] transient failure on attempt {attempt + 1}, retrying in {wait}s: {exc}",
                file=sys.stderr,
            )
            time.sleep(wait)
    raise last_exc  # unreachable but satisfies the type checker


def _import_gemini():
    from google import genai
    return genai


def _import_groq():
    from groq import Groq
    return Groq


def _import_cerebras():
    from cerebras.cloud.sdk import Cerebras
    return Cerebras


def _import_openai():
    from openai import OpenAI
    return OpenAI


def call_gemini(system_prompt: str, user_message: str) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    genai = _import_gemini()
    client = genai.Client(api_key=api_key)
    full_prompt = f"{system_prompt}\n\n---\n\n{user_message}"
    response = client.models.generate_content(model=GEMINI_MODEL, contents=full_prompt)
    return response.text


def call_groq(system_prompt: str, user_message: str) -> str:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set")
    Groq = _import_groq()
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )
    return response.choices[0].message.content


def call_cerebras(system_prompt: str, user_message: str) -> str:
    api_key = os.environ.get("CEREBRAS_API_KEY")
    if not api_key:
        raise RuntimeError("CEREBRAS_API_KEY not set")
    Cerebras = _import_cerebras()
    client = Cerebras(api_key=api_key)
    response = client.chat.completions.create(
        model=CEREBRAS_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )
    return response.choices[0].message.content


def call_openrouter(system_prompt: str, user_message: str) -> str:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    OpenAI = _import_openai()
    client = OpenAI(api_key=api_key, base_url=OPENROUTER_BASE_URL)
    response = client.chat.completions.create(
        model=OPENROUTER_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        extra_body={"max_tokens": 8000},
    )
    return response.choices[0].message.content


def call_gemini_json(system_prompt: str, user_message: str) -> dict:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    genai = _import_gemini()
    client = genai.Client(api_key=api_key)
    full_prompt = f"{system_prompt}\n\n---\n\n{user_message}"
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=full_prompt,
        config={"response_mime_type": "application/json"},
    )
    return _strict_json_loads(response.text)


def call_groq_json(system_prompt: str, user_message: str) -> dict:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set")
    Groq = _import_groq()
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
    )
    return _strict_json_loads(response.choices[0].message.content)


def call_cerebras_json(system_prompt: str, user_message: str) -> dict:
    api_key = os.environ.get("CEREBRAS_API_KEY")
    if not api_key:
        raise RuntimeError("CEREBRAS_API_KEY not set")
    Cerebras = _import_cerebras()
    client = Cerebras(api_key=api_key)
    response = client.chat.completions.create(
        model=CEREBRAS_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
    )
    return _strict_json_loads(response.choices[0].message.content)


def call_openrouter_json(system_prompt: str, user_message: str) -> dict:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    OpenAI = _import_openai()
    client = OpenAI(api_key=api_key, base_url=OPENROUTER_BASE_URL)
    response = client.chat.completions.create(
        model=OPENROUTER_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
        extra_body={"max_tokens": 8000},
    )
    return _strict_json_loads(response.choices[0].message.content)


PROVIDERS_TEXT = [
    ("Gemini", call_gemini),
    ("Groq", call_groq),
    ("Cerebras", call_cerebras),
    ("OpenRouter", call_openrouter),
]

PROVIDERS_JSON = [
    ("Gemini", call_gemini_json),
    ("Groq", call_groq_json),
    ("Cerebras", call_cerebras_json),
    ("OpenRouter", call_openrouter_json),
]


def _try_chain(providers, system_prompt, user_message):
    errors = []
    for name, fn in providers:
        try:
            return _call_with_retry(fn, system_prompt, user_message), name
        except Exception as exc:
            errors.append(f"{name}: {exc}")
            print(f"[llm] {name} failed: {exc}", file=sys.stderr)
    raise RuntimeError("All LLM providers failed:\n" + "\n".join(errors))


def call_llm(system_prompt: str, user_message: str) -> tuple[str, str]:
    return _try_chain(PROVIDERS_TEXT, system_prompt, user_message)


def call_llm_json(system_prompt: str, user_message: str) -> tuple[dict, str]:
    return _try_chain(PROVIDERS_JSON, system_prompt, user_message)
