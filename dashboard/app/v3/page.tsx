import CollapsibleSection from "../components/CollapsibleSection";
import CircuitBreakerPanel from "../components/CircuitBreakerPanel";
import DistributionHistogram from "../components/DistributionHistogram";
import DrawdownChart from "../components/DrawdownChart";
import EdgeBadge from "../components/EdgeBadge";
import EquityChart from "../components/EquityChart";
import ExperimentalBanner from "../components/ExperimentalBanner";
import LongShortSplit from "../components/LongShortSplit";
import PerPairPanel from "../components/PerPairPanel";
import PositionManagementPanel from "../components/PositionManagementPanel";
import StatCard from "../components/StatCard";
import StreakBadge from "../components/StreakBadge";
import WinrateTrendChart from "../components/WinrateTrendChart";
import { getV3Summary } from "../lib/getSummary";

export const dynamic = "force-dynamic";

export default function V3Page() {
  const summary = getV3Summary();

  return (
    <main className="mx-auto max-w-[1400px] px-3 py-3 lg:px-5 lg:py-3" id="dashboard-capture">
      <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-lg font-bold lg:text-xl">FredbV3 — Experimental</h1>
            {summary && (
              <EdgeBadge profitFactor={summary.profit_factor} winratePct={summary.winrate_pct} />
            )}
          </div>
          <p className="mt-0.5 text-[11px] text-muted">
            {summary
              ? `${summary.strategy} · ${summary.exchange ?? "unknown exchange"} · ${summary.trading_mode ?? ""} · ${summary.timeframe}/${summary.informative_timeframe} · ${summary.timerange}`
              : "No FredbV3 backtest results published yet"}
          </p>
        </div>
        <a href="/" className="text-[11px] text-muted underline hover:text-zinc-300">
          ← back to production dashboard (V2)
        </a>
      </div>

      {!summary && (
        <div className="rounded-lg border border-dashed border-border bg-card p-8 text-center text-[13px] text-muted">
          No FredbV3 backtest results published yet. Run{" "}
          <code>freqtrade backtesting -c user_data/config-v3.json --strategy FredbV3Strategy</code>{" "}
          then <code>python3 scripts/export_summary_v3.py</code>, and copy
          <code> bot/user_data/backtest_results/latest_v3.json</code> to{" "}
          <code>dashboard/public/backtest-v3.json</code>.
        </div>
      )}

      {summary && (
        <div className="space-y-2.5">
          <ExperimentalBanner status={summary.prod_lock_status} />

          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-7">
            <StatCard
              label="Total %"
              value={summary.total_profit_pct}
              decimals={2}
              suffix="%"
              prefix={summary.total_profit_pct >= 0 ? "+" : ""}
              accent={summary.total_profit_pct >= 0 ? "profit" : "loss"}
            />
            <StatCard
              label="Profit Factor"
              value={summary.profit_factor ?? 0}
              decimals={2}
              accent={summary.profit_factor !== null && summary.profit_factor >= 1.5 ? "profit" : "loss"}
            />
            <StatCard label="Winrate" value={summary.winrate_pct} decimals={1} suffix="%" />
            <StatCard label="Max Drawdown" value={summary.max_drawdown_pct} decimals={2} suffix="%" accent="loss" />
            <StatCard label="Trades" value={summary.total_trades} sub={`${summary.trades_per_day}/day`} />
            <StatCard label="Sharpe" value={summary.sharpe} decimals={2} />
            <div className="rounded-lg border border-border bg-card p-2.5">
              <div className="mb-1 truncate text-[10.5px] text-muted">Current Streak</div>
              <StreakBadge streak={summary.current_streak} />
            </div>
          </div>

          <CollapsibleSection id="section-direction" title="Long vs Short (the direction V2 didn't have)">
            <LongShortSplit split={summary.direction_split} />
          </CollapsibleSection>

          <CollapsibleSection id="section-position-mgmt" title="Staggered entry/exit ('hedge when odds shift' surrogate)">
            <PositionManagementPanel data={summary.position_management} />
          </CollapsibleSection>

          <CollapsibleSection id="section-circuit-breakers" title="Circuit breakers">
            <CircuitBreakerPanel data={summary.circuit_breakers} />
          </CollapsibleSection>

          <CollapsibleSection id="section-performance" title="Equity & Drawdown">
            <div className="grid grid-cols-1 gap-3 lg:grid-cols-3">
              <div className="rounded-lg border border-border bg-card p-2.5 lg:col-span-2">
                <EquityChart data={summary.equity_curve} />
              </div>
              <div className="rounded-lg border border-border bg-card p-2.5">
                <div className="mb-1 text-[10.5px] text-muted">Drawdown</div>
                <DrawdownChart data={summary.equity_curve} />
              </div>
            </div>
          </CollapsibleSection>

          <CollapsibleSection id="section-winrate-story" title="Winrate Story">
            <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
              <div className="rounded-lg border border-border bg-card p-2.5">
                <div className="mb-1 text-[10.5px] text-muted">
                  Rolling winrate (last {summary.winrate_trend.length} trades)
                </div>
                <WinrateTrendChart data={summary.winrate_trend} />
              </div>
              <div className="rounded-lg border border-border bg-card p-2.5">
                <div className="mb-1 text-[10.5px] text-muted">Trade size distribution (profit %)</div>
                <DistributionHistogram data={summary.win_loss_sizes} />
              </div>
            </div>
          </CollapsibleSection>

          <CollapsibleSection id="section-pairs" title="Per-pair results">
            <div className="rounded-lg border border-border bg-card p-2.5">
              <PerPairPanel pairs={summary.pairs} />
            </div>
          </CollapsibleSection>

          <CollapsibleSection id="section-exit-reasons" title="Exit reason breakdown">
            <div className="rounded-lg border border-border bg-card p-3 text-[12px] text-zinc-300">
              {Object.entries(summary.exit_reason_breakdown).map(([reason, count]) => (
                <div key={reason} className="flex justify-between border-b border-border/50 py-1 last:border-0">
                  <span>{reason}</span>
                  <span className="text-zinc-400">{count}</span>
                </div>
              ))}
            </div>
          </CollapsibleSection>
        </div>
      )}
    </main>
  );
}
