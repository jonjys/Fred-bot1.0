"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function RunBacktestButton() {
  const [status, setStatus] = useState<"idle" | "running" | "error">("idle");
  const router = useRouter();

  async function run() {
    setStatus("running");
    try {
      const res = await fetch("/api/refresh", { method: "POST" });
      if (!res.ok) throw new Error(await res.text());
      setStatus("idle");
      router.refresh();
    } catch (err) {
      console.error(err);
      setStatus("error");
    }
  }

  return (
    <button
      onClick={run}
      disabled={status === "running"}
      style={{
        background: status === "running" ? "#222226" : "#4f9dff",
        color: status === "running" ? "#9aa4b2" : "#0A0A0B",
        border: "none",
        borderRadius: 7,
        padding: "6px 12px",
        fontSize: 12,
        fontWeight: 600,
        cursor: status === "running" ? "default" : "pointer",
      }}
    >
      {status === "running"
        ? "Running backtest…"
        : status === "error"
          ? "Failed — retry"
          : "Run Backtest"}
    </button>
  );
}
