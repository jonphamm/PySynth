"use client";

import { Highlight, themes, type Language } from "prism-react-renderer";

type Props = {
  code: string;
  language?: Language;
};

/**
 * IDE-style syntax-highlighted code block. Wraps prism-react-renderer's
 * vsDark theme inside the PySynth code-frame (cyan border, inset glow,
 * Fira Code). Single source of truth for highlighted code across the app.
 */
export function SyntaxHighlight({ code, language = "python" }: Props) {
  const trimmed = code.replace(/\n+$/, "");
  return (
    <Highlight code={trimmed} language={language} theme={themes.vsDark}>
      {({ className, style, tokens, getLineProps, getTokenProps }) => (
        <pre
          className={`${className} font-mono text-[12.5px] overflow-x-auto rounded-lg px-4 py-3`}
          style={{
            ...style,
            background: "rgba(2,2,3,0.7)",
            border: "1px solid rgba(0,245,255,0.18)",
            boxShadow: "0 0 24px rgba(0,245,255,0.08) inset",
            margin: 0,
          }}
        >
          <code>
            {tokens.map((line, lineIdx) => {
              const { key: lineKey, ...lineProps } = getLineProps({
                line,
                key: lineIdx,
              });
              return (
                <div key={lineIdx} {...lineProps}>
                  {line.map((token, tokenIdx) => {
                    const { key: tokenKey, ...tokenProps } = getTokenProps({
                      token,
                      key: tokenIdx,
                    });
                    return <span key={tokenIdx} {...tokenProps} />;
                  })}
                </div>
              );
            })}
          </code>
        </pre>
      )}
    </Highlight>
  );
}
