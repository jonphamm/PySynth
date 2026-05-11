"use client";

import { useEffect, useRef } from "react";
import { useWizard } from "@/hooks/useWizard";
import { wizardOrder } from "@/lib/tokens";
import { startSession } from "@/lib/api";
import { parseChapter } from "@/lib/topic";
import { Sidebar } from "./Sidebar";
import { HeaderBar } from "./HeaderBar";
import { FooterStatus } from "./FooterStatus";
import { StagePanel } from "./StagePanel";
import { MentorPanel } from "./MentorPanel";
import { MouseFollowerGlow } from "./MouseFollowerGlow";
import { ProgressOrbit } from "./ui/ProgressOrbit";

export function DashboardShell() {
  const wizard = useWizard();
  const { stage, goTo, index, sessionData, setSessionData, status, setStatus, initAnswerSlots } =
    wizard;
  const startedRef = useRef(false);
  const progress = (index + 1) / wizardOrder.length;

  useEffect(() => {
    if (startedRef.current || sessionData) return;
    startedRef.current = true;
    setStatus({ kind: "loading", what: "Generating today's session…" });
    startSession()
      .then((data) => {
        setSessionData(data);
        initAnswerSlots(data.questions.length);
        setStatus({ kind: "idle" });
      })
      .catch((err: Error) => {
        startedRef.current = false;
        setStatus({ kind: "error", message: err.message });
      });
  }, [sessionData, setSessionData, setStatus, initAnswerSlots]);

  const headerChapter = sessionData?.topic
    ? `${sessionData.topic.chapter} — ${sessionData.topic.concept}`
    : "Loading today's chapter…";
  const sidebarPointer = sessionData?.topic
    ? parseChapter(sessionData.topic.chapter).pointer
    : "";
  const sidebarConcept = sessionData?.topic?.concept ?? "";

  return (
    <>
      <MouseFollowerGlow />

      <div className="relative z-10 mx-auto flex h-screen max-w-[1500px] flex-col gap-3 p-4">
        {/* Header row: header bar with progress orbit */}
        <div className="flex items-center gap-3">
          <div className="flex-1">
            <HeaderBar
              chapter={headerChapter}
              concept="MOOC.fi 2026 · Daily"
              xp={120}
            />
          </div>
          <div className="glass flex h-14 items-center gap-3 px-4">
            <ProgressOrbit value={progress} size={40} stroke={3} />
            <div className="leading-tight">
              <div
                className="font-mono text-[10px] uppercase tracking-[0.3em]"
                style={{ color: "#9aa0a6" }}
              >
                Stage
              </div>
              <div className="text-xs font-semibold" style={{ color: "#cdeefd" }}>
                {index + 1} / {wizardOrder.length}
              </div>
            </div>
          </div>
        </div>

        {/* Three-pane Command Center */}
        <div className="grid min-h-0 flex-1 grid-cols-[260px_1fr_340px] gap-3">
          <Sidebar
            current={stage}
            onJump={goTo}
            chapterPointer={sidebarPointer}
            conceptLabel={sidebarConcept}
          />
          <StagePanel wizard={wizard} />
          <MentorPanel />
        </div>

        {/* Footer */}
        <FooterStatus status={status} />
      </div>
    </>
  );
}
