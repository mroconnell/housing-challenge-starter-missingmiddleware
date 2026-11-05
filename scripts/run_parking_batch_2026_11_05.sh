#!/usr/bin/env bash
# Batch rerun after the sample fixes (CAUSAL_FRAMEWORK_PLAN.md, "Batch rerun after the sample fixes").
# Reads and writes a working copy of reference/ (MM_REFERENCE_DIR), so the committed originals are never touched.
# Changed or new files are copied, with subpaths, to reference/batch_2026-11-05/. Usage: bash scripts/run_parking_batch_2026_11_05.sh
set -euo pipefail
cd "$(dirname "$0")/.."
export VECLIB_MAXIMUM_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
WORK="$PWD/data/processed/batch_2026-11-05_ref"
OUT=reference/batch_2026-11-05
LOGDIR="$PWD/data/processed/batch_2026-11-05_logs"
rm -rf "$WORK" "$LOGDIR"; mkdir -p "$WORK" "$LOGDIR" "$OUT"
rsync -a --exclude "batch_2026-11-05/" reference/ "$WORK/"
TOD_BEFORE=$(shasum reference/tod_* reference/parking_lot_cities_checks_near_transit.csv | shasum)
export MM_REFERENCE_DIR="$WORK" MM_GATE_TIME="15:50" MM_BATCH_COMMITTED_DIR="$OUT"
run() {
  local log="$LOGDIR/$(basename "$1" .py)$( [ $# -gt 1 ] && echo "_${*:2}" | tr ' -' '__' ).log"
  echo "== $(date -u +%H:%M:%S) $*"
  if ! uv run --all-extras python "$@" > "$log" 2>&1; then tail -30 "$log"; echo "FAILED: $*"; exit 1; fi
  { grep -v -E "Warn|warn|ufunc|sqr =" "$log" || true; } | tail -25
}
run scripts/run_parking_salvage.py
run scripts/run_parking_partial.py
run scripts/run_parking_expanded.py
run scripts/run_parking_placebo.py --full --save-draws
run scripts/run_parking_method2.py --corrected --stage 1
run scripts/pick_parking_method2_corrected.py
cp "$WORK/parking_method2_corrected_pick.csv" "$OUT/parking_method2_corrected_pick.csv"
git add "$OUT/parking_method2_corrected_pick.csv"
git commit -q -m "Batch rerun: corrected method-2 pick on the fixed sample, committed in the batch folder for the stage-2 gate

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
run scripts/run_parking_method2.py --corrected --stage 2
run scripts/run_parking_t49_event_time.py
# copy changed or new files (with subpaths) into the batch folder
uv run python - "$WORK" "$OUT" <<'PY'
import filecmp, shutil, sys
from pathlib import Path
work, out = Path(sys.argv[1]), Path(sys.argv[2])
ref = Path("reference")
n = 0
for f in work.rglob("*"):
    if not f.is_file():
        continue
    rel = f.relative_to(work)
    orig = ref / rel
    if orig.exists() and filecmp.cmp(f, orig, shallow=False):
        continue
    dst = out / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(f, dst)
    n += 1
print("copied", n, "changed or new files to", out)
PY
git diff --quiet -- reference ":(exclude)reference/batch_2026-11-05" ":(exclude)reference/tod_*" ":(exclude)reference/parking_lot_cities_checks_near_transit.csv" || { echo "ORIGINALS CHANGED"; exit 1; }
[ -z "$(git status --porcelain reference | grep -v -E "reference/(batch_2026-11-05/|tod_|parking_lot_cities_checks_near_transit)")" ] || { echo "NEW OR CHANGED FILES UNDER reference/"; git status --porcelain reference; exit 1; }
[ "$TOD_BEFORE" = "$(shasum reference/tod_* reference/parking_lot_cities_checks_near_transit.csv | shasum)" ] || { echo "TOD FILES CHANGED"; exit 1; }
git add "$OUT"
git commit -q -m "Batch rerun outputs (changed or new files, with subpaths) in $OUT; originals untouched

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
echo "== done $(date -u +%H:%M:%S)"
