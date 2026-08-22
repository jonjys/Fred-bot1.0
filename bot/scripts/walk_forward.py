"""Deterministic 3x30-day OOS runner for PROD LOCK validation."""
from __future__ import annotations

import argparse
import json
import subprocess
import zipfile
from pathlib import Path

WINDOWS = (
    ("20250518", "20250617"),
    ("20250617", "20250717"),
    ("20250717", "20250816"),
)
ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "user_data/backtest_results"


def extract(archive: Path) -> dict:
    with zipfile.ZipFile(archive) as zf:
        name = next(n for n in zf.namelist() if n.endswith(".json") and "config" not in n)
        payload = json.loads(zf.read(name))
    strategy = next(iter(payload["strategy"].values()))
    return {
        "profit_factor": strategy.get("profit_factor"),
        "trades": strategy.get("total_trades"),
        "max_drawdown_pct": round((strategy.get("max_drawdown_account") or 0) * 100, 3),
        "sharpe": strategy.get("sharpe"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", action="append", required=True)
    parser.add_argument("--strategy", default="FredbV2ProdStrategy")
    parser.add_argument("--output", default="walk-forward-report.json")
    args = parser.parse_args()
    windows = []
    for index, (start, end) in enumerate(WINDOWS, 1):
        command = ["freqtrade", "backtesting"]
        for config in args.config:
            command += ["-c", config]
        command += [
            "--userdir", "user_data", "--strategy", args.strategy,
            "--timerange", f"{start}-{end}", "--export", "trades",
        ]
        subprocess.run(command, cwd=ROOT, check=True)
        pointer = json.loads((RESULTS / ".last_result.json").read_text())["latest_backtest"]
        metrics = extract(RESULTS / pointer)
        metrics.update({"window": index, "start": start, "end": end})
        windows.append(metrics)
    failed = [w["window"] for w in windows if w["profit_factor"] is None or w["profit_factor"] <= 1.5]
    mean_pf = sum(w["profit_factor"] for w in windows) / len(windows)
    report = {
        "schema": "fredb.walk_forward.v1",
        "strategy": args.strategy,
        "windows": windows,
        "mean_oos_profit_factor": round(mean_pf, 4),
        "all_windows_pf_gt_1_5": not failed,
        "all_windows_pf_gte_1_5": not failed,
        "failed_windows": failed,
    }
    Path(args.output).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if failed:
        raise SystemExit(f"OOS promotion gate failed in windows {failed}")


if __name__ == "__main__":
    main()
