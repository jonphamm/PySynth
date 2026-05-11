"use client";

import { useState } from "react";
import { parseChapter } from "@/lib/topic";
import { GlassPanel } from "./ui/GlassPanel";

type Props = {
  targetChapter: string;
  onCancel: () => void;
  onConfirm: () => Promise<void> | void;
};

export function SwitchChapterModal({ targetChapter, onCancel, onConfirm }: Props) {
  const [submitting, setSubmitting] = useState(false);
  const { pointer, title } = parseChapter(targetChapter);
  const headerLine = title ? `${pointer} — ${title}` : pointer;

  const handleConfirm = async () => {
    if (submitting) return;
    setSubmitting(true);
    try {
      await onConfirm();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-6"
      style={{ background: "rgba(2, 2, 3, 0.65)", backdropFilter: "blur(8px)" }}
      onClick={onCancel}
    >
      <GlassPanel
        variant="strong"
        className="w-full max-w-md p-7 text-center"
        onClick={(e) => e.stopPropagation()}
      >
        <div
          className="font-mono text-[10px] uppercase tracking-[0.5em]"
          style={{ color: "#00f5ff" }}
        >
          Switch chapter
        </div>
        <h2 className="mt-3 text-2xl font-semibold tracking-tight">
          Revisit {headerLine}?
        </h2>
        <p
          className="mt-3 text-sm leading-relaxed"
          style={{ color: "rgba(255,255,255,0.70)" }}
        >
          You&apos;ll lose any in-progress quiz answers or code on the current
          session. Tomorrow&apos;s session will resume the normal flow.
        </p>

        <div className="mt-6 flex flex-col gap-3">
          <button
            type="button"
            onClick={handleConfirm}
            disabled={submitting}
            className="rounded-lg px-5 py-2.5 text-sm font-semibold transition-all hover:scale-[1.02] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60"
            style={{
              background: "linear-gradient(135deg, #00f5ff 0%, #7000ff 100%)",
              color: "#020203",
              boxShadow: "0 6px 24px rgba(0,245,255,0.30)",
            }}
          >
            {submitting ? "Switching…" : "Switch to this chapter"}
          </button>
          <button
            type="button"
            onClick={onCancel}
            disabled={submitting}
            className="rounded-lg px-5 py-2.5 text-sm font-semibold transition-all hover:scale-[1.01] active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-60"
            style={{
              background: "rgba(255, 255, 255, 0.06)",
              border: "1px solid rgba(255, 255, 255, 0.14)",
              color: "#f5f5f5",
            }}
          >
            Cancel
          </button>
        </div>
      </GlassPanel>
    </div>
  );
}
