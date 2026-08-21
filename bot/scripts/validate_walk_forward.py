import json
import sys
from pathlib import Path

files = [Path(p) for p in sys.argv[1:]]
if len(files) != 3:
    raise SystemExit("Expected exactly three OOS window summaries")
rows = [json.loads(p.read_text()) for p in files]
failed = [i + 1 for i, row in enumerate(rows) if row.get("profit_factor") is None or row["profit_factor"] < 1.5]
report = {"windows": rows, "all_windows_pf_gte_1_5": not failed, "failed_windows": failed}
Path("walk-forward-report.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
if failed:
    raise SystemExit(f"OOS PF gate failed in windows {failed}; run broad-space recovery hyperopt")
