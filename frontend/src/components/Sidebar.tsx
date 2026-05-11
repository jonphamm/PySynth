"use client";

import { parseChapter } from "@/lib/topic";
import { wizardOrder } from "@/lib/tokens";
import type { DoneChapter, WizardStage } from "@/types/session";

const STAGE_META: Record<
  WizardStage,
  { label: string; glyph: string }
> = {
  concept: { label: "Concept", glyph: "◔" },
  quiz: { label: "Quiz", glyph: "◑" },
  editor: { label: "Code", glyph: "◕" },
  grade: { label: "Grade", glyph: "●" },
  done: { label: "Done", glyph: "✦" },
};

type SidebarProps = {
  current: WizardStage;
  onJump?: (stage: WizardStage) => void;
  chapterPointer: string;
  conceptLabel: string;
  currentChapter: string;
  onSwitchChapter: (chapter: string) => void;
  doneChapters: DoneChapter[];
};

export function Sidebar({
  current,
  onJump,
  chapterPointer,
  conceptLabel,
  currentChapter,
  onSwitchChapter,
  doneChapters,
}: SidebarProps) {
  const currentIdx = wizardOrder.indexOf(current);

  const visibleChapters = doneChapters.filter(
    (c) => c.chapter !== currentChapter,
  );

  return (
    <aside className="glass relative flex h-full w-[260px] flex-col p-5">
      <div className="mb-6">
        <div
          className="font-mono text-[10px] uppercase tracking-[0.4em]"
          style={{ color: "#00f5ff" }}
        >
          PYSYNTH
        </div>
        <div className="mt-1 text-sm font-semibold tracking-tight">
          Learning Paths
        </div>
        <div className="mt-1 text-[11px]" style={{ color: "#9aa0a6" }}>
          MOOC.fi 2026 · Daily Session
        </div>
      </div>

      <nav className="relative">
        {/* Vertical progress line behind the icons */}
        <div
          aria-hidden
          className="absolute left-[19px] top-2 bottom-2 w-px"
          style={{ background: "rgba(255,255,255,0.08)" }}
        />
        <div
          aria-hidden
          className="absolute left-[19px] top-2 w-px"
          style={{
            background:
              "linear-gradient(to bottom, #00f5ff 0%, #7000ff 100%)",
            boxShadow: "0 0 12px rgba(0,245,255,0.55)",
            height: `calc(${(currentIdx / (wizardOrder.length - 1)) * 100}% - 4px)`,
            transition: "height 600ms cubic-bezier(0.2,0.8,0.2,1)",
          }}
        />

        <ul className="relative space-y-1">
          {wizardOrder.map((stage, idx) => {
            const meta = STAGE_META[stage];
            const isActive = stage === current;
            const isPast = idx < currentIdx;
            return (
              <li key={stage}>
                <button
                  type="button"
                  onClick={onJump ? () => onJump(stage) : undefined}
                  disabled={!onJump}
                  className={`group relative flex w-full items-center gap-3 rounded-lg px-2 py-2 text-left transition-colors ${
                    onJump ? "cursor-pointer" : "cursor-default"
                  }`}
                  aria-current={isActive ? "step" : undefined}
                >
                  {/* Stage marker */}
                  <span
                    className="z-10 flex h-9 w-9 shrink-0 items-center justify-center rounded-full font-mono text-base transition-all"
                    style={{
                      background: isActive
                        ? "linear-gradient(135deg, #00f5ff, #7000ff)"
                        : isPast
                        ? "rgba(0,245,255,0.18)"
                        : "rgba(255,255,255,0.04)",
                      border: isActive
                        ? "1px solid rgba(255,255,255,0.30)"
                        : "1px solid rgba(255,255,255,0.10)",
                      color: isActive
                        ? "#020203"
                        : isPast
                        ? "#cdeefd"
                        : "rgba(255,255,255,0.55)",
                      boxShadow: isActive
                        ? "0 0 24px rgba(0,245,255,0.55)"
                        : "none",
                    }}
                  >
                    {meta.glyph}
                  </span>
                  <div className="min-w-0">
                    <div
                      className="text-sm font-medium"
                      style={{
                        color: isActive
                          ? "#f5f5f5"
                          : isPast
                          ? "rgba(245,245,245,0.85)"
                          : "rgba(245,245,245,0.55)",
                      }}
                    >
                      {meta.label}
                    </div>
                    <div
                      className="font-mono text-[10px] uppercase tracking-widest"
                      style={{ color: "#9aa0a6" }}
                    >
                      Stage {idx + 1}
                    </div>
                  </div>
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      {visibleChapters.length > 0 && (
        <div
          className="mt-4 flex-1 overflow-y-auto border-t pt-4"
          style={{ borderColor: "rgba(255,255,255,0.08)" }}
        >
          <div
            className="font-mono text-[10px] uppercase tracking-[0.3em]"
            style={{ color: "#9aa0a6" }}
          >
            Past chapters · {visibleChapters.length}
          </div>
          <ul className="mt-2 space-y-1">
            {visibleChapters.map((c) => {
              const { pointer, title } = parseChapter(c.chapter);
              return (
                <li key={c.chapter}>
                  <button
                    type="button"
                    onClick={() => onSwitchChapter(c.chapter)}
                    className="w-full rounded-md px-2 py-1.5 text-left transition-colors hover:bg-white/5"
                    title={`Last done ${c.last_date}`}
                  >
                    <div
                      className="truncate text-[12px] font-medium"
                      style={{ color: "#cdeefd" }}
                    >
                      {pointer}
                    </div>
                    {title ? (
                      <div
                        className="truncate text-[10px]"
                        style={{ color: "#9aa0a6" }}
                      >
                        {title}
                      </div>
                    ) : null}
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      )}

      <div className="mt-4 border-t pt-4" style={{ borderColor: "rgba(255,255,255,0.08)" }}>
        <div className="font-mono text-[10px] uppercase tracking-[0.3em]" style={{ color: "#9aa0a6" }}>
          Session
        </div>
        {chapterPointer ? (
          <>
            <div className="mt-1 truncate text-sm" style={{ color: "#cdeefd" }}>
              {chapterPointer}
            </div>
            <div
              className="truncate text-[11px]"
              style={{ color: "#9aa0a6" }}
              title={conceptLabel}
            >
              {conceptLabel}
            </div>
          </>
        ) : (
          <div className="mt-1 text-sm italic" style={{ color: "rgba(255,255,255,0.35)" }}>
            Loading…
          </div>
        )}
      </div>
    </aside>
  );
}
