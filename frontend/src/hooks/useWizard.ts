"use client";

import { useCallback, useState } from "react";
import { startSession } from "@/lib/api";
import { wizardOrder } from "@/lib/tokens";
import type {
  ExerciseResult,
  GradeResult,
  NeedsIntent,
  ReviewResult,
  SessionData,
  StartIntent,
  Status,
  WizardStage,
} from "@/types/session";

export type Wizard = ReturnType<typeof useWizard>;

export function useWizard(initial: WizardStage = "concept") {
  const [stage, setStage] = useState<WizardStage>(initial);

  const [sessionData, setSessionData] = useState<SessionData | null>(null);
  const [exerciseResult, setExerciseResult] = useState<ExerciseResult | null>(
    null,
  );
  const [gradeResult, setGradeResult] = useState<GradeResult | null>(null);
  const [reviewResult, setReviewResult] = useState<ReviewResult | null>(null);
  const [pendingChoice, setPendingChoice] = useState<NeedsIntent | null>(null);

  const [answers, setAnswers] = useState<string[]>([]);
  const [pickedIndexes, setPickedIndexes] = useState<(number | null)[]>([]);
  const [code, setCode] = useState<string>("# Write your solution here\n\n");
  const [feeling, setFeeling] = useState<string>("");

  const [status, setStatus] = useState<Status>({ kind: "idle" });

  const advance = useCallback(() => {
    setStage((current) => {
      const idx = wizardOrder.indexOf(current);
      if (idx < 0 || idx === wizardOrder.length - 1) return current;
      return wizardOrder[idx + 1];
    });
  }, []);

  const goTo = useCallback((next: WizardStage) => {
    setStage(next);
  }, []);

  const reset = useCallback(() => {
    setStage("concept");
    setSessionData(null);
    setExerciseResult(null);
    setGradeResult(null);
    setReviewResult(null);
    setPendingChoice(null);
    setAnswers([]);
    setPickedIndexes([]);
    setCode("# Write your solution here\n\n");
    setFeeling("");
    setStatus({ kind: "idle" });
  }, []);

  const initAnswerSlotsFor = useCallback((n: number) => {
    setAnswers(Array.from({ length: n }, () => ""));
    setPickedIndexes(Array.from({ length: n }, () => null));
  }, []);

  const startWithIntent = useCallback(
    async (intent?: StartIntent) => {
      const loadingMessage =
        intent === "review"
          ? "Reviewing from a different angle…"
          : "Generating today's session…";
      setStatus({ kind: "loading", what: loadingMessage });
      try {
        const response = await startSession(intent);
        if (response.kind === "needs_intent") {
          setPendingChoice(response);
          setSessionData(null);
          setStatus({ kind: "idle" });
          return;
        }
        setPendingChoice(null);
        setSessionData(response);
        initAnswerSlotsFor(response.questions.length);
        setStatus({ kind: "idle" });
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        setStatus({ kind: "error", message });
      }
    },
    [initAnswerSlotsFor],
  );

  const setAnswer = useCallback((i: number, text: string) => {
    setAnswers((prev) => {
      const next = [...prev];
      next[i] = text;
      return next;
    });
  }, []);

  const setPicked = useCallback((i: number, idx: number | null) => {
    setPickedIndexes((prev) => {
      const next = [...prev];
      next[i] = idx;
      return next;
    });
  }, []);

  const initAnswerSlots = useCallback((n: number) => {
    setAnswers((prev) =>
      prev.length === n ? prev : Array.from({ length: n }, () => ""),
    );
    setPickedIndexes((prev) =>
      prev.length === n ? prev : Array.from({ length: n }, () => null),
    );
  }, []);

  const index = wizardOrder.indexOf(stage);
  const isLast = index === wizardOrder.length - 1;

  return {
    stage,
    advance,
    goTo,
    reset,
    index,
    isLast,
    sessionData,
    setSessionData,
    exerciseResult,
    setExerciseResult,
    gradeResult,
    setGradeResult,
    reviewResult,
    setReviewResult,
    pendingChoice,
    startWithIntent,
    answers,
    pickedIndexes,
    setAnswer,
    setPicked,
    initAnswerSlots,
    code,
    setCode,
    feeling,
    setFeeling,
    status,
    setStatus,
  };
}
