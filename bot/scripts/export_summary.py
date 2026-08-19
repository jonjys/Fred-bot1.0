#!/usr/bin/env python3
"""
Flattens the most recent freqtrade backtest export (a .zip containing the
full per-strategy result JSON) into user_data/backtest_results/latest.json:
a small, stable summary the dashboard can fetch and render directly instead
of parsing freqtrade's internal export format.
"""

import json
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path

USER_DATA = Path(__file__).resolve().parent.parent / "user_data"
BACKTEST_DIR = USER_DATA / "backtest_results"
STRATEGY_PARAMS_PATH = USER_DATA / "strategies" / "FredbV2Strategy.json"
HYPEROPT_MARKER_PATH = USER_DATA / "hyperopt_results" / "last_run.json"

STRATEGY_VERSION = "FredbV2.1"


def main() -> None:
    last_result_path = BACKTEST_DIR / ".last_result.json"
    if not last_result_path.exists():
        print(f"No backtest export found at {last_result_path}", file=sys.stderr)
        sys.exit(1)

    last_result = json.loads(last_result_path.read_text())
    zip_path = BACKTEST_DIR / last_result["latest_backtest"]
    json_name = zip_path.stem + ".json"
    config_name = zip_path.stem + "_config.json"

    with zipfile.ZipFile(zip_path) as zf:
        result = json.loads(zf.read(json_name))
        used_config = json.loads(zf.read(config_name))

    strategy_name = next(iter(result["strategy"]))
    strat = result["strategy"][strategy_name]

    # Only closed trades for stats derived here (streak, histogram, trend,
    # profit split) - an open trade's profit is unrealized and would skew
    # them, and strat["wins"]/["losses"]/["winrate"] etc. from freqtrade
    # itself are closed-trade-only too, so this keeps everything consistent.
    trades = sorted((t for t in strat["trades"] if not t.get("is_open")), key=lambda t: t["close_date"])

    summary = {
        "strategy": strategy_name,
        "strategy_version": STRATEGY_VERSION,
        # Which exchange this backtest's data actually came from. Not
        # necessarily "binance" - backtest.yml falls back to OKX when
        # Binance blocks the runner's IP (see README), and this field is
        # how the dashboard/user can tell which happened for this run.
        "exchange": used_config.get("exchange", {}).get("name"),
        "timerange": strat["timerange"],
        "generated_at": datetime.now(UTC).isoformat(),
        "total_trades": strat["total_trades"],
        "total_profit_pct": round(strat["profit_total"] * 100, 2),
        "total_profit_abs": round(strat["profit_total_abs"], 3),
        "profit_factor": round(strat["profit_factor"], 3) if strat["profit_factor"] is not None else None,
        "winrate_pct": round(strat["winrate"] * 100, 2),
        "wins": strat["wins"],
        "losses": strat["losses"],
        "draws": strat["draws"],
        "max_drawdown_pct": round(strat["max_drawdown_account"] * 100, 2),
        "sharpe": round(strat["sharpe"], 2),
        "sortino": round(strat["sortino"], 2),
        "expectancy": round(strat["expectancy"], 4),
        "expectancy_ratio": round(strat["expectancy_ratio"], 3),
        "max_consecutive_wins": strat["max_consecutive_wins"],
        "max_consecutive_losses": strat["max_consecutive_losses"],
        "backtest_start": strat["backtest_start"],
        "backtest_end": strat["backtest_end"],
        "pairs": _per_pair(strat, trades),
        "equity_curve": _equity_curve(strat),
        "trades": _trade_list(trades),
        # strat["left_open_trades"] is aggregate per-pair stats (mirrors
        # results_per_pair), not individual trade records - the actual
        # still-open trades (if any) are just the is_open=True rows of the
        # full trade list.
        "open_trades": _trade_list(
            sorted((t for t in strat["trades"] if t.get("is_open")), key=lambda t: t["open_date"])
        ),
        "current_streak": _current_streak(trades),
        "profit_split": _profit_split(trades),
        "win_loss_sizes": _win_loss_sizes(trades),
        "winrate_trend": _winrate_trend(trades),
        "hyperopt": _hyperopt_info(),
    }

    out_path = BACKTEST_DIR / "latest.json"
    out_path.write_text(json.dumps(summary, indent=2))
    print(f"Wrote {out_path}")


def _equity_curve(strat: dict) -> list[dict]:
    starting_balance = strat["starting_balance"]
    cumulative = starting_balance
    peak = starting_balance
    curve = []
    for date, daily_abs_profit in strat["daily_profit"]:
        cumulative += daily_abs_profit
        peak = max(peak, cumulative)
        drawdown_pct = (peak - cumulative) / peak * 100 if peak > 0 else 0
        curve.append(
            {
                "date": date,
                "balance": round(cumulative, 3),
                "drawdown_pct": round(drawdown_pct, 3),
            }
        )
    return curve


