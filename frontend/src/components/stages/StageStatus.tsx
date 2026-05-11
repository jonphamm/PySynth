"use client";

import type { Status } from "@/types/session";

type Props = {
  label: string;
  status: Status;
  loadingMessage: string;
  onRetry?: () => void;
};

export function StageStatus({ label, status, loadingMessage, onRetry }: Props) {
  const isError = status.kind === "error";

  return (
    <div className="flex h-full min-h-0 flex-col">
      <header className="border-b px-4 py-4 sm:px-7 sm:py-5" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
        <div
          className="font-mono text-[10px] uppercase tracking-[0.4em]"
          style={{ color: "#00f5ff" }}
        >
          {label}
        </div>
        <h2 className="mt-1 text-2xl font-semibold tracking-tight">
          {isError ? "Something went wrong" : "Generating…"}
        </h2>
      </header>

      <div className="flex flex-1 min-h-0 flex-col items-center justify-center px-10 py-10 text-center">
        {isError ? (
          <>
            <p
              className="max-w-md text-sm leading-relaxed"
              style={{ color: "rgba(255,200,200,0.85)" }}
            >
              {status.message}
            </p>
            {onRetry && (
              <button
                type="button"
                onClick={onRetry}
                className="mt-6 rounded-lg px-5 py-2 text-sm font-semibold transition-all hover:scale-[1.02] active:scale-[0.98]"
                style={{
                  background: "linear-gradient(135deg, #00f5ff 0%, #7000ff 100%)",
                  color: "#020203",
                  boxShadow: "0 3px 12px rgba(0,245,255,0.25)",
                }}
              >
                Retry
              </button>
            )}
          </>
        ) : (
          <>
            <Spinner />
            <p
              className="mt-5 text-sm"
              style={{ color: "rgba(255,255,255,0.55)" }}
            >
              {status.kind === "loading" ? status.what : loadingMessage}
            </p>
          </>
        )}
      </div>
    </div>
  );
}

function Spinner() {
  return (
    <div
      className="h-10 w-10 animate-spin rounded-full"
      style={{
        border: "3px solid rgba(0,245,255,0.15)",
        borderTopColor: "#00f5ff",
        borderRightColor: "#7000ff",
      }}
    />
  );
}
