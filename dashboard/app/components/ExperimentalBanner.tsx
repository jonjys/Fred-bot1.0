export default function ExperimentalBanner({ status }: { status: string }) {
  return (
    <div className="mb-3 rounded-lg border border-warn/30 bg-warn/10 px-3 py-2 text-[12px] text-warn">
      <strong>EXPERIMENTAL</strong> — {status}. This page reads its own data file
      (<code>backtest-v3.json</code>) and never overwrites the live V2 production
      dashboard. See <code>docs/PROD_PLAN_V3.md</code> for what promotion to prod
      would actually require.
    </div>
  );
}
