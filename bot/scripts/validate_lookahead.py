"""Fail closed unless Freqtrade produced an explicit bias-free CSV result."""
import csv
import sys
from pathlib import Path

path = Path(sys.argv[1])
if not path.is_file() or path.stat().st_size == 0:
    raise SystemExit("Lookahead gate failed: result CSV was not produced")
with path.open(newline="") as handle:
    rows = list(csv.DictReader(handle))
if not rows:
    raise SystemExit("Lookahead gate failed: result CSV contains no strategy result")
biased = [row for row in rows if row.get("has_bias", "").strip().lower() not in {"no", "false"}]
if biased:
    raise SystemExit(f"Lookahead gate failed: biased or invalid result: {biased}")
print(f"Lookahead gate OK: {len(rows)} strategy result(s), has_bias=No")
