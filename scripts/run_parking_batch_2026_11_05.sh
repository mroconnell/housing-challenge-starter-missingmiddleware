#!/usr/bin/env bash
# Batch rerun after the sample fixes (CAUSAL_FRAMEWORK_PLAN.md, "Batch rerun after the sample fixes").
# Runs in place, then copies every changed or new reference file to reference/batch_2026-11-05/ and restores the
# committed originals (the tool's inputs are left as they were). Usage: bash scripts/run_parking_batch_2026_11_05.sh
set -euo pipefail
cd "$(dirname "$0")/.."
export VECLIB_MAXIMUM_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
BASE=$(git rev-parse HEAD)
OUT=reference/batch_2026-11-05
mkdir -p "$OUT"
run() { echo "== $(date -u +%H:%M:%S) $*"; uv run --all-extras python "$@" 2>&1 | grep -v -E "Warn|warn|ufunc|sqr =" | tail -25; }
run scripts/run_parking_salvage.py
run scripts/run_parking_partial.py
run scripts/run_parking_expanded.py
run scripts/run_parking_placebo.py --full --save-draws
run scripts/run_parking_method2.py --corrected --stage 1
run scripts/pick_parking_method2_corrected.py
git add reference/parking_method2_corrected_pick.csv
git commit -q -m "Batch rerun (interim, restored at the end): corrected method-2 pick on the fixed sample, committed for the stage-2 gate

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
run scripts/run_parking_method2.py --corrected --stage 2
run scripts/run_parking_t49_event_time.py
# keep every changed or new file under reference/ (top level only), then restore the committed originals
for f in $( (git diff --name-only "$BASE" -- reference; git ls-files --others --exclude-standard reference) | grep -v "^reference/batch_" | sort -u ); do
  case "$f" in reference/tod_*|reference/parking_lot_cities_checks_near_transit.csv) continue;; esac
  cp "$f" "$OUT/$(basename "$f")"
done
for f in $(git diff --name-only "$BASE" -- reference | grep -v -E "^reference/(batch_|tod_|parking_lot_cities_checks_near_transit)"); do
  git checkout "$BASE" -- "$f"
done
git add "$OUT" reference/parking_method2_corrected_pick.csv
git commit -q -m "Batch rerun outputs saved to $OUT; committed originals restored (tool inputs unchanged)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
echo "== done $(date -u +%H:%M:%S)"
