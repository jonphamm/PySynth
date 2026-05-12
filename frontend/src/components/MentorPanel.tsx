"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import type { Language } from "prism-react-renderer";
import { askMentor } from "@/lib/api";
import { SyntaxHighlight } from "@/components/ui/SyntaxHighlight";
import type { ChatMessage, WizardStage } from "@/types/session";
import { AIOrb } from "./ui/AIOrb";

type MentorPanelProps = {
  chapter: string;
  concept: string;
  stage: WizardStage;
  mobileOpen: boolean;
  onMobileClose: () => void;
};

type ChatStatus = "idle" | "thinking" | "error";

const EXAMPLE_PROMPTS = [
  "Walk me through one more example.",
  "How would I use this in a cybersecurity script?",
  "What's a common beginner mistake here?",
];

const MARKDOWN_COMPONENTS = {
  code({
    className,
    children,
    ...rest
  }: React.ClassAttributes<HTMLElement> &
    React.HTMLAttributes<HTMLElement> & {
      className?: string;
      children?: React.ReactNode;
    }) {
    const lang = className?.replace(/^language-/, "");
    const text = String(children ?? "").replace(/\n$/, "");
    if (!lang) {
      return (
        <code className={className} {...rest}>
          {children}
        </code>
      );
    }
    return <SyntaxHighlight code={text} language={lang as Language} />;
  },
};

export function MentorPanel({
  chapter,
  concept,
  stage,
  mobileOpen,
  onMobileClose,
}: MentorPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [status, setStatus] = useState<ChatStatus>("idle");
  const [errorMsg, setErrorMsg] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  // Clear chat history when chapter changes (new session)
  useEffect(() => {
    setMessages([]);
    setStatus("idle");
    setErrorMsg("");
  }, [chapter]);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, status]);

  const send = useCallback(
    async (override?: string) => {
      const question = (override ?? input).trim();
      if (!question || status === "thinking") return;
      const nextHistory: ChatMessage[] = [
        ...messages,
        { role: "user", text: question },
      ];
      setMessages(nextHistory);
      setInput("");
      setStatus("thinking");
      setErrorMsg("");
      try {
        const result = await askMentor({
          question,
          chapter,
          concept,
          stage,
          history: messages,
        });
        setMessages([
          ...nextHistory,
          { role: "mentor", text: result.answer },
        ]);
        setStatus("idle");
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        setStatus("error");
        setErrorMsg(message);
      }
    },
    [input, status, messages, chapter, concept, stage],
  );

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void send();
    }
  };

  const orbState = status === "thinking" ? "thinking" : "idle";

  return (
    <>
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={onMobileClose}
          aria-hidden
        />
      )}
      <aside
        className={`glass relative flex h-full min-h-0 w-[340px] flex-col overflow-hidden p-5 transition-transform duration-300 ease-out max-lg:fixed max-lg:inset-y-2 max-lg:right-2 max-lg:z-50 max-lg:h-[calc(100%-1rem)] max-md:w-[calc(100%-1rem)] md:max-lg:w-[420px] ${
          mobileOpen ? "max-lg:translate-x-0" : "max-lg:translate-x-[120%]"
        } lg:translate-x-0`}
      >
        <button
          type="button"
          onClick={onMobileClose}
          className="absolute right-2 top-2 inline-flex h-8 w-8 items-center justify-center rounded-md transition-colors hover:bg-white/10 lg:hidden"
          aria-label="Close mentor chat"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinecap="round"
            style={{ color: "#cdeefd" }}
          >
            <line x1="4" y1="4" x2="12" y2="12" />
            <line x1="12" y1="4" x2="4" y2="12" />
          </svg>
        </button>
        <div className="mb-4 flex items-center gap-3">
        <AIOrb state={orbState} size={42} />
        <div>
          <div
            className="font-mono text-[10px] uppercase tracking-[0.4em]"
            style={{ color: "#00f5ff" }}
          >
            Mentor
          </div>
          <div className="mt-0.5 text-sm font-semibold">PySynth Tutor</div>
        </div>
      </div>

      <div
        ref={scrollRef}
        className="flex-1 min-h-0 overflow-y-auto rounded-lg p-3 text-[12.5px]"
        style={{
          background: "rgba(2,2,3,0.55)",
          border: "1px solid rgba(255,255,255,0.06)",
        }}
      >
        {messages.length === 0 && status === "idle" && (
          <div className="space-y-2">
            <p
              className="text-[10px] uppercase tracking-[0.3em]"
              style={{ color: "#9aa0a6" }}
            >
              Try asking
            </p>
            {EXAMPLE_PROMPTS.map((prompt) => (
              <button
                key={prompt}
                type="button"
                onClick={() => void send(prompt)}
                disabled={!chapter || status !== "idle"}
                className="block w-full rounded-md px-3 py-2 text-left text-[12px] leading-snug transition-colors hover:bg-white/5 disabled:opacity-50"
                style={{
                  background: "rgba(0,245,255,0.04)",
                  border: "1px solid rgba(0,245,255,0.18)",
                  color: "rgba(205,238,253,0.85)",
                }}
              >
                {prompt}
              </button>
            ))}
          </div>
        )}

        <div className="space-y-3">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={msg.role === "user" ? "flex justify-end" : ""}
            >
              {msg.role === "user" ? (
                <div
                  className="max-w-[88%] rounded-lg px-3 py-2 text-[12.5px]"
                  style={{
                    background: "rgba(0,245,255,0.10)",
                    border: "1px solid rgba(0,245,255,0.22)",
                    color: "#cdeefd",
                  }}
                >
                  {msg.text}
                </div>
              ) : (
                <div
                  className="markdown rounded-lg px-3 py-2"
                  style={{
                    background: "rgba(255,255,255,0.03)",
                    border: "1px solid rgba(255,255,255,0.06)",
                    color: "rgba(245,245,245,0.88)",
                  }}
                >
                  <ReactMarkdown components={MARKDOWN_COMPONENTS}>
                    {msg.text}
                  </ReactMarkdown>
                </div>
              )}
            </div>
          ))}

          {status === "thinking" && (
            <div
              className="rounded-lg px-3 py-2 text-[12px] italic"
              style={{ color: "rgba(255,255,255,0.45)" }}
            >
              Thinking…
            </div>
          )}
          {status === "error" && (
            <div
              className="rounded-lg px-3 py-2 text-[12px]"
              style={{ color: "rgba(255,200,200,0.85)" }}
            >
              {errorMsg || "Mentor unreachable."}
            </div>
          )}
        </div>
      </div>

      <div className="mt-3">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          disabled={status === "thinking" || !chapter}
          placeholder={
            chapter
              ? "Ask the tutor… (Enter to send, Shift+Enter for newline)"
              : "Waiting for session to load…"
          }
          rows={2}
          className="w-full resize-none rounded-lg px-3 py-2 text-[13px] outline-none transition-colors focus:border-[rgba(0,245,255,0.55)] disabled:opacity-50"
          style={{
            background: "rgba(2,2,3,0.6)",
            border: "1px solid rgba(255,255,255,0.08)",
            color: "rgba(245,245,245,0.95)",
            fontFamily: "var(--font-sans)",
          }}
        />
      </div>
      </aside>
    </>
  );
}
