"""Build the all-housing baseline (shared by the parking and TOD scenarios).

    uv run python scripts/build_housing_baseline.py

Inputs (from the foundation build, scripts/build_foundation.py; git-ignored):
    data/processed/foundation/bps_place_annual.parquet, bps_muni_crosswalk.parquet,
    bps_county_unincorporated_allocation.parquet, areas.parquet
    data/raw/census_bps_state/st<year>a.txt (published state totals)
Outputs (committed):
    reference/housing_baseline_history.csv          area x year, units by structure type, 2015-2025
    reference/housing_baseline_by_area.csv          area x structure type: projection 2027-2031
    reference/housing_baseline_by_county.csv        county x structure type: same, summed
    reference/housing_baseline_statewide_by_year.csv state x year x type, observed and projected
    reference/housing_baseline_reconciliation.csv   year x type: state, allocated, unallocated
    reference/housing_baseline_holdout.csv          held-out-year test, every origin/window/type
    reference/housing_baseline_window_choice.csv    the test summary and the chosen candidate
    reference/housing_baseline_band.csv             low/high multipliers by structure type (long run)
    reference/housing_baseline_band_recent.csv      the recent-decade held-out band (sensitivity)
    reference/housing_baseline_milwaukee_check.csv  Milwaukee BPS vs city property file (check)
    reference/housing_baseline_long_run_ratios.csv  1990-2025 five-year outcomes vs flat mean
Documented in docs/shared/HOUSING_BASELINE.md.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware import housing_baseline as hb  # noqa: E402
from missing_middleware.foundation import parsers  # noqa: E402
from missing_middleware.foundation.build import KNOWN_BPS_GAPS  # noqa: E402
from missing_middleware.paths import PROCESSED, RAW, REFERENCE  # noqa: E402

F = PROCESSED / "foundation"
MILWAUKEE_AREA = "muni:5507953000"
LONG_RUN_YEARS = tuple(range(1990, 2026))   # state files used only for the long-run band
BPS_STATE_URL = "https://www2.census.gov/econ/bps/State/st{y}a.txt"


def fetch_long_run_state(force: bool = False) -> None:
    """Download the published state annual files 1990-2014 (2015-2025 come from the
    foundation build) into data/raw/census_bps_state, recording URL, date, bytes, SHA-256."""
    import datetime as dt
    import hashlib
    import json
    import urllib.request
    d = RAW / "census_bps_state"
    d.mkdir(parents=True, exist_ok=True)
    log_path = d / "_downloads.json"
    log = json.loads(log_path.read_text()) if log_path.exists() else {}
    for y in LONG_RUN_YEARS:
        f = d / f"st{y}a.txt"
        if f.exists() and not force:
            continue
        url = BPS_STATE_URL.format(y=y)
        req = urllib.request.Request(url, headers={"User-Agent": "missing-middleware research (public records)"})
        data = urllib.request.urlopen(req, timeout=60).read()
        f.write_bytes(data)
        log[f.name] = {"accessed": dt.date.today().isoformat(), "bytes": len(data),
                       "sha256": hashlib.sha256(data).hexdigest(), "url": url}
    log_path.write_text(json.dumps(dict(sorted(log.items())), indent=2) + "\n")


def read_state_long_run() -> pd.DataFrame:
    """Wisconsin state totals by year and structure type, 1990-2025 (year from the file name,
    since 1990s files use a two-digit survey date)."""
    rows = []
    for y in LONG_RUN_YEARS:
        df = parsers.read_bps(RAW / "census_bps_state" / f"st{y}a.txt", "state")
        for t, c in hb.BPS_UNIT_COLS.items():
            rows.append(dict(year=y, structure_type=t, units=float(df[c].sum())))
    return pd.DataFrame(rows)


def milwaukee_check(hist: pd.DataFrame) -> pd.DataFrame | None:
    """Milwaukee city: BPS permitted units vs units in buildings by year built from the city's
    Master Property file (MPROP; only YR_BUILT and NR_UNITS are read). Year built is a
    completion-side measure, so it lags permits by about one to two years; this is a check
    of the BPS series, not a replacement."""
    f = RAW / "milwaukee_mprop" / "mprop.csv"
    if not f.exists():
        return None
    m = pd.read_csv(f, usecols=["YR_BUILT", "NR_UNITS"], low_memory=False)
    m = m.apply(pd.to_numeric, errors="coerce").dropna()
    m = m[(m["YR_BUILT"] >= 2015) & (m["YR_BUILT"] <= 2025) & (m["NR_UNITS"] > 0)]
    m["structure_type"] = pd.cut(m["NR_UNITS"], [0, 1, 2, 4, 1e9], labels=list(hb.TYPES)).astype(str)
    mp = m.groupby(["YR_BUILT", "structure_type"])["NR_UNITS"].sum().rename("mprop_units_by_year_built")
    mp.index = mp.index.set_names(["year", "structure_type"])
    b = hist[hist["area_id"] == MILWAUKEE_AREA].groupby(["year", "structure_type"])["units"].sum(min_count=1)
    out = pd.concat([b.rename("bps_permitted_units"), mp], axis=1).reset_index()
    out["year"] = out["year"].astype(int)
    out["mprop_units_by_year_built"] = out["mprop_units_by_year_built"].fillna(0.0)
    return out.sort_values(["structure_type", "year"])


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true", help="download the 1990-2014 state files if missing")
    args = ap.parse_args()
    if args.fetch or not (RAW / "census_bps_state" / "st1990a.txt").exists():
        fetch_long_run_state()
    bps = pd.read_parquet(F / "bps_place_annual.parquet")
    xw = pd.read_parquet(F / "bps_muni_crosswalk.parquet")
    alloc = pd.read_parquet(F / "bps_county_unincorporated_allocation.parquet")
    areas = pd.read_parquet(F / "areas.parquet")
    st = pd.concat([parsers.read_bps(RAW / "census_bps_state" / f"st{y}a.txt", "state") for y in hb.HISTORY_YEARS])
    state = pd.concat([pd.DataFrame({"year": st["year"], "structure_type": t, "units": st[c].astype(float)})
                       for t, c in hb.BPS_UNIT_COLS.items()], ignore_index=True)

    long = hb.long_bps(bps, KNOWN_BPS_GAPS)
    by_area = hb.reconcile(hb.allocate(long, xw, alloc), state)
    hist = hb.area_year_type(by_area)

    # every municipality piece appears, even with no BPS row (zero only if covered: no -> null)
    munis = areas[areas["level"] == "municipality"][
        ["area_id", "name", "parent_county_id", "muni_type", "context_group", "housing_units_acs"]]
    ids = pd.concat([munis["area_id"], pd.Series([hb.UNALLOCATED])], ignore_index=True)
    grid = pd.MultiIndex.from_product([ids, hb.HISTORY_YEARS, hb.TYPES],
                                      names=["area_id", "year", "structure_type"]).to_frame(index=False)
    hist = grid.merge(hist, on=["area_id", "year", "structure_type"], how="left")
    hist["allocation"] = hist["allocation"].fillna("no_bps_row")

    # reconciliation table
    rec = state.rename(columns={"units": "state_published"}).merge(
        hist[hist["area_id"] != hb.UNALLOCATED].groupby(["year", "structure_type"])["units"].sum().rename("allocated_to_areas"),
        on=["year", "structure_type"]).merge(
        hist[hist["area_id"] == hb.UNALLOCATED][["year", "structure_type", "units"]].rename(columns={"units": "unallocated"}),
        on=["year", "structure_type"])
    rec["check_sum"] = rec["allocated_to_areas"] + rec["unallocated"]
    gap_years = sorted({y for (_, y) in KNOWN_BPS_GAPS})
    rec["note"] = ["state total contains Milwaukee city's unreported (zero) series" if (y in gap_years and t in hb.GAP_TYPES) else ""
                   for y, t in zip(rec["year"], rec["structure_type"])]

    # held-out test, window choice, band, projection
    scores = hb.holdout_scores(hist)
    best, summ = hb.choose(scores)
    recent_band = hb.band(scores, best)
    _, k_best, trend_best = next(c for c in hb.CANDIDATES if c[0] == best)
    if trend_best is not None:
        raise SystemExit(f"{best} is a trend candidate; the long-run band is defined for flat means only")
    lr = hb.state_long_run_ratios(read_state_long_run(), k_best)
    bands = hb.long_run_band(lr)
    proj = hb.project(hist, best, bands[bands["structure_type"] != "all"])

    # outputs
    REFERENCE.mkdir(exist_ok=True)
    meta = munis.rename(columns={"parent_county_id": "county_id", "context_group": "context"})
    meta = pd.concat([meta, pd.DataFrame([{"area_id": hb.UNALLOCATED, "name": "Unallocated (reconciles to state)"}])],
                     ignore_index=True)

    wide = hist.pivot_table(index=["area_id", "year"], columns="structure_type", values="units", dropna=False,
                            aggfunc="first").reset_index()
    wide.columns.name = None
    wide = wide.rename(columns={t: f"units_{t}" for t in hb.TYPES})
    unit_cols = [f"units_{t}" for t in hb.TYPES]
    wide["units_all"] = wide[unit_cols].sum(axis=1, min_count=len(hb.TYPES))
    kinds = hist.groupby(["area_id", "year"])["allocation"].agg(lambda s: ";".join(sorted(set(";".join(s).split(";"))))).reset_index()
    wide = wide.merge(kinds, on=["area_id", "year"]).merge(meta[["area_id", "name", "county_id"]], on="area_id", how="left")
    wide = wide[["area_id", "name", "county_id", "year"] + unit_cols + ["units_all", "allocation"]]
    wide.round(3).sort_values(["area_id", "year"]).to_csv(REFERENCE / "housing_baseline_history.csv", index=False)

    five = proj[proj["in_five_year_total"]].groupby(["area_id", "structure_type"])[["low", "central", "high"]].sum()
    annual = proj[proj["year"] == hb.FORECAST_YEARS[0]].set_index(["area_id", "structure_type"])
    ba = annual[["method", "window_years", "no_data_in_window"]].join(
        annual[["low", "central", "high"]].add_prefix("annual_")).join(five.add_prefix("five_year_")).reset_index()
    ba = meta.merge(ba, on="area_id", how="right")
    ba = ba[["area_id", "name", "county_id", "muni_type", "context", "housing_units_acs", "structure_type",
             "method", "window_years", "no_data_in_window", "annual_low", "annual_central", "annual_high",
             "five_year_low", "five_year_central", "five_year_high"]]
    ba.round(3).sort_values(["area_id", "structure_type"]).to_csv(REFERENCE / "housing_baseline_by_area.csv", index=False)

    bc = ba[ba["area_id"] != hb.UNALLOCATED].groupby(["county_id", "structure_type"])[
        ["annual_low", "annual_central", "annual_high", "five_year_low", "five_year_central", "five_year_high"]].sum().reset_index()
    bc.round(3).to_csv(REFERENCE / "housing_baseline_by_county.csv", index=False)

    obs = state.rename(columns={"units": "central"}).assign(kind="observed_published_state_total")
    obs["low"] = obs["central"]
    obs["high"] = obs["central"]
    p = proj.groupby(["year", "structure_type"])[["low", "central", "high"]].sum().reset_index()
    p["kind"] = ["projected_bridge_year" if y == hb.BRIDGE_YEAR else "projected" for y in p["year"]]
    sw = pd.concat([obs, p], ignore_index=True)[["year", "structure_type", "kind", "low", "central", "high"]]
    allt = sw.groupby(["year", "kind"])[["low", "central", "high"]].sum().reset_index().assign(structure_type="all")
    sw = pd.concat([sw, allt], ignore_index=True).sort_values(["year", "structure_type"])
    sw.round(1).to_csv(REFERENCE / "housing_baseline_statewide_by_year.csv", index=False)

    rec.round(3).to_csv(REFERENCE / "housing_baseline_reconciliation.csv", index=False)
    scores.round(4).to_csv(REFERENCE / "housing_baseline_holdout.csv", index=False)
    summ.round(4).to_csv(REFERENCE / "housing_baseline_window_choice.csv", index=False)
    bands.assign(candidate=best, basis="long-run 1990-2025 state totals, 10th-90th percentile of five-year outcomes").round(4).to_csv(
        REFERENCE / "housing_baseline_band.csv", index=False)
    recent_band.assign(candidate=best, basis="held-out years 2019-2022 origins, min-max (sensitivity)").round(4).to_csv(
        REFERENCE / "housing_baseline_band_recent.csv", index=False)
    mk = milwaukee_check(hist)
    if mk is not None:
        mk.to_csv(REFERENCE / "housing_baseline_milwaukee_check.csv", index=False)
    lr.round(4).to_csv(REFERENCE / "housing_baseline_long_run_ratios.csv", index=False)

    tot = sw[(sw["structure_type"] == "all") & sw["year"].isin(hb.FORECAST_YEARS)][["low", "central", "high"]].sum()
    print(f"chosen: {best}; five-year 2027-2031 all units: "
          f"low {tot['low']:.0f}, central {tot['central']:.0f}, high {tot['high']:.0f}")
    print(summ.to_string(index=False))
    print(bands.to_string(index=False))


if __name__ == "__main__":
    main()
