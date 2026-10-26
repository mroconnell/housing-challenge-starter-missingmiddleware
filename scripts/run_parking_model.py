"""Wisconsin parking scenario under option A (AQ-046, AQ-048).

    uv run python scripts/run_parking_model.py

Inputs: data/processed/foundation/areas.parquet (ACS homes and population per municipality piece),
reference/housing_baseline_by_area.csv and _statewide_by_year.csv (shared baseline),
reference/parking_reform_cases.csv (Wisconsin places already at the benchmark),
reference/parking_comparison_estimates.csv and _robustness.csv (rates),
reference/adu_model_district_crosswalk.csv (Assembly and Senate districts).
Outputs: reference/parking_model_*.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware.parking import model as pm  # noqa: E402
from missing_middleware.paths import PROCESSED, REFERENCE  # noqa: E402

TYPE_SUFFIX = r" (city|village|town)$"


def benchmark_places(munis: pd.DataFrame) -> pd.DataFrame:
    """Wisconsin municipality pieces already at (or near) the benchmark, from the PRN-based
    classification, matched by name to cities and villages (never towns)."""
    c = pd.read_csv(REFERENCE / "parking_reform_cases.csv")
    c = c[(c["state"] == "Wisconsin") & (c["status"] == "adopted")].drop_duplicates(["place", "benchmark_rating"])
    m = munis[munis["muni_type"] != "town"].copy()
    m["base"] = m["name"].str.replace(TYPE_SUFFIX, "", regex=True)
    rows = []
    for r in c.itertuples():
        place = r.place.replace(" (City)", "")
        want_type = "city" if "(City)" in r.place else None
        hit = m[(m["base"] == place) & ((m["muni_type"] == want_type) if want_type else True)]
        for h in hit.itertuples():
            rows.append(dict(area_id=h.area_id, name=h.name, prn_place=r.place, benchmark_rating=r.benchmark_rating,
                             adopted_date=r.adopted_date, rating_reason=r.rating_reason))
    return pd.DataFrame(rows).drop_duplicates(["area_id", "benchmark_rating"])


def main() -> None:
    areas = pd.read_parquet(PROCESSED / "foundation" / "areas.parquet")
    munis = areas[areas["level"] == "municipality"][
        ["area_id", "name", "parent_county_id", "muni_type", "context_group", "housing_units_acs", "population", "metro_county"]
    ].rename(columns={"parent_county_id": "county_id", "housing_units_acs": "homes", "context_group": "context"})
    bench = benchmark_places(munis)
    bench.to_csv(REFERENCE / "parking_wi_benchmark_places.csv", index=False)
    at = set(bench.loc[bench["benchmark_rating"] == "at", "area_id"])
    near = set(bench.loc[bench["benchmark_rating"] == "near", "area_id"])

    est = pd.read_csv(REFERENCE / "parking_comparison_estimates.csv")
    rob = pd.read_csv(REFERENCE / "parking_comparison_robustness.csv")
    m0 = est[(est["model"] == "M0 one average") & (est["term"] == "intercept")].set_index("outcome")
    upper_all = float(m0.loc["all", "p95"])
    upper_apts = float(m0.loc["2plus", "p95"])
    upper_no_sf = float(rob[(rob["outcome"] == "all") & (rob["check"] == "without San Francisco")]["p95"].iloc[0])
    m4 = est[(est["outcome"] == "all") & est["model"].str.startswith("M4")].set_index("term")["estimate"]
    beta = (m4["intercept"], m4["log_pop"], m4["metro"])

    homes = pm.eligible_homes(munis, at)
    upper = pm.additions(homes, upper_all)
    base = pd.read_csv(REFERENCE / "housing_baseline_by_area.csv")
    base = base[base["area_id"] != "unallocated"].groupby("area_id")[["five_year_low", "five_year_central", "five_year_high"]].sum()

    ba = munis.set_index("area_id").join(base.add_prefix("baseline_"))
    ba["at_benchmark"] = ba.index.isin(at)
    ba["near_benchmark"] = ba.index.isin(near)
    ba["eligible_homes"] = homes
    ba["addition_central_five_year"] = 0.0
    ba["addition_upper_per_year"] = upper[pm.FORECAST_YEARS[0]]
    ba["addition_upper_five_year"] = upper.sum(axis=1)
    ba = ba.reset_index()
    ba.round(3).to_csv(REFERENCE / "parking_model_by_area.csv", index=False)

    # statewide by year
    sw = pd.read_csv(REFERENCE / "housing_baseline_statewide_by_year.csv")
    sw = sw[(sw["structure_type"] == "all") & (sw["kind"].isin(["projected", "projected_bridge_year"]))][
        ["year", "low", "central", "high"]].rename(columns=lambda c: c if c == "year" else f"baseline_{c}")
    sw["addition_central"] = 0.0
    sw["addition_upper"] = [float(upper[y].sum()) if y in pm.FORECAST_YEARS else 0.0 for y in sw["year"]]
    sw["upper_rate_per_1000_homes"] = upper_all
    sw = sw.round(1)
    sw["upper_rate_per_1000_homes"] = round(upper_all, 2)
    sw.to_csv(REFERENCE / "parking_model_statewide_by_year.csv", index=False)

    # by county and district (upper case; central is 0 everywhere)
    ba.groupby("county_id")[["eligible_homes", "baseline_five_year_central", "addition_upper_five_year"]].sum().round(1) \
        .to_csv(REFERENCE / "parking_model_by_county.csv")
    xw = pd.read_csv(REFERENCE / "adu_model_district_crosswalk.csv")
    for col, out in (("assembly_district", "assembly"), ("senate_district", "senate")):
        d = xw.merge(ba[["area_id", "eligible_homes", "baseline_five_year_central", "addition_upper_five_year"]], on="area_id")
        for v in ("eligible_homes", "baseline_five_year_central", "addition_upper_five_year"):
            d[v] = d[v] * d["share"]
        d.groupby(col)[["eligible_homes", "baseline_five_year_central", "addition_upper_five_year"]].sum().round(1) \
            .to_csv(REFERENCE / f"parking_model_by_{out}_district.csv")

    # sensitivities (five-year totals, 2027-2031)
    tot = lambda h, r: float(pm.additions(h, r).values.sum())  # noqa: E731
    sens = [
        dict(case="Upper case (headline)", moves="statewide addition", value=tot(homes, upper_all),
             description=f"High end of the likely range for all units, {upper_all:.2f} permits per 1,000 existing homes per year."),
        dict(case="Apartments only", moves="statewide addition", value=tot(homes, upper_apts),
             description=f"High end of the likely range for units in buildings of 2+ units only, {upper_apts:.2f} per 1,000 homes per year."),
        dict(case="Without San Francisco", moves="statewide addition", value=tot(homes, upper_no_sf),
             description=f"High end of the likely range when San Francisco (a quarter of the weight) is left out, {upper_no_sf:.2f} per 1,000 homes per year."),
        dict(case="Size and metro model (central)", moves="statewide addition and where it lands",
             value=tot(homes, pm.size_metro_rate(munis.set_index("area_id")["population"], munis.set_index("area_id")["metro_county"], beta)),
             description="The size-and-metro model's own prediction for each place, floored at zero. It predicted slightly better than one average, but its terms are not distinguishable from zero."),
        dict(case="Towns at zero", moves="statewide addition and where it lands", value=tot(pm.eligible_homes(munis, at, ("town",)), upper_all),
             description="Upper case with towns left out, for the case where most towns have few or no parking minimums today."),
        dict(case="Near-benchmark places at zero", moves="statewide addition and where it lands",
             value=tot(pm.eligible_homes(munis, at | near), upper_all),
             description="Upper case with the 9 places that nearly meet the benchmark also getting nothing."),
    ]
    pub = REFERENCE / "housing_baseline_sensitivity_published.csv"
    if pub.exists():
        p = pd.read_csv(pub).set_index("structure_type")
        sens.append(dict(case="Baseline: Census as published for Milwaukee", moves="baseline only",
                         value=float(p.loc["all", "central"]),
                         description="Baseline over 2027-2031 without the Milwaukee apartment adjustment (the parking addition does not change)."))
    pd.DataFrame(sens).round(1).to_csv(REFERENCE / "parking_model_sensitivities.csv", index=False)

    print(f"eligible homes {homes.sum():,.0f}; places at benchmark {len(at)}, near {len(near)}")
    print(pd.DataFrame(sens)[["case", "value"]].round(0).to_string(index=False))
    print(sw.round(0).to_string(index=False))


if __name__ == "__main__":
    main()
