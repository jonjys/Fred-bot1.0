import json
import sys
from pathlib import Path

path = Path(sys.argv[1] if len(sys.argv) > 1 else "user_data/backtest_results/latest.json")
minimum = float(sys.argv[2] if len(sys.argv) > 2 else 1.5)
data = json.loads(path.read_text())
pf = data.get("profit_factor")
if pf is None or float(pf) < minimum:
    raise SystemExit(f"PF gate failed: {pf!r} < {minimum}")
if not data.get("hyperopt"):
    raise SystemExit("Hyperopt panel payload is missing")
print(f"PF gate OK: {pf} >= {minimum}; hyperopt payload present")
