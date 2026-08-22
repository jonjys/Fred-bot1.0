import fs from "fs";
import path from "path";
import type { BacktestSummary, LiveStatus } from "./types";

/**
 * The dashboard reads a small, pre-flattened summary from public/, written
 * by bot/scripts/export_summary.py (see backtest.yml). public/ is always
 * bundled with the Next.js deployment, unlike the sibling bot/ directory
 * outside the dashboard's Vercel root - so this is the reliable path,
 * even though bot/user_data/backtest_results/latest.json is the real
 * source of truth the CI job generates it from.
 */
export function getSummary(): BacktestSummary | null {
  const filePath = path.join(process.cwd(), "public", "backtest-latest.json");
  if (!fs.existsSync(filePath)) {
    return null;
  }
  const raw = fs.readFileSync(filePath, "utf-8");
  return normalize(JSON.parse(raw));
}

export function getLiveStatus(): LiveStatus {
  const filePath = path.join(process.cwd(), "public", "live-status.json");
  const fallback: LiveStatus = {
    connected: false,
    mode: "offline",
    updated_at: null,
    equity: null,
    pnl_pct: null,
    profit_factor: null,
    winrate_pct: null,
    max_drawdown_pct: null,
    sharpe: null,
    avg_trade_duration_minutes: null,
    open_trades: 0,
    circuit_breaker: false,
    alerting: "none",
    trades: [],
  };
  if (!fs.existsSync(filePath)) return fallback;
  return { ...fallback, ...JSON.parse(fs.readFileSync(filePath, "utf-8")) };
}

/**
 * Backfills fields that older export_summary.py versions didn't write yet,
 * so a stale committed latest.json (generated before a schema change lands)
 * degrades to empty sections instead of crashing the page.
 */
function normalize(data: Partial<BacktestSummary>): BacktestSummary {
  return {
    strategy_version: "FredbV2",
    expectancy: 0,
    expectancy_ratio: 0,
    max_consecutive_wins: 0,
    max_consecutive_losses: 0,
    trades: [],
    open_trades: [],
    current_streak: { count: 0, type: null },
    profit_split: { gross_profit_abs: 0, gross_loss_abs: 0, avg_win_abs: 0, avg_loss_abs: 0 },
    win_loss_sizes: { buckets: [], bucket_size: 0 },
    winrate_trend: [],
    hyperopt: null,
    ...data,
    pairs: (data.pairs ?? []).map((p) => ({ ...p, sparkline: p.sparkline ?? [] })),
    equity_curve: (data.equity_curve ?? []).map((e) => ({ ...e, drawdown_pct: e.drawdown_pct ?? 0 })),
  } as BacktestSummary;
}
