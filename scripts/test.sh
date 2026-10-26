#!/usr/bin/env bash
# Run the repository's offline tests (no network), then check the licences of the installed
# Python dependencies against the permissive allowlist.
set -euo pipefail
cd "$(dirname "$0")/.."
if command -v uv >/dev/null 2>&1; then UV=(uv); else UV=(python3 -m uv); fi
"${UV[@]}" run --all-extras python -m unittest discover -s tests -v
"${UV[@]}" run --all-extras python scripts/check_python_licenses.py
