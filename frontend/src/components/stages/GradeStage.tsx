"use client";

import ReactMarkdown from "react-markdown";
import type { Language } from "prism-react-renderer";
import type { Wizard } from "@/hooks/useWizard";
import { SyntaxHighlight } from "@/components/ui/SyntaxHighlight";
import { StageStatus } from "./StageStatus";

type Props = {
  wizard: Wizard;
};

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

export function GradeStage({ wizard }: Props) {
  const {
    gradeResult,
    reviewResult,
    exerciseResult,
    feeling,
    setFeeling,
    advance,
    status,
    setStatus,
  } = wizard;

  if (!gradeResult || !reviewResult) {
    return (
      <StageStatus
        label="Grade & Review"
        status={status}
        loadingMessage="Crunching your answers and code review…"
        onRetry={() => setStatus({ kind: "idle" })}
      />
    );
  }

  const verdictBadge =
    reviewResult.verdict === "pass"
      ? { label: "PASS", color: "#22f5a3" }
      : reviewResult.verdict === "close"
        ? { label: "CLOSE", color: "#ffae42" }
        : { label: "NEEDS FIX", color: "#ff5f57" };

  const showReference =
    reviewResult.verdict !== "pass" && !!reviewResult.reference_solution?.trim();

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
          Grade & Review
        </div>
        <div className="mt-1 flex items-baseline gap-3">
          <h2 className="text-2xl font-semibold tracking-tight">
            {gradeResult.score_correct} / {gradeResult.score_total}
          </h2>
          <span
            className="rounded-md px-2 py-0.5 font-mono text-[10px] font-bold uppercase tracking-widest"
            style={{
              color: verdictBadge.color,
              border: `1px solid ${verdictBadge.color}66`,
              background: `${verdictBadge.color}14`,
            }}
          >
            {verdictBadge.label}
          </span>
        </div>
      </header>

      <div className="flex-1 min-h-0 overflow-y-auto px-7 py-5 space-y-7">
        <Section label="Quiz grade">
          <div className="markdown">
            <ReactMarkdown components={MARKDOWN_COMPONENTS}>
              {gradeResult.grade_markdown}
            </ReactMarkdown>
          </div>
        </Section>

        <Section label="Code review">
          <div className="markdown">
            <ReactMarkdown components={MARKDOWN_COMPONENTS}>
              {reviewResult.review_markdown}
            </ReactMarkdown>
          </div>
        </Section>

        {showReference && (
          <Section label="Reference solution">
            <p
              className="mb-3 text-xs"
              style={{ color: "rgba(255,255,255,0.55)" }}
            >
              One clean, idiomatic way to solve this exercise. Compare against
              your submission to spot the gap.
            </p>
            <SyntaxHighlight code={reviewResult.reference_solution ?? ""} />
          </Section>
        )}

        {exerciseResult?.apply_at_work && (
          <Section
            label={`Apply at work — Angle ${exerciseResult.apply_at_work.angle}`}
          >
            <p className="bullet-md text-[13.5px] leading-relaxed">
              {exerciseResult.apply_at_work.text}
            </p>
          </Section>
        )}

        <Section label="Feeling note (optional)">
          <input
            type="text"
            maxLength={20}
            value={feeling}
            onChange={(e) => setFeeling(e.target.value)}
            placeholder="One word — e.g. clicked, smooth, rough"
            className="w-full rounded-lg px-3 py-2 text-[13.5px] outline-none transition-colors focus:border-[rgba(0,245,255,0.55)]"
            style={{
              background: "rgba(2,2,3,0.6)",
              border: "1px solid rgba(255,255,255,0.08)",
              color: "rgba(245,245,245,0.95)",
              fontFamily: "var(--font-sans)",
            }}
          />
        </Section>
      </div>

      <footer
        className="flex items-center justify-end gap-3 border-t px-7 py-4"
        style={{ borderColor: "rgba(255,255,255,0.06)" }}
      >
        <button
          type="button"
          onClick={advance}
          className="rounded-lg px-5 py-2 text-sm font-semibold transition-all hover:scale-[1.02] active:scale-[0.98]"
          style={{
            background: "linear-gradient(135deg, #00f5ff 0%, #7000ff 100%)",
            color: "#020203",
            boxShadow: "0 6px 24px rgba(0,245,255,0.35)",
          }}
        >
          Wrap up →
        </button>
      </footer>
    </div>
  );
}

function Section({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <section>
      <div
        className="mb-3 font-mono text-[10px] uppercase tracking-[0.3em]"
        style={{ color: "#00f5ff" }}
      >
        {label}
      </div>
      <div style={{ color: "rgba(245,245,245,0.88)" }}>{children}</div>
    </section>
  );
}
