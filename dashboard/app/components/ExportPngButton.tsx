"use client";

import { useState } from "react";

export default function ExportPngButton({ targetId }: { targetId: string }) {
  const [busy, setBusy] = useState(false);

  async function exportPng() {
    const el = document.getElementById(targetId);
    if (!el) return;
    setBusy(true);
    try {
      const { default: html2canvas } = await import("html2canvas");
      const canvas = await html2canvas(el, {
        backgroundColor: "#0A0A0B",
        scale: 2,
      });
      const link = document.createElement("a");
      link.download = `fred-bot-dashboard-${new Date().toISOString().slice(0, 10)}.png`;
      link.href = canvas.toDataURL("image/png");
      link.click();
    } catch (err) {
      console.error("PNG export failed", err);
    } finally {
      setBusy(false);
    }
  }

  return (
    <button
      onClick={exportPng}
      disabled={busy}
      className="rounded-md border border-border bg-card px-2.5 py-1 text-[11px] font-medium text-zinc-300 hover:bg-white/5 disabled:opacity-50"
    >
      {busy ? "Exporting…" : "Export PNG"}
    </button>
  );
}
