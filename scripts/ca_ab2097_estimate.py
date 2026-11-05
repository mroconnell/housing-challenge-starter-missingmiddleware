"""CA AB 2097 study: build the areas and permit tables, and compute every estimate in the locked plan.

Plan: docs/parking/CA_AB2097_PLAN.md (locked 2026-11-05 16:48 UTC; section 8 and the section 9 changes after lock).
This script must be committed and checked by the audit BEFORE it is run; its first run is the first time permits are
counted by area for this study.

    uv run python scripts/ca_ab2097_estimate.py --build     # areas and permit tables (git-ignored cache)
    uv run python scripts/ca_ab2097_estimate.py --estimate  # all estimates -> reference/ca_ab2097_results*.csv

What it computes (units: homes in issued building permits per 1,000 existing homes (2020 census) per year, unless a
row says per acre; ranges are 90%, 2,000 resamples of whole jurisdictions, seed 20261105, unless a row says otherwise)

Maps (stop sets; distances straight-line from stop points, EPSG:3310)
- main: dated end-2022 rail, ferry and Amtrak stops (reference/ca_ab2097_rail_stations.csv) + today's Caltrans
  existing bus and BRT major stops (labelled "later map, 20-minute rule") + planned stops from SCAG's 2020 plan
  (Connect SoCal 2020, 2045 plan year, not within 150 m of a 2016 existing stop). Other regions' 2022-era planned
  stops are not mapped (listed in the output).
- rail_only: dated end-2022 rail stops only. no_planned: main without planned stops. no_new_stations: main without
  rail stops opened 2018-2022 (and with blocks/permits nearest to them left out).
Zones: near (< 1/2 mile), ring (1/2 to 1 1/2 miles), beyond (>= 1 1/2 miles); bands 0-1/3, 1/3-1/2, 1/2-2/3 mile,
  with the 1-1 1/2 mile ring as their comparison; edge = 1/3-1/2 vs 1/2-2/3 mile with a 25 m donut each side.
Groups: main = full reporters (geocoded permits every year 2018-2025) less the placebo places and Mountain View;
  placebo = the 14 places that already had no minimums or repealed citywide (ab2097.ALREADY_NO_MINIMUMS +
  REPEALED_CITYWIDE_LATER). Los Angeles's 2017 TOC areas are left out of the main group's near and ring land.
Permits: Table A2, the earlier test's cleaning rules (issue-date dating, cross-report-year de-duplication), points =
  HCD street-level points plus accepted Census re-geocodes (main); HCD street-level only (check).
Outcomes: main = homes other than ADUs; also all homes, homes in 2+ unit buildings, ADU homes; secondary
  (descriptive only): density-bonus share of 5+ projects (A), homes in density-bonus projects (B), LIHTC share (C),
  homes in LIHTC projects (D), deed-restricted homes.
Estimates: headline (2023-2025 vs 2018-2022); year by year against 2022 (leads 2018-2021, lags 2023-2025); lead
  check (2018-2020 vs 2021-2022) and lead slope; placebo date (2018-2019 vs 2020-2022); anticipation (2023-2025 vs
  2018-2021); bands; edges (main map, rail-only map with other-stop land removed, Palo Alto with project resampling);
  checks (each map; street-level points only; report-year dating; entitlement-date dating; drop 2023; drop the largest
  project; drop Los Angeles; equal weight per jurisdiction; stable-geocode jurisdictions; per acre); minimum detectable
  effect = 1.645 x the standard deviation of the resampled estimates.
City-level (dose) check: Census BPS place permits (all units) per 1,000 existing homes a year, 2023-2025 minus
  2018-2022, regressed on the share of the place's 2020 homes within 1/2 mile on the main map, weighted by 2020
  homes (equal weight beside it), placebo places left out; lead placebo 2021-2022 minus 2018-2020; 90% range from
  2,000 resamples of places.
Labels carried with every result (audit): (1) the dose check uses BPS all units, which counts ADUs differently from
  Table A2, while the main point-based outcome excludes ADUs; (2) planned stops are mapped only for SCAG: elsewhere
  land near 2022-era planned stops counts as ring (land the law covers moved into the comparison), and the no_planned
  check shows only the SCAG part; (3) bus areas use today's Caltrans layer (20-minute rule, later map); (4) the
  synthetic tests (tests/test_ca_ab2097.py) were run with python directly because pytest is not installed in the venv.
Reading rules (plan): evidence only if leads are balanced, the placebo group's range includes 0 and the placebo date
  shows nothing; a statewide claim only if the city-level check agrees. Secondary outcomes are descriptive only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from missing_middleware.foundation import parsers  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
from missing_middleware.tod import ab2097 as ab  # noqa: E402
import run_ab2097_test as run  # noqa: E402

CACHE = RAW.parent / "processed" / "ca_ab2097"
MILE = ab.MILE_M
YEARS = list(range(2018, 2026))
BEFORE, AFTER = [2018, 2019, 2020, 2021, 2022], [2023, 2024, 2025]
DRAWS, SEED, LEVEL = 2000, 20261105, 0.90
PLACEBO = set(ab.ALREADY_NO_MINIMUMS) | set(ab.REPEALED_CITYWIDE_LATER)
DROPPED = {"MOUNTAIN VIEW"}
LIHTC_RE = r"(?i)tax credit|lihtc|\bctcac\b|\btcac\b|\bcdlac\b"
DR_COLS = ["BP_ACUTELY_LOW_INCOME_DR", "BP_EXTREMELY_LOW_INCOME_DR", "BP_VLOW_INCOME_DR", "BP_LOW_INCOME_DR",
           "BP_MOD_INCOME_DR"]
A2_COLS = ["JURIS_NAME", "YEAR", "UNIT_CAT", "NO_BUILDING_PERMITS", "LATITUDE", "LONGITUDE", "STD_ADDRESS",
           "STREET_ADDRESS", "BP_ISSUE_DT1", "ENT_APPROVE_DT1", "DENSITY_BONUS_TOTAL", "FIN_ASSIST_NAME"] + DR_COLS
OUTCOMES = ["homes_non_adu", "all_units", "units_2plus", "adu_units"]
SECONDARY = ["db_homes", "lihtc_homes", "lihtc_apartments", "dr_homes", "dr_low_and_below", "dr_moderate"]
SPECS = ["main", "rail_only", "no_planned", "no_new_stations"]
EXISTING = {"before 2018 (assumed: not in openings table)", "2018-2022", "closed or moved after 2022 (added back)"}


# =========================================================================== build

def stop_sets() -> dict[str, pd.DataFrame]:
    """Stop points (x, y in EPSG:3310) for each map."""
    from missing_middleware.geom_extra_station import nearest_lowest, read_vector
    st = pd.read_csv(REFERENCE / "ca_ab2097_rail_stations.csv")
    st = st[st.opened.isin(EXISTING)]
    rail = run.lonlat_points(st[st["mode"] != "ferry"].reset_index(drop=True), st[st["mode"] != "ferry"].lon,
                             st[st["mode"] != "ferry"].lat)
    ferry = run.lonlat_points(st[st["mode"] == "ferry"].reset_index(drop=True), st[st["mode"] == "ferry"].lon,
                              st[st["mode"] == "ferry"].lat)
    new_rail = rail[rail.opened == "2018-2022"]
    ct = read_vector(RAW / "ab2097" / "major_transit_stops.geojson", run.CRS)
    bus = ct[ct.hqta_type.isin(["major_stop_bus", "major_stop_brt"]) & (ct.plan_name.fillna("").str.strip() == "")]
    bus = bus[["x", "y"]].reset_index(drop=True)
    scag_p = read_vector(RAW / "parking_la_ab2097_map" / "scag_mts_2045_plan.geojson", run.CRS)
    scag_e = read_vector(RAW / "parking_la_ab2097_map" / "scag_mts_2016_existing.geojson", run.CRS)
    _, d = nearest_lowest(scag_p.x.to_numpy(float), scag_p.y.to_numpy(float),
                          scag_e.x.to_numpy(float), scag_e.y.to_numpy(float))
    planned = scag_p[d > 150.0][["x", "y"]].reset_index(drop=True)
    xy = lambda *fs: pd.concat([f[["x", "y"]] for f in fs], ignore_index=True)  # noqa: E731
    main = xy(rail, ferry, bus, planned)
    return {"main": main, "rail_only": xy(rail), "no_planned": xy(rail, ferry, bus),
            "no_new_stations": xy(rail[rail.opened != "2018-2022"], ferry, bus, planned),
            "_new_rail": xy(new_rail), "_other_than_rail": xy(ferry, bus, planned)}


def clean_permits_full(a2: pd.DataFrame) -> pd.DataFrame:
    """The earlier test's cleaning (ab2097.clean_permits) with the extra fields this study needs kept. Geocoding is
    applied later (HCD street-level points or accepted Census points), so rows are not dropped for it here."""
    d = a2.copy()
    d["geo_key"] = raw_keys(d)  # same row hash as scripts/ca_ab2097_regeocode.py, made before any row is dropped
    d["units"] = pd.to_numeric(d.NO_BUILDING_PERMITS, errors="coerce").fillna(0.0)
    d["report_year"] = d.YEAR
    bp = pd.to_datetime(d.BP_ISSUE_DT1, errors="coerce")
    d["bp_date"] = bp.dt.strftime("%Y-%m-%d").fillna("")
    d["year"] = bp.dt.year.fillna(d.YEAR).astype(int)
    d["ent_year"] = pd.to_datetime(d.ENT_APPROVE_DT1, errors="coerce").dt.year
    d = d[(d.units > 0) & d.year.isin(YEARS)].copy()
    d["addr"] = ab._norm(d.STREET_ADDRESS).where(ab._norm(d.STREET_ADDRESS) != "", ab._norm(d.STD_ADDRESS))
    d = d.sort_values("report_year", kind="stable").drop_duplicates(
        ["JURIS_NAME", "addr", "year", "UNIT_CAT", "units", "bp_date"])
    d["juris"] = d.JURIS_NAME.astype(str).str.upper().str.strip()
    d["project"] = ab.project_id(d.JURIS_NAME, d.STD_ADDRESS.fillna(d.STREET_ADDRESS))
    cat = d.UNIT_CAT.astype(str).str.strip()
    d["all_units"] = d.units
    d["homes_non_adu"] = np.where(cat == "ADU", 0.0, d.units)
    d["adu_units"] = np.where(cat == "ADU", d.units, 0.0)
    d["units_2plus"] = np.where(cat.isin(ab.TWO_PLUS), d.units, 0.0)
    d["db_flag"] = pd.to_numeric(d.DENSITY_BONUS_TOTAL, errors="coerce").fillna(0) > 0
    d["lihtc_flag"] = d.FIN_ASSIST_NAME.fillna("").astype(str).str.contains(LIHTC_RE, regex=True)
    d["fin_filled"] = d.FIN_ASSIST_NAME.fillna("").astype(str).str.strip() != ""
    d["db_homes"] = np.where(d.db_flag, d.units, 0.0)
    d["lihtc_homes"] = np.where(d.lihtc_flag, d.units, 0.0)
    d["dr_homes"] = d[DR_COLS].apply(pd.to_numeric, errors="coerce").fillna(0).sum(axis=1)
    d["project_homes"] = d.groupby(["project", "year"]).units.transform("sum")
    d["is_5plus_project"] = d.project_homes >= 5
    dr = d[DR_COLS].apply(pd.to_numeric, errors="coerce").fillna(0)
    d["dr_low_and_below"] = dr[[c for c in DR_COLS if "MOD" not in c]].sum(axis=1)  # acutely/extremely/very low, low
    d["dr_moderate"] = dr["BP_MOD_INCOME_DR"]
    d["lihtc_apartments"] = np.where(d.lihtc_flag & d.is_5plus_project, d.units, 0.0)
    lat, lon = pd.to_numeric(d.LATITUDE, errors="coerce"), pd.to_numeric(d.LONGITUDE, errors="coerce")
    d["hcd_street"] = ab.is_geocoded(lat, lon, d.STD_ADDRESS)
    d["lat"], d["lon"] = lat.where(d.hcd_street), lon.where(d.hcd_street)
    return d


def raw_keys(a2: pd.DataFrame) -> pd.Series:
    """Row hash identical to scripts/ca_ab2097_regeocode.row_key, on the raw Table A2 frame."""
    import ca_ab2097_regeocode as rg
    return rg.row_key(a2)


def add_census_points(p: pd.DataFrame, raw_key_set: set) -> pd.DataFrame:
    """Accepted Census re-geocodes for rows without an HCD street-level point (scripts/ca_ab2097_regeocode.py).
    Stops the run if the points file is missing or the join does not line up (audit)."""
    f = RAW.parent / "interim" / "ca_ab2097_geocode" / "points.parquet"
    if not f.exists():
        raise SystemExit(f"{f} is missing: run the re-geocode first (audit: main must not silently become HCD-only)")
    g = pd.read_parquet(f)
    g = g[g.kind == "failed_hcd"].set_index("key")
    missing = set(g.index) - raw_key_set
    if missing:
        raise SystemExit(f"{len(missing)} accepted Census keys do not exist in Table A2: the row hash does not line up")
    expected = int(p.geo_key.isin(g.index).sum())  # accepted rows that survive cleaning (duplicates removed)
    p["census_point"] = False
    key = p.geo_key
    hit = key.isin(g.index) & ~p.hcd_street
    p.loc[hit, "lat"] = key[hit].map(g.lat).to_numpy()
    p.loc[hit, "lon"] = key[hit].map(g.lon).to_numpy()
    p.loc[hit, "census_point"] = True
    print(f"accepted Census rows: {len(g):,}; of them in the cleaned permit set: {expected:,}; joined: {int(hit.sum()):,}")
    if int(hit.sum()) != expected:
        raise SystemExit("joined Census rows differ from accepted rows in the cleaned set")
    return p


def zones_of(d: np.ndarray) -> dict[str, np.ndarray]:
    return {"zone": ab.zone_of(d),
            "band": np.select([d < MILE / 3, d < MILE / 2, d < 2 * MILE / 3, (d >= MILE) & (d < 1.5 * MILE)],
                              ["b0_1_3", "b1_3_1_2", "b1_2_2_3", "ring_1_1_5"], "other"),
            "edge": np.select([(d >= MILE / 3) & (d < MILE / 2 - 25), (d >= MILE / 2 + 25) & (d < 2 * MILE / 3)],
                              ["inside", "outside"], "other")}


def build() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    stops = stop_sets()
    b = run.read_blocks(["GEOID20", "COUNTYFP20", "ALAND20", "HOUSING20", "INTPTLAT20", "INTPTLON20"])
    b["juris"] = run.block_juris(b)
    b["upz"] = run.in_toc(b) & (b.juris == ab.LA)
    b["homes"], b["acres"] = b.HOUSING20.astype(float), b.ALAND20.astype(float) / 4046.8564224
    a2 = pd.read_csv(RAW / "hcd_apr_a2" / "tablea2.csv", usecols=A2_COLS, low_memory=False)
    a2 = a2.reindex(columns=list(dict.fromkeys(A2_COLS)))
    fb = RAW.parent / "interim" / "ca_ab2097_geocode" / "failed_batches.txt"
    if not fb.exists():
        raise SystemExit("re-geocode has not finished (failed_batches.txt missing)")
    if fb.read_text().strip():
        print(f"re-geocode failed batches (their rows count as not geocoded): {fb.read_text().strip()}")
    p = add_census_points(clean_permits_full(a2), set(raw_keys(a2)))
    p = p[p.lat.notna() & p.lon.notna()].copy()
    pts = run.lonlat_points(p, p.lon, p.lat)
    p["upz"] = run.in_toc(pts) & (p.juris == ab.LA)
    other_b = run.nearest_m(b, stops["_other_than_rail"])
    other_p = run.nearest_m(pts, stops["_other_than_rail"])
    newr_b, newr_p = run.nearest_m(b, stops["_new_rail"]), run.nearest_m(pts, stops["_new_rail"])
    cells = []
    for spec in SPECS:
        db, dp = run.nearest_m(b, stops[spec]), run.nearest_m(pts, stops[spec])
        for k, v in zones_of(db).items():
            b[f"{k}_{spec}"] = v
        for k, v in zones_of(dp).items():
            p[f"{k}_{spec}"] = v
        if spec == "main":  # post hoc (audit, after the first run): within 150 m of the 1/2-mile line
            b["line150_main"] = np.abs(db - MILE / 2) < 150
            p["line150_main"] = np.abs(dp - MILE / 2) < 150
    # rail-only edge: land within 1/2 mile of any other (non-rail) stop removed from both sides (plan)
    for frame, dist in ((b, other_b), (p, other_p)):
        frame["edge_rail_only"] = np.where(dist < MILE / 2, "other", frame["edge_rail_only"])
    # no_new_stations: blocks and permits whose nearest rail stop opened 2018-2022 are left out of near/ring
    for frame, dist in ((b, newr_b), (p, newr_p)):
        frame["new_station_land"] = dist < 1.5 * MILE
    keep_cols = ["juris", "upz", "homes", "acres", "new_station_land", "line150_main"] + [c for c in b.columns if c.split("_")[0] in ("zone", "band", "edge")]
    b[keep_cols + ["GEOID20"]].to_parquet(CACHE / "blocks.parquet")
    pcols = (["juris", "project", "year", "report_year", "ent_year", "upz", "hcd_street", "census_point",
              "is_5plus_project", "db_flag", "lihtc_flag", "fin_filled", "new_station_land", "line150_main"] + OUTCOMES + SECONDARY
             + [c for c in p.columns if c.split("_")[0] in ("zone", "band", "edge")])
    p[pcols].to_parquet(CACHE / "permits.parquet")  # hashed project ids; no addresses or coordinates
    meta = {"stops": {k: int(len(v)) for k, v in stops.items()},
            "permit_rows": int(len(p)), "census_point_rows": int(p.census_point.sum()),
            "planned_stops_mapped": "SCAG Connect SoCal 2020 only; other regions' 2022-era planned stops not mapped"}
    (CACHE / "meta.json").write_text(json.dumps(meta, indent=1))
    print(json.dumps(meta, indent=1))


# =========================================================================== estimate helpers

def cells_for(b: pd.DataFrame, spec: str, zone_kind: str = "zone") -> pd.DataFrame:
    col = f"{zone_kind}_{spec}"
    c = b.dropna(subset=["juris"]).groupby(["juris", "upz", col])[["homes", "acres"]].sum().reset_index()
    return c.rename(columns={col: "zone"})


def permits_for(p: pd.DataFrame, spec: str, zone_kind: str = "zone") -> pd.DataFrame:
    q = p.copy()
    q["zone"] = q[f"{zone_kind}_{spec}"]
    return q


def with_treated_land(c: pd.DataFrame, juris: list[str], treat=("near", False)) -> list[str]:
    """Plan: the comparison is land in the same jurisdictions, so only jurisdictions with treated land (homes > 0 in
    the treated zone) enter a group (as ab2097.define_groups does). Fix found after the first run (2026-11-05)."""
    has = set(c[(c.zone == treat[0]) & (c.upz == treat[1]) & (c.homes > 0)].juris)
    return [j for j in juris if j in has]


def group(name: str, juris: list[str], treat=("near", False), comp=("ring", False)) -> ab.Group:
    return ab.Group(name, sorted(juris), treat, comp)


def year_arrays(g: ab.Group, c: pd.DataFrame, p: pd.DataFrame, outcome: str, denom: str = "homes"):
    arr = ab._arrays(g, c, p, outcome, denom, YEARS)
    return arr["t"], arr["c"]


def event_study(g, c, p, outcome, ref=(2022,), denom="homes", scale=1000.0, draws=DRAWS, seed=SEED):
    """Each year's near-minus-comparison rate gap minus the mean gap in the reference years; jurisdiction resampling.
    Returns (estimates by year, draws matrix [draws x years])."""
    (tm, td), (cm, cd) = year_arrays(g, c, p, outcome, denom)
    ri = [YEARS.index(y) for y in ref]

    def gaps(tm_, td_, cm_, cd_):
        if td_ <= 0 or cd_ <= 0:
            return np.full(len(YEARS), np.nan)
        gap = tm_ / td_ * scale - cm_ / cd_ * scale
        return gap - gap[ri].mean()
    est = gaps(tm.sum(0), td.sum(), cm.sum(0), cd.sum())
    J = len(g.juris)
    dr = np.full((draws, len(YEARS)), np.nan)
    rng = np.random.default_rng(seed)
    for k in range(draws):
        s = rng.integers(0, J, J)
        dr[k] = gaps(tm[s].sum(0), td[s].sum(), cm[s].sum(0), cd[s].sum())
    return est, dr


def interval(x: np.ndarray) -> tuple[float, float]:
    x = x[np.isfinite(x)]
    if not len(x):
        return float("nan"), float("nan")
    lo, hi = np.quantile(x, [(1 - LEVEL) / 2, 1 - (1 - LEVEL) / 2])
    return float(lo), float(hi)


def period_contrast(est, dr, before, after):
    """Mean of event-study values over `after` minus over `before` (both relative to the same reference)."""
    bi, ai = [YEARS.index(y) for y in before], [YEARS.index(y) for y in after]
    e = float(np.nanmean(est[ai]) - np.nanmean(est[bi]))
    d = np.nanmean(dr[:, ai], axis=1) - np.nanmean(dr[:, bi], axis=1)
    return e, d


def lead_slope(est, dr, leads=(2018, 2019, 2020, 2021)):
    li = [YEARS.index(y) for y in leads]
    x = np.array(leads, float) - np.mean(leads)
    slope = lambda v: float(np.sum(x * (v[li] - np.mean(v[li]))) / np.sum(x * x))  # noqa: E731
    return slope(est), np.array([slope(r) for r in dr])


def equal_weight(g, c, p, outcome, before=BEFORE, after=AFTER, scale=1000.0, draws=DRAWS, seed=SEED):
    """Mean over jurisdictions of each jurisdiction's own difference-in-differences (both areas with homes)."""
    (tm, td), (cm, cd) = year_arrays(g, c, p, outcome)
    ok = (td > 0) & (cd > 0)
    bi, ai = [YEARS.index(y) for y in before], [YEARS.index(y) for y in after]
    with np.errstate(divide="ignore", invalid="ignore"):
        t = tm / td[:, None] * scale
        cc = cm / cd[:, None] * scale
    per = (t[:, ai].mean(1) - t[:, bi].mean(1)) - (cc[:, ai].mean(1) - cc[:, bi].mean(1))
    per = per[ok]
    rng = np.random.default_rng(seed)
    dr = np.array([per[rng.integers(0, len(per), len(per))].mean() for _ in range(draws)]) if len(per) else np.array([])
    return float(per.mean()) if len(per) else float("nan"), dr


