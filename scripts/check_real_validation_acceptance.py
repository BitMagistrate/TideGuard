"""Apply the pre-registered acceptance rule to a real_validation JSON.

The acceptance rule (per ``docs/pre_registration_osf.md``) is::

    accept = (diebold_mariano_p < ALPHA) and (bootstrap_ci_upper < 0)

This script reads a JSON file produced by
``tideguard_ml.eval.real_validation``, evaluates the rule for the
primary forecast horizon and the three secondary horizons (after
Bonferroni correction), and prints a deterministic verdict + exits 0
on PASS, 1 on FAIL.

CLI::

    uv run python scripts/check_real_validation_acceptance.py \
        reports/real_validation_latest.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ALPHA_PRIMARY = 0.05
SECONDARY_HORIZONS = 3


def _verdict(test: dict, alpha: float) -> str:
    dm_p = float(test.get("diebold_mariano", {}).get("p_value", 1.0))
    ci_hi = float(test.get("bootstrap_ci", {}).get("upper", 0.0))
    if dm_p < alpha and ci_hi < 0:
        return f"PASS  (DM p={dm_p:.4f} < {alpha}, CI_upper={ci_hi:.5f} < 0)"
    return f"FAIL  (DM p={dm_p:.4f}, CI_upper={ci_hi:.5f})"


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: check_real_validation_acceptance.py <json>", file=sys.stderr)
        return 2
    path = Path(argv[1])
    if not path.exists():
        print(f"file not found: {path}", file=sys.stderr)
        return 2

    payload = json.loads(path.read_text())
    tests = payload.get("statistical_tests", {})
    if not tests:
        print("No statistical_tests block found.", file=sys.stderr)
        return 2

    print(f"Pre-registered acceptance rule (α={ALPHA_PRIMARY}, AND of DM + bootstrap CI):")
    primary = tests.get("primary")
    if primary is None:
        # fall back to "horizon_7" or first key
        primary_key = next(iter(tests))
        primary = tests[primary_key]
        print(f"  (no 'primary' key, using '{primary_key}')")
    print("  Primary:", _verdict(primary, ALPHA_PRIMARY))

    alpha_secondary = ALPHA_PRIMARY / SECONDARY_HORIZONS
    print(f"\nBonferroni-corrected secondary (α={alpha_secondary:.4f}):")
    for key, sec in tests.items():
        if key in ("primary",) or sec is primary:
            continue
        print(f"  {key}: {_verdict(sec, alpha_secondary)}")

    primary_dm_p = float(primary.get("diebold_mariano", {}).get("p_value", 1.0))
    primary_ci_hi = float(primary.get("bootstrap_ci", {}).get("upper", 0.0))
    accept = primary_dm_p < ALPHA_PRIMARY and primary_ci_hi < 0
    print(f"\nOverall (primary horizon): {'ACCEPT H1' if accept else 'FAIL TO REJECT H0'}")
    return 0 if accept else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