def _trade_list(trades: list[dict]) -> list[dict]:
    return [
        {
            "pair": t["pair"],
            "profit_ratio": round(t["profit_ratio"], 5),
            "profit_abs": round(t["profit_abs"], 3),
            "open_date": t["open_date"],
            "close_date": t.get("close_date"),
            "exit_reason": t.get("exit_reason"),
        }
        for t in trades
    ]


def _per_pair(strat: dict, trades: list[dict]) -> list[dict]:
    pairs = []
    for p in strat["results_per_pair"]:
        if p["key"] == "TOTAL":
            continue
        pair_trades = [t for t in trades if t["pair"] == p["key"]]
        cumulative = 0.0
        sparkline = []
        for t in pair_trades:
            cumulative += t["profit_abs"]
            sparkline.append(round(cumulative, 3))
        pairs.append(
            {
                "pair": p["key"],
                "trades": p["trades"],
                "avg_profit_pct": round(p["profit_mean_pct"], 2),
                "total_profit_abs": round(p["profit_total_abs"], 3),
                "winrate_pct": round(p["winrate"] * 100, 2),
                "sparkline": sparkline,
            }
        )
    return pairs


def _current_streak(trades: list[dict]) -> dict:
    """Current consecutive win/loss streak, most recent trade first."""
    if not trades:
        return {"count": 0, "type": None}
    streak_type = "win" if trades[-1]["profit_abs"] > 0 else "loss" if trades[-1]["profit_abs"] < 0 else None
    if streak_type is None:
        return {"count": 0, "type": None}
    count = 0
    for t in reversed(trades):
        is_win = t["profit_abs"] > 0
        if (streak_type == "win") == is_win and t["profit_abs"] != 0:
            count += 1
        else:
            break
    return {"count": count, "type": streak_type}


def _profit_split(trades: list[dict]) -> dict:
    gross_profit = sum(t["profit_abs"] for t in trades if t["profit_abs"] > 0)
    gross_loss = sum(-t["profit_abs"] for t in trades if t["profit_abs"] < 0)
    wins = [t["profit_abs"] for t in trades if t["profit_abs"] > 0]
    losses = [t["profit_abs"] for t in trades if t["profit_abs"] < 0]
    return {
        "gross_profit_abs": round(gross_profit, 3),
        "gross_loss_abs": round(gross_loss, 3),
        "avg_win_abs": round(sum(wins) / len(wins), 3) if wins else 0,
        "avg_loss_abs": round(sum(losses) / len(losses), 3) if losses else 0,
    }


def _win_loss_sizes(trades: list[dict], bins: int = 10) -> dict:
    """Histogram-ready buckets of trade profit_ratio (%), split wins/losses."""
    ratios = [t["profit_ratio"] * 100 for t in trades]
    if not ratios:
        return {"buckets": [], "bucket_size": 0}
    lo, hi = min(ratios), max(ratios)
    if lo == hi:
        lo, hi = lo - 1, hi + 1
    bucket_size = (hi - lo) / bins
    counts = [0] * bins
    for r in ratios:
        idx = min(int((r - lo) / bucket_size), bins - 1)
        counts[idx] += 1
    buckets = [
        {
            "range_low": round(lo + i * bucket_size, 2),
            "range_high": round(lo + (i + 1) * bucket_size, 2),
            "count": counts[i],
        }
        for i in range(bins)
    ]
    return {"buckets": buckets, "bucket_size": round(bucket_size, 3)}


def _winrate_trend(trades: list[dict], window: int = 10) -> list[dict]:
    """Rolling winrate over the trade sequence (last up to 100 trades)."""
    recent = trades[-100:]
    trend = []
    for i in range(len(recent)):
        start = max(0, i - window + 1)
        chunk = recent[start : i + 1]
        wins = sum(1 for t in chunk if t["profit_abs"] > 0)
        trend.append(
            {
                "index": i + 1,
                "winrate_pct": round(wins / len(chunk) * 100, 1),
            }
        )
    return trend


def _hyperopt_info() -> dict | None:
    """
    Reads the strategy params hyperopt.yml commits (FredbV2Strategy.json,
    freqtrade's --print-json output: a flat "params" dict covering both
    buy/sell-space values, plus minimal_roi/stoploss/trailing at the top
    level) and the marker file hyperopt.yml writes alongside it recording
    which run produced them. Returns None if no hyperopt run has ever
    landed on this branch yet.
    """
    if not STRATEGY_PARAMS_PATH.exists() or not HYPEROPT_MARKER_PATH.exists():
        return None
    params = json.loads(STRATEGY_PARAMS_PATH.read_text())
    marker = json.loads(HYPEROPT_MARKER_PATH.read_text())
    return {
        "epochs": marker.get("epochs"),
        "loss_function": marker.get("loss_function"),
        "run_at": marker.get("run_at"),
        "params": params.get("params", {}),
        "stoploss": params.get("stoploss"),
        "minimal_roi": params.get("minimal_roi"),
        "trailing_stop_positive": params.get("trailing_stop_positive"),
        "trailing_stop_positive_offset": params.get("trailing_stop_positive_offset"),
    }


if __name__ == "__main__":
    main()
