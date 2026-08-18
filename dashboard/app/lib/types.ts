export interface PairStat {
  pair: string;
  trades: number;
  avg_profit_pct: number;
  total_profit_abs: number;
  winrate_pct: number;
}

export interface EquityPoint {
  date: string;
  balance: number;
}

export interface BacktestSummary {
  strategy: string;
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
  backtest_start: string;
  backtest_end: string;
  pairs: PairStat[];
  equity_curve: EquityPoint[];
}
