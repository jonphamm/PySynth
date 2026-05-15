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


def _normalize_private_key(raw: str) -> str:
    """Return the raw 32-byte EC private key as a single base64url line.

    `py_vapid.Vapid.from_string()` (which pywebpush calls internally) does NOT
    parse PEM. It strips newlines from the input, base64url-decodes the whole
    string, and only succeeds if the decoded length is exactly 32 bytes
    (raw EC scalar). If we hand it PEM, it tries to decode the BEGIN/END
    markers as base64url and the result is gibberish.

    So this function always returns the raw form:
    - Raw input (no PEM markers) → strip whitespace, pass through
    - PEM input → parse to extract the 32-byte scalar, re-encode as
      base64url. Lets users migrate from older PEM-style env vars without
      having to regenerate keys."""
    raw = raw.strip()
    if "BEGIN" not in raw and "END" not in raw:
        return raw

    key_obj = serialization.load_pem_private_key(raw.encode("ascii"), password=None)
    if not isinstance(key_obj, ec.EllipticCurvePrivateKey):
        raise PushConfigError("VAPID_PRIVATE_KEY must be an EC P-256 key")
    raw_bytes = key_obj.private_numbers().private_value.to_bytes(32, "big")
    return base64.urlsafe_b64encode(raw_bytes).rstrip(b"=").decode("ascii")


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
