"use client";

import { useCallback, useEffect, useState } from "react";

import { sendTestPush } from "@/lib/api";
import {
  disablePush,
  enablePush,
  getPermission,
  isIOS,
  isPushSupported,
  isStandalone,
  isSubscribed,
} from "@/lib/push";

type State =
  | { kind: "loading" }
  | { kind: "unsupported" }
  | { kind: "needs-pwa-install" } // iOS Safari tab, not yet added to home screen
  | { kind: "denied" }
  | { kind: "ready"; subscribed: boolean };

export function NotificationsToggle() {
  const [state, setState] = useState<State>({ kind: "loading" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    // Scope to iOS only by design — Jon picked iPhone-only at planning time,
    // and the "Add to Home Screen" prompt is only meaningful on iOS anyway.
    // Desktop and non-iOS mobile users see nothing.
    if (!isIOS()) {
      setState({ kind: "unsupported" });
      return;
    }
    // iOS Safari tab doesn't expose Notification/PushManager — Apple gates the
    // API behind PWA installation. So we can't probe isPushSupported() here;
    // we know we're on iOS, so show the install prompt directly.
    if (!isStandalone()) {
      setState({ kind: "needs-pwa-install" });
      return;
    }
    // Now we're inside the installed PWA — the full Push API should exist.
    if (!isPushSupported()) {
      setState({ kind: "unsupported" });
      return;
    }
    const permission = getPermission();
    if (permission === "denied") {
      setState({ kind: "denied" });
      return;
    }
    const subscribed = await isSubscribed();
    setState({ kind: "ready", subscribed });
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const onEnable = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      await enablePush();
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to enable notifications.");
    } finally {
      setBusy(false);
    }
  }, [refresh]);

  const onDisable = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      await disablePush();
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to disable notifications.");
    } finally {
      setBusy(false);
    }
  }, [refresh]);

  const onTest = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const result = await sendTestPush();
      if (result.sent === 0) {
        setError("Backend returned 0 sent — subscription may be expired. Try disabling and re-enabling.");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Test push failed.");
    } finally {
      setBusy(false);
    }
  }, []);

  if (state.kind === "loading" || state.kind === "unsupported") {
    // Render nothing while loading (avoids hydration flash) or if push is just
    // not available in this browser.
    return null;
  }

  return (
    <div
      className="mt-4 border-t pt-4"
      style={{ borderColor: "rgba(255,255,255,0.08)" }}
    >
      <div
        className="font-mono text-[10px] uppercase tracking-[0.3em]"
        style={{ color: "#9aa0a6" }}
      >
        Daily reminder
      </div>

      {state.kind === "needs-pwa-install" && (
        <p className="mt-2 text-[11px] leading-relaxed" style={{ color: "#9aa0a6" }}>
          Add PySynth to your home screen first (Share → Add to Home Screen),
          then reopen from the icon to enable push notifications.
        </p>
      )}

      {state.kind === "denied" && (
        <p className="mt-2 text-[11px] leading-relaxed" style={{ color: "#ff8a80" }}>
          Notifications are blocked. Enable them in iOS Settings → PySynth →
          Notifications, then come back.
        </p>
      )}

      {state.kind === "ready" && !state.subscribed && (
        <button
          type="button"
          onClick={onEnable}
          disabled={busy}
          className="mt-2 w-full rounded-md px-3 py-2 font-mono text-[11px] uppercase tracking-widest transition-colors hover:bg-[rgba(0,245,255,0.12)] disabled:opacity-50"
          style={{
            border: "1px solid rgba(0,245,255,0.35)",
            color: "rgba(0,245,255,0.85)",
            background: "rgba(0,245,255,0.05)",
          }}
        >
          {busy ? "Enabling…" : "Enable daily reminder"}
        </button>
      )}

      {state.kind === "ready" && state.subscribed && (
        <>
          <p className="mt-2 text-[11px] leading-relaxed" style={{ color: "#9aa0a6" }}>
            You&apos;ll be pinged daily if you haven&apos;t studied yet.
          </p>
          <button
            type="button"
            onClick={onTest}
            disabled={busy}
            className="mt-2 w-full rounded-md px-3 py-2 font-mono text-[11px] uppercase tracking-widest transition-colors hover:bg-[rgba(0,245,255,0.12)] disabled:opacity-50"
            style={{
              border: "1px solid rgba(0,245,255,0.35)",
              color: "rgba(0,245,255,0.85)",
              background: "rgba(0,245,255,0.05)",
            }}
          >
            {busy ? "Sending…" : "Send test push"}
          </button>
          <button
            type="button"
            onClick={onDisable}
            disabled={busy}
            className="mt-2 w-full rounded-md px-3 py-2 font-mono text-[11px] uppercase tracking-widest transition-colors hover:bg-white/5 disabled:opacity-50"
            style={{
              border: "1px solid rgba(255,255,255,0.12)",
              color: "rgba(245,245,245,0.65)",
            }}
          >
            {busy ? "Disabling…" : "Disable reminder"}
          </button>
        </>
      )}

      {error && (
        <p className="mt-2 text-[11px] leading-relaxed" style={{ color: "#ff8a80" }}>
          {error}
        </p>
      )}
    </div>
  );
}
