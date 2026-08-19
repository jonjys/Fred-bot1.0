"use client";

import { useState } from "react";

export default function FallbackBanner({ exchange }: { exchange: string }) {
  const [open, setOpen] = useState(true);

  return (
    <div className="mb-3 overflow-hidden rounded-lg border border-warn/30 bg-warn/10 text-[12px] text-warn">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between gap-2 px-3 py-2 text-left"
        aria-expanded={open}
      >
        <span>
          ⚠ Data from <strong>{exchange}</strong>, not Binance
        </span>
        <span className="text-[11px] opacity-70">{open ? "hide" : "why?"}</span>
      </button>
      {open && (
        <p className="m-0 px-3 pb-2.5 leading-snug">
          The <code>backtest.yml</code> workflow falls back to OKX when Binance
          blocks the CI runner&apos;s IP (HTTP 451) — see the README. Re-run
          the workflow, or run it somewhere Binance is reachable, for
          Binance-specific numbers.
        </p>
      )}
    </div>
  );
}
