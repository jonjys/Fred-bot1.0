# FredbV3 production plan

FredbV3 is experimental. This document is the answer to "how do we get
this safe for live in 48h" - and the honest answer is: **not by skipping
the gate V2 went through, by reusing it.** V2's promotion pipeline
(`bot/scripts/walk_forward.py`, `promote_candidate.py`,
`prod_preflight.py`, `deploy_prod.yml`, `promote_prod.yml`,
`PROD_LOCK.json`) already does exactly what a "PROD LOCK" ask requires:
fail-closed preflight, an explicit multi-window OOS gate, immutable
version-tracked params, and a deploy workflow that refuses to ship
without green CI and a PF floor. V3 does not get a parallel, weaker
version of that. It either clears the same bar or it stays dry-run.

## What's genuinely new here vs. what's reused

**Reused, unchanged:** `prod_preflight.py`'s fail-closed pattern (refuse
live mode without exchange keys, an explicit `LIVE_TRADING_ACK`, and
configured alerting), `deploy_prod.yml`'s "green CI + PF floor + no
runtime errors" deploy gate, the `PROD_LOCK.json` versioning idea, and
`walk_forward.py`'s 3x30d OOS methodology itself (extended, not
replaced - see below).

**New, because V3 is a structurally different strategy, not a re-tuned
V2:**

- `walk_forward.py` now takes an optional `--windows` flag (defaults to
  the original V2 range if omitted, so `promote_prod.yml`'s existing
  call is untouched). V3 uses fresh windows against the last 90 days
  of real data, not V2's year-old validation period - a bar this stale
  wouldn't mean anything for a same-day scalper.
- `compare_to_prod_lock.py` is a **read-only** verdict script: it reads
  a candidate's walk-forward report and the current `PROD_LOCK.json`
  and prints ELIGIBLE/NOT ELIGIBLE. It does not touch `PROD_LOCK.json`
  or any `*ProdStrategy.json` file - see why below.
- `promote_candidate.py` is intentionally left alone. It hardcodes V2's
  param shape (`buy_adx`, `stoploss` as two specific numeric keys) and
  always targets `FredbV2ProdStrategy.json`. That's correct for
  re-tuning V2's existing entry/exit code with new numbers, but V3 has
  different indicators and different entry/exit code entirely - there
  is no "same shape, new numbers" promotion to automate here. Swapping
  which strategy CLASS the prod facade runs is a one-time, reviewed
  code change (a new `FredbV3ProdStrategy.py` file, mirroring
  `FredbV2ProdStrategy.py`'s "immutable facade" pattern), not something
  a script should do unattended. That is a deliberate scope boundary,
  not a missing feature.

## Circuit breakers

Two layers, both real (enforced by freqtrade at runtime, not just
documentation):

1. **`FredbV3Strategy.protections`** (in the strategy, freqtrade
   deprecated config-level `protections` in this version):
   - `CooldownPeriod` (3 candles = 15 min) after any close, on any pair.
   - `StoplossGuard` - 3 stoplosses in 96 candles (8h) on one pair halts
     new entries on that pair for 24 candles (2h). Contains a pair-specific
     losing streak instead of letting it keep re-entering into whatever's
     causing it.
   - `MaxDrawdown` - 8% account drawdown over the last 288 candles (24h)
     halts ALL new entries for 12 candles (1h). This is the DD<8% target
     enforced live, not just measured after the fact in a backtest.
2. **`prod_preflight.py`-style fail-closed startup checks**, extended for
   V3's shape: refuse to start live without `LIVE_TRADING_ACK` matching
   the current PROD LOCK version, exchange keys present, and
   Telegram/webhook alerting configured - identical requirements to V2,
   just re-run against whichever strategy/config pair is being started.

Neither layer is optional or bypassable from strategy config alone - the
preflight script is what `start_prod.sh` actually calls, so a live start
without it isn't a supported code path.

## PROD LOCK: what promotion would actually mean for V3

`PROD_LOCK.json`'s schema (`params: {buy_adx, stoploss}`) is V2-specific
by construction. If FredbV3 ever clears `compare_to_prod_lock.py`'s
ELIGIBLE bar, promotion means, as a **reviewed, human-approved PR**, not
an automatic CI action:

1. Create `FredbV3ProdStrategy.py` (subclasses `FredbV3Strategy`, loads
   params from a frozen `FredbV3ProdStrategy.json` snapshot - identical
   pattern to `FredbV2ProdStrategy.py`).
2. Evolve `PROD_LOCK.json` to a `strategy_class` field plus an opaque
   `params` blob (instead of the two V2-specific keys), so the schema
   stops assuming "the prod strategy is always V2's code with different
   numbers."
3. Point `PROD_CONFIG.json`'s `strategy` field and `start_prod.sh` at
   `FredbV3ProdStrategy`.
4. Cut `PROD LOCK v2` referencing the walk-forward report that justified
   it, same as V1's `promoted_at`/`sha`/`pf` fields today.
5. A new `promote_prod_v3.yml`, mirroring `promote_prod.yml`'s
   `ALLOW_PROD_PROMOTION=explicit-workflow` gate, drives steps 1-4 - not
   a modification of the existing V2 promotion workflow.

This repo does not do steps 1-4 for you until a human has looked at the
real numbers and decided the bar is cleared. That's the same posture the
existing V2 pipeline already takes towards its own promotions - V3 gets
no shortcut past it.

## 48-hour rollout runbook

**Hour 0-4 (done in this branch):** strategy + config + hyperopt loss
written; real 90-day backtest and 3x30d walk-forward run against actual
OKX perpetual swap data; results committed to `fredbv3-quant-redesign`,
not `main`.

**Review checkpoint (human):** look at the real walk-forward report
(`bot/candidate-oos-report-v3.json`) and `compare_to_prod_lock.py`'s
verdict. If NOT ELIGIBLE, this stops here - V3 stays an experiment, no
further action needed, nothing about V2's live production changes.

**If ELIGIBLE and a human wants to proceed toward live:**
1. Merge `fredbv3-quant-redesign` into `main` as dry-run-only (dashboard
   panels + strategy code visible, no prod cutover yet).
2. Let `walk_forward.yml`-equivalent CI for V3 run for several days in
   dry-run against live market data (paper trading), watching the
   dashboard's live-divergence alarm (`/api/live`, already built for
   V2) for backtest-vs-live PF drift.
3. Only after that live-dry-run period, do the reviewed PROD LOCK
   cutover described above (steps 1-5), through `promote_prod_v3.yml`,
   with the same `LIVE_TRADING_ACK`/exchange-key/alerting preflight
   checks V2 requires today.
4. `deploy_prod.yml` deploys the artifact exactly as it does for V2 -
   no separate, weaker deploy path for V3.

There is no step where an agent session sets `dry_run: false` or ships
exchange credentials on your behalf. That decision, and the live-money
risk that comes with it, stays a human action gated behind the same
preflight this repo already built for V2.
