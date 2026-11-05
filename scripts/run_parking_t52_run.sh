#!/usr/bin/env bash
# Test 52 parts c, e, g, h (CAUSAL_FRAMEWORK_PLAN.md, "Test 52"), on the fixed 74-place batch sample.
# Usage: bash scripts/run_parking_t52_run.sh pool_rules [variants...]   (52g, 52h; must run first: writes D base files)
#        bash scripts/run_parking_t52_run.sh ce                         (52c, 52e)
# Works on a copy of reference/ with the batch 2026-11-05 outputs laid over it (data/processed/t52/ref), as in
# run_parking_t51_lihtc.sh; the committed reference/ files are never read-modified by the pipeline. Only the new
# reference/parking_t52_{c,e,g,h}_*.csv summaries are written by the t52 scripts themselves.
set -euo pipefail
cd "$(dirname "$0")/.."
PART=$1; shift
export VECLIB_MAXIMUM_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
WORK="$PWD/data/processed/t52/ref"; LOG="$PWD/data/processed/t52/logs"
mkdir -p "$LOG"
if [ "$PART" = "pool_rules" ]; then
  rm -rf "$WORK"; mkdir -p "$WORK"
  rsync -a --exclude "batch_2026-11-05/" reference/ "$WORK/"
  rsync -a reference/batch_2026-11-05/ "$WORK/"
fi
export MM_REFERENCE_DIR="$WORK" MM_GATE_TIME="15:50" MM_BATCH_COMMITTED_DIR="reference/batch_2026-11-05"
echo "== t52 $PART start $(date -u +%H:%M:%S) commit $(git rev-parse --short HEAD)"
uv run --all-extras python "scripts/run_parking_t52_${PART}.py" "$@" > "$LOG/$PART.log" 2>&1 || { tail -30 "$LOG/$PART.log"; echo "FAILED $PART"; exit 1; }
grep -v -E "Warn|warn|ufunc|sqr =" "$LOG/$PART.log" | tail -60
echo "== t52 $PART done $(date -u +%H:%M:%S)"
