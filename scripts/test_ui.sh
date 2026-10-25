#!/usr/bin/env bash
# Bundle tests (Python), licence check, type check, production build and Playwright smoke
# tests (desktop and mobile Chromium). Uses an existing Playwright Chromium install; if none is
# found, install one with: (cd ui && npx playwright install chromium)
set -euo pipefail
cd "$(dirname "$0")/.."
if command -v uv >/dev/null 2>&1; then UV=(uv); else UV=(python3 -m uv); fi
"${UV[@]}" run --all-extras python -m unittest tests.test_ui_bundle -v
cd ui
[ -d node_modules ] || npm ci --no-audit --no-fund
npm run licenses
npm run build
npx playwright test
