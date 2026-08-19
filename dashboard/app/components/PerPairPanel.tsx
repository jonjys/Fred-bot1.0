import type { PairStat } from "../lib/types";
import PairSparkline from "./PairSparkline";

function heatColor(pct: number, maxAbs: number) {
  if (maxAbs === 0) return "transparent";
  const intensity = Math.min(1, Math.abs(pct) / maxAbs);
  const alpha = 0.08 + intensity * 0.28;
  return pct >= 0 ? `rgba(61, 255, 138, ${alpha})` : `rgba(255, 92, 92, ${alpha})`;
}

export default function PerPairPanel({ pairs }: { pairs: PairStat[] }) {
  const maxAbs = Math.max(1e-9, ...pairs.map((p) => Math.abs(p.avg_profit_pct)));

  return (
    <div className="overflow-x-auto scrollbar-thin">
      <table className="w-full min-w-[480px] border-collapse text-[12.5px]">
        <thead>
          <tr className="border-b border-border text-left text-muted">
            <th className="py-1.5 pr-3 font-medium">Pair</th>
            <th className="py-1.5 pr-3 font-medium">Trades</th>
            <th className="py-1.5 pr-3 font-medium">Avg %</th>
            <th className="py-1.5 pr-3 font-medium">Total USDT</th>
            <th className="py-1.5 pr-3 font-medium">Win%</th>
            <th className="py-1.5 pr-3 font-medium">Trend</th>
          </tr>
        </thead>
        <tbody>
          {pairs.map((p) => (
            <tr key={p.pair} className="border-b border-border/60">
              <td className="whitespace-nowrap py-1.5 pr-3 font-medium">{p.pair}</td>
              <td className="py-1.5 pr-3 text-zinc-300">{p.trades}</td>
              <td className="py-1.5 pr-3">
                <span
                  className="rounded px-1.5 py-0.5"
                  style={{ background: heatColor(p.avg_profit_pct, maxAbs) }}
                >
                  {p.avg_profit_pct >= 0 ? "+" : ""}
                  {p.avg_profit_pct}%
                </span>
              </td>
              <td className={`py-1.5 pr-3 ${p.total_profit_abs >= 0 ? "text-profit" : "text-loss"}`}>
                {p.total_profit_abs >= 0 ? "+" : ""}
                {p.total_profit_abs}
              </td>
              <td className="py-1.5 pr-3 text-zinc-300">{p.winrate_pct}%</td>
              <td className="py-1.5 pr-3">
                <PairSparkline values={p.sparkline} positive={p.total_profit_abs >= 0} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
