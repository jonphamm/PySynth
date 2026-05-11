import type { HTMLAttributes, ReactNode } from "react";

type Variant = "default" | "strong";

type GlassPanelProps = HTMLAttributes<HTMLDivElement> & {
  variant?: Variant;
  children?: ReactNode;
};

export function GlassPanel({
  variant = "default",
  className = "",
  children,
  ...rest
}: GlassPanelProps) {
  const base = variant === "strong" ? "glass-strong" : "glass";
  return (
    <div className={`${base} ${className}`} {...rest}>
      {children}
    </div>
  );
}
