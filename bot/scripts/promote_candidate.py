"""Promote experiment params only after a >10% all-window OOS PF gain."""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
report = json.loads(Path(sys.argv[1]).read_text())
lock_path = ROOT / "user_data/PROD_LOCK_V1.json"
lock = json.loads(lock_path.read_text())
windows = report.get("windows", [])
if len(windows) != 3 or not report.get("all_windows_pf_gte_1_5"):
    raise SystemExit("Candidate rejected: all three OOS windows must clear PF 1.5")
candidate_pf = sum(w["profit_factor"] for w in windows) / 3
required = lock["baseline"]["profit_factor"] * 1.10
if candidate_pf <= required:
    raise SystemExit(f"Candidate rejected: mean OOS PF {candidate_pf:.3f} <= {required:.3f}")
candidate = ROOT / "user_data/strategies/FredbV2Strategy.json"
target = ROOT / "user_data/strategies/FredbV2ProdStrategy.json"
payload = json.loads(candidate.read_text())
payload["strategy_name"] = "FredbV2ProdStrategy"
payload["prod_lock"] = "PROD LOCK v2"
target.write_text(json.dumps(payload, indent=2) + "\n")
lock["lock_id"] = "PROD LOCK v2"
lock["baseline"]["profit_factor"] = round(candidate_pf, 3)
lock["params"]["buy_adx"] = payload["params"]["buy"]["buy_adx"]
lock["params"]["stoploss"] = payload["params"]["stoploss"]["stoploss"]
lock_path.write_text(json.dumps(lock, indent=2) + "\n")
print(f"Promoted candidate: mean OOS PF {candidate_pf:.3f} > {required:.3f}")
