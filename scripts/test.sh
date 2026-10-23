#!/usr/bin/env bash
# Run the repository's offline tests (no network).
set -euo pipefail
cd "$(dirname "$0")/.."
if command -v uv >/dev/null 2>&1; then UV=(uv); else UV=(python3 -m uv); fi
"${UV[@]}" run --all-extras python -m unittest discover -s tests -v
