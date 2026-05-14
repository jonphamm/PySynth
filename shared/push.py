"""Web Push sender — wraps pywebpush with VAPID auth from env.

Called by `/push/send-daily` in `backend/app.py`. The VAPID keypair is
generated once (see `scripts/generate_vapid_keys.py`) and lives in env vars
on Render. The public key is also exposed to the frontend as
`NEXT_PUBLIC_VAPID_PUBLIC_KEY` so the browser can subscribe.

`send_push` is synchronous (pywebpush uses requests under the hood).
Callers in async endpoints should offload via `asyncio.to_thread` if many
subscriptions are involved; for the daily reminder loop the count is tiny
so calling inline is fine.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

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


def _vapid_config() -> tuple[str, dict]:
    private_key = os.environ.get("VAPID_PRIVATE_KEY")
    subject = os.environ.get("VAPID_SUBJECT")
    if not private_key or not subject:
        raise PushConfigError(
            "VAPID_PRIVATE_KEY and VAPID_SUBJECT must be set in the environment"
        )
    return private_key, {"sub": subject}


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
