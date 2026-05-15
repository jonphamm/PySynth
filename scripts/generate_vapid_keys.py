"""One-shot VAPID keypair generator for PySynth web push.

Run once locally; copy the printed values into env vars:
    - Render (backend):  VAPID_PRIVATE_KEY, VAPID_PUBLIC_KEY, VAPID_SUBJECT
    - Vercel (frontend): NEXT_PUBLIC_VAPID_PUBLIC_KEY (same value as VAPID_PUBLIC_KEY)

Also writes the values to `.vapid_keys.local` at repo root (gitignored) for
reference if you forget to save them right away.

Re-running generates a NEW keypair — existing browser subscriptions tied to the
old public key will no longer be valid. Don't re-run unless you intend to
invalidate every active subscription.
"""

from __future__ import annotations

import base64
import os
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_FILE = REPO_ROOT / ".vapid_keys.local"
# VAPID requires a contact (email or URL) the push service can reach if there
# are problems. Override via env var, e.g.:
#   VAPID_SUBJECT=mailto:you@example.com python scripts/generate_vapid_keys.py
SUBJECT_DEFAULT = os.environ.get("VAPID_SUBJECT", "mailto:admin@example.com")


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def main() -> None:
    if OUT_FILE.exists():
        raise SystemExit(
            f"{OUT_FILE} already exists. Delete it manually if you really want "
            "to regenerate (this will invalidate every existing push "
            "subscription)."
        )

    private = ec.generate_private_key(ec.SECP256R1())
    public = private.public_key()

    # Web Push expects the public key as the raw uncompressed point (65 bytes,
    # leading 0x04) encoded base64url. SubjectPublicKeyInfo (DER) is *not* the
    # right format here.
    public_raw = public.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )
    public_b64 = _b64url(public_raw)

    # Raw 32-byte EC private key, base64url-encoded — single line, no PEM
    # wrapping. Safer to paste into cloud env-var UIs than the multi-line
    # PEM block (some Render/Vercel textareas mangle whitespace/newlines
    # and corrupt PEM, but a single base64url line is immune).
    raw_priv_bytes = private.private_numbers().private_value.to_bytes(32, "big")
    private_b64 = _b64url(raw_priv_bytes)

    body = (
        "# PySynth VAPID keypair — DO NOT COMMIT.\n"
        "# Paste these into Render + Vercel env vars, then optionally delete this file.\n\n"
        f"VAPID_SUBJECT={SUBJECT_DEFAULT}\n\n"
        f"VAPID_PUBLIC_KEY={public_b64}\n\n"
        f"# Frontend exposes the public key (safe to ship in bundle):\n"
        f"NEXT_PUBLIC_VAPID_PUBLIC_KEY={public_b64}\n\n"
        "# Backend-only; treat like a password. Single-line base64url —\n"
        "# safe to paste into Render's env-var UI without whitespace corruption.\n"
        f"VAPID_PRIVATE_KEY={private_b64}\n"
    )
    OUT_FILE.write_text(body, encoding="utf-8")

    print(f"Wrote {OUT_FILE}")
    print()
    print("Copy these into env vars:")
    print(f"  VAPID_SUBJECT={SUBJECT_DEFAULT}")
    print(f"  VAPID_PUBLIC_KEY={public_b64}")
    print(f"  NEXT_PUBLIC_VAPID_PUBLIC_KEY={public_b64}")
    print(f"  VAPID_PRIVATE_KEY={private_b64}")


if __name__ == "__main__":
    main()
