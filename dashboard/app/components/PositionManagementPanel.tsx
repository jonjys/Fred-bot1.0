import type { PositionManagement } from "../lib/types";

function Row({
  label,
  used,
  usedPct,
  usedAvg,
  unusedAvg,
}: {
  label: string;
  used: number;
  usedPct: number;
  usedAvg: number;
  unusedAvg: number;
}) {
  const helped = usedAvg > unusedAvg;
  return (
    <div className="rounded-lg border border-border bg-card p-2.5">
      <div className="mb-1 flex items-center justify-between">
        <span className="text-[10.5px] text-muted">{label}</span>
        <span className="text-[11px] text-zinc-400">
          {used} trades ({usedPct}%)
        </span>
      </div>
      <div className="flex items-center gap-3 text-[12px]">
        <span className={helped ? "text-profit" : "text-loss"}>
          used: {usedAvg >= 0 ? "+" : ""}
          {usedAvg}%
        </span>
        <span className="text-zinc-500">vs. not used: {unusedAvg >= 0 ? "+" : ""}{unusedAvg}%</span>
      </div>
    </div>
  );
}

export default function PositionManagementPanel({ data }: { data: PositionManagement }) {
  return (
    <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
      <Row
        label="Staggered entry (bounded DCA re-entry)"
        used={data.dca_trades}
        usedPct={data.dca_trades_pct}
        usedAvg={data.dca_avg_profit_pct}
        unusedAvg={data.no_dca_avg_profit_pct}
      />
      <Row
        label="Staggered exit (partial take-profit)"
        used={data.partial_tp_trades}
        usedPct={data.partial_tp_trades_pct}
        usedAvg={data.partial_tp_avg_profit_pct}
        unusedAvg={data.no_partial_tp_avg_profit_pct}
      />
    </div>
  );
}
