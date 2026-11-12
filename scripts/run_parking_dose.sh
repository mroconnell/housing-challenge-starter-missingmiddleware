#!/usr/bin/env bash
# Parking dose-response (docs/parking/DOSE_PLAN.md; code notes docs/parking/DOSE_CODE_NOTES.md).
# Pipeline for one outcome working copy:
#   bash scripts/run_parking_dose.sh all_homes [main|droppools]   # MM_BPS_OUTCOME unset (the batch's all-homes outcome)
#   bash scripts/run_parking_dose.sh units_2_4 [main|droppools]   # MM_BPS_OUTCOME=units_2_4 (Test 56's outcome)
# Fit, in this order (each step refuses to start out of order):
#   bash scripts/run_parking_dose.sh identity    # (a) the 74 at dose 100 reproduce today's averages, or stop
#   bash scripts/run_parking_dose.sh first       # (b) identity again, gap MDE and counts per dose group; commit the outputs
#   bash scripts/run_parking_dose.sh all         # (c) identity again, the 88 cells and the reading
# Working copies (as Test 56): data/processed/dose/<outcome>_ref (main) and <outcome>_droppools_ref (C5 check: every dated
# partial housing reform appended to the copy's taxonomy, so it leaves every comparison and stand-in pool). reference/ is
# never written by the pipeline. Nothing runs unless reference/parking_doses.csv matches the frozen sha256 in
# docs/parking/DOSES_BUILT.md and both are committed (audit fix 6). The four pipeline runs are independent: run them
# side by side (e.g. four terminals, or & and wait), under caffeinate on a laptop.
set -euo pipefail
cd "$(dirname "$0")/.."
NAME=$1; VARIANT=${2:-main}
export VECLIB_MAXIMUM_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
uv run --all-extras python -c "import sys; sys.path.insert(0, 'scripts'); import parking_dose_common as dc; print('doses frozen, sha256', dc.require_frozen_doses())"
case "$NAME" in
  identity|first|all)
    unset MM_REFERENCE_DIR MM_BPS_OUTCOME
    uv run --all-extras python scripts/run_parking_dose.py "--$NAME"
    exit 0 ;;
  all_homes|units_2_4) ;;
  *) echo "usage: $0 <all_homes|units_2_4> [main|droppools] | identity | first | all"; exit 2 ;;
esac
case "$VARIANT" in main) DIR="$NAME" ;; droppools) DIR="${NAME}_droppools" ;; *) echo "variant: main or droppools"; exit 2 ;; esac
WORK="$PWD/data/processed/dose/${DIR}_ref"; LOG="$PWD/data/processed/dose/${DIR}_logs"
rm -rf "$WORK" "$LOG"; mkdir -p "$WORK" "$LOG"
rsync -a --exclude "batch_2026-11-05/" reference/ "$WORK/"
rsync -a reference/batch_2026-11-05/ "$WORK/"
H_ACS=$(shasum -a 256 reference/parking_acs_crowding.csv | cut -d' ' -f1)
H_WORK=$(shasum -a 256 "$WORK/parking_acs_crowding.csv" | cut -d' ' -f1)
[ "$H_ACS" = "$H_WORK" ] || { echo "parking_acs_crowding.csv copy differs"; exit 1; }
H_DOSE=$(shasum -a 256 reference/parking_doses.csv | cut -d' ' -f1)
HLINE="$(date -u +%Y-%m-%dT%H:%M:%SZ) run=$DIR commit=$(git rev-parse --short HEAD) sha256(reference/parking_acs_crowding.csv)=$H_ACS sha256(reference/parking_doses.csv)=$H_DOSE"
echo "$HLINE" > "$LOG/inputs_hash.txt"
echo "$HLINE" >> "$PWD/reference/parking_dose_inputs_hash.txt"
export MM_REFERENCE_DIR="$WORK" MM_GATE_TIME="15:50" MM_BATCH_COMMITTED_DIR="reference/batch_2026-11-05" MM_BPS_LAST_YEAR="2025"
if [ "$NAME" = "all_homes" ]; then unset MM_BPS_OUTCOME; else export MM_BPS_OUTCOME="$NAME"; fi
unset MM_LIHTC_ADJUST MM_LIHTC_TIMING
run() {
  local log="$LOG/$(basename "$1" .py)${3:+_$3}.log"
  echo "== $DIR $(date -u +%H:%M:%S) $*"
  uv run --all-extras python "$@" > "$log" 2>&1 || { tail -30 "$log"; echo "FAILED $DIR: $*"; exit 1; }
}
if [ "$VARIANT" = "droppools" ]; then
  run scripts/run_parking_dose_effects.py --augment-taxonomy
fi
run scripts/run_parking_salvage.py
run scripts/run_parking_partial.py
run scripts/run_parking_expanded.py
run scripts/run_parking_placebo.py --full --save-draws
run scripts/run_parking_t56_method2.py --corrected --stage 2
if [ "$VARIANT" = "main" ]; then
  run scripts/run_parking_t56_extras.py --parts event,placebo_dates
  run scripts/run_parking_dose_effects.py --parts match,effects,standins,event,shift
else
  run scripts/run_parking_dose_effects.py --parts match,effects,standins
fi
echo "== $DIR done $(date -u +%H:%M:%S)"
