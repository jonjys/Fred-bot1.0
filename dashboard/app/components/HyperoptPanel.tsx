import type { HyperoptInfo } from "../lib/types";

export default function HyperoptPanel({
  hyperopt,
  strategyVersion,
  profitFactor,
}: {
  hyperopt: HyperoptInfo | null;
  strategyVersion: string;
  profitFactor: number | null;
}) {
  const belowThreshold = profitFactor !== null && profitFactor < 1.5;

  if (!hyperopt) {
    return (
      <div className="rounded-lg border border-border bg-card p-3 text-xs text-muted">
        <span className="font-semibold text-zinc-300">{strategyVersion}</span> · running on
        hand-set defaults — no hyperopt.yml run has landed on this branch yet.
      </div>
    );
  }

  const paramEntries = Object.entries(hyperopt.params);

  return (
    <div className="rounded-lg border border-border bg-card p-3 text-xs">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <span className="font-semibold text-zinc-100">
          {strategyVersion} @ {hyperopt.epochs}e
        </span>
        <span className="rounded-full border border-border px-1.5 py-0.5 text-[10px] text-muted">
          {hyperopt.loss_function}
        </span>
        {belowThreshold && (
          <span className="rounded-full border border-warn/50 bg-warn/10 px-1.5 py-0.5 text-[10px] font-bold text-warn">
            ⚠ PF {profitFactor?.toFixed(2)} &lt; 1.5 target
          </span>
        )}
      </div>
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-muted">
        {paramEntries.map(([k, v]) => (
          <span key={k}>
            <span className="text-zinc-500">{k}:</span>{" "}
            <span className="text-zinc-300">{typeof v === "number" ? v : String(v)}</span>
          </span>
        ))}
        {hyperopt.stoploss !== null && (
          <span>
            <span className="text-zinc-500">stoploss:</span>{" "}
            <span className="text-zinc-300">{(hyperopt.stoploss * 100).toFixed(1)}%</span>
          </span>
        )}
      </div>
    </div>
  );
}
