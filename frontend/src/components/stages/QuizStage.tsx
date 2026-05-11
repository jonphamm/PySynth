"use client";

import type { Wizard } from "@/hooks/useWizard";
import type { Question } from "@/types/session";
import { gradeQuiz } from "@/lib/api";
import { InlineMarkdown } from "@/lib/markdown";
import { SyntaxHighlight } from "@/components/ui/SyntaxHighlight";
import { StageStatus } from "./StageStatus";

type Props = {
  wizard: Wizard;
};

export function QuizStage({ wizard }: Props) {
  const {
    sessionData,
    answers,
    pickedIndexes,
    setAnswer,
    setPicked,
    setGradeResult,
    setStatus,
    status,
    advance,
  } = wizard;

  if (!sessionData) {
    return (
      <StageStatus
        label="Quiz"
        status={status}
        onRetry={() => setStatus({ kind: "idle" })}
        loadingMessage="Preparing the quiz…"
      />
    );
  }

  const questions = sessionData.questions;
  const allAnswered = questions.every((q, i) => {
    if (q.type === "mc") return pickedIndexes[i] != null;
    return (answers[i] ?? "").trim().length > 0;
  });

  const onSubmit = () => {
    // Eagerly fire grade — by the time the user reaches GradeStage it'll be loaded.
    setStatus({ kind: "loading", what: "Grading your answers…" });
    gradeQuiz({
      questions,
      answers,
      picked_indexes: pickedIndexes,
    })
      .then((result) => {
        setGradeResult(result);
        setStatus({ kind: "idle" });
      })
      .catch((err: Error) => {
        setStatus({ kind: "error", message: err.message });
      });
    advance();
  };

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
          Quiz
        </div>
        <h2 className="mt-1 text-2xl font-semibold tracking-tight">
          Four questions
        </h2>
        <p className="mt-1 text-sm" style={{ color: "rgba(255,255,255,0.55)" }}>
          Three anchors and one stretch. The stretch is where real learning lives.
        </p>
      </header>

      <div className="flex-1 min-h-0 overflow-y-auto px-7 py-5 space-y-6">
        {questions.map((q, i) => (
          <QuestionCard
            key={i}
            index={i}
            q={q}
            picked={pickedIndexes[i] ?? null}
            answer={answers[i] ?? ""}
            onPick={(idx) => setPicked(i, idx)}
            onType={(text) => setAnswer(i, text)}
          />
        ))}
      </div>

      <footer
        className="flex items-center justify-between gap-3 border-t px-7 py-4"
        style={{ borderColor: "rgba(255,255,255,0.06)" }}
      >
        <p className="text-xs" style={{ color: "rgba(255,255,255,0.45)" }}>
          {allAnswered ? "Ready to submit." : "Answer all four to continue."}
        </p>
        <button
          type="button"
          disabled={!allAnswered}
          onClick={onSubmit}
          className="rounded-lg px-5 py-2 text-sm font-semibold transition-all hover:scale-[1.02] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40"
          style={{
            background: "linear-gradient(135deg, #00f5ff 0%, #7000ff 100%)",
            color: "#020203",
            boxShadow: "0 6px 24px rgba(0,245,255,0.35)",
          }}
        >
          Submit answers →
        </button>
      </footer>
    </div>
  );
}

function QuestionCard({
  index,
  q,
  picked,
  answer,
  onPick,
  onType,
}: {
  index: number;
  q: Question;
  picked: number | null;
  answer: string;
  onPick: (idx: number) => void;
  onType: (text: string) => void;
}) {
  return (
    <div
      className="rounded-2xl border p-5"
      style={{
        background: "rgba(2,2,3,0.45)",
        borderColor: "rgba(255,255,255,0.06)",
      }}
    >
      <div
        className="mb-2 font-mono text-[10px] uppercase tracking-[0.3em]"
        style={{ color: "#00f5ff" }}
      >
        Question {index + 1}
      </div>
      <div className="bullet-md text-[14px] font-medium" style={{ color: "rgba(245,245,245,0.95)" }}>
        <InlineMarkdown>{q.text}</InlineMarkdown>
      </div>
      {q.type === "mc" && q.code && (
        <div className="mt-3">
          <SyntaxHighlight code={q.code} />
        </div>
      )}

      {q.type === "mc" ? (
        <div className="mt-4 space-y-2">
          {q.options.map((opt, idx) => {
            const selected = picked === idx;
            return (
              <button
                key={idx}
                type="button"
                onClick={() => onPick(idx)}
                className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-[13.5px] transition-all"
                style={{
                  background: selected
                    ? "rgba(0,245,255,0.12)"
                    : "rgba(255,255,255,0.03)",
                  border: selected
                    ? "1px solid rgba(0,245,255,0.55)"
                    : "1px solid rgba(255,255,255,0.08)",
                  color: selected ? "#cdeefd" : "rgba(245,245,245,0.85)",
                  boxShadow: selected ? "0 0 18px rgba(0,245,255,0.25)" : "none",
                }}
              >
                <span
                  className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full font-mono text-[11px]"
                  style={{
                    background: selected
                      ? "linear-gradient(135deg, #00f5ff, #7000ff)"
                      : "rgba(255,255,255,0.06)",
                    color: selected ? "#020203" : "rgba(255,255,255,0.55)",
                  }}
                >
                  {String.fromCharCode(97 + idx)}
                </span>
                <span className="font-mono">{opt}</span>
              </button>
            );
          })}
        </div>
      ) : (
        <textarea
          value={answer}
          onChange={(e) => onType(e.target.value)}
          placeholder="Type your answer…"
          rows={3}
          className="mt-4 w-full resize-none rounded-lg px-3 py-2 text-[13.5px] outline-none transition-colors focus:border-[rgba(0,245,255,0.55)]"
          style={{
            background: "rgba(2,2,3,0.6)",
            border: "1px solid rgba(255,255,255,0.08)",
            color: "rgba(245,245,245,0.95)",
            fontFamily: "var(--font-sans)",
          }}
        />
      )}
    </div>
  );
}
