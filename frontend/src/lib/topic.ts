/**
 * Parse the LLM's free-form `topic.chapter` string into a normalized pointer
 * + chapter title. Mirrors the Python `next_chapter` formatting in
 * `shared/chapters.py` but stays UI-only on the frontend.
 *
 * Accepts: "Part 1 / Chapter 1 — Getting Started"
 *          "Part 1 / Ch 4 — Arithmetic Operations"
 *          "Part 1: Chapter 1 - Getting Started"
 * Returns: { pointer: "Part 1 · Chapter 1", title: "Getting Started" }
 *
 * Falls back to the raw string with empty title if the regex doesn't match.
 */
export function parseChapter(raw: string): { pointer: string; title: string } {
  if (!raw) return { pointer: "", title: "" };
  const match = raw.match(
    /Part\s+(\d+)\s*[/:]\s*Ch(?:apter)?\s+(\d+)\s*(?:[—\-]\s*(.+))?/i,
  );
  if (!match) return { pointer: raw, title: "" };
  const [, part, chapter, title] = match;
  return {
    pointer: `Part ${part} · Chapter ${chapter}`,
    title: (title ?? "").trim(),
  };
}
