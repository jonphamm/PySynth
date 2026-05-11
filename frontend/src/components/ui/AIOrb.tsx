type AIOrbProps = {
  state?: "idle" | "thinking" | "speaking";
  size?: number;
};

export function AIOrb({ state = "idle", size = 36 }: AIOrbProps) {
  const intensity =
    state === "thinking" ? 0.85 : state === "speaking" ? 1 : 0.55;

  return (
    <div
      className="relative inline-flex items-center justify-center"
      style={{ width: size, height: size }}
      aria-label={`AI tutor: ${state}`}
      role="img"
    >
      {/* Outer halo */}
      <div
        className="absolute inset-0 rounded-full"
        style={{
          background: `radial-gradient(circle, rgba(0,245,255,${intensity * 0.4}) 0%, rgba(0,245,255,0) 70%)`,
          filter: "blur(2px)",
        }}
      />
      {/* Core */}
      <div
        className="absolute rounded-full animate-[orbPulse_2.6s_ease-in-out_infinite]"
        style={{
          width: size * 0.55,
          height: size * 0.55,
          background:
            "radial-gradient(circle at 35% 30%, #ffffff 0%, #00f5ff 35%, #7000ff 100%)",
          boxShadow: `0 0 ${size * 0.7}px rgba(0,245,255,${intensity})`,
        }}
      />
      {/* Inner highlight */}
      <div
        className="absolute rounded-full"
        style={{
          width: size * 0.18,
          height: size * 0.18,
          top: size * 0.22,
          left: size * 0.28,
          background: "rgba(255,255,255,0.85)",
          filter: "blur(1px)",
        }}
      />
    </div>
  );
}