def share_did(g, p, flag: str, base_mask: pd.Series, before=BEFORE, after=AFTER, draws=DRAWS, seed=SEED):
    """Difference-in-differences of a project share (flag among base_mask projects), near vs comparison."""
    q = p[base_mask & p.juris.isin(g.juris)]
    q = q[((q.zone == g.treat[0]) & (q.upz == g.treat[1])) | ((q.zone == g.comp[0]) & (q.upz == g.comp[1]))].copy()
    q["area"] = np.where(q.zone == g.treat[0], "t", "c")
    q["period"] = np.where(q.year.isin(after), "a", np.where(q.year.isin(before), "b", "x"))
    q = q[q.period != "x"]
    proj = q.groupby(["juris", "project", "area", "period"])[flag].max().reset_index()
    J = sorted(proj.juris.unique())
    tab = proj.groupby(["juris", "area", "period"])[flag].agg(["sum", "size"]).unstack(["area", "period"], fill_value=0)

    def did(t):
        s = t.sum()
        r = lambda a, per: s[("sum", a, per)] / s[("size", a, per)] if s.get(("size", a, per), 0) else np.nan  # noqa: E731
        return (r("t", "a") - r("t", "b")) - (r("c", "a") - r("c", "b"))
    est = float(did(tab))
    rng = np.random.default_rng(seed)
    dr = np.array([did(tab.loc[[J[i] for i in rng.integers(0, len(J), len(J))]]) for _ in range(draws)]) if J else np.array([])
    return est, dr


