#!/usr/bin/env bash
# Run the repository's offline tests (standard library only, no network).
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m unittest discover -s tests -v
