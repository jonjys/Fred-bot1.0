#!/usr/bin/env python3
"""
Flattens FredbV3Strategy's backtest export into
user_data/backtest_results/latest_v3.json - a separate file from V2's
latest.json/backtest-latest.json on purpose. V3 is experimental and lives
on its own branch; this must never overwrite the data feeding the live V2
production dashboard.

Shares export_summary.py's core stat fields (so the dashboard can reuse
the same StatCard/EquityChart/PerPairPanel/etc. components for both), and
adds V3-specific fields the brief asked to monitor: long vs short split,
DCA/partial-exit usage and their effect on outcomes, and the live
protections (circuit breaker) configuration.
"""

import json
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path

USER_DATA = Path(__file__).resolve().parent.parent / "user_data"
BACKTEST_DIR = USER_DATA / "backtest_results"

STRATEGY_VERSION = "FredbV3.0-experimental"

# Mirrors FredbV3Strategy.protections - kept here as data rather than
# imported from the strategy module so this script has no import-time
# dependency on freqtrade being installed with the strategy's deps.
PROTECTIONS = [
    {"method": "CooldownPeriod", "stop_duration_candles": 3},
    {
        "method": "StoplossGuard",
        "lookback_period_candles": 96,
        "trade_limit": 3,
        "stop_duration_candles": 24,
        "only_per_pair": True,
    },
    {
        "method": "MaxDrawdown",
        "lookback_period_candles": 288,
        "trade_limit": 10,
        "stop_duration_candles": 12,
        "max_allowed_drawdown": 0.08,
    },
]
MAX_ALLOWED_DRAWDOWN_PCT = 8.0


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

    trades = sorted((t for t in strat["trades"] if not t.get("is_open")), key=lambda t: t["close_date"])

    backtest_start = datetime.fromisoformat(strat["backtest_start"])
    backtest_end = datetime.fromisoformat(strat["backtest_end"])
    days = max((backtest_end - backtest_start).total_seconds() / 86400, 1e-9)

    summary = {
        "strategy": strategy_name,
        "strategy_version": STRATEGY_VERSION,
        "exchange": used_config.get("exchange", {}).get("name"),
        "trading_mode": used_config.get("trading_mode"),
        "timeframe": strat["timeframe"],
        "informative_timeframe": "1h",
        "timerange": strat["timerange"],
        "generated_at": datetime.now(UTC).isoformat(),
        "total_trades": strat["total_trades"],
        "trades_per_day": round(strat["total_trades"] / days, 2),
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
        "open_trades": _trade_list(
            sorted((t for t in strat["trades"] if t.get("is_open")), key=lambda t: t["open_date"])
        ),
        "current_streak": _current_streak(trades),
        "profit_split": _profit_split(trades),
        "win_loss_sizes": _win_loss_sizes(trades),
        "winrate_trend": _winrate_trend(trades),
        "direction_split": _direction_split(trades),
        "position_management": _position_management(trades),
        "exit_reason_breakdown": _exit_reason_breakdown(trades),
        "circuit_breakers": {
            "protections": PROTECTIONS,
            "max_allowed_drawdown_pct": MAX_ALLOWED_DRAWDOWN_PCT,
            "current_max_drawdown_pct": round(strat["max_drawdown_account"] * 100, 2),
        },
        "prod_lock_status": "EXPERIMENTAL - not PROD LOCKED",
    }

    out_path = BACKTEST_DIR / "latest_v3.json"
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
        curve.append({"date": date, "balance": round(cumulative, 3), "drawdown_pct": round(drawdown_pct, 3)})
    return curve


def _trade_list(trades: list[dict]) -> list[dict]:
    return [
        {
            "pair": t["pair"],
            "is_short": t.get("is_short", False),
            "enter_tag": t.get("enter_tag"),
            "leverage": t.get("leverage"),
            "profit_ratio": round(t["profit_ratio"], 5) if t.get("profit_ratio") is not None else None,
            "profit_abs": round(t["profit_abs"], 3) if t.get("profit_abs") is not None else None,
            "open_date": t["open_date"],
            "close_date": t.get("close_date"),
            "exit_reason": t.get("exit_reason"),
            "dca_used": (t.get("nr_of_successful_entries") or 1) > 1,
            "partial_tp_used": (t.get("nr_of_successful_exits") or 1) > 1,
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
    return {
        "buckets": [
            {"range_low": round(lo + i * bucket_size, 2), "range_high": round(lo + (i + 1) * bucket_size, 2), "count": counts[i]}
            for i in range(bins)
        ],
        "bucket_size": round(bucket_size, 3),
    }


def _winrate_trend(trades: list[dict], window: int = 10) -> list[dict]:
    recent = trades[-100:]
    trend = []
    for i in range(len(recent)):
        start = max(0, i - window + 1)
        chunk = recent[start : i + 1]
        wins = sum(1 for t in chunk if t["profit_abs"] > 0)
        trend.append({"index": i + 1, "winrate_pct": round(wins / len(chunk) * 100, 1)})
    return trend


def _pf_and_winrate(subset: list[dict]) -> dict:
    if not subset:
        return {"trades": 0, "winrate_pct": 0.0, "profit_factor": None, "total_profit_abs": 0.0}
    gross_profit = sum(t["profit_abs"] for t in subset if t["profit_abs"] > 0)
    gross_loss = -sum(t["profit_abs"] for t in subset if t["profit_abs"] < 0)
    wins = sum(1 for t in subset if t["profit_abs"] > 0)
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (gross_profit if gross_profit > 0 else None)
    return {
        "trades": len(subset),
        "winrate_pct": round(wins / len(subset) * 100, 2),
        "profit_factor": round(profit_factor, 3) if profit_factor is not None else None,
        "total_profit_abs": round(sum(t["profit_abs"] for t in subset), 3),
    }


def _direction_split(trades: list[dict]) -> dict:
    longs = [t for t in trades if not t.get("is_short")]
    shorts = [t for t in trades if t.get("is_short")]
    return {"long": _pf_and_winrate(longs), "short": _pf_and_winrate(shorts)}


def _position_management(trades: list[dict]) -> dict:
    def avg_profit_pct(subset: list[dict]) -> float:
        if not subset:
            return 0.0
        return round(sum(t["profit_ratio"] for t in subset) / len(subset) * 100, 3)

    dca = [t for t in trades if (t.get("nr_of_successful_entries") or 1) > 1]
    no_dca = [t for t in trades if (t.get("nr_of_successful_entries") or 1) <= 1]
    ptp = [t for t in trades if (t.get("nr_of_successful_exits") or 1) > 1]
    no_ptp = [t for t in trades if (t.get("nr_of_successful_exits") or 1) <= 1]

    total = len(trades) or 1
    return {
        "dca_trades": len(dca),
        "dca_trades_pct": round(len(dca) / total * 100, 1),
        "dca_avg_profit_pct": avg_profit_pct(dca),
        "no_dca_avg_profit_pct": avg_profit_pct(no_dca),
        "partial_tp_trades": len(ptp),
        "partial_tp_trades_pct": round(len(ptp) / total * 100, 1),
        "partial_tp_avg_profit_pct": avg_profit_pct(ptp),
        "no_partial_tp_avg_profit_pct": avg_profit_pct(no_ptp),
    }


def _exit_reason_breakdown(trades: list[dict]) -> dict:
    breakdown: dict[str, int] = {}
    for t in trades:
        reason = t.get("exit_reason") or "unknown"
        breakdown[reason] = breakdown.get(reason, 0) + 1
    return breakdown


if __name__ == "__main__":
    main()
