"""
Read-only comparison of a candidate's walk-forward report against the
currently locked production strategy's PF - prints a verdict, changes
nothing.

This deliberately does NOT touch PROD_LOCK.json or any *ProdStrategy.json
file. promote_candidate.py's promotion path is strategy-specific (V2's
hyperopt params have a fixed shape: buy_adx, stoploss - it literally
extracts those two keys). FredbV3 is a structurally different strategy
(different indicators, different entry logic, long+short vs long-only),
so its "promotion" is not a drop-in of the same mechanism: it means
swapping which strategy CLASS the immutable prod facade delegates to, not
swapping a same-shape params file. That is a deliberate, reviewed,
one-time cutover a human makes (see docs/PROD_PLAN_V3.md), not something
this script or any CI job should do automatically.

Usage:
    python3 scripts/compare_to_prod_lock.py candidate-oos-report.json
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: compare_to_prod_lock.py <candidate-walk-forward-report.json>")

    report = json.loads(Path(sys.argv[1]).read_text())
    lock = json.loads((ROOT / "user_data/PROD_LOCK.json").read_text())

    windows = report.get("windows", [])
    if len(windows) != 3:
        print(f"VERDICT: NOT ELIGIBLE - expected 3 OOS windows, got {len(windows)}")
        return

    pfs = [w["profit_factor"] for w in windows]
    if any(pf is None for pf in pfs):
        print("VERDICT: NOT ELIGIBLE - at least one window produced no profit factor (likely 0 trades)")
        return

    dds = [w.get("max_drawdown_pct") for w in windows]
    all_windows_pf_1_5 = all(pf >= 1.5 for pf in pfs)
    mean_candidate_pf = sum(pfs) / 3
    required_pf = lock["pf"] * (1 + lock["promotion"]["minimum_mean_improvement_pct"] / 100)
    beats_locked_pf = mean_candidate_pf > required_pf
    dd_target_met = all(dd is not None and dd < 8.0 for dd in dds)

    print(f"Candidate strategy:      {report.get('strategy')}")
    print(f"Currently locked:        {lock['version']} (PF {lock['pf']})")
    print(f"Candidate OOS windows:   {pfs}")
    print(f"Candidate mean OOS PF:   {mean_candidate_pf:.3f}")
    print(f"Required (>{lock['promotion']['minimum_mean_improvement_pct']}% over locked): {required_pf:.3f}")
    print(f"All windows PF >= 1.5:   {all_windows_pf_1_5}")
    print(f"All windows DD < 8%:     {dd_target_met} ({dds})")
    print()

    if all_windows_pf_1_5 and beats_locked_pf:
        print("VERDICT: ELIGIBLE FOR PROMOTION REVIEW")
        print(
            "This does not promote anything by itself. Promotion means a human-reviewed "
            "cutover: create FredbV3ProdStrategy.py (mirroring FredbV2ProdStrategy.py's "
            "immutable-facade pattern), point PROD_CONFIG.json's strategy field and "
            "start_prod.sh at it, and cut a new PROD_LOCK version documenting the change "
            "of strategy class, not just of params."
        )
    else:
        reasons = []
        if not all_windows_pf_1_5:
            reasons.append("not all OOS windows clear PF 1.5")
        if not beats_locked_pf:
            reasons.append(f"mean OOS PF {mean_candidate_pf:.3f} does not beat locked PF by >10%")
        print("VERDICT: NOT ELIGIBLE - " + "; ".join(reasons))


if __name__ == "__main__":
    main()
