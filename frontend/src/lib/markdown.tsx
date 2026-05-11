"use client";

import ReactMarkdown from "react-markdown";

/**
 * Renders short markdown (bold, inline code, em) without wrapping the result
 * in a `<p>` block. Use inside `<li>` / `<p>` / `<span>` so the LLM's
 * `**bold**` and `` `inline code` `` flow inline.
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
