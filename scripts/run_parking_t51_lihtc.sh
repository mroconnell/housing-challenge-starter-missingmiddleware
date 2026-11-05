#!/usr/bin/env bash
# Test 51 (CAUSAL_FRAMEWORK_PLAN.md): one configuration of the LIHTC-adjusted rerun.
# Usage: bash scripts/run_parking_t51_lihtc.sh <name> <last permit year> <none|units_100pct|li_units> [timing]
# Works on a copy of reference/ with the batch 2026-11-05 outputs laid over it (the fixed 74-place sample), in
# data/processed/t51/<name>_ref; the committed reference/ files are never written. Outputs stay in that folder.
set -euo pipefail
cd "$(dirname "$0")/.."
NAME=$1; LAST=$2; ADJ=$3; TIMING=${4:-allocation + 1}
export VECLIB_MAXIMUM_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
WORK="$PWD/data/processed/t51/${NAME}_ref"; LOG="$PWD/data/processed/t51/${NAME}_logs"
rm -rf "$WORK" "$LOG"; mkdir -p "$WORK" "$LOG"
rsync -a --exclude "batch_2026-11-05/" reference/ "$WORK/"
rsync -a reference/batch_2026-11-05/ "$WORK/"
export MM_REFERENCE_DIR="$WORK" MM_GATE_TIME="15:50" MM_BATCH_COMMITTED_DIR="reference/batch_2026-11-05" MM_BPS_LAST_YEAR="$LAST"
if [ "$ADJ" != "none" ]; then export MM_LIHTC_ADJUST="$ADJ" MM_LIHTC_TIMING="$TIMING"; fi
run() {
  local log="$LOG/$(basename "$1" .py).log"
  echo "== $NAME $(date -u +%H:%M:%S) $*"
  uv run --all-extras python "$@" > "$log" 2>&1 || { tail -30 "$log"; echo "FAILED $NAME: $*"; exit 1; }
}
run scripts/run_parking_salvage.py
run scripts/run_parking_partial.py
run scripts/run_parking_expanded.py
run scripts/run_parking_placebo.py --full --save-draws
run scripts/run_parking_method2.py --corrected --stage 2
echo "== $NAME done $(date -u +%H:%M:%S)"
