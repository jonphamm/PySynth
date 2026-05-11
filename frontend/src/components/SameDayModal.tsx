"use client";

import { useState } from "react";
import { parseChapter } from "@/lib/topic";
import type { NeedsIntent, StartIntent } from "@/types/session";
import { GlassPanel } from "./ui/GlassPanel";

type Props = {
  choice: NeedsIntent;
  onChoose: (intent: StartIntent) => Promise<void> | void;
};

export function SameDayModal({ choice, onChoose }: Props) {
  const [submitting, setSubmitting] = useState<StartIntent | null>(null);
  const { pointer, title } = parseChapter(choice.today_chapter);
  const headerLine = title ? `${pointer} — ${title}` : pointer;

  const handle = async (intent: StartIntent) => {
    if (submitting) return;
    setSubmitting(intent);
    try {
      await onChoose(intent);
    } finally {
      setSubmitting(null);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-6"
      style={{ background: "rgba(2, 2, 3, 0.65)", backdropFilter: "blur(8px)" }}
    >
      <GlassPanel
        variant="strong"
        className="w-full max-w-md p-7 text-center"
      >
        <div
          className="font-mono text-[10px] uppercase tracking-[0.5em]"
          style={{ color: "#00f5ff" }}
        >
          Already done today
        </div>
        <h2 className="mt-3 text-2xl font-semibold tracking-tight">
          What now?
        </h2>
        <p
          className="mt-3 text-sm leading-relaxed"
          style={{ color: "rgba(255,255,255,0.70)" }}
        >
          You already finished today&apos;s session on{" "}
          <span className="font-semibold" style={{ color: "#cdeefd" }}>
            {headerLine}
          </span>
          {choice.today_concept ? (
            <>
              {" "}
              ({choice.today_concept})
            </>
          ) : null}
          . Review the same chapter from a different angle, or move on to the
          next one?
        </p>

        <div className="mt-6 flex flex-col gap-3">
          <button
            type="button"
            onClick={() => handle("review")}
            disabled={submitting !== null}
            className="rounded-lg px-5 py-2.5 text-sm font-semibold transition-all hover:scale-[1.02] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60"
            style={{
              background: "linear-gradient(135deg, #00f5ff 0%, #7000ff 100%)",
              color: "#020203",
              boxShadow: "0 6px 24px rgba(0,245,255,0.30)",
            }}
          >
            {submitting === "review"
              ? "Reviewing from a different angle…"
              : "Review this chapter (fresh angle)"}
          </button>
          <button
            type="button"
            onClick={() => handle("advance")}
            disabled={submitting !== null}
            className="rounded-lg px-5 py-2.5 text-sm font-semibold transition-all hover:scale-[1.01] active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-60"
            style={{
              background: "rgba(255, 255, 255, 0.06)",
              border: "1px solid rgba(255, 255, 255, 0.14)",
              color: "#f5f5f5",
            }}
          >
            {submitting === "advance"
              ? "Generating next chapter…"
              : "Move on to the next chapter"}
          </button>
        </div>
      </GlassPanel>
    </div>
  );
}
