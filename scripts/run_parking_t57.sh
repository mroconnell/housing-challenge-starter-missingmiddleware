#!/usr/bin/env bash
# Test 57 (CAUSAL_FRAMEWORK_PLAN.md, Test 57 LOCK) runner. Needs Ryan's go before "first"; "all" only after the
# --first numbers (cells and jobs per arm, too-few flags, MDE) have been reported.
#
#   bash scripts/run_parking_t57.sh check   # synthetic tests only (tests/test_parking_t57.py); reads no real data
#   bash scripts/run_parking_t57.sh first   # synthetic tests, build NY and SF panels, summarise --first (no effect)
#   bash scripts/run_parking_t57.sh all     # summarise --all (every cell and the reading), same panels as "first"
#
# Raw inputs come from scripts/fetch_parking_t57_outcomes.py, fetch_parking_t57_gis.py, fetch_parking_t57_sf.py,
# fetch_parking_lot_cities.py and fetch_tod_cases.py (all git-ignored). Panels go to data/processed/t57/ (git-ignored);
# outputs to reference/parking_t57_{counts,mde,cells,reading}.csv. "first" records the commit and the sha256 of every
# panel in reference/parking_t57_inputs_hash.txt; "all" refuses to run if any panel changed since.
set -euo pipefail
cd "$(dirname "$0")/.."
STEP=${1:?usage: run_parking_t57.sh check|first|all}
export VECLIB_MAXIMUM_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
P=data/processed/t57; LOG=$P/logs; HASH=reference/parking_t57_inputs_hash.txt
mkdir -p "$LOG"
run() {
  local log="$LOG/$(basename "$1" .py).log"
  echo "== $STEP $(date -u +%H:%M:%S) $*"
  uv run python "$@" > "$log" 2>&1 || { tail -30 "$log"; echo "FAILED: $*"; exit 1; }
  tail -12 "$log"
}
panel_hashes() { shasum -a 256 $P/panel_*.csv | awk '{print $2"="$1}' | sort; }
case "$STEP" in
  check)
    uv run python -W ignore -m unittest tests.test_parking_t57 ;;
  first)
    uv run python -W ignore -m unittest tests.test_parking_t57
    run scripts/build_parking_t57_ny_panel.py --out "$P"
    run scripts/build_parking_t57_sf_panel.py --out "$P"
    { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) step=first commit=$(git rev-parse --short HEAD)"; panel_hashes; } > "$HASH"
    run scripts/summarise_parking_t57.py --first --panels "$P" ;;
  all)
    [ -f "$HASH" ] || { echo "run 'first' before 'all'"; exit 1; }
    diff <(grep "^data/processed/t57/panel_" "$HASH") <(panel_hashes) || { echo "panels changed since 'first'"; exit 1; }
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) step=all commit=$(git rev-parse --short HEAD)" >> "$HASH"
    run scripts/summarise_parking_t57.py --all --panels "$P" ;;
  *) echo "unknown step $STEP"; exit 1 ;;
esac
echo "== $STEP done $(date -u +%H:%M:%S)"
