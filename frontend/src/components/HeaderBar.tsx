type HeaderBarProps = {
  chapter: string;
  concept: string;
  xp?: number;
};

export function HeaderBar({ chapter, concept, xp = 0 }: HeaderBarProps) {
  return (
    <header className="glass flex h-14 items-center justify-between px-5">
      <div className="flex items-center gap-3 min-w-0">
        <span
          className="font-mono text-[10px] uppercase tracking-[0.4em]"
          style={{ color: "#00f5ff" }}
        >
          Lesson
        </span>
        <span
          aria-hidden
          className="h-3 w-px"
          style={{ background: "rgba(255,255,255,0.18)" }}
        />
        <div className="min-w-0 truncate">
          <span className="text-sm font-semibold">{chapter}</span>
          <span className="mx-2" style={{ color: "rgba(255,255,255,0.25)" }}>
            ·
          </span>
          <span className="text-sm" style={{ color: "rgba(255,255,255,0.65)" }}>
            {concept}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-2">
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
