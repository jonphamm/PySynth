import { AIOrb } from "./ui/AIOrb";

export function MentorPanel() {
  return (
    <aside className="glass hidden h-full min-h-0 w-[340px] flex-col overflow-hidden p-5 lg:flex">
      <div className="mb-5 flex items-center gap-3">
        <AIOrb state="idle" size={42} />
        <div>
          <div
            className="font-mono text-[10px] uppercase tracking-[0.4em]"
            style={{ color: "#00f5ff" }}
          >
            Mentor
          </div>
          <div className="mt-0.5 text-sm font-semibold">PySynth Tutor</div>
        </div>
      </div>

      <div
        className="mb-5 rounded-xl p-3 text-xs leading-relaxed"
        style={{
          background: "rgba(0,245,255,0.06)",
          border: "1px solid rgba(0,245,255,0.18)",
          color: "rgba(255,255,255,0.85)",
        }}
      >
        Walk through the concept, then I&apos;ll quiz you. Submit code and
        I&apos;ll review it for correctness and idiomatic Python — one improvement
        at a time.
      </div>

      <div className="mb-3">
        <div
          className="font-mono text-[10px] uppercase tracking-[0.3em]"
          style={{ color: "#9aa0a6" }}
        >
          Output
        </div>
      </div>

      <div
        className="scanlines flex-1 rounded-lg p-3 font-mono text-[12px]"
        style={{
          background: "rgba(2,2,3,0.65)",
          border: "1px solid rgba(255,255,255,0.06)",
          color: "rgba(205,238,253,0.85)",
        }}
      >
        <p style={{ color: "#00f5ff" }}>
          <span style={{ color: "#7000ff" }}>$</span> pysynth.ready()
        </p>
        <p>{"// Console output will stream here."}</p>
        <p>{"// Submit your solution to begin."}</p>
        <p className="mt-2" style={{ color: "rgba(255,255,255,0.35)" }}>
          ▍
        </p>
      </div>
    </aside>
  );
}
