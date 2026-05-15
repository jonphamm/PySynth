"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { listDoneChapters } from "@/lib/api";
import { useWizard } from "@/hooks/useWizard";
import { wizardOrder } from "@/lib/tokens";
import { parseChapter } from "@/lib/topic";
import type { DoneChapter } from "@/types/session";
import { Sidebar } from "./Sidebar";
import { HeaderBar } from "./HeaderBar";
import { FooterStatus } from "./FooterStatus";
import { StagePanel } from "./StagePanel";
import { MentorPanel } from "./MentorPanel";
import { MouseFollowerGlow } from "./MouseFollowerGlow";
import { SameDayModal } from "./SameDayModal";
import { SwitchChapterModal } from "./SwitchChapterModal";
import { ProgressOrbit } from "./ui/ProgressOrbit";

export function DashboardShell() {
  const wizard = useWizard();
  const {
    stage,
    goTo,
    index,
    sessionData,
    pendingChoice,
    startWithIntent,
    status,
  } = wizard;
  const startedRef = useRef(false);
  const [pendingSwitch, setPendingSwitch] = useState<string | null>(null);
  const [doneChapters, setDoneChapters] = useState<DoneChapter[]>([]);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [mentorOpen, setMentorOpen] = useState(false);
  const progress = (index + 1) / wizardOrder.length;

  const refreshDoneChapters = useCallback(() => {
    listDoneChapters()
      .then((res) => setDoneChapters(res.chapters))
      .catch(() => {
        /* sidebar list is non-critical — fail silently */
      });
  }, []);

  useEffect(() => {
    refreshDoneChapters();
  }, [refreshDoneChapters]);

  const handleSwitchChapter = useCallback(
    (chapter: string) => {
      if (sessionData) {
        setPendingSwitch(chapter);
      } else {
        void startWithIntent(undefined, chapter);
      }
    },
    [sessionData, startWithIntent],
  );

  useEffect(() => {
    if (!sessionData && !pendingChoice) startedRef.current = false;
  }, [sessionData, pendingChoice]);

  useEffect(() => {
    if (startedRef.current || sessionData || pendingChoice) return;
    startedRef.current = true;
    void startWithIntent();
  }, [sessionData, pendingChoice, startWithIntent]);

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

      <div className="app-shell relative z-10 mx-auto flex h-dvh max-w-[1500px] flex-col gap-3">
        {/* Header row: header bar with progress orbit */}
        <div className="flex items-center gap-3">
          <div className="min-w-0 flex-1">
            <HeaderBar
              chapter={headerChapter}
              concept="MOOC.fi 2026 · Daily"
              xp={120}
              onMenuClick={() => setMobileMenuOpen(true)}
              onMentorClick={() => setMentorOpen(true)}
            />
          </div>
          <div className="glass hidden h-14 items-center gap-3 px-4 sm:flex">
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

        {/* Responsive Command Center: 1 col mobile, 2 col tablet, 3 col desktop */}
        <div className="grid min-h-0 flex-1 grid-cols-1 gap-3 md:grid-cols-[260px_1fr] lg:grid-cols-[260px_1fr_340px]">
          <Sidebar
            current={stage}
            onJump={goTo}
            chapterPointer={sidebarPointer}
            conceptLabel={sidebarConcept}
            currentChapter={sessionData?.topic.chapter ?? ""}
            onSwitchChapter={handleSwitchChapter}
            doneChapters={doneChapters}
            mobileOpen={mobileMenuOpen}
            onMobileClose={() => setMobileMenuOpen(false)}
          />
          <StagePanel wizard={wizard} onSessionLogged={refreshDoneChapters} />
          <MentorPanel
            chapter={sessionData?.topic.chapter ?? ""}
            concept={sessionData?.topic.concept ?? ""}
            stage={stage}
            mobileOpen={mentorOpen}
            onMobileClose={() => setMentorOpen(false)}
          />
        </div>

        {/* Footer */}
        <FooterStatus status={status} />
      </div>

      {pendingChoice && (
        <SameDayModal choice={pendingChoice} onChoose={startWithIntent} />
      )}

      {pendingSwitch && (
        <SwitchChapterModal
          targetChapter={pendingSwitch}
          onCancel={() => setPendingSwitch(null)}
          onConfirm={async () => {
            const target = pendingSwitch;
            setPendingSwitch(null);
            await startWithIntent(undefined, target);
          }}
        />
      )}
    </>
  );
}
