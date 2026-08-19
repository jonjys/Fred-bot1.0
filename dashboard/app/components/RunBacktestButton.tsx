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
      className={`rounded-md px-3 py-1.5 text-[12px] font-semibold ${
        status === "running"
          ? "cursor-default bg-[#222226] text-muted"
          : "bg-[#4f9dff] text-bg hover:bg-[#6babff]"
      }`}
    >
      {status === "running"
        ? "Running backtest…"
        : status === "error"
          ? "Failed — retry"
          : "Run Backtest"}
    </button>
  );
}
