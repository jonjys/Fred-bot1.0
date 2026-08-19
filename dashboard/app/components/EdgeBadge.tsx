const PF_THRESHOLD = 2.0;
const WR_THRESHOLD = 65;

/**
 * Only lights up when the strategy's actual committed numbers clear both
 * bars - never hardcoded on. With today's real numbers (PF ~2.1, WR ~52%)
 * this renders muted, and that's correct: it should not claim an edge the
 * data doesn't back up.
 */
export default function EdgeBadge({
  profitFactor,
  winratePct,
}: {
  profitFactor: number | null;
  winratePct: number;
}) {
  const hasEdge = profitFactor !== null && profitFactor >= PF_THRESHOLD && winratePct >= WR_THRESHOLD;

  if (hasEdge) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full border border-live/50 bg-live/10 px-2.5 py-1 text-[10px] font-bold tracking-wide text-live shadow-glow-live">
        <span className="h-1.5 w-1.5 rounded-full bg-live animate-pulse-glow" />
        EDGE CONFIRMED
      </span>
    );
  }

  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-2.5 py-1 text-[10px] font-semibold tracking-wide text-muted"
      title={`Needs PF ≥ ${PF_THRESHOLD} and winrate ≥ ${WR_THRESHOLD}% - currently PF ${profitFactor?.toFixed(2) ?? "—"}, WR ${winratePct}%`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-zinc-600" />
      NO EDGE YET
    </span>
  );
}