# =========================================================================== dose check

def dose_check(b: pd.DataFrame, spec: str = "main", draws=DRAWS, seed=SEED) -> list[dict]:
    """City-level check with Census BPS place totals (not permit points)."""
    cw = pd.read_csv(REFERENCE / "ca_jurisdiction_crosswalk.csv", dtype=str)
    cities = cw[(cw.juris_type == "city") & cw.placefp.notna()][["juris_name", "placefp"]]
    bp = []
    for y in YEARS:
        f = RAW / "census_bps_ca" / f"place_{y}.txt"
        d = parsers.read_bps(f, "place", state_fips="06")
        d["year"] = y
        bp.append(d[["fips_place", "year", "units_total"]])
    bp = pd.concat(bp)
    units = bp.groupby(["fips_place", "year"]).units_total.sum().unstack(fill_value=0)
    homes = b.groupby("juris").homes.sum()
    near = b[b[f"zone_{spec}"] == "near"].groupby("juris").homes.sum()
    t = cities.assign(homes=cities.juris_name.map(homes), near=cities.juris_name.map(near).fillna(0))
    t = t[(t.homes > 0) & ~t.juris_name.isin(PLACEBO | DROPPED) & t.placefp.isin(units.index)].copy()
    u = units.loc[t.placefp]
    rate = u.div(t.homes.to_numpy(), axis=0) * 1000
    t["share"] = (t.near / t.homes).to_numpy()
    t["change"] = (rate[AFTER].mean(1) - rate[BEFORE].mean(1)).to_numpy()
    t["lead"] = (rate[[2021, 2022]].mean(1) - rate[[2018, 2019, 2020]].mean(1)).to_numpy()
    out = []

    def slope(x, y, w):
        w = w / w.sum()
        xm, ym = (w * x).sum(), (w * y).sum()
        return float((w * (x - xm) * (y - ym)).sum() / (w * (x - xm) ** 2).sum())
    rng = np.random.default_rng(seed)
    idx = [rng.integers(0, len(t), len(t)) for _ in range(draws)]
    for col, label in (("change", "dose: 2023-2025 minus 2018-2022"), ("lead", "dose lead placebo: 2021-2022 minus 2018-2020")):
        for wname, w in (("homes-weighted", t.homes.to_numpy(float)), ("equal weight", np.ones(len(t)))):
            x, y = t.share.to_numpy(float), t[col].to_numpy(float)
            est = slope(x, y, w)
            dr = np.array([slope(x[i], y[i], w[i]) for i in idx])
            lo, hi = interval(dr)
            out.append({"case": label, "weight": wname, "estimate": est, "low": lo, "high": hi,
                        "mde": 1.645 * float(np.nanstd(dr)), "n_places": int(len(t)),
                        "unit": "change in BPS permits per 1,000 existing homes a year per 1.0 share of homes within "
                                "1/2 mile (i.e. all homes near transit vs none)",
                        "interval_method": "places, 2,000 resamples"})
    # statewide count from the homes-weighted slope (plan: headline x covered homes / 1,000 x 3 years)
    covered = float(t.near.sum())
    for r in out:
        if r["case"].startswith("dose:") and r["weight"] == "homes-weighted":
            r["extra_homes_2023_2025_in_kept_places"] = r["estimate"] * covered / 1000 * 3
            r["extra_homes_low"], r["extra_homes_high"] = r["low"] * covered / 1000 * 3, r["high"] * covered / 1000 * 3
    return out


