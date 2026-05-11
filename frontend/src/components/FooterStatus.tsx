import type { Status } from "@/types/session";
import { AIOrb } from "./ui/AIOrb";

type FooterStatusProps = {
  status: Status;
};

export function FooterStatus({ status }: FooterStatusProps) {
  const { label, message, orbState } = describe(status);
  return (
    <footer className="glass flex h-11 items-center gap-3 px-4">
      <AIOrb state={orbState} size={26} />
      <span
        className="font-mono text-[10px] uppercase tracking-[0.4em]"
        style={{ color: orbState === "thinking" ? "#ffae42" : status.kind === "error" ? "#ff5f57" : "#00f5ff" }}
      >
        AI · {label}
      </span>
      <span
        aria-hidden
        className="h-3 w-px"
        style={{ background: "rgba(255,255,255,0.18)" }}
      />
      <p
        className="truncate text-xs"
        style={{ color: status.kind === "error" ? "rgba(255,200,200,0.85)" : "rgba(255,255,255,0.65)" }}
      >
        {message}
      </p>
    </footer>
  );
}

function describe(status: Status): {
  label: string;
  message: string;
  orbState: "idle" | "thinking" | "speaking";
} {
  if (status.kind === "loading") {
    return { label: "Thinking", message: status.what, orbState: "thinking" };
  }
  if (status.kind === "error") {
    return {
      label: "Error",
      message: status.message,
      orbState: "idle",
    };
  }
  return {
    label: "Idle",
    message: "AI Tutor standing by.",
    orbState: "idle",
  };
}
