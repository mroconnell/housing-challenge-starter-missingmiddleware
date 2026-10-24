"""Download and build California Census BPS annual tables, 2010-2025.

Run: uv run python scripts/build_ca_bps.py [--force-download]
Outputs: data/processed/comparison_ca/bps_ca_{state,county,place}_annual.parquet
"""
import sys

from missing_middleware.comparison import ca_bps

if __name__ == "__main__":
    ca_bps.fetch(force="--force-download" in sys.argv)
    t = ca_bps.build()
    print(ca_bps.checks(t).to_string())
    print({k: len(v) for k, v in t.items()})
