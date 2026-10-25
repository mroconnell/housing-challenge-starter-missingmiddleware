#!/usr/bin/env bash
# Build the JSON bundle from the adopted model outputs, build the web tool, and serve it on
# http://127.0.0.1:4173/ (Ctrl+C to stop). Needs `bash scripts/setup.sh` first.
# If the processed model run is not on this machine (data/processed is not in git), the
# committed bundle in ui/public/runs/ is used as is.
set -euo pipefail
cd "$(dirname "$0")/.."
if command -v uv >/dev/null 2>&1; then UV=(uv); else UV=(python3 -m uv); fi
if [ -f data/processed/model_run/results_long.parquet ]; then
  "${UV[@]}" run --all-extras python scripts/build_ui_bundle.py
else
  echo "data/processed/model_run not found: using the committed bundle $(cat ui/public/runs/latest.json)"
fi
cd ui
[ -d node_modules ] || npm ci --no-audit --no-fund
npm run build
echo "Open http://127.0.0.1:${PORT:-4173}/ in a browser."
exec npx vite preview --host 127.0.0.1 --port "${PORT:-4173}" --strictPort
