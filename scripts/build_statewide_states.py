"""Build the statewide-ADU-law states tables (Gate 3, owner question 2026-10-24).

    uv run python scripts/build_statewide_states.py            # write reference/statewide_states_*.csv
    uv run python scripts/build_statewide_states.py --print    # also print summary tables

Inputs (read only):
    data/raw/census_acs5_2024_tbsf/acsdt5y2024-b25024.dat
    data/raw/census_acs5_2024_tbsf_market/acsdt5y2024-b25077.dat, acsdt5y2024-b25064.dat
    data/raw/statewide_states/census_place_codes/st<fips>_<st>_place2020.txt  (Census 2020 place codes)
Annual ADU counts are data in missing_middleware/comparison/statewide_states.py (SERIES), each
transcribed or extracted from the official source named there; raw copies of most sources are
in data/raw/statewide_states/<state>/ with _downloads.json (URL, access date, bytes, SHA-256).
Outputs (aggregates only):
    reference/statewide_states_laws.csv           one row per state: law, dates, provisions, data
    reference/statewide_states_acs.csv            denominators and market per data geography
    reference/statewide_states_annual.csv         annual ADU counts and rates per series
    reference/statewide_states_period_rates.csv   before/after window rates (+ CA study rows)
    reference/statewide_states_ranking.csv        usefulness ranking for the Wisconsin test
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from missing_middleware.comparison import statewide_states as ss  # noqa: E402

RAW = ROOT / "data" / "raw"
REF = ROOT / "reference"
CODES = RAW / "statewide_states" / "census_place_codes"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--print", action="store_true")
    args = ap.parse_args()

    place_codes = {"53": CODES / "st53_wa_place2020.txt", "41": CODES / "st41_or_place2020.txt"}
    acs = ss.acs_geographies(
        RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25024.dat",
        RAW / "census_acs5_2024_tbsf_market" / "acsdt5y2024-b25077.dat",
        RAW / "census_acs5_2024_tbsf_market" / "acsdt5y2024-b25064.dat",
        place_codes=place_codes)
    homes = dict(zip(acs["key"], acs["homes"]))
    values = dict(zip(acs["key"], acs["median_value"]))

    laws = ss.states_table()
    annual = ss.annual_table(homes=homes)
    periods = ss.period_rates(homes=homes)
    periods = pd.concat([periods, ss.ca_rate_rows()], ignore_index=True)
    state_values = {ab: values[key] for ab, key in ss.DATA_GEOGRAPHY.items()}
    # California is the fitting state of the regression, so it is not ranked as a test.
    ranking = ss.rank_states([s for s in ss.STATES if s["abbr"] != "CA"], state_values, wi_value=values["state_WI"])
    ranking["data_geography"] = ranking["abbr"].map(ss.DATA_GEOGRAPHY)

    REF.mkdir(exist_ok=True)
    laws.to_csv(REF / "statewide_states_laws.csv", index=False)
    acs.to_csv(REF / "statewide_states_acs.csv", index=False, float_format="%.0f")
    annual.to_csv(REF / "statewide_states_annual.csv", index=False, float_format="%.3f")
    periods.to_csv(REF / "statewide_states_period_rates.csv", index=False, float_format="%.3f")
    ranking.to_csv(REF / "statewide_states_ranking.csv", index=False)

    if args.print:
        pd.set_option("display.width", 250, "display.max_columns", 30, "display.max_colwidth", 60)
        print(acs[["key", "n_geographies", "homes", "median_value", "median_rent"]].to_string())
        print(periods[["series", "phase", "label", "years_observed", "adu_count", "rate", "rate_lo",
                       "rate_hi", "years_after_treatment"]].to_string())
        print(ranking.to_string())


if __name__ == "__main__":
    main()
