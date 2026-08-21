"""Extract compact metrics from a Freqtrade backtest ZIP."""
import json
import sys
import zipfile
from pathlib import Path

archive = Path(sys.argv[1])
output = Path(sys.argv[2])
with zipfile.ZipFile(archive) as zf:
    candidates = [n for n in zf.namelist() if n.endswith(".json") and "config" not in n]
    if not candidates:
        raise SystemExit(f"No result JSON in {archive}")
    payload = json.loads(zf.read(candidates[0]))
strategy = next(iter(payload["strategy"].values()))
metrics = {
    "profit_factor": strategy.get("profit_factor"),
    "trades": strategy.get("total_trades"),
    "winrate": strategy.get("wins", 0) / max(strategy.get("total_trades", 0), 1),
    "max_drawdown": strategy.get("max_drawdown_account"),
    "sharpe": strategy.get("sharpe"),
}
output.write_text(json.dumps(metrics, indent=2))
print(json.dumps(metrics))
