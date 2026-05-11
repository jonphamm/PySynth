type ProgressOrbitProps = {
  /** 0..1 progress fraction */
  value: number;
  size?: number;
  stroke?: number;
};

export function ProgressOrbit({
  value,
  size = 56,
  stroke = 3,
}: ProgressOrbitProps) {
  const clamped = Math.max(0, Math.min(1, value));
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - clamped);
  const pct = Math.round(clamped * 100);

  return (
    <div
      className="relative inline-flex items-center justify-center"
      style={{ width: size, height: size }}
      aria-label={`Progress: ${pct}%`}
      role="progressbar"
      aria-valuenow={pct}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <svg width={size} height={size} className="-rotate-90">
        {/* Track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="rgba(255,255,255,0.10)"
          strokeWidth={stroke}
          fill="none"
        />
        {/* Fill */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="url(#orbitGradient)"
          strokeWidth={stroke}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{
            transition: "stroke-dashoffset 600ms cubic-bezier(0.2,0.8,0.2,1)",
            filter: "drop-shadow(0 0 6px rgba(0,245,255,0.6))",
          }}
        />
        <defs>
          <linearGradient id="orbitGradient" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#00f5ff" />
            <stop offset="100%" stopColor="#7000ff" />
          </linearGradient>
        </defs>
      </svg>
      <span
        className="absolute font-mono text-[10px] font-semibold tracking-wider"
        style={{ color: "#cdeefd" }}
      >
        {pct}
      </span>
    </div>
  );
}
