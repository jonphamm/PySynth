"use client";

import { useEffect, useRef, useState } from "react";
import type { Wizard } from "@/hooks/useWizard";
import { logSession } from "@/lib/api";

type Props = {
  wizard: Wizard;
  onSessionLogged?: () => void;
};

export function DoneStage({ wizard, onSessionLogged }: Props) {
  const {
    sessionData,
    exerciseResult,
    gradeResult,
    reviewResult,
    code,
    feeling,
    reset,
  } = wizard;
  const loggedRef = useRef(false);
  const [logState, setLogState] = useState<"pending" | "ok" | "error">("pending");
  const [logError, setLogError] = useState<string>("");

  useEffect(() => {
    if (loggedRef.current) return;
    if (!sessionData || !exerciseResult || !gradeResult || !reviewResult) return;
    loggedRef.current = true;

    const apply = exerciseResult.apply_at_work;
    const applySummary = apply?.text
      ? apply.text.split(/\s+/).slice(0, 12).join(" ")
      : "";
    const verdictWord =
      reviewResult.verdict === "pass"
        ? "pass"
        : reviewResult.verdict === "close"
          ? "partial"
          : "needs fix";

    logSession({
      chapter: sessionData.topic.chapter || "?",
      topic: sessionData.topic.concept || "?",
      quiz_score: `${gradeResult.score_correct}/${gradeResult.score_total}`,
      exercise_verdict: verdictWord,
      apply_summary: applySummary,
      angle: exerciseResult.angle || "A",
      feeling: feeling.trim(),
      code,
      exercise_text: exerciseResult.exercise_text || "",
      type: "Daily",
    })
      .then(() => {
        setLogState("ok");
        onSessionLogged?.();
      })
      .catch((err: Error) => {
        loggedRef.current = false;
        setLogState("error");
        setLogError(err.message);
      });
  }, [sessionData, exerciseResult, gradeResult, reviewResult, code, feeling, onSessionLogged]);

  return (
    <div className="flex h-full min-h-0 flex-col items-center justify-center px-10 py-10 text-center">
      <div
        className="font-mono text-[10px] uppercase tracking-[0.5em]"
        style={{ color: "#00f5ff" }}
      >
        Session complete
      </div>
      <h2 className="mt-3 text-3xl font-semibold tracking-tight">
        Nice work today.
      </h2>
      <p
        className="mt-3 max-w-md text-sm leading-relaxed"
        style={{ color: "rgba(255,255,255,0.65)" }}
      >
        {logState === "pending" && "Logging your session…"}
        {logState === "ok" && "Logged. Tomorrow's session picks up where you left off."}
        {logState === "error" && (
          <span style={{ color: "rgba(255,200,200,0.85)" }}>
            Couldn&apos;t log session: {logError}
          </span>
        )}
      </p>
      <button
        type="button"
        onClick={reset}
        className="mt-7 rounded-lg px-5 py-2 text-sm font-semibold transition-all hover:scale-[1.02] active:scale-[0.98]"
        style={{
          background: "linear-gradient(135deg, #00f5ff 0%, #7000ff 100%)",
          color: "#020203",
          boxShadow: "0 6px 24px rgba(0,245,255,0.35)",
        }}
      >
        Start another session
      </button>
    </div>
  );
}
