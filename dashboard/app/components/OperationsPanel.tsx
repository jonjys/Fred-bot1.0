import type { BacktestSummary, LiveStatus } from "../lib/types";

function metric(value: number | null, suffix = "") {
  return value === null ? "—" : `${value.toFixed(2)}${suffix}`;
}

export default function OperationsPanel({ live, backtest }: { live: LiveStatus; backtest: BacktestSummary }) {
  const pfDivergence = live.profit_factor === null || backtest.profit_factor === null
    ? null
    : ((live.profit_factor - backtest.profit_factor) / backtest.profit_factor) * 100;
  const divergenceWarning = live.connected && (
    (live.profit_factor !== null && live.profit_factor < 1.3) ||
    (pfDivergence !== null && pfDivergence < -25) ||
    (live.max_drawdown_pct !== null && live.max_drawdown_pct > Math.max(backtest.max_drawdown_pct * 2, 5))
  );

  return (
    <section className="overflow-hidden rounded-lg border border-border bg-card">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border px-3 py-2">
        <div>
          <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">Production Operations</div>
          <div className="mt-0.5 text-sm font-semibold">PROD LOCK v1 · FredbV2ProdStrategy</div>
        </div>
        <div className={`rounded-full border px-2.5 py-1 text-[10px] font-bold ${
          live.connected ? "border-profit/40 bg-profit/10 text-profit" : "border-warn/40 bg-warn/10 text-warn"
        }`}>
          {live.connected ? `${live.mode.toUpperCase()} TELEMETRY` : "LIVE FEED NOT CONNECTED"}
        </div>
      </div>
      <div className="grid grid-cols-2 divide-x divide-y divide-border sm:grid-cols-4 lg:grid-cols-8">
        {[
          ["Live equity", metric(live.equity, " USDT")],
          ["Live P&L", metric(live.pnl_pct, "%")],
          ["Live PF", metric(live.profit_factor)],
          ["Live winrate", metric(live.winrate_pct, "%")],
          ["Live max DD", metric(live.max_drawdown_pct, "%")],
          ["Live Sharpe", metric(live.sharpe)],
          ["Open trades", String(live.open_trades)],
          ["Alert route", live.alerting.toUpperCase()],
        ].map(([label, value]) => (
          <div className="p-2.5" key={label}>
            <div className="text-[9px] uppercase tracking-wider text-zinc-600">{label}</div>
            <div className="mt-1 text-sm font-semibold text-zinc-200">{value}</div>
          </div>
        ))}
      </div>
      <div className={`flex items-center justify-between gap-3 border-t px-3 py-2 text-[11px] ${
        divergenceWarning || live.circuit_breaker ? "border-loss/40 bg-loss/10 text-loss" : "border-border text-muted"
      }`}>
        <span>
          {!live.connected
            ? "Backtest is validated; connect the bot telemetry publisher before live capital is enabled."
            : divergenceWarning
              ? "LIVE/BACKTEST DIVERGENCE — entries must remain circuit-blocked pending review."
              : `Live PF divergence: ${pfDivergence === null ? "—" : `${pfDivergence.toFixed(1)}%`}`}
        </span>
        <span className="whitespace-nowrap">PF floor 1.30 · OOS gate 1.50</span>
      </div>
    </section>
  );
}
