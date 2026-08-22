import type { DirectionSplit } from "../lib/types";
import StatCard from "./StatCard";

function Side({ label, stat }: { label: string; stat: DirectionSplit["long"] }) {
  return (
    <div className="rounded-lg border border-border bg-card p-2.5">
      <div className="mb-1.5 text-[10.5px] font-semibold uppercase tracking-wide text-muted">{label}</div>
      <div className="grid grid-cols-3 gap-2">
        <StatCard label="Trades" value={stat.trades} />
        <StatCard label="Winrate" value={stat.winrate_pct} decimals={1} suffix="%" />
        <StatCard
          label="PF"
          value={stat.profit_factor ?? 0}
          decimals={2}
          accent={stat.profit_factor !== null && stat.profit_factor >= 1.5 ? "profit" : "loss"}
        />
      </div>
    </div>
  );
}

export default function LongShortSplit({ split }: { split: DirectionSplit }) {
  return (
    <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
      <Side label="Long" stat={split.long} />
      <Side label="Short" stat={split.short} />
    </div>
  );
}
