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
  prod_lock?: string | null;
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

// --- FredbV3 (experimental, separate branch/page from the V2 types above) ---

export interface DirectionStat {
  trades: number;
  winrate_pct: number;
  profit_factor: number | null;
  total_profit_abs: number;
}

export interface DirectionSplit {
  long: DirectionStat;
  short: DirectionStat;
}

export interface PositionManagement {
  dca_trades: number;
  dca_trades_pct: number;
  dca_avg_profit_pct: number;
  no_dca_avg_profit_pct: number;
  partial_tp_trades: number;
  partial_tp_trades_pct: number;
  partial_tp_avg_profit_pct: number;
  no_partial_tp_avg_profit_pct: number;
}

export interface ProtectionConfig {
  method: string;
  [key: string]: string | number | boolean;
}

export interface CircuitBreakerInfo {
  protections: ProtectionConfig[];
  max_allowed_drawdown_pct: number;
  current_max_drawdown_pct: number;
}

export interface V3Trade {
  pair: string;
  is_short: boolean;
  enter_tag: string | null;
  leverage: number | null;
  profit_ratio: number | null;
  profit_abs: number | null;
  open_date: string;
  close_date: string | null;
  exit_reason: string | null;
  dca_used: boolean;
  partial_tp_used: boolean;
}

export interface V3Summary {
  strategy: string;
  strategy_version: string;
  exchange: string | null;
  trading_mode: string | null;
  timeframe: string;
  informative_timeframe: string;
  timerange: string;
  generated_at: string;
  total_trades: number;
  trades_per_day: number;
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
  trades: V3Trade[];
  open_trades: V3Trade[];
  current_streak: CurrentStreak;
  profit_split: ProfitSplit;
  win_loss_sizes: WinLossSizes;
  winrate_trend: WinrateTrendPoint[];
  direction_split: DirectionSplit;
  position_management: PositionManagement;
  exit_reason_breakdown: Record<string, number>;
  circuit_breakers: CircuitBreakerInfo;
  prod_lock_status: string;
}

export interface LiveStatus {
  connected: boolean;
  mode: "dry_run" | "live" | "offline";
  updated_at: string | null;
  equity: number | null;
  pnl_pct: number | null;
  profit_factor: number | null;
  winrate_pct: number | null;
  max_drawdown_pct: number | null;
  sharpe: number | null;
  avg_trade_duration_minutes: number | null;
  open_trades: number;
  circuit_breaker: boolean;
  alerting: "telegram" | "discord" | "none";
  trades: LiveTrade[];
}

export interface LiveTrade {
  id: string;
  pair: string;
  side: "long" | "short";
  opened_at: string;
  closed_at: string | null;
  profit_pct: number | null;
  status: "open" | "closed";
  exit_reason: string | null;
}
