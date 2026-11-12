#!/usr/bin/env bash
# Parking lot-fit test runner (docs/parking/LOT_FIT_PLAN.md; code choices in docs/parking/LOT_FIT_CODE_NOTES.md).
#
#   scripts/run_parking_lotfit.sh            # tests + synthetic smoke run only (default; no real shares)
#   scripts/run_parking_lotfit.sh --go       # real run: only after the audit clears and Ryan says go
#
# Steps: fetch inputs if missing -> unit tests on synthetic lots -> licence check -> run. Logs go to
# data/raw/parking_lotfit/run_<UTC time>.log (git-ignored). Kept awake with caffeinate on macOS.
set -euo pipefail
cd "$(dirname "$0")/.."
if command -v uv >/dev/null 2>&1; then UV=(uv); else UV=(python3 -m uv); fi
WAKE=(); command -v caffeinate >/dev/null 2>&1 && WAKE=(caffeinate -i)
mkdir -p data/raw/parking_lotfit
LOG="data/raw/parking_lotfit/run_$(date -u +%Y%m%dT%H%M%SZ).log"
{
  if [ ! -f data/raw/parking_lotfit/manifest.json ]; then
    "${WAKE[@]}" "${UV[@]}" run python scripts/fetch_parking_lotfit.py
  fi
  "${UV[@]}" run --all-extras python -m unittest tests.test_parking_lotfit -v
  "${UV[@]}" run --all-extras python scripts/check_python_licenses.py
  if [ "${1:-}" = "--go" ]; then
    "${WAKE[@]}" "${UV[@]}" run --all-extras python scripts/run_parking_lotfit.py --go
  else
    OUT="$(mktemp -d)"
    "${UV[@]}" run --all-extras python scripts/run_parking_lotfit.py --synthetic --out "$OUT"
    echo "synthetic smoke outputs (not results): $OUT"
  fi
} 2>&1 | tee "$LOG"
