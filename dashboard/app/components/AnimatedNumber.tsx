"use client";

import { useEffect, useRef, useState } from "react";

/** Counts up from 0 to `value` on mount, then renders `formatted` verbatim. */
export default function AnimatedNumber({
  value,
  decimals = 0,
  suffix = "",
  prefix = "",
  durationMs = 700,
}: {
  value: number;
  decimals?: number;
  suffix?: string;
  prefix?: string;
  durationMs?: number;
}) {
  const [display, setDisplay] = useState(0);
  const startRef = useRef<number | null>(null);

  useEffect(() => {
    let raf: number;
    const step = (t: number) => {
      if (startRef.current === null) startRef.current = t;
      const elapsed = t - startRef.current;
      const progress = Math.min(1, elapsed / durationMs);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(value * eased);
      if (progress < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  // Number#toFixed follows the underlying binary float (2.155 can become
  // 2.15). Round to the requested decimal precision first so financial
  // metrics use deterministic half-up presentation.
  const factor = 10 ** decimals;
  const roundedDisplay = Math.round((display + Math.sign(display) * Number.EPSILON) * factor) / factor;

  return (
    <>
      {prefix}
      {roundedDisplay.toFixed(decimals)}
      {suffix}
    </>
  );
}
