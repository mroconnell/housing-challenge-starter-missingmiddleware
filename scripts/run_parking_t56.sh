#!/usr/bin/env bash
# Test 56 (CAUSAL_FRAMEWORK_PLAN.md, "Test 56: one reading at lock"): the batch pipeline for one Census BPS outcome.
# Usage: bash scripts/run_parking_t56.sh <units_2_4|1unit_units|5plus_units|units_2_4_rep|...> [extras]
#        bash scripts/run_parking_t56.sh all [extras]    # DRY RUN: MM_BPS_OUTCOME left unset (the already-seen
#                                                        # all-homes outcome), working copy data/processed/t56/dryrun_allhomes_ref
# Works on a copy of reference/ with the batch 2026-11-05 outputs laid over it (the fixed 74-place sample), in
# data/processed/t56/<outcome>_ref; the committed reference/ files are never written. Outputs stay in that folder.
# MM_BPS_OUTCOME swaps the permit outcome (run_parking_comparison.outcome_swap); MM_BPS_LAST_YEAR=2025 keeps the batch's
# years and skips the expanded script's prediction-tool scoring. Method 2 runs through run_parking_t56_method2.py, which
# keeps D's pools and existing-homes counts on all permits. With a second argument "extras", the 2-4 unit checks run
# after the pipeline (scripts/run_parking_t56_extras.py: event study, long set, Poisson, placebo dates, pool rules).
# The sha256 of reference/parking_acs_crowding.csv (read by method 2; not tracked in git) is recorded with the commit:
# reference/parking_t56_inputs_hash.txt for real runs, <logs>/inputs_hash.txt for the dry run.
set -euo pipefail
cd "$(dirname "$0")/.."
NAME=$1; EXTRAS=${2:-}
export VECLIB_MAXIMUM_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
if [ "$NAME" = "all" ]; then
  DIR="dryrun_allhomes"; HASHFILE=""
else
  DIR="$NAME"; HASHFILE="$PWD/reference/parking_t56_inputs_hash.txt"
fi
WORK="$PWD/data/processed/t56/${DIR}_ref"; LOG="$PWD/data/processed/t56/${DIR}_logs"
rm -rf "$WORK" "$LOG"; mkdir -p "$WORK" "$LOG"
rsync -a --exclude "batch_2026-11-05/" reference/ "$WORK/"
rsync -a reference/batch_2026-11-05/ "$WORK/"
H_REF=$(shasum -a 256 reference/parking_acs_crowding.csv | cut -d' ' -f1)
H_WORK=$(shasum -a 256 "$WORK/parking_acs_crowding.csv" | cut -d' ' -f1)
[ "$H_REF" = "$H_WORK" ] || { echo "parking_acs_crowding.csv copy differs"; exit 1; }
HLINE="$(date -u +%Y-%m-%dT%H:%M:%SZ) outcome=$NAME commit=$(git rev-parse --short HEAD) sha256(reference/parking_acs_crowding.csv)=$H_REF"
echo "$HLINE" > "$LOG/inputs_hash.txt"
[ -n "$HASHFILE" ] && echo "$HLINE" >> "$HASHFILE"
export MM_REFERENCE_DIR="$WORK" MM_GATE_TIME="15:50" MM_BATCH_COMMITTED_DIR="reference/batch_2026-11-05" MM_BPS_LAST_YEAR="2025"
if [ "$NAME" = "all" ]; then
  unset MM_BPS_OUTCOME
else
  export MM_BPS_OUTCOME="$NAME"
fi
unset MM_LIHTC_ADJUST MM_LIHTC_TIMING
run() {
  local log="$LOG/$(basename "$1" .py).log"
  echo "== $NAME $(date -u +%H:%M:%S) $*"
  uv run --all-extras python "$@" > "$log" 2>&1 || { tail -30 "$log"; echo "FAILED $NAME: $*"; exit 1; }
}
run scripts/run_parking_salvage.py
run scripts/run_parking_partial.py
run scripts/run_parking_expanded.py
run scripts/run_parking_placebo.py --full --save-draws
run scripts/run_parking_t56_method2.py --corrected --stage 2
if [ "$EXTRAS" = "extras" ]; then
  run scripts/run_parking_t56_extras.py
fi
echo "== $NAME done $(date -u +%H:%M:%S)"
