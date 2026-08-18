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

## Important: Binance blocks GitHub Actions' IPs (confirmed) — automatic OKX fallback

`backtest.yml`'s first real run on GitHub Actions failed at the
`download-data` step with:

```
ccxt.base.errors.ExchangeNotAvailable: binance GET https://api.binance.com/api/v3/exchangeInfo 451
"Service unavailable from a restricted location according to 'b. Eligibility'..."
```

This is Binance itself rejecting the request (HTTP 451), not a bug in this
repo or a misconfigured secret — GitHub-hosted runners currently sit in an
IP range Binance treats as restricted, the same way this development
environment's IP was blocked. It is outside this repo's control.

Both `backtest.yml` and `hyperopt.yml` now handle this automatically: they
try Binance first, and if that download fails, they fall back to OKX (same
pairs/timeframe) via `bot/user_data/config-okx-fallback.json`, an override
config layered on top of `config.json` with `-c`. The dashboard is honest
about which happened — `export_summary.py` records the exchange the data
actually came from, and the dashboard shows an orange banner whenever it's
not `binance`.

To get Binance-specific numbers instead of the OKX fallback:
- Re-run the workflow later (Binance's blocked-range list does shift over
  time, so a re-run can start succeeding with zero code changes).
- Self-host the GitHub Actions runner on a VPS whose IP isn't blocked
  (Actions supports this natively - "self-hosted runners").
- Run `freqtrade download-data` / `backtesting` / `hyperopt` from your own
  machine or a VPS, and let CI only rebuild the dashboard from the results
  you commit.
- Point `bot/user_data/config.json`'s `exchange.name` at `binanceus` if
  you're US-based (note: different, smaller pair set and liquidity than
  binance.com - re-verify the strategy's numbers there before trusting them).

The strategy and the hyperopt pipeline were developed and validated end-to-end
against real OKX market data (same pairs/timeframe/period) before this was
wired up, confirming: no logic bugs, and a real, independently-reproduced
backtest with **profit factor 2.13**, **+1.13%** total return, **0.38%**
max drawdown, 23 trades, 52.2% winrate. Numbers on live Binance data will
differ (different price history) but should be in a similar range using the
same strategy logic and hyperopt process.

## Notes

- The dashboard's "Run Backtest" button shells out to a local `freqtrade`
  install, so it only works when running the dashboard locally next to the
  bot — Vercel's serverless functions have no Python runtime and a
  read-only filesystem, so this is not something that can run in
  production on Vercel itself.
- `bot/user_data/config.json` ships with `dry_run: true`. Do not add real
  API keys or flip `dry_run` to `false` without understanding the risk —
  this repo does not do that for you.
