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


def parse_windows(raw: str) -> tuple[tuple[str, str], ...]:
    """Parse '--windows start:end,start:end,...' into the same shape as
    the WINDOWS constant. Kept optional/additive so existing callers
    (promote_prod.yml) that don't pass --windows keep using the original
    V2 validation range unchanged."""
    parsed = tuple(tuple(pair.split(":")) for pair in raw.split(","))
    for pair in parsed:
        if len(pair) != 2:
            raise SystemExit(f"Invalid --windows segment: {pair!r} (expected start:end)")
    return parsed
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
    parser.add_argument(
        "--windows",
        default=None,
        help="Override the default 3 OOS windows: 'start1:end1,start2:end2,start3:end3' "
        "(YYYYMMDD). Omit to use the original V2 validation range unchanged.",
    )
    args = parser.parse_args()
    windows_to_run = parse_windows(args.windows) if args.windows else WINDOWS
    windows = []
    for index, (start, end) in enumerate(windows_to_run, 1):
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
