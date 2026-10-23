#!/usr/bin/env bash
# Install Python dependencies into a local virtual environment with uv.
set -euo pipefail
cd "$(dirname "$0")/.."
if command -v uv >/dev/null 2>&1; then UV=(uv); else
  python3 -m pip install --user --quiet uv
  UV=(python3 -m uv)
fi
"${UV[@]}" sync --all-extras
