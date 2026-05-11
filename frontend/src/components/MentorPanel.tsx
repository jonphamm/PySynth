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
};

type ChatStatus = "idle" | "thinking" | "error";

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

export function MentorPanel({ chapter, concept, stage }: MentorPanelProps) {
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

  const send = useCallback(async () => {
    const question = input.trim();
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
  }, [input, status, messages, chapter, concept, stage]);

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void send();
    }
  };

  const orbState = status === "thinking" ? "thinking" : "idle";

  return (
    <aside className="glass hidden h-full min-h-0 w-[340px] flex-col overflow-hidden p-5 lg:flex">
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
          <p
            className="text-[12px] leading-relaxed"
            style={{ color: "rgba(255,255,255,0.55)" }}
          >
            Ask anything about today&apos;s concept — examples, intuition, how
            to use it at work. I won&apos;t spoil the quiz or solve the
            exercise.
          </p>
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
  );
}
