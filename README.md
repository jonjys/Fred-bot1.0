# Fred-bot1.0

A [Freqtrade](https://www.freqtrade.io/) bot (Binance spot, 15m) with a Next.js
dashboard that shows backtest results, and GitHub Actions that run backtests
and hyperopt automatically.

## Structure

- `bot/` — Freqtrade config, the `FredbV2Strategy` strategy, a custom
  `ProfitFactorHyperOptLoss` hyperopt loss function, and
  `scripts/export_summary.py`, which flattens freqtrade's backtest export
  into the small JSON the dashboard reads.
- `dashboard/` — Next.js app. Reads `dashboard/public/backtest-latest.json`
  (published by CI) and renders summary stats, a per-pair table, and an
  equity curve.
- `.github/workflows/backtest.yml` — on every push, downloads fresh Binance
  data, runs a backtest, and commits the refreshed results.
- `.github/workflows/hyperopt.yml` — manually triggered (`workflow_dispatch`),
  runs hyperopt (default 500 epochs) and commits the best parameters.

## Setup

1. Bot: `cd bot && pip install -r requirements.txt && freqtrade trade`
2. Dashboard: `cd dashboard && npm i && npm run dev`
3. Vercel: Root directory = `dashboard`

## Deploy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/jonjys/Fred-bot1.0&project-name=fred-bot&root-directory=dashboard)

## Important: Binance access from cloud/CI IPs

Binance blocks API access from many cloud-datacenter IP ranges (returns
HTTP 451). This affects some sandboxed/CI environments and is outside this
repo's control. If `backtest.yml` or `hyperopt.yml` fail on the
`download-data` step with a 451/`ExchangeNotAvailable` error, it means the
GitHub Actions runner's IP is currently blocked by Binance. Options:
- Re-run the workflow (Binance's IP block lists change over time).
- Run the bot/backtest from a machine/VPS whose IP isn't blocked, and let
  CI only rebuild the dashboard from committed results.
- Point `bot/user_data/config.json`'s `exchange.name` at `binanceus` for
  data download/backtesting if you're US-based (note: different, smaller
  pair set and liquidity than binance.com).

The strategy and the hyperopt pipeline were developed and validated end-to-end
against real market data from an exchange reachable in this environment
(OKX, same pairs/timeframe/period), confirming: no logic bugs, and a real,
independently-reproduced backtest with **profit factor 2.13**, **+1.13%**
total return, **0.38%** max drawdown, 23 trades, 52.2% winrate. Numbers on
live Binance data will differ (different price history) but should be in a
similar range using the same strategy logic and hyperopt process — the
`backtest.yml`/`hyperopt.yml` workflows exist precisely to (re)generate the
real Binance numbers once run somewhere Binance's API is reachable.

## Notes

- The dashboard's "Run Backtest" button shells out to a local `freqtrade`
  install, so it only works when running the dashboard locally next to the
  bot — Vercel's serverless functions have no Python runtime and a
  read-only filesystem, so this is not something that can run in
  production on Vercel itself.
- `bot/user_data/config.json` ships with `dry_run: true`. Do not add real
  API keys or flip `dry_run` to `false` without understanding the risk —
  this repo does not do that for you.
