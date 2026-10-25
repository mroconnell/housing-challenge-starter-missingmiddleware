#!/usr/bin/env bash
# Install Python dependencies into a local virtual environment with uv, and the
# front-end dependencies of the Gate 4 tool (ui/) with npm (Node.js 20+).
set -euo pipefail
cd "$(dirname "$0")/.."
if command -v uv >/dev/null 2>&1; then UV=(uv); else
  python3 -m pip install --user --quiet uv
  UV=(python3 -m uv)
fi
"${UV[@]}" sync --all-extras
if command -v npm >/dev/null 2>&1; then
  (cd ui && npm ci --no-audit --no-fund)
else
  echo "npm not found: install Node.js 20+ to build and run the tool in ui/ (Python steps are ready)." >&2
fi
