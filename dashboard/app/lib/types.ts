export interface PairStat {
  pair: string;
  trades: number;
  avg_profit_pct: number;
  total_profit_abs: number;
  winrate_pct: number;
  sparkline: number[];
}

export interface EquityPoint {
  date: string;
  balance: number;
  drawdown_pct: number;
}

export interface Trade {
  pair: string;
  profit_ratio: number;
  profit_abs: number;
  open_date: string;
  close_date: string | null;
  exit_reason: string | null;
}

export interface CurrentStreak {
  count: number;
  type: "win" | "loss" | null;
}

export interface ProfitSplit {
  gross_profit_abs: number;
  gross_loss_abs: number;
  avg_win_abs: number;
  avg_loss_abs: number;
}

export interface HistogramBucket {
  range_low: number;
  range_high: number;
  count: number;
}

export interface WinLossSizes {
  buckets: HistogramBucket[];
  bucket_size: number;
}

export interface WinrateTrendPoint {
  index: number;
  winrate_pct: number;
}

export interface HyperoptInfo {
  epochs: string | number | null;
  loss_function: string | null;
  run_at: string | null;
  params: Record<string, number | string>;
  stoploss: number | null;
  minimal_roi: Record<string, number> | null;
  trailing_stop_positive: number | null;
  trailing_stop_positive_offset: number | null;
}

export interface BacktestSummary {
  strategy: string;
  strategy_version: string;
  exchange: string | null;
  timerange: string;
  generated_at: string;
  total_trades: number;
  total_profit_pct: number;
  total_profit_abs: number;
  profit_factor: number | null;
  winrate_pct: number;
  wins: number;
  losses: number;
  draws: number;
  max_drawdown_pct: number;
  sharpe: number;
  sortino: number;
  expectancy: number;
  expectancy_ratio: number;
  max_consecutive_wins: number;
  max_consecutive_losses: number;
  backtest_start: string;
  backtest_end: string;
  pairs: PairStat[];
  equity_curve: EquityPoint[];
  trades: Trade[];
  open_trades: Trade[];
  current_streak: CurrentStreak;
  profit_split: ProfitSplit;
  win_loss_sizes: WinLossSizes;
  winrate_trend: WinrateTrendPoint[];
  hyperopt: HyperoptInfo | null;
}
