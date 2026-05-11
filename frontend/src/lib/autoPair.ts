/**
 * VSCode-style typing convenience for the solution textarea.
 *
 * Pure logic: given the current `value` + selection range and a key event,
 * return the new value + new selection. No DOM access, no React. The caller
 * is responsible for `e.preventDefault()` when this returns non-null and for
 * applying the new value/selection.
 *
 * This is typing convenience only — bracket pairing, indent continuation,
 * tab-as-spaces. NO identifier suggestions, NO autocomplete that could leak
 * exercise answers.
 */

const OPEN_TO_CLOSE: Record<string, string> = {
  "(": ")",
  "[": "]",
  "{": "}",
  '"': '"',
  "'": "'",
  "`": "`",
};

const CLOSING = new Set(Object.values(OPEN_TO_CLOSE));
const PAIRS = new Set(
  Object.entries(OPEN_TO_CLOSE).map(([o, c]) => o + c),
);

const INDENT = "    ";

export type EditResult = {
  value: string;
  selectionStart: number;
  selectionEnd: number;
};

export function handleAutoPair(
  e: React.KeyboardEvent<HTMLTextAreaElement>,
  value: string,
  selStart: number,
  selEnd: number,
): EditResult | null {
  const before = value.slice(0, selStart);
  const after = value.slice(selEnd);
  const selected = value.slice(selStart, selEnd);
  const nextChar = after.charAt(0);
  const prevChar = before.charAt(before.length - 1);

  // Tab: insert 4 spaces (or dedent on Shift+Tab)
  if (e.key === "Tab") {
    if (e.shiftKey) {
      // Shift+Tab — remove up to 4 spaces from the line's leading whitespace.
      const lineStart = before.lastIndexOf("\n") + 1;
      const lineLeading = value.slice(lineStart, selStart);
      const stripCount = Math.min(
        4,
        lineLeading.length - lineLeading.replace(/^ +/, "").length,
      );
      if (stripCount === 0) return null;
      return {
        value: value.slice(0, lineStart) + lineLeading.slice(stripCount) + value.slice(selStart),
        selectionStart: selStart - stripCount,
        selectionEnd: selEnd - stripCount,
      };
    }
    return {
      value: before + INDENT + after,
      selectionStart: selStart + INDENT.length,
      selectionEnd: selStart + INDENT.length,
    };
  }

  // Enter: continue indentation; extra indent after `:`; split-line for empty pair
  if (e.key === "Enter" && !e.shiftKey && !e.metaKey && !e.ctrlKey && !e.altKey) {
    const lineStart = before.lastIndexOf("\n") + 1;
    const lineSoFar = value.slice(lineStart, selStart);
    const leading = lineSoFar.match(/^\s*/)?.[0] ?? "";
    const trimmedLine = lineSoFar.trimEnd();
    const endsWithColon = trimmedLine.endsWith(":");

    // Empty pair split: cursor between `(|)` `[|]` `{|}` => two newlines, indented body
    if (
      selStart === selEnd &&
      prevChar &&
      nextChar &&
      PAIRS.has(prevChar + nextChar)
    ) {
      const inner = "\n" + leading + INDENT;
      const closer = "\n" + leading;
      return {
        value: before + inner + closer + after,
        selectionStart: selStart + inner.length,
        selectionEnd: selStart + inner.length,
      };
    }

    const insert = "\n" + leading + (endsWithColon ? INDENT : "");
    return {
      value: before + insert + after,
      selectionStart: selStart + insert.length,
      selectionEnd: selStart + insert.length,
    };
  }

  // Backspace: delete an empty pair around cursor
  if (
    e.key === "Backspace" &&
    selStart === selEnd &&
    prevChar &&
    nextChar &&
    PAIRS.has(prevChar + nextChar)
  ) {
    return {
      value: before.slice(0, -1) + after.slice(1),
      selectionStart: selStart - 1,
      selectionEnd: selStart - 1,
    };
  }

  // Closing char: skip if it matches the next char (lets users type the closer naturally)
  if (
    CLOSING.has(e.key) &&
    selStart === selEnd &&
    nextChar === e.key
  ) {
    return {
      value,
      selectionStart: selStart + 1,
      selectionEnd: selStart + 1,
    };
  }

  // Opening char: insert pair (or wrap selection)
  if (e.key in OPEN_TO_CLOSE) {
    const open = e.key;
    const close = OPEN_TO_CLOSE[open];

    // For quote chars, don't auto-pair if user is in the middle of a word
    // (avoids `it's` becoming `it''s`). Heuristic: prev char is alphanumeric.
    if (
      (open === "'" || open === '"' || open === "`") &&
      selStart === selEnd &&
      /[A-Za-z0-9_]/.test(prevChar ?? "")
    ) {
      return null;
    }

    // If next char is a word/identifier char, don't pair (typing in front of one)
    if (
      selStart === selEnd &&
      /[A-Za-z0-9_]/.test(nextChar ?? "") &&
      open !== "(" &&
      open !== "[" &&
      open !== "{"
    ) {
      return null;
    }

    if (selStart !== selEnd) {
      // Wrap selection
      return {
        value: before + open + selected + close + after,
        selectionStart: selStart + 1,
        selectionEnd: selEnd + 1,
      };
    }
    return {
      value: before + open + close + after,
      selectionStart: selStart + 1,
      selectionEnd: selStart + 1,
    };
  }

  return null;
}
