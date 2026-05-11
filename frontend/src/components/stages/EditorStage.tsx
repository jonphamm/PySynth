"use client";

import { useEffect, useLayoutEffect, useRef } from "react";
import type { Wizard } from "@/hooks/useWizard";
import { generateExercise, reviewCode } from "@/lib/api";
import { handleAutoPair } from "@/lib/autoPair";
import { InlineMarkdown } from "@/lib/markdown";
import { StageStatus } from "./StageStatus";

type Props = {
  wizard: Wizard;
};

export function EditorStage({ wizard }: Props) {
  const {
    sessionData,
    exerciseResult,
    setExerciseResult,
    setReviewResult,
    code,
    setCode,
    status,
    setStatus,
    advance,
  } = wizard;
  const requestedRef = useRef(false);
  const submittingRef = useRef(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const pendingSelectionRef = useRef<[number, number] | null>(null);

  useEffect(() => {
    if (!sessionData || exerciseResult || requestedRef.current) return;
    requestedRef.current = true;
    setStatus({ kind: "loading", what: "Building today's coding exercise…" });
    generateExercise({
      topic: sessionData.topic,
      concept: sessionData.topic.concept,
    })
      .then((result) => {
        setExerciseResult(result);
        setStatus({ kind: "idle" });
      })
      .catch((err: Error) => {
        requestedRef.current = false;
        setStatus({ kind: "error", message: err.message });
      });
  }, [sessionData, exerciseResult, setExerciseResult, setStatus]);

  useLayoutEffect(() => {
    if (pendingSelectionRef.current && textareaRef.current) {
      const [s, e] = pendingSelectionRef.current;
      textareaRef.current.setSelectionRange(s, e);
      pendingSelectionRef.current = null;
    }
  }, [code]);

  if (!exerciseResult) {
    return (
      <StageStatus
        label="Coding Exercise"
        status={status}
        loadingMessage="Building today's coding exercise…"
        onRetry={() => {
          requestedRef.current = false;
          setStatus({ kind: "idle" });
        }}
      />
    );
  }

  const { exercise } = exerciseResult;

  const onSubmit = () => {
    if (submittingRef.current) return;
    submittingRef.current = true;
    setStatus({ kind: "loading", what: "Reviewing your code…" });
    reviewCode({ exercise, code })
      .then((result) => {
        setReviewResult(result);
        setStatus({ kind: "idle" });
        advance();
      })
      .catch((err: Error) => {
        submittingRef.current = false;
        setStatus({ kind: "error", message: err.message });
      });
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    const ta = e.currentTarget;
    const result = handleAutoPair(e, ta.value, ta.selectionStart, ta.selectionEnd);
    if (result) {
      e.preventDefault();
      pendingSelectionRef.current = [result.selectionStart, result.selectionEnd];
      setCode(result.value);
    }
  };

  const submitting = status.kind === "loading" && status.what.startsWith("Reviewing");

  return (
    <div className="flex h-full min-h-0 flex-col">
      <header
        className="border-b px-7 py-5"
        style={{ borderColor: "rgba(255,255,255,0.06)" }}
      >
        <div
          className="font-mono text-[10px] uppercase tracking-[0.4em]"
          style={{ color: "#00f5ff" }}
        >
          Coding Exercise
        </div>
        <h2 className="mt-1 text-2xl font-semibold tracking-tight">
          {exercise.topic}
        </h2>
      </header>

      <div className="flex-1 min-h-0 overflow-y-auto px-7 py-5 space-y-6">
        <section>
          <div
            className="mb-3 font-mono text-[10px] uppercase tracking-[0.3em]"
            style={{ color: "#00f5ff" }}
          >
            Task
          </div>
          <div className="bullet-md text-[13.5px] leading-relaxed">
            <InlineMarkdown>{exercise.task}</InlineMarkdown>
          </div>
        </section>

        {exercise.expected_output && (
          <section>
            <div
              className="mb-3 font-mono text-[10px] uppercase tracking-[0.3em]"
              style={{ color: "#00f5ff" }}
            >
              Expected output
            </div>
            <pre
              className="overflow-x-auto rounded-lg px-3 py-2 font-mono text-[12.5px]"
              style={{
                background: "rgba(2,2,3,0.6)",
                border: "1px solid rgba(0,245,255,0.16)",
                color: "#cdeefd",
              }}
            >
              <code>{exercise.expected_output}</code>
            </pre>
          </section>
        )}

        {exercise.constraints?.length > 0 && (
          <section>
            <div
              className="mb-3 font-mono text-[10px] uppercase tracking-[0.3em]"
              style={{ color: "#00f5ff" }}
            >
              Constraints
            </div>
            <ul className="bullet-list">
              {exercise.constraints.map((c, i) => (
                <li key={i} className="bullet-md">
                  <InlineMarkdown>{c}</InlineMarkdown>
                </li>
              ))}
            </ul>
          </section>
        )}

        <section>
          <div
            className="mb-3 flex items-center justify-between font-mono text-[10px] uppercase tracking-[0.3em]"
            style={{ color: "#00f5ff" }}
          >
            <span>Editor</span>
            <span style={{ color: "#9aa0a6" }}>solution.py</span>
          </div>
          <div
            className="overflow-hidden rounded-xl"
            style={{
              background: "rgba(2,2,3,0.7)",
              border: "1px solid rgba(0,245,255,0.18)",
              boxShadow: "0 0 24px rgba(0,245,255,0.08) inset",
            }}
          >
            {/* Mac-style window control dots */}
            <div
              className="flex items-center gap-2 border-b px-3 py-2"
              style={{ borderColor: "rgba(255,255,255,0.06)" }}
            >
              <span className="h-3 w-3 rounded-full" style={{ background: "#ff5f57" }} />
              <span className="h-3 w-3 rounded-full" style={{ background: "#febc2e" }} />
              <span className="h-3 w-3 rounded-full" style={{ background: "#28c840" }} />
              <span
                className="ml-3 font-mono text-[11px]"
                style={{ color: "rgba(255,255,255,0.45)" }}
              >
                solution.py
              </span>
            </div>
            <textarea
              ref={textareaRef}
              value={code}
              onChange={(e) => setCode(e.target.value)}
              onKeyDown={onKeyDown}
              spellCheck={false}
              rows={12}
              className="block w-full resize-y px-4 py-3 outline-none"
              style={{
                background: "transparent",
                color: "#cdeefd",
                fontFamily: "var(--font-mono)",
                fontSize: "13px",
                lineHeight: 1.55,
                fontFeatureSettings: '"liga" 1, "calt" 1',
                tabSize: 4,
              }}
            />
          </div>
        </section>
      </div>

      <footer
        className="flex items-center justify-end gap-3 border-t px-7 py-4"
        style={{ borderColor: "rgba(255,255,255,0.06)" }}
      >
        <button
          type="button"
          disabled={code.trim().length === 0 || submitting}
          onClick={onSubmit}
          className="rounded-lg px-5 py-2 text-sm font-semibold transition-all hover:scale-[1.02] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40"
          style={{
            background: "linear-gradient(135deg, #00f5ff 0%, #7000ff 100%)",
            color: "#020203",
            boxShadow: "0 6px 24px rgba(0,245,255,0.35)",
          }}
        >
          {submitting ? "Reviewing…" : "Submit code →"}
        </button>
      </footer>
    </div>
  );
}
