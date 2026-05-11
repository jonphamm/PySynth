"use client";

import { AnimatePresence, motion } from "framer-motion";
import { ConceptStage } from "./stages/ConceptStage";
import { QuizStage } from "./stages/QuizStage";
import { EditorStage } from "./stages/EditorStage";
import { GradeStage } from "./stages/GradeStage";
import { DoneStage } from "./stages/DoneStage";
import type { Wizard } from "@/hooks/useWizard";

type StagePanelProps = {
  wizard: Wizard;
  onSessionLogged?: () => void;
};

export function StagePanel({ wizard, onSessionLogged }: StagePanelProps) {
  const { stage } = wizard;

  return (
    <section className="glass-strong flowing-border scanlines relative flex h-full min-h-0 flex-col overflow-hidden">
      <div className="flex h-full min-h-0 flex-col">
        <AnimatePresence mode="wait">
          <motion.div
            key={stage}
            initial={{ opacity: 0, filter: "blur(8px)", y: 8 }}
            animate={{ opacity: 1, filter: "blur(0px)", y: 0 }}
            exit={{ opacity: 0, filter: "blur(8px)", y: -8 }}
            transition={{ duration: 0.35, ease: [0.2, 0.8, 0.2, 1] }}
            className="flex h-full min-h-0 flex-col"
          >
            {stage === "concept" && <ConceptStage wizard={wizard} />}
            {stage === "quiz" && <QuizStage wizard={wizard} />}
            {stage === "editor" && <EditorStage wizard={wizard} />}
            {stage === "grade" && <GradeStage wizard={wizard} />}
            {stage === "done" && (
              <DoneStage wizard={wizard} onSessionLogged={onSessionLogged} />
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </section>
  );
}
