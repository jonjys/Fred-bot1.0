"""FredbV3 3x30-day OOS runner and fail-closed promotion gates."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import zipfile
from pathlib import Path
from typing import Any

WINDOWS = (
    ("20260524", "20260623"),
    ("20260623", "20260723"),
    ("20260723", "20260822"),
)
ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "user_data" / "backtest_results"


def extract(archive: Path) -> dict[str, Any]:
    if not archive.is_file():
        raise SystemExit(f"Missing backtest archive: {archive}")
    with zipfile.ZipFile(archive) as zf:
        names = [n for n in zf.namelist() if n.endswith(".json") and "config" not in n]
        if len(names) != 1:
            raise SystemExit(f"Expected one result JSON in {archive}, found {names}")
        payload = json.loads(zf.read(names[0]))
    strategies = payload.get("strategy", {})
    if len(strategies) != 1:
        raise SystemExit(f"Expected one strategy result in {archive}")
    row = next(iter(strategies.values()))
    required = ("profit_factor", "total_trades", "max_drawdown_account", "sharpe", "profit_total")
    missing = [key for key in required if key not in row]
    if missing:
        raise SystemExit(f"Missing metrics in {archive}: {missing}")
    return {
        "profit_factor": float(row["profit_factor"]) if row["profit_factor"] is not None else None,
        "trades": int(row["total_trades"]),
        "max_drawdown_pct": round(float(row["max_drawdown_account"]) * 100, 6),
        "sharpe": float(row["sharpe"]) if row["sharpe"] is not None else None,
        "profit_total": float(row["profit_total"]),
    }


def copy_latest(output: str) -> Path:
    pointer_path = RESULTS / ".last_result.json"
    if not pointer_path.is_file():
        raise SystemExit("Freqtrade did not create .last_result.json")
    pointer = json.loads(pointer_path.read_text()).get("latest_backtest")
    if not pointer:
        raise SystemExit("Freqtrade result pointer has no latest_backtest")
    source = RESULTS / pointer
    if not source.is_file():
        raise SystemExit(f"Freqtrade result archive is missing: {source}")
    target = RESULTS / output
    shutil.copy2(source, target)
    return target


def run_windows(args: argparse.Namespace) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows = []
    for index, (start, end) in enumerate(WINDOWS, 1):
        filename = f"wf_v3_{index}.zip"
        command = [
            "freqtrade", "backtesting", "--config", args.config,
            "--userdir", "user_data", "--strategy", args.strategy,
            "--timerange", f"{start}-{end}", "--cache", "none",
            "--export", "trades",
        ]
        subprocess.run(command, cwd=ROOT, check=True)
        metrics = extract(copy_latest(filename))
        metrics.update({"window": index, "start": start, "end": end})
        rows.append(metrics)
    failed = [
        row["window"] for row in rows
        if row["profit_factor"] is None or row["profit_factor"] < 1.5
    ]
    report = {
        "schema": "fredb.v3.walk-forward.v1",
        "strategy": args.strategy,
        "windows": rows,
        "all_windows_pf_gte_1_5": not failed,
        "failed_windows": failed,
    }
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


def validate(args: argparse.Namespace) -> None:
    base = extract(ROOT / args.base)
    fee = extract(ROOT / args.fee_stress)
    wf_path = ROOT / args.walk_forward
    if not wf_path.is_file():
        raise SystemExit(f"Missing walk-forward report: {wf_path}")
    walk_forward = json.loads(wf_path.read_text())
    checks = {
        "profit_factor_gte_3": base["profit_factor"] is not None and base["profit_factor"] >= 3.0,
        "drawdown_lte_8_pct": base["max_drawdown_pct"] <= 8.0,
        "sharpe_gte_1_5": base["sharpe"] is not None and base["sharpe"] >= 1.5,
        "trades_gte_300": base["trades"] >= 300,
        "all_oos_pf_gte_1_5": walk_forward.get("all_windows_pf_gte_1_5") is True,
        "lookahead_bias_free": os.environ.get("BIAS_STATUS") == "PASS",
        "fee_stress_pf_gte_1_5": fee["profit_factor"] is not None and fee["profit_factor"] >= 1.5,
        "fee_stress_profitable": fee["profit_total"] > 0,
    }
    report = {
        "schema": "fredb.v3.validation.v1",
        "commit": os.environ.get("VALIDATED_COMMIT", "UNKNOWN"),
        "status": "PASS" if all(checks.values()) else "FAIL",
        "base": base,
        "walk_forward": walk_forward,
        "fee_stress": fee,
        "checks": checks,
    }
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise SystemExit("Hard promotion gates failed: " + ", ".join(failed))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--config", required=True)
    run.add_argument("--strategy", default="FredbV3Strategy")
    run.add_argument("--output", required=True)
    copy = sub.add_parser("copy-latest")
    copy.add_argument("--output", required=True)
    gate = sub.add_parser("validate")
    gate.add_argument("--base", required=True)
    gate.add_argument("--walk-forward", required=True)
    gate.add_argument("--fee-stress", required=True)
    gate.add_argument("--output", required=True)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    if arguments.command == "run":
        run_windows(arguments)
    elif arguments.command == "copy-latest":
        print(copy_latest(arguments.output))
    else:
        validate(arguments)
