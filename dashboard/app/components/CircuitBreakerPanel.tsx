import type { CircuitBreakerInfo } from "../lib/types";

function describe(protection: CircuitBreakerInfo["protections"][number]): string {
  switch (protection.method) {
    case "CooldownPeriod":
      return `Cooldown ${protection.stop_duration_candles} candles after any close`;
    case "StoplossGuard":
      return `${protection.trade_limit} stoplosses in ${protection.lookback_period_candles} candles halts that pair for ${protection.stop_duration_candles} candles`;
    case "MaxDrawdown":
      return `${Math.round(Number(protection.max_allowed_drawdown) * 100)}% drawdown over ${protection.lookback_period_candles} candles halts all new entries for ${protection.stop_duration_candles} candles`;
    default:
      return protection.method;
  }
}

export default function CircuitBreakerPanel({ data }: { data: CircuitBreakerInfo }) {
  const ratio = Math.min(data.current_max_drawdown_pct / data.max_allowed_drawdown_pct, 1);
  const armed = ratio >= 0.75;

  return (
    <div className="space-y-2.5">
      <div className="rounded-lg border border-border bg-card p-2.5">
        <div className="mb-1 flex items-center justify-between text-[10.5px] text-muted">
          <span>Max drawdown vs. circuit breaker</span>
          <span className={armed ? "text-warn" : "text-zinc-400"}>
            {data.current_max_drawdown_pct}% / {data.max_allowed_drawdown_pct}%
          </span>
        </div>
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-border">
          <div
            className={`h-full rounded-full ${armed ? "bg-warn" : "bg-live"}`}
            style={{ width: `${ratio * 100}%` }}
          />
        </div>
      </div>
      <div className="rounded-lg border border-border bg-card p-2.5">
        <div className="mb-1.5 text-[10.5px] text-muted">Active protections</div>
        <ul className="space-y-1 text-[12px] text-zinc-300">
          {data.protections.map((p, i) => (
            <li key={i}>• {describe(p)}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
