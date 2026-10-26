#!/usr/bin/env bash
# Refresh sbom/sbom.spdx.json from GitHub's dependency graph (the same SPDX 2.3 document as
# Insights -> Dependency graph -> Export SBOM). Needs the GitHub CLI (gh), signed in, and
# reflects the dependency manifests on the default branch as GitHub last read them.
set -euo pipefail
cd "$(dirname "$0")/.."
REPO="${REPO:-mroconnell/housing-challenge-starter-missingmiddleware}"
mkdir -p sbom
tmp="$(mktemp)"
gh api "repos/${REPO}/dependency-graph/sbom" --jq '.sbom' > "$tmp"
python3 -m json.tool --indent 2 "$tmp" > sbom/sbom.spdx.json
rm -f "$tmp"
python3 - <<'PY'
import json
d = json.load(open("sbom/sbom.spdx.json"))
print(f"sbom/sbom.spdx.json: {d['spdxVersion']}, created {d['creationInfo']['created']}, {len(d['packages'])} packages")
PY
