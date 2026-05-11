"use client";

import { useEffect, useRef } from "react";

/**
 * Fixed-position cyan/violet radial gradient that smoothly trails the cursor.
 * Sits behind glass panels (z-index 0); content above gets the diffused glow
 * through their backdrop-filter.
 */
export function MouseFollowerGlow() {
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    let rafId = 0;
    let targetX = window.innerWidth / 2;
    let targetY = window.innerHeight / 2;
    let x = targetX;
    let y = targetY;

    const onMove = (e: MouseEvent) => {
      targetX = e.clientX;
      targetY = e.clientY;
    };

    const tick = () => {
      x += (targetX - x) * 0.10;
      y += (targetY - y) * 0.10;
      el.style.transform = `translate(${x}px, ${y}px) translate(-50%, -50%)`;
      rafId = requestAnimationFrame(tick);
    };

    window.addEventListener("mousemove", onMove);
    rafId = requestAnimationFrame(tick);

    return () => {
      window.removeEventListener("mousemove", onMove);
      cancelAnimationFrame(rafId);
    };
  }, []);

  return (
    <div
      ref={ref}
      aria-hidden
      className="pointer-events-none fixed left-0 top-0 z-0 h-[600px] w-[600px] rounded-full"
      style={{
        background:
          "radial-gradient(circle, rgba(0,245,255,0.22) 0%, rgba(112,0,255,0.15) 35%, rgba(0,0,0,0) 70%)",
        filter: "blur(40px)",
        willChange: "transform",
      }}
    />
  );
}
