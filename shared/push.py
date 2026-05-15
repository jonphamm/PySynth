"""Web Push sender — wraps pywebpush with VAPID auth from env.

Called by `/push/send-daily` in `backend/app.py`. The VAPID keypair is
generated once (see `scripts/generate_vapid_keys.py`) and lives in env vars
on Render. The public key is also exposed to the frontend as
`NEXT_PUBLIC_VAPID_PUBLIC_KEY` so the browser can subscribe.

`VAPID_PRIVATE_KEY` accepts two formats:
1. Single-line base64url-encoded raw 32-byte EC private key (preferred —
   immune to whitespace/newline corruption when stored in cloud env-var UIs).
2. Full PEM block including `-----BEGIN PRIVATE KEY-----` markers (legacy
   fallback; can break if the cloud provider's textarea mangles newlines).

`send_push` is synchronous (pywebpush uses requests under the hood).
Callers in async endpoints should offload via `asyncio.to_thread` if many
subscriptions are involved; for the daily reminder loop the count is tiny
so calling inline is fine.
"""

from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from pywebpush import WebPushException, webpush


class PushExpired(Exception):
    """The subscription is gone (410). Caller should delete the row."""


class PushConfigError(RuntimeError):
    """VAPID env vars are missing or malformed."""


@dataclass(frozen=True)
class Subscription:
    endpoint: str
    p256dh: str
    auth: str

    def to_pywebpush(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "keys": {"p256dh": self.p256dh, "auth": self.auth},
        }


def _decode_raw_b64url(s: str) -> bytes:
    s = s.strip()
    padded = s + "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(padded)


def _normalize_private_key(raw: str) -> str:
    """Return a clean PEM block regardless of which input format was used.

    - If the value looks like PEM (`BEGIN`/`END` markers), assume that's what
      it is and pass through after stripping per-line leading whitespace
      that some cloud env-var UIs introduce when the source file was
      indented.
    - Otherwise, treat the value as a base64url-encoded raw 32-byte EC
      private key and reconstruct a PEM block in-memory."""
    if "BEGIN" in raw and "END" in raw:
        # Strip leading whitespace per line (the most common Render-paste mistake)
        cleaned = "\n".join(line.strip() for line in raw.splitlines())
        return cleaned

    # Raw base64url format
    key_bytes = _decode_raw_b64url(raw)
    if len(key_bytes) != 32:
        raise PushConfigError(
            f"VAPID_PRIVATE_KEY decoded to {len(key_bytes)} bytes, expected 32 "
            f"(if you meant PEM format, include the BEGIN/END markers)"
        )
    private_int = int.from_bytes(key_bytes, "big")
    key_obj = ec.derive_private_key(private_int, ec.SECP256R1())
    pem = key_obj.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return pem.decode("ascii")


def _vapid_config() -> tuple[str, dict]:
    private_key_raw = os.environ.get("VAPID_PRIVATE_KEY")
    subject = os.environ.get("VAPID_SUBJECT")
    if not private_key_raw or not subject:
        raise PushConfigError(
            "VAPID_PRIVATE_KEY and VAPID_SUBJECT must be set in the environment"
        )
    return _normalize_private_key(private_key_raw), {"sub": subject}


def send_push(sub: Subscription, title: str, body: str, url: str = "/") -> None:
    """Send one push notification. Raises PushExpired on 410, WebPushException
    on other transport errors, PushConfigError if VAPID env is missing."""
    private_key, claims = _vapid_config()
    payload = json.dumps({"title": title, "body": body, "url": url})
    try:
        webpush(
            subscription_info=sub.to_pywebpush(),
            data=payload,
            vapid_private_key=private_key,
            vapid_claims=claims,
        )
    except WebPushException as exc:
        status = getattr(exc.response, "status_code", None)
        if status in (404, 410):
            raise PushExpired(str(exc)) from exc
        raise
