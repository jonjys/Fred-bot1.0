"use client";

import { useEffect, useState } from "react";
import type { BacktestSummary, LiveStatus } from "../lib/types";

const fmt = (value: number | null, suffix = "") => value === null ? "—" : `${value.toFixed(2)}${suffix}`;

export default function OperationsPanel({ initialLive, backtest }: { initialLive: LiveStatus; backtest: BacktestSummary }) {
  const [live, setLive] = useState(initialLive);
  useEffect(() => {
    let active = true;
    const refresh = async () => {
      try {
        const response = await fetch("/api/live", { cache: "no-store" });
        if (active && response.ok) setLive(await response.json());
      } catch { /* disconnected is explicit in the UI */ }
    };
    refresh();
    const timer = window.setInterval(refresh, 5000);
    return () => { active = false; window.clearInterval(timer); };
  }, []);

  const pfDelta = live.profit_factor === null || backtest.profit_factor === null
    ? null : ((live.profit_factor - backtest.profit_factor) / backtest.profit_factor) * 100;
  const enoughTrades = live.trades.filter((trade) => trade.status === "closed").length > 10;
  const divergence = live.connected && enoughTrades && pfDelta !== null && Math.abs(pfDelta) > 30;
  const alertsOk = live.alerting !== "none";
  const rows = live.trades.slice(0, 20);
  const strip = [
    ["MODE", live.mode === "offline" ? "BACKTEST" : live.mode.replace("_", "-").toUpperCase(), "text-zinc-100"],
    ["TELEMETRY", live.connected ? "CONNECTED" : "DISCONNECTED", live.connected ? "text-profit" : "text-warn"],
    ["ALERTS", alertsOk ? "OK" : "MISCONFIGURED", alertsOk ? "text-profit" : "text-loss"],
    ["DIVERGENCE", divergence ? "WARNING" : "OK", divergence ? "text-loss" : "text-profit"],
  ];
  const cards = [
    ["Live P&L", fmt(live.pnl_pct, "%")], ["Live PF", fmt(live.profit_factor)],
    ["Winrate", fmt(live.winrate_pct, "%")], ["Max DD", fmt(live.max_drawdown_pct, "%")],
    ["Sharpe", fmt(live.sharpe)], ["Avg duration", fmt(live.avg_trade_duration_minutes, "m")],
    ["Open trades", live.connected ? String(live.open_trades) : "—"],
  ];

  return <section className="overflow-hidden rounded-lg border border-border bg-card">
    {(divergence || live.circuit_breaker) && <div className="border-b border-loss/50 bg-loss/15 px-3 py-2 text-xs font-bold text-loss">🚨 LIVE/BACKTEST DIVERGENCE — PF differs by over 30% after 10 trades. Entries halted.</div>}
    <div className="grid grid-cols-2 border-b border-border sm:grid-cols-4">
      {strip.map(([label,value,color]) => <div className="border-r border-border px-3 py-2" key={label}><span className="text-[9px] font-bold tracking-[0.18em] text-zinc-600">{label}: </span><span className={`text-[11px] font-black ${color}`}>{value}</span></div>)}
    </div>
    <div className="flex items-center justify-between border-b border-border px-3 py-2"><div><div className="text-[9px] font-bold uppercase tracking-[0.2em] text-zinc-500">Production Operations</div><div className="text-sm font-semibold">PROD LOCK v1 · PF 2.156</div></div><span className="text-[10px] text-zinc-600">5s telemetry poll</span></div>
    <div className="grid grid-cols-2 divide-x divide-y divide-border sm:grid-cols-4 lg:grid-cols-7">{cards.map(([label,value]) => <div className="p-2.5" key={label}><div className="text-[9px] uppercase tracking-wider text-zinc-600">{label}</div><div className="mt-1 text-sm font-semibold">{value}</div></div>)}</div>
    <div className="border-t border-border"><div className="px-3 py-2 text-[10px] font-bold uppercase tracking-[0.16em] text-zinc-500">Live trade history</div>
      {rows.length === 0 ? <div className="px-3 pb-3 text-xs text-muted">No live trades received. Backtest trades are never presented as live.</div> : <div className="max-h-56 overflow-auto"><table className="w-full text-left text-[11px]"><thead className="sticky top-0 bg-card text-zinc-500"><tr>{["Pair","Side","Opened","Status","P&L","Exit"].map(h=><th className="px-3 py-1.5" key={h}>{h}</th>)}</tr></thead><tbody>{rows.map(t=><tr className="border-t border-border/70" key={t.id}><td className="px-3 py-1.5 font-medium">{t.pair}</td><td className="px-3 py-1.5">{t.side}</td><td className="px-3 py-1.5">{new Date(t.opened_at).toLocaleString()}</td><td className="px-3 py-1.5">{t.status}</td><td className={`px-3 py-1.5 ${(t.profit_pct ?? 0) >= 0 ? "text-profit" : "text-loss"}`}>{fmt(t.profit_pct,"%")}</td><td className="px-3 py-1.5">{t.exit_reason ?? "—"}</td></tr>)}</tbody></table></div>}
    </div>
  </section>;
}
