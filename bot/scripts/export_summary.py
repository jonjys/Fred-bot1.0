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


def main() -> None:
    last_result_path = BACKTEST_DIR / ".last_result.json"
    if not last_result_path.exists():
        print(f"No backtest export found at {last_result_path}", file=sys.stderr)
        sys.exit(1)

    last_result = json.loads(last_result_path.read_text())
    zip_path = BACKTEST_DIR / last_result["latest_backtest"]
    json_name = zip_path.stem + ".json"

    with zipfile.ZipFile(zip_path) as zf:
        result = json.loads(zf.read(json_name))

    strategy_name = next(iter(result["strategy"]))
    strat = result["strategy"][strategy_name]

    summary = {
        "strategy": strategy_name,
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
        "backtest_start": strat["backtest_start"],
        "backtest_end": strat["backtest_end"],
        "pairs": [
            {
                "pair": p["key"],
                "trades": p["trades"],
                "avg_profit_pct": round(p["profit_mean_pct"], 2),
                "total_profit_abs": round(p["profit_total_abs"], 3),
                "winrate_pct": round(p["winrate"] * 100, 2),
            }
            for p in strat["results_per_pair"]
            if p["key"] != "TOTAL"
        ],
        "equity_curve": _equity_curve(strat),
    }

    out_path = BACKTEST_DIR / "latest.json"
    out_path.write_text(json.dumps(summary, indent=2))
    print(f"Wrote {out_path}")


def _equity_curve(strat: dict) -> list[dict]:
    starting_balance = strat["starting_balance"]
    cumulative = starting_balance
    curve = []
    for date, daily_abs_profit in strat["daily_profit"]:
        cumulative += daily_abs_profit
        curve.append({"date": date, "balance": round(cumulative, 3)})
    return curve


if __name__ == "__main__":
    main()
