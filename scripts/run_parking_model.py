"""Wisconsin parking scenario: central 0; high end from the placebo test (AQ-046, AQ-048; owner option B, 2026-10-27).

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


def v6_resample_high() -> float:
    """95th percentile of 2,000 resamples of the V6 places (docs/parking/IMPROVE_R1_RESULTS.md)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import run_parking_expanded as rpe
    g = pd.read_csv(REFERENCE / "parking_improve_r1_places.csv")
    g = g[g["variant"].str.startswith("V6 ")].dropna(subset=["effect"]).reset_index(drop=True)
    return rpe.boot_mean(g["effect"].values, g["weight"].values)[2]


def main() -> None:
    areas = pd.read_parquet(PROCESSED / "foundation" / "areas.parquet")
    munis = areas[areas["level"] == "municipality"][
        ["area_id", "name", "parent_county_id", "muni_type", "context_group", "housing_units_acs", "population", "metro_county", "land_area_sqm"]
    ].rename(columns={"parent_county_id": "county_id", "housing_units_acs": "homes", "context_group": "context"})
    munis["land_acres"] = munis.pop("land_area_sqm") / 4046.8564224
    cnames = areas[areas["level"] == "county"].set_index("area_id")["name"]
    munis["county_name"] = munis["county_id"].map(cnames)
    bench = benchmark_places(munis)
    bench.to_csv(REFERENCE / "parking_wi_benchmark_places.csv", index=False)
    at = set(bench.loc[bench["benchmark_rating"] == "at", "area_id"])
    near = set(bench.loc[bench["benchmark_rating"] == "near", "area_id"])

    # rates: the expanded 71-place comparison (owner, 2026-10-27: option A); the first 24-place estimate is a sensitivity
    xe = pd.read_csv(REFERENCE / "parking_expanded_estimates.csv").set_index("case")
    upper_resample = float(xe.loc["Expanded, all units (headline candidate)", "p95"])
    # owner option B (2026-10-27): the high end is the placebo-based range (spread of 500 placebo averages, centred
    # on the real average); the resampling high end is kept as a sensitivity
    upper_all = float(pd.read_csv(REFERENCE / "parking_placebo_full_summary.csv")["range_from_placebo_high"].iloc[0])
    if not np.isfinite(upper_all):  # flag, do not stop (owner 2026-10-28); a blank high end must never reach the tool as 0
        print("=== CHECKS === placebo high end is blank; falling back to the resampling high end")
        upper_all = upper_resample
    upper_apts = float(xe.loc["Expanded, units in buildings of 2+ units", "p95"])
    upper_no_sf = float(xe.loc["Expanded, without San Francisco", "p95"])
    upper_ca = float(xe.loc["Expanded US and California, precision-weighted (sensitivity)", "p95"])
    est = pd.read_csv(REFERENCE / "parking_comparison_estimates.csv")
    m0 = est[(est["model"] == "M0 one average") & (est["term"] == "intercept")].set_index("outcome")
    upper_first24 = float(m0.loc["all", "p95"])
    m4 = est[(est["outcome"] == "all") & est["model"].str.startswith("M4")].set_index("term")["estimate"]
    beta = (m4["intercept"], m4["log_pop"], m4["metro"])

    homes = pm.eligible_homes(munis, at)
    upper = pm.additions(homes, upper_all)
    # owner 2026-11-01: no logical floor at 0; the low line is the measured average of the 76 repeal places against
    # similar places (the same comparison as the high end), applied unfloored
    lower_all = float(pd.read_csv(REFERENCE / "parking_placebo_full_summary.csv")["real_average"].iloc[0])
    lower_total = float(pm.additions(homes, lower_all, floor=False).values.sum())
    # spread (audit, 2026-11-01): a reduction cuts what would have been built, so the statewide total is shared in
    # proportion to each eligible place's current-law permits, not its existing homes; no place can go below zero
    bl = pd.read_csv(REFERENCE / "housing_baseline_by_area.csv")
    bl = bl[bl["area_id"] != "unallocated"].groupby("area_id")["annual_central"].sum().reindex(homes.index).fillna(0.0)
    bl = bl.where(homes > 0, 0.0)
    lower = pd.DataFrame({y: lower_total / len(pm.FORECAST_YEARS) * bl / bl.sum() for y in pm.FORECAST_YEARS})
    lower.index.name = "area_id"
    base = pd.read_csv(REFERENCE / "housing_baseline_by_area.csv")
    base = base[base["area_id"] != "unallocated"].groupby("area_id")[["five_year_low", "five_year_central", "five_year_high"]].sum()

    ba = munis.set_index("area_id").join(base.add_prefix("baseline_"))
    ba["at_benchmark"] = ba.index.isin(at)
    ba["near_benchmark"] = ba.index.isin(near)
    ba["eligible_homes"] = homes
    ba["addition_central_five_year"] = 0.0
    ba["addition_lower_per_year"] = lower[pm.FORECAST_YEARS[0]]
    ba["addition_lower_five_year"] = lower.sum(axis=1)
    ba["addition_upper_per_year"] = upper[pm.FORECAST_YEARS[0]]
    ba["addition_upper_five_year"] = upper.sum(axis=1)
    ba = ba.reset_index()
    ba.round(3).to_csv(REFERENCE / "parking_model_by_area.csv", index=False)

    # statewide by year
    sw = pd.read_csv(REFERENCE / "housing_baseline_statewide_by_year.csv")
    sw = sw[(sw["structure_type"] == "all") & (sw["kind"].isin(["projected", "projected_bridge_year"]))][
        ["year", "low", "central", "high"]].rename(columns=lambda c: c if c == "year" else f"baseline_{c}")
    sw["addition_central"] = 0.0
    sw["addition_lower"] = [float(lower[y].sum()) if y in pm.FORECAST_YEARS else 0.0 for y in sw["year"]]
    sw["addition_upper"] = [float(upper[y].sum()) if y in pm.FORECAST_YEARS else 0.0 for y in sw["year"]]
    sw["lower_rate_per_1000_homes"] = round(lower_all, 2)
    sw["upper_rate_per_1000_homes"] = upper_all
    sw = sw.round(3)
    sw["upper_rate_per_1000_homes"] = round(upper_all, 2)
    sw.to_csv(REFERENCE / "parking_model_statewide_by_year.csv", index=False)

    # by county and district (upper case; central is 0 everywhere)
    ba.groupby(["county_id", "county_name"])[["eligible_homes", "land_acres", "baseline_five_year_central", "addition_upper_five_year"]].sum().round(1) \
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
             description=f"High end from the control-city (placebo) test: the spread of 20,000 placebo studies of cities that never repealed, centred on the real average, {upper_all:.2f} permits per 1,000 existing homes per year."),
        dict(case="Low end (headline)", moves="statewide addition", value=float(lower.values.sum()),
             description=f"Low end: the measured average of the 76 repeal places against similar places, {lower_all:.2f} permits per 1,000 existing homes per year, applied without a floor at zero (owner, 2026-11-01). Mostly San Francisco and Minneapolis; the typical repeal place changed by about 0."),
        dict(case="Resampling the real places (earlier high end)", moves="statewide addition", value=tot(homes, upper_resample),
             description=f"The earlier high end: 95th percentile of the average from 2,000 resamples of the 76 places, {upper_resample:.2f} per 1,000 existing homes per year."),
        dict(case="Cleaned data, undated reforms kept as comparisons (placebo)", moves="statewide addition",
             value=tot(homes, float(pd.read_csv(REFERENCE / "parking_placebo_full_v6u_summary.csv")["range_from_placebo_high"].iloc[0])),
             description="High end after round-1 data fixes (estimated permit months scaled, comparison places with dated parking reforms left out, pre-repeal homes), from the placebo test. One big city fell 1 short of 20 look-alikes, so by the rule set in advance it does not replace the headline."),
        dict(case="Cleaned data, strict comparison cleaning (resampling)", moves="statewide addition",
             value=tot(homes, v6_resample_high()),
             description="High end after round-1 data fixes, with every comparison city that has any recorded parking reform left out, from resampling the 73 repeal places. Shown as a sensitivity: switching to this method after seeing results is not allowed."),
        dict(case="Cleaned data, strict comparison cleaning (placebo)", moves="statewide addition",
             value=tot(homes, float(pd.read_csv(REFERENCE / "parking_placebo_full_v6_summary.csv")["range_from_placebo_high"].iloc[0])),
             description="As above, from the placebo test. Big repeal cities are left with 3 to 18 look-alikes, so this figure is noisy. All the cleaned-data high ends are above the headline 19,937, so the headline high end is the lowest and may be understated; the high end is uncertain by about 2x."),
        dict(case="Cleaned data, only apartment-scale reforms disqualify comparisons (placebo)", moves="statewide addition",
             value=tot(homes, float(pd.read_csv(REFERENCE / "parking_placebo_full_v7_summary.csv")["range_from_placebo_high"].iloc[0])),
             description="Round 2: a comparison city is left out only if it removed parking minimums for apartments or all housing (reference/parking_reform_material.csv). San Jose and Austin fell 1 to 2 short of 20 look-alikes, so by the rule set in advance it does not replace the headline."),
        dict(case="As above, plus state laws in California, Oregon and Washington (placebo)", moves="statewide addition",
             value=tot(homes, float(pd.read_csv(REFERENCE / "parking_placebo_full_v7s_summary.csv")["range_from_placebo_high"].iloc[0])),
             description="Round 2 with every city in California and Oregon treated as reformed from 2023, and Washington from 2024. San Jose and Austin fell 2 to 3 short of 20 look-alikes, so it does not replace the headline. All five cleaned-data high ends are above the headline."),
        dict(case="Buildings of 2 or more units only", moves="statewide addition", value=tot(homes, upper_apts),
             description=f"Resampling high end when only units in buildings of 2 or more units are counted, {upper_apts:.2f} per 1,000 existing homes per year."),
        dict(case="Without San Francisco", moves="statewide addition", value=tot(homes, upper_no_sf),
             description=f"Resampling high end when San Francisco is left out, {upper_no_sf:.2f} per 1,000 existing homes per year."),
        dict(case="Combined with California's transit-area law", moves="statewide addition", value=tot(homes, upper_ca),
             description=f"High end when the 76 US places are combined with 185 California cities under AB 2097, {upper_ca:.2f} per 1,000 existing homes per year."),
        dict(case="First 24 places only (earlier estimate)", moves="statewide addition", value=tot(homes, upper_first24),
             description=f"The high end from the first, smaller comparison of 24 places, {upper_first24:.2f} per 1,000 existing homes per year."),
        dict(case="Size and metro model (central)", moves="statewide addition and where it lands",
             value=tot(homes, pm.size_metro_rate(munis.set_index("area_id")["population"], munis.set_index("area_id")["metro_county"], beta)),
             description="Each place gets its own rate from a model using city size and whether it is in a metro area (never below zero). It favours small places in metro areas. It predicted slightly better than one average for all places, but not reliably so."),
        dict(case="Towns at zero", moves="statewide addition and where it lands", value=tot(pm.eligible_homes(munis, at, ("town",)), upper_all),
             description="The high end, with towns left out, in case most towns have few or no parking minimums today."),
        dict(case="Near-benchmark places at zero", moves="statewide addition and where it lands",
             value=tot(pm.eligible_homes(munis, at | near), upper_all),
             description="The high end, with the 9 places that removed minimums with conditions also getting nothing."),
    ]
    pub = REFERENCE / "housing_baseline_sensitivity_published.csv"
    if pub.exists():
        p = pd.read_csv(pub).set_index("structure_type")
        sens.append(dict(case="Baseline: Census as published for Milwaukee", moves="baseline only",
                         value=float(p.loc["all", "central"]),
                         description="Baseline over 2027-2031 without the Milwaukee apartment adjustment (the parking addition does not change)."))
    nr = REFERENCE / "parking_no_reform_wisconsin_r6.csv"
    if nr.exists():  # no-reform model, boosted trees (docs/parking/NO_REFORM_MODEL_RESULTS.md); owner approved 2026-10-31
        w = pd.read_csv(nr).set_index(["origin", "model"])
        ratio = float(w.loc[(2025, "M4 boosted trees"), "vs_M0"])
        central = float(pd.read_csv(REFERENCE / "housing_baseline_statewide_by_year.csv").query(
            "structure_type == 'all' and kind == 'projected' and 2027 <= year <= 2031")["central"].sum())
        sens.append(dict(case="Baseline: boosted-trees no-reform model", moves="baseline only", value=ratio * central,
                         description=f"Baseline over 2027-2031 from a model trained on places with no parking reform nationwide, {ratio:.2f} times the same-pace baseline. "
                                     "In held-out tests no model beat same pace: on single cities same pace is as good as any, and on state totals the tree models only match same pace with a national level adjustment. Same pace ran 17-23% low in 2020-2025. "
                                     "The parking addition does not change."))
    bm = REFERENCE / "parking_baseline_models_wisconsin_r4.csv"
    if bm.exists():  # owner, 2026-10-31: follow the audit - central stays same pace; side line "if recent strength continues"
        cen = float(pd.read_csv(REFERENCE / "housing_baseline_statewide_by_year.csv").query(
            "structure_type == 'all' and kind == 'projected' and 2027 <= year <= 2031")["central"].sum())
        w = pd.read_csv(bm).query("origin == 2025").set_index("model")["vs_M0"] * cen  # scaled to the current central
        sens.append(dict(case="Baseline: if recent strength continues", moves="baseline only", value=float(w["Random forest"]),
                         description=f"Baseline over 2027-2031 if 2020-2025's strength continues: {w['Random forest']:,.0f} (random forest, scikit-learn; "
                                     "owner 2026-11-02: no dependency on the removed econml package; its honest forest gave a similar figure), and up to {w['M0L same pace x level']:,.0f} if every place keeps 2020-2025's full "
                                     "level over its earlier pace. In Wisconsin's own 2021-2025 back-test, same pace came in at 0.77 of actual, the forests at 0.95 "
                                     "and the full-level version at 1.01. The parking addition does not change (docs/parking/BASELINE_MODELS_RESULTS.md)."))
    pd.DataFrame(sens).round(1).to_csv(REFERENCE / "parking_model_sensitivities.csv", index=False)

    print(f"eligible homes {homes.sum():,.0f}; places at benchmark {len(at)}, near {len(near)}")
    print(pd.DataFrame(sens)[["case", "value"]].round(0).to_string(index=False))
    print(sw.round(0).to_string(index=False))


if __name__ == "__main__":
    main()
