"use client";

import ReactMarkdown from "react-markdown";

/**
 * Renders markdown without wrapping the result in a `<p>` block, so the LLM's
 * `**bold**` and `` `inline code` `` flow inline with surrounding text.
 *
 * Use inside a block-level container (`<div>` / `<li>` / `<section>`). AVOID
 * `<p>` — the LLM may emit fenced code blocks that render as `<pre>`, which
 * is illegal inside `<p>` and causes a Next.js hydration error.
 */
export function InlineMarkdown({ children }: { children: string }) {
  return (
    <ReactMarkdown
      components={{
        p: ({ children }) => <>{children}</>,
      }}
    >
      {children}
    </ReactMarkdown>
  );
}
