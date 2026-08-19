import CollapsibleSection from "./components/CollapsibleSection";
import CommandPalette, { type PaletteItem } from "./components/CommandPalette";
import DistributionHistogram from "./components/DistributionHistogram";
import DrawdownChart from "./components/DrawdownChart";
import EdgeBadge from "./components/EdgeBadge";
import EquityChart from "./components/EquityChart";
import ExportPngButton from "./components/ExportPngButton";
import FallbackBanner from "./components/FallbackBanner";
import HyperoptPanel from "./components/HyperoptPanel";
import LiveBadge from "./components/LiveBadge";
import PerPairPanel from "./components/PerPairPanel";
import RunBacktestButton from "./components/RunBacktestButton";
import StatCard from "./components/StatCard";
import StreakBadge from "./components/StreakBadge";
import WinrateTrendChart from "./components/WinrateTrendChart";
import { getSummary } from "./lib/getSummary";

// Re-read backtest-latest.json on every request instead of baking it into
// the static build, so "Run Backtest" (and a fresh CI-published file) show
// up without a full redeploy.
export const dynamic = "force-dynamic";

export default function Home() {
  const summary = getSummary();

  const paletteItems: PaletteItem[] = summary
    ? [
        { label: "Total %", group: "metric", targetId: "stat-total-pct" },
        { label: "Profit Factor", group: "metric", targetId: "stat-pf" },
        { label: "Winrate", group: "metric", targetId: "stat-winrate" },
        { label: "Max Drawdown", group: "metric", targetId: "stat-maxdd" },
        { label: "Expectancy", group: "metric", targetId: "stat-expectancy" },
        { label: "Current Streak", group: "metric", targetId: "stat-streak" },
        { label: "Equity Curve", group: "section", targetId: "section-performance" },
        { label: "Winrate Story", group: "section", targetId: "section-winrate-story" },
        { label: "Per-pair results", group: "section", targetId: "section-pairs" },
        { label: "Open Trades", group: "section", targetId: "section-open-trades" },
        ...summary.pairs.map((p) => ({
          label: p.pair,
          group: "pair",
          targetId: "section-pairs",
        })),
      ]
    : [];

  return (
    <main className="mx-auto max-w-[1400px] px-3 py-3 lg:px-5 lg:py-3" id="dashboard-capture">
      {summary && <CommandPalette items={paletteItems} />}

      <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-lg font-bold lg:text-xl">Fred Bot Dashboard</h1>
            {summary && <LiveBadge />}
            {summary && (
              <EdgeBadge profitFactor={summary.profit_factor} winratePct={summary.winrate_pct} />
            )}
          </div>
          <p className="mt-0.5 text-[11px] text-muted">
            {summary
              ? `${summary.strategy} · ${summary.exchange ?? "unknown exchange"} · ${summary.timerange}`
              : "No backtest results yet"}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {summary && <ExportPngButton targetId="dashboard-capture" />}
          <div className="flex flex-col items-end gap-0.5">
            <RunBacktestButton />
            <span className="text-[9px] text-zinc-600">Local only · ⌘K to search</span>
          </div>
        </div>
      </div>

      {!summary && (
        <div className="rounded-lg border border-dashed border-border bg-card p-8 text-center text-[13px] text-muted">
          No backtest results published yet. Push to the repo to trigger the{" "}
          <code>backtest.yml</code> GitHub Action, or run{" "}
          <code>freqtrade backtesting</code> locally and click &quot;Run Backtest&quot;.
        </div>
      )}

      {summary && summary.exchange !== "binance" && (
        <FallbackBanner exchange={summary.exchange ?? "unknown"} />
      )}

      {summary && (
        <div className="space-y-2.5">
          <HyperoptPanel
            hyperopt={summary.hyperopt}
            strategyVersion={summary.strategy_version}
            profitFactor={summary.profit_factor}
          />

          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-7">
            <StatCard
              id="stat-total-pct"
              label="Total %"
              value={summary.total_profit_pct}
              decimals={2}
              suffix="%"
              prefix={summary.total_profit_pct >= 0 ? "+" : ""}
              accent={summary.total_profit_pct >= 0 ? "profit" : "loss"}
            />
            <StatCard
              id="stat-pf"
              label="Profit Factor"
              value={summary.profit_factor ?? 0}
              decimals={2}
              accent={
                summary.profit_factor !== null && summary.profit_factor >= 1.5 ? "profit" : "loss"
              }
            />
            <StatCard
              id="stat-winrate"
              label="Winrate"
              value={summary.winrate_pct}
              decimals={1}
              suffix="%"
            />
            <StatCard
              id="stat-maxdd"
              label="Max Drawdown"
              value={summary.max_drawdown_pct}
              decimals={2}
              suffix="%"
              accent="loss"
            />
            <StatCard label="Trades" value={summary.total_trades} />
            <StatCard
              id="stat-expectancy"
              label="Expectancy"
              value={summary.expectancy}
              decimals={3}
            />
            <StatCard
              label="Avg Win"
              value={summary.profit_split.avg_win_abs}
              decimals={2}
              prefix="+"
              accent="profit"
            />
            <StatCard
              label="Avg Loss"
              value={summary.profit_split.avg_loss_abs}
              decimals={2}
              accent="loss"
            />
            <StatCard label="Sharpe" value={summary.sharpe} decimals={2} />
            <StatCard label="Sortino" value={summary.sortino} decimals={2} />
            <StatCard label="Max Win Streak" value={summary.max_consecutive_wins} accent="profit" />
            <StatCard label="Max Loss Streak" value={summary.max_consecutive_losses} accent="loss" />
            <div id="stat-streak" className="rounded-lg border border-border bg-card p-2.5">
              <div className="mb-1 truncate text-[10.5px] text-muted">Current Streak</div>
              <StreakBadge streak={summary.current_streak} />
            </div>
          </div>

          <CollapsibleSection id="section-performance" title="Equity &amp; Drawdown">
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
                <div className="mb-1 text-[10.5px] text-muted">
                  Trade size distribution (profit %)
                </div>
                <DistributionHistogram data={summary.win_loss_sizes} />
              </div>
            </div>
          </CollapsibleSection>

          <CollapsibleSection id="section-pairs" title="Per-pair results">
            <div className="rounded-lg border border-border bg-card p-2.5">
              <PerPairPanel pairs={summary.pairs} />
            </div>
          </CollapsibleSection>

          <CollapsibleSection id="section-open-trades" title="Open Trades">
            <div className="rounded-lg border border-border bg-card p-3 text-[12px] text-muted">
              {summary.open_trades.length === 0
                ? "No open positions — every trade in this backtest window closed before the end date."
                : `${summary.open_trades.length} position(s) still open at backtest end: ${summary.open_trades
                    .map((t) => t.pair)
                    .join(", ")}`}
            </div>
          </CollapsibleSection>
        </div>
      )}
    </main>
  );
}