# =========================================================================== run all estimates

def estimate() -> None:
    b = pd.read_parquet(CACHE / "blocks.parquet")
    p_all = pd.read_parquet(CACHE / "permits.parquet")
    rep = ab.full_reporters(p_all)
    stable = pd.read_csv(REFERENCE / "ca_ab2097_geocode_stability.csv")
    stable = set(stable[stable.kept_stable_geocode_check].juris)
    main_j = [j for j in rep if j not in PLACEBO | DROPPED]
    plac_j = [j for j in rep if j in PLACEBO]
    rows, years_rows = [], []

    def add(case, spec, gname, outcome, est, dr, method="jurisdictions", **kw):
        lo, hi = interval(dr) if len(dr) else (float("nan"), float("nan"))
        rows.append({"case": case, "map": spec, "group": gname, "outcome": outcome, "estimate": est,
                     "low": lo, "high": hi, "mde": 1.645 * float(np.nanstd(dr)) if len(dr) else float("nan"),
                     "interval_method": method, **kw})

    def block(case, spec, p, juris, gname, outcomes=OUTCOMES, before=BEFORE, after=AFTER, ref=(2022,),
              zone_kind="zone", treat=("near", False), comp=("ring", False), per_acre=False, keep_years=False):
        c, q = cells_for(b, spec, zone_kind), permits_for(p, spec, zone_kind)
        juris = with_treated_land(c, juris, treat)
        g = group(gname, juris, treat, comp)
        for oc in outcomes:
            est, dr = event_study(g, c, q, oc, ref, denom="acres" if per_acre else "homes",
                                  scale=1.0 if per_acre else 1000.0)
            e, d = period_contrast(est, dr, before, after)
            add(case, spec, gname, oc + (" per acre" if per_acre else ""), e, d,
                n_jurisdictions=len(juris))
            if keep_years:
                for y, v, col in zip(YEARS, est, dr.T):
                    lo, hi = interval(col)
                    years_rows.append({"case": case, "map": spec, "group": gname, "outcome": oc, "year": y,
                                       "estimate_vs_2022": v, "low": lo, "high": hi})
            if case == "headline" and not per_acre:
                for lab, bb, aa in (("lead check: 2021-2022 vs 2018-2020", [2018, 2019, 2020], [2021, 2022]),
                                    ("placebo date: 2020-2022 vs 2018-2019", [2018, 2019], [2020, 2021, 2022])):
                    e2, d2 = period_contrast(est, dr, bb, aa)
                    add(lab, spec, gname, oc, e2, d2, n_jurisdictions=len(juris))
                s, sd = lead_slope(est, dr)
                add("lead slope (per year, 2018-2021 vs 2022)", spec, gname, oc, s, sd, n_jurisdictions=len(juris))

    p_main = p_all
    p_street = p_all[p_all.hcd_street]
    # headline, year by year, leads, placebo date: main and placebo groups, main map
    for gname, juris in (("main", main_j), ("placebo", plac_j)):
        block("headline", "main", p_main, juris, gname, outcomes=OUTCOMES + SECONDARY, keep_years=True)
        block("headline", "main", p_main, juris, gname, outcomes=["homes_non_adu"], per_acre=True)
    # anticipation: reference 2018-2021
    block("anticipation (reference 2018-2021)", "main", p_main, main_j, "main", outcomes=["homes_non_adu"],
          before=[2018, 2019, 2020, 2021], ref=(2018, 2019, 2020, 2021))
    # checks: maps
    for spec in ("rail_only", "no_planned"):
        block("check: map", spec, p_main, main_j, "main", outcomes=["homes_non_adu", "all_units"])
    nn = p_main[~p_main.new_station_land]
    b_nn = b[~b.new_station_land]
    c_nn = cells_for(b_nn, "no_new_stations")
    g = group("main", with_treated_land(c_nn, main_j))
    est, dr = event_study(g, c_nn, permits_for(nn, "no_new_stations"), "homes_non_adu")
    e, d = period_contrast(est, dr, BEFORE, AFTER)
    add("check: without land near 2018-2022 rail openings", "no_new_stations", "main", "homes_non_adu", e, d,
        n_jurisdictions=len(g.juris))
    s, sd = lead_slope(est, dr)
    add("check: lead slope without land near 2018-2022 rail openings", "no_new_stations", "main", "homes_non_adu", s, sd,
        n_jurisdictions=len(g.juris))
    # checks: points, dating, years, jurisdictions
    rep_street = ab.full_reporters(p_street)  # the check's own full-reporter list (audit)
    block("check: HCD street-level points only", "main", p_street,
          [j for j in rep_street if j not in PLACEBO | DROPPED], "main", outcomes=["homes_non_adu"])
    for lab, ycol in (("check: report-year dating", "report_year"), ("check: entitlement-date dating", "ent_year")):
        q = p_main.copy()
        q["year"] = q[ycol]
        q = q[q.year.isin(YEARS)]
        block(lab, "main", q, main_j, "main", outcomes=["homes_non_adu"])
    block("check: drop 2023", "main", p_main, main_j, "main", outcomes=["homes_non_adu"], after=[2024, 2025])
    block("check: drop Los Angeles", "main", p_main, [j for j in main_j if j != ab.LA], "main", outcomes=["homes_non_adu"])
    block("check: stable-geocode jurisdictions", "main", p_main, [j for j in main_j if j in stable], "main",
          outcomes=["homes_non_adu"])
    c, q = cells_for(b, "main"), permits_for(p_main, "main")
    g = group("main", with_treated_land(c, main_j))
    q2 = ab.drop_largest(g, q.assign(units=q.homes_non_adu), "homes_non_adu")
    est, dr = event_study(g, c, q2, "homes_non_adu")
    e, d = period_contrast(est, dr, BEFORE, AFTER)
    add("check: drop the largest project in each area and period", "main", "main", "homes_non_adu", e, d,
        n_jurisdictions=len(g.juris))
    e, d = equal_weight(g, c, q, "homes_non_adu")
    add("check: equal weight per jurisdiction", "main", "main", "homes_non_adu", e, d, n_jurisdictions=len(g.juris))
    # bands and edges
    for band in ("b0_1_3", "b1_3_1_2", "b1_2_2_3"):
        block(f"band {band} vs 1-1 1/2 mile", "main", p_main, main_j, "main", outcomes=["homes_non_adu"],
              zone_kind="band", treat=(band, False), comp=("ring_1_1_5", False))
    block("edge: 1/3-1/2 vs 1/2-2/3 mile (25 m donut)", "main", p_main, main_j, "main", outcomes=["homes_non_adu"],
          zone_kind="edge", treat=("inside", False), comp=("outside", False))
    block("edge, rail-only map (other-stop land removed)", "rail_only", p_main, main_j, "main",
          outcomes=["homes_non_adu"], zone_kind="edge", treat=("inside", False), comp=("outside", False))
    # Palo Alto edge, project resampling (one jurisdiction)
    gp = group("Palo Alto", ["PALO ALTO"], ("inside", False), ("outside", False))
    cp, qp = cells_for(b, "rail_only", "edge"), permits_for(p_main, "rail_only", "edge")
    r = ab.estimate(gp, cp, qp, "homes_non_adu", "per_1000_homes")
    lo, hi, drp = ab.project_interval(gp, cp, qp, "homes_non_adu", "per_1000_homes")
    rows.append({"case": "edge, Palo Alto (rail-only map)", "map": "rail_only", "group": "Palo Alto",
                 "outcome": "homes_non_adu", "estimate": r["estimate"], "low": lo, "high": hi,
                 "mde": 1.645 * float(np.nanstd(drp)), "interval_method": "projects (one jurisdiction)",
                 "n_jurisdictions": 1})
    # secondary shares (descriptive only)
    c, q = cells_for(b, "main"), permits_for(p_main, "main")
    g = group("main", with_treated_land(c, main_j))
    for lab, flag, base in (("A: density-bonus share of 5+ projects", "db_flag", q.is_5plus_project),
                            ("C: LIHTC share of 5+ projects with financing filled", "lihtc_flag",
                             q.is_5plus_project & q.fin_filled)):
        e, d = share_did(g, q, flag, base)
        add(lab + " (descriptive only)", "main", "main", "share of projects", e, d, n_jurisdictions=len(g.juris))

    # D2 plain counts (descriptive): LIHTC homes and projects in 5+ home projects, near vs ring, by period
    q = permits_for(p_main, "main")
    q = q[q.juris.isin(with_treated_land(cells_for(b, "main"), main_j)) & ~q.upz & q.zone.isin(["near", "ring"]) & (q.lihtc_apartments > 0)]
    q["period"] = np.where(q.year.isin(AFTER), "2023-2025", "2018-2022")
    q.groupby(["zone", "period"]).agg(lihtc_homes=("lihtc_apartments", "sum"), lihtc_projects=("project", "nunique")
                                      ).reset_index().assign(
        note="raw counts; near and ring hold different numbers of existing homes, so compare zones only with D2's "
             "per-1,000-homes rate").to_csv(REFERENCE / "ca_ab2097_results_lihtc_counts.csv", index=False)
    res = pd.DataFrame(rows)
    res["unit"] = np.where(res.outcome.str.contains("per acre"), "permits per acre per year",
                           np.where(res.outcome == "share of projects", "share of projects (0-1)",
                                    "homes in issued permits per 1,000 existing homes (2020) per year"))
    res["labels"] = ("bus areas: today's Caltrans layer (20-minute rule, later map); planned stops mapped for SCAG only "
                     "(elsewhere planned-stop land counts as ring); points: HCD street-level + Census re-geocodes")
    res.to_csv(REFERENCE / "ca_ab2097_results.csv", index=False)
    pd.DataFrame(years_rows).to_csv(REFERENCE / "ca_ab2097_results_by_year.csv", index=False)
    pd.DataFrame(dose_check(b)).to_csv(REFERENCE / "ca_ab2097_results_dose.csv", index=False)
    print(res[["case", "map", "group", "outcome", "estimate", "low", "high"]].round(3).to_string(index=False))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--estimate", action="store_true")
    a = ap.parse_args()
    if a.build:
        build()
    if a.estimate:
        estimate()
    if not (a.build or a.estimate):
        print(__doc__)


if __name__ == "__main__":
    main()
