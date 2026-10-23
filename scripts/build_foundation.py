#!/usr/bin/env python3
"""Build the Wisconsin statewide foundation (areas, inventory, state_conditions,
BPS-to-municipality crosswalk, coverage summary) from keyless Census files.

Usage:
  uv run python scripts/build_foundation.py                  # download if missing, then build
  uv run python scripts/build_foundation.py --force-download # re-download every source file
  uv run python scripts/build_foundation.py --out foundation_test

See docs/gate2/FOUNDATION.md.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from missing_middleware.foundation.build import build  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force-download", action="store_true")
    ap.add_argument("--out", default="foundation", help="folder under data/processed/")
    a = ap.parse_args()
    checks = build(out_name=a.out, force_download=a.force_download)
    problems = {k: v for k, v in checks["contract_validation"].items() if v}
    print(json.dumps({"contract_problems": problems,
                      "state_1unit_detached": checks["state_1unit_detached_acs5"],
                      "crosswalk_2025": checks["crosswalk_2025"]}, indent=2, default=str))
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
