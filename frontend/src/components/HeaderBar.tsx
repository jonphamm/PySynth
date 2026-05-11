type HeaderBarProps = {
  chapter: string;
  concept: string;
  xp?: number;
  onMenuClick?: () => void;
};

export function HeaderBar({ chapter, concept, xp = 0, onMenuClick }: HeaderBarProps) {
  return (
    <header className="glass flex h-14 items-center justify-between gap-2 px-3 sm:px-5">
      <div className="flex min-w-0 items-center gap-3">
        {onMenuClick && (
          <button
            type="button"
            onClick={onMenuClick}
            className="-ml-1 inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-md transition-colors hover:bg-white/5 md:hidden"
            aria-label="Open navigation"
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 18 18"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.75"
              strokeLinecap="round"
              style={{ color: "#cdeefd" }}
            >
              <line x1="3" y1="5" x2="15" y2="5" />
              <line x1="3" y1="9" x2="15" y2="9" />
              <line x1="3" y1="13" x2="15" y2="13" />
            </svg>
          </button>
        )}
        <span
          className="hidden font-mono text-[10px] uppercase tracking-[0.4em] sm:inline"
          style={{ color: "#00f5ff" }}
        >
          Lesson
        </span>
        <span
          aria-hidden
          className="hidden h-3 w-px sm:inline-block"
          style={{ background: "rgba(255,255,255,0.18)" }}
        />
        <div className="min-w-0 flex-1 truncate">
          <span className="text-sm font-semibold">{chapter}</span>
          <span className="mx-2 hidden sm:inline" style={{ color: "rgba(255,255,255,0.25)" }}>
            ·
          </span>
          <span className="hidden text-sm sm:inline" style={{ color: "rgba(255,255,255,0.65)" }}>
            {concept}
          </span>
        </div>
      </div>

      <div className="hidden shrink-0 items-center gap-2 sm:flex">
        <span
          className="font-mono text-[10px] uppercase tracking-[0.3em]"
          style={{ color: "#9aa0a6" }}
        >
          XP
        </span>
        <span
          className="font-mono text-base font-semibold tabular-nums"
          style={{
            color: "#cdeefd",
            textShadow: "0 0 14px rgba(0,245,255,0.45)",
          }}
        >
          {xp.toString().padStart(4, "0")}
        </span>
      </div>
    </header>
  );
}
