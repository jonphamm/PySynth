"use client";

import type { Wizard } from "@/hooks/useWizard";
import { SyntaxHighlight } from "@/components/ui/SyntaxHighlight";
import { InlineMarkdown } from "@/lib/markdown";
import { StageStatus } from "./StageStatus";

type Props = {
  wizard: Wizard;
};

export function ConceptStage({ wizard }: Props) {
  const { sessionData, advance, status, setStatus } = wizard;

  if (!sessionData) {
    return (
      <StageStatus
        label="Concept Review"
        status={status}
        onRetry={() => setStatus({ kind: "idle" })}
        loadingMessage="Generating today's session…"
      />
    );
  }

  const { concept_review: review, topic } = sessionData;

  return (
    <div className="flex h-full min-h-0 flex-col">
      <header className="border-b px-4 py-4 sm:px-7 sm:py-5" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
        <div
          className="font-mono text-[10px] uppercase tracking-[0.4em]"
          style={{ color: "#00f5ff" }}
        >
          Concept Review
        </div>
        <h2 className="mt-1 text-2xl font-semibold tracking-tight">
          {topic.concept}
        </h2>
        <p className="mt-1 text-sm" style={{ color: "rgba(255,255,255,0.55)" }}>
          {topic.chapter}
        </p>
      </header>

      <div className="flex-1 min-h-0 overflow-y-auto px-4 py-4 sm:px-7 sm:py-5 space-y-7 text-[13.5px] leading-relaxed">
        <Section label="Definition">
          <div className="bullet-md">
            <InlineMarkdown>{review.definition}</InlineMarkdown>
          </div>
        </Section>

        <Section label="How it works">
          <BulletList items={review.how_it_works} />
        </Section>

        <Section label="Syntax forms">
          <div className="space-y-4">
            {review.syntax_forms.map((form, i) => (
              <div key={i}>
                <div
                  className="mb-1.5 font-mono text-[10px] uppercase tracking-widest"
                  style={{ color: "#9aa0a6" }}
                >
                  {form.label}
                </div>
                <SyntaxHighlight code={form.code} />
              </div>
            ))}
          </div>
        </Section>

        <Section label="Worked example">
          <SyntaxHighlight code={review.worked_example_code} />
          <BulletList items={review.worked_example_walkthrough} className="mt-4" />
        </Section>

        <Section label="Common patterns">
          <BulletList items={review.common_patterns} />
        </Section>

        <Section label="When to use it">
          <div className="bullet-md">
            <InlineMarkdown>{review.when_to_use}</InlineMarkdown>
          </div>
        </Section>

        <Section label="Analogy">
          <div className="bullet-md">
            <InlineMarkdown>{review.analogy}</InlineMarkdown>
          </div>
        </Section>

        <Section label="Watch out for">
          <div className="bullet-md">
            <InlineMarkdown>{review.gotcha}</InlineMarkdown>
          </div>
        </Section>
      </div>

      <footer
        className="flex items-center justify-end gap-3 border-t px-4 py-3 sm:px-7 sm:py-4"
        style={{ borderColor: "rgba(255,255,255,0.06)" }}
      >
        <p className="text-xs" style={{ color: "rgba(255,255,255,0.45)" }}>
          Read through, then move on to the quiz.
        </p>
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
          Start Quiz →
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

function BulletList({
  items,
  className = "",
}: {
  items: string[];
  className?: string;
}) {
  return (
    <ul className={`bullet-list ${className}`.trim()}>
      {items.map((item, i) => (
        <li key={i} className="bullet-md">
          <InlineMarkdown>{item}</InlineMarkdown>
        </li>
      ))}
    </ul>
  );
}

