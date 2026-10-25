#!/usr/bin/env bash
# Download the Census cartographic boundary files (2024, 1:500,000, shoreline-clipped) that the Gate 4 tool's
# map draws, into data/raw/census_cb_2024/, and check them against the recorded sha256 (public domain, no key).
set -euo pipefail
cd "$(dirname "$0")/.."
dir=data/raw/census_cb_2024
mkdir -p "$dir"
base=https://www2.census.gov/geo/tiger/GENZ2024/shp
while read -r f sum; do
  [ -f "$dir/$f" ] || curl -sSfL -o "$dir/$f" "$base/$f"
  echo "$sum  $dir/$f" | shasum -a 256 -c -
done <<'LIST'
cb_2024_55_cousub_500k.zip 7612db2d2f79a29206a4fd7d210da46579d125ed4351c9bc627892ef17d7289a
cb_2024_us_county_500k.zip da4051717caec55c75e3748c3608c2a3dbde8d1ff401bbaf4f952e3c3fb63ef1
LIST
