"use client";

import { useState } from "react";

export default function FallbackBanner({ exchange }: { exchange: string }) {
  const [open, setOpen] = useState(true);

  return (
    <div
      style={{
        background: "#1f160a",
        border: "1px solid #3d2c14",
        borderRadius: 10,
        marginBottom: 16,
        color: "#e8c07d",
        fontSize: 12,
        overflow: "hidden",
      }}
    >
      <button
        onClick={() => setOpen((v) => !v)}
        style={{
          width: "100%",
          background: "none",
          border: "none",
          color: "inherit",
          font: "inherit",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 8,
          padding: "8px 12px",
          cursor: "pointer",
          textAlign: "left",
        }}
        aria-expanded={open}
      >
        <span>
          ⚠ Data from <strong>{exchange}</strong>, not Binance
        </span>
        <span style={{ opacity: 0.7, fontSize: 11 }}>{open ? "hide" : "why?"}</span>
      </button>
      {open && (
        <p style={{ margin: 0, padding: "0 12px 10px", lineHeight: 1.4 }}>
          The <code>backtest.yml</code> workflow falls back to OKX when Binance
          blocks the CI runner&apos;s IP (HTTP 451) — see the README. Re-run
          the workflow, or run it somewhere Binance is reachable, for
          Binance-specific numbers.
        </p>
      )}
    </div>
  );
}
