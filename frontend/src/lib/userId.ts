const STORAGE_KEY = "pysynth.user_id";

/** Get or lazily create a stable per-browser UUID. Returns "" on the server
 * (SSR) — callers should only invoke this from client components or event
 * handlers, never from a server component. */
export function getOrCreateUserId(): string {
  if (typeof window === "undefined") return "";
  let id = window.localStorage.getItem(STORAGE_KEY);
  if (!id) {
    id = crypto.randomUUID();
    window.localStorage.setItem(STORAGE_KEY, id);
  }
  return id;
}
