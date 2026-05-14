/**
 * Browser-side Web Push helpers.
 *
 * iOS gotcha: Notification.requestPermission() only succeeds when the page is
 * running as an installed PWA (display-mode: standalone), NOT in a regular
 * Safari tab. Callers should check isStandalone() before offering to subscribe.
 */

import { subscribePush, unsubscribePush } from "./api";

const VAPID_PUBLIC_KEY = process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY ?? "";

export function isPushSupported(): boolean {
  if (typeof window === "undefined") return false;
  return (
    "serviceWorker" in navigator &&
    "PushManager" in window &&
    "Notification" in window
  );
}

export function isStandalone(): boolean {
  if (typeof window === "undefined") return false;
  // iOS Safari sets navigator.standalone on home-screen PWAs.
  // Standards-compliant browsers report it via the matchMedia query.
  type IOSNavigator = Navigator & { standalone?: boolean };
  const iosStandalone = (navigator as IOSNavigator).standalone === true;
  const mqStandalone = window.matchMedia("(display-mode: standalone)").matches;
  return iosStandalone || mqStandalone;
}

export function getPermission(): NotificationPermission | "unsupported" {
  if (!isPushSupported()) return "unsupported";
  return Notification.permission;
}

async function getRegistration(): Promise<ServiceWorkerRegistration> {
  const existing = await navigator.serviceWorker.getRegistration("/");
  if (existing) return existing;
  return navigator.serviceWorker.register("/sw.js", { scope: "/" });
}

function urlBase64ToArrayBuffer(base64String: string): ArrayBuffer {
  // pushManager.subscribe wants applicationServerKey as a BufferSource backed
  // by an ArrayBuffer. TS narrows Uint8Array.buffer to ArrayBufferLike, which
  // is wider than what subscribe accepts, so we return the ArrayBuffer directly.
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const raw = atob(base64);
  const buf = new ArrayBuffer(raw.length);
  const view = new Uint8Array(buf);
  for (let i = 0; i < raw.length; i++) view[i] = raw.charCodeAt(i);
  return buf;
}

function bufferToBase64Url(buffer: ArrayBuffer | null): string {
  if (!buffer) return "";
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export type PushReady = {
  endpoint: string;
  keys: { p256dh: string; auth: string };
};

function toServerPayload(sub: PushSubscription): PushReady {
  return {
    endpoint: sub.endpoint,
    keys: {
      p256dh: bufferToBase64Url(sub.getKey("p256dh")),
      auth: bufferToBase64Url(sub.getKey("auth")),
    },
  };
}

/**
 * Idempotent: registers the SW, requests permission if needed, subscribes via
 * PushManager, and tells the backend. Returns the subscription endpoint.
 *
 * Throws if VAPID key is missing or permission is denied.
 */
export async function enablePush(): Promise<string> {
  if (!isPushSupported()) {
    throw new Error("Push notifications are not supported in this browser.");
  }
  if (!VAPID_PUBLIC_KEY) {
    throw new Error(
      "NEXT_PUBLIC_VAPID_PUBLIC_KEY is missing — set it in Vercel env."
    );
  }
  const permission = await Notification.requestPermission();
  if (permission !== "granted") {
    throw new Error("Notification permission was not granted.");
  }
  const reg = await getRegistration();
  let sub = await reg.pushManager.getSubscription();
  if (!sub) {
    sub = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToArrayBuffer(VAPID_PUBLIC_KEY),
    });
  }
  await subscribePush(toServerPayload(sub));
  return sub.endpoint;
}

/**
 * Idempotent: unsubscribes the current PushSubscription if any, and tells the
 * backend to forget it.
 */
export async function disablePush(): Promise<void> {
  if (!isPushSupported()) return;
  const reg = await navigator.serviceWorker.getRegistration("/");
  if (!reg) return;
  const sub = await reg.pushManager.getSubscription();
  if (!sub) return;
  const endpoint = sub.endpoint;
  await sub.unsubscribe();
  try {
    await unsubscribePush(endpoint);
  } catch {
    // Backend record will be cleaned up the next time we try to send and get
    // a 410 — don't block the UI on this.
  }
}

/** True if this browser has an active push subscription registered. */
export async function isSubscribed(): Promise<boolean> {
  if (!isPushSupported()) return false;
  const reg = await navigator.serviceWorker.getRegistration("/");
  if (!reg) return false;
  const sub = await reg.pushManager.getSubscription();
  return sub !== null;
}
