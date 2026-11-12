"""Test 57 (CAUSAL_FRAMEWORK_PLAN.md, Test 57 LOCK): New York 2016 Transit Zone panels, one per run.

    uv run python scripts/build_parking_t57_ny_panel.py [--out data/processed/t57]

WRITES PANELS ONLY. Nothing is printed or written by arm or by year except the panel files themselves (read only by
scripts/summarise_parking_t57.py). Stdout: file names, panel row counts and whole-file job totals.

Inputs (git-ignored):
  data/raw/parking_t57/nyctransitzones_201601.zip     DCP 2016 Transit Zone (primary line; Map 3 from this file)
  data/raw/parking_t57/nybb_16a.zip                   borough boundaries (water / city edge test of the line)
  data/raw/parking_t57/mih_areas.geojson              MIH areas with adoption dates (m79g-k9r4)
  data/raw/parking_t57/dobnow_nb.json                 DOB NOW: Build filings (w9ak-ipjd), New Building + ALT-CO
  data/raw/parking_t57/hpd_affordable_by_building.json  HPD Affordable Housing Production by Building (hg8x-zxpr)
  data/raw/tod_cases/nyc/dob_nb_all.csv               DOB legacy job filings (ic3t-wcy2), NB, document 01
  data/raw/tod_cases/nyc/mappluto_16v1.zip            lots as of March 2016 (zoning, land use, lot area, centroid)

Arms and cells (same geometry as scripts/build_parking_t57_nyc_tz.py, which made the committed cell counts):
- The 2016 line is the 2016 file's boundary sampled every 25 ft; samples with water or the city edge within 60 ft on
  either side are dropped ("land line"). A lot is in the band if its PLUTO centroid is 50-400 m from the land line
  (50 m donut); T = inside the 2016 Transit Zone, C = outside.
- Outside lots in Manhattan community districts 101-108 (Manhattan Core) are dropped: residential parking has not been
  required there since 1982, so they are already treated and the plan never uses already-treated areas as controls.
- 500 m grid (same origin as the check script); a cell split by the line keeps one part per arm and is ONE cluster.
- Eligible land (TOD's rule, missing_middleware/tod/case_nyc.py): residential, commercial or mixed zoning (PLUTO 16v1
  ZoneDist1) and land use not 08 (public facilities and institutions) or 09 (open space). Acres = LotArea / 43,560.
Outcomes:
- DOB units = proposed dwelling units of new-building jobs with at least 1 unit, by FILING year.
  Legacy: one row per job number (document 01), pre__filing_date, any date (no seam). DOB NOW: job_type
  'New Building' only (ALT-CO left out), one row per job: the initial filing (-I1), else the job's earliest filing.
- HPD units = income-restricted units (extremely low + very low + low + moderate + middle income; "other" =
  superintendent units left out) in New Construction buildings, by project start year.
- Each record is placed on a 16v1 lot: same BBL unless that lot's centroid lies more than 100 m from the record's own
  point; otherwise the nearest 16v1 lot centroid within 40 m of the point (TOD's rule, with centroids). Unplaced records
  are dropped (whole-file totals in the diagnostics file). The record takes its lot's arm, cluster and flags.
MIH (addendum 2): a lot is MIH-mapped if its centroid lies in an MIH area; its adoption date is the earliest
date_adopte of the areas holding it. Primary runs drop such a lot from both arms from that date: its records filed on or
after the date are dropped and its acres count only for the part of the adoption year before the date (0 after).
"keepmih" runs keep them (labelled "bundled with MIH").
Same-zoning edge (pre-set sensitivity 1): each land-line sample is classed as in the check script (modal 16v1
ZoneDist1 of lot centroids within 300 ft on each side, more than 20 ft off the line); a lot is kept when its nearest
land-line sample has lots on both sides with the same modal district.
Runs (scripts/parking_t57_common.RUNS): ny_dob, ny_dob_keepmih, ny_dob_samezone, ny_dob_legacy2020, ny_hpd,
ny_hpd_keepmih. Output: <out>/panel_<run>.csv (cluster, arm, year, units, jobs, acres), <out>/build_ny_diag.json,
<out>/hpd_placement_by_year.csv (HPD records and not-placed share by project start year, whole city, not by arm).
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import build_parking_t57_nyc_tz as TZ  # noqa: E402
import parking_t57_common as C  # noqa: E402
from missing_middleware import geom as G  # noqa: E402
from missing_middleware import geom_extra_station as X  # noqa: E402
from missing_middleware.paths import RAW  # noqa: E402
from missing_middleware.tod.case_nyc import zone_class  # noqa: E402

D, NYC = RAW / "parking_t57", RAW / "tod_cases" / "nyc"
M_FT = 1 / TZ.FT                         # feet per metre
BBL_MAX_FT, NEAR_MAX_FT = 100 * M_FT, 40 * M_FT
BORO = {"MANHATTAN": 1, "BRONX": 2, "BROOKLYN": 3, "QUEENS": 4, "STATEN ISLAND": 5}
YEARS_DOB, YEARS_HPD = range(C.FIRST_YEAR["New York"], 2024), range(2014, 2024)
HPD_INCOME = ["extremely_low_income_units", "very_low_income_units", "low_income_units", "moderate_income_units",
              "middle_income_units"]


# ------------------------------------------------------------------------------------------------ geometry
def line_samples(t16, bb):
    """Land-line samples of the 2016 line (x, y, normal) and the water flag, as in build_parking_t57_nyc_tz.run()."""
    px, py, nx, ny = TZ.boundary_samples(t16.polys, 25.0)
    water = np.zeros(len(px), bool)
    for sgn in (1, -1):
        b = X.first_within(px + sgn * 60.0 * nx, py + sgn * 60.0 * ny, bb.geometry.tolist())
        water |= b < 0
    return px, py, nx, ny, water


def same_zone_flags(px, py, nx, ny, water, lots) -> np.ndarray:
    """True where both sides of a land-line sample have lots within 300 ft and the same modal ZoneDist1."""
    tree = cKDTree(np.c_[lots.XCoord, lots.YCoord])
    zd = lots.ZoneDist1.fillna("").to_numpy()
    lx, ly = lots.XCoord.to_numpy(), lots.YCoord.to_numpy()
    out = np.zeros(len(px), bool)
    for k, cand in enumerate(tree.query_ball_point(np.c_[px, py], r=300.0)):
        if water[k] or not cand:
            continue
        cand = np.asarray(cand)
        s = (lx[cand] - px[k]) * nx[k] + (ly[cand] - py[k]) * ny[k]
        a, b = zd[cand[s > 20]], zd[cand[s < -20]]
        if len(a) and len(b):
            out[k] = Counter(a).most_common(1)[0][0] == Counter(b).most_common(1)[0][0]
    return out


def lot_table(tmp: Path) -> tuple[pd.DataFrame, dict]:
    t16 = G.read_shapefile(TZ.unzip_shp(D / "nyctransitzones_201601.zip", tmp))
    bb = X.read_vector(TZ.unzip_shp(D / "nybb_16a.zip", tmp), columns=["BoroCode"])
    lots = TZ.pluto16()
    px, py, nx, ny, water = line_samples(t16, bb)
    land = ~water
    same = same_zone_flags(px, py, nx, ny, water, lots)
    x, y = lots.XCoord.to_numpy(float), lots.YCoord.to_numpy(float)
    dist, near = cKDTree(np.c_[px[land], py[land]]).query(np.c_[x, y])
    inside = G.points_in_any(x, y, t16.polys, union=True)
    band = (dist >= TZ.BAND_IN) & (dist <= TZ.BAND_OUT)
    lots["arm"] = np.where(band & inside, "T", np.where(band & ~inside, "C", ""))
    core = (pd.to_numeric(lots.CD, errors="coerce").between(101, 108)).to_numpy()
    lots.loc[(lots.arm == "C") & core, "arm"] = ""                 # Manhattan Core: already treated, never a control
    lots["cluster"] = (((y - TZ.BOX[1]) // TZ.CELL).astype(int) * 10000 + ((x - TZ.BOX[0]) // TZ.CELL).astype(int))
    lu = lots.LandUse.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(2)
    lots["eligible"] = lots.ZoneDist1.map(zone_class).isin(["res", "com", "mixed"]) & ~lu.isin(["08", "09"])
    lots["acres"] = pd.to_numeric(lots.LotArea, errors="coerce").fillna(0.0) / 43560.0
    lots["same_zone"] = same[np.flatnonzero(land)[near]]
    lots["bbl"] = lots.boro.astype(np.int64) * 10**9 + pd.to_numeric(lots.Block).astype(np.int64) * 10**4 + \
        pd.to_numeric(lots.Lot).astype(np.int64)
    # MIH adoption date per lot (earliest area holding the centroid); only band lots need it
    mih = G.read_geojson(D / "mih_areas.geojson").to_crs(2263)
    md = pd.to_datetime(mih.attrs["date_adopte"], errors="coerce")
    lots["mih_date"] = pd.Series(pd.NaT, index=lots.index, dtype="datetime64[ns]")
    sel = np.flatnonzero(lots.arm.ne("").to_numpy())
    for d0 in sorted(md.dropna().unique()):
        polys = [mih.polys[i] for i in np.flatnonzero((md == d0).to_numpy())]
        hit = G.points_in_any(x[sel], y[sel], polys, union=True) & lots.mih_date.iloc[sel].isna().to_numpy()
        lots.loc[lots.index[sel[hit]], "mih_date"] = pd.Timestamp(d0)
    diag = dict(land_line_samples=int(land.sum()), land_line_same_zone_share=round(float(same[land].mean()), 4),
                mih_areas=int(len(md)), mih_areas_without_date=int(md.isna().sum()),
                lots_16v1=int(len(lots)), lots_in_band_any_arm=int(lots.arm.ne("").sum()),
                outside_band_lots_dropped_manhattan_core=int((band & ~inside & core).sum()))
    return lots, diag


# ------------------------------------------------------------------------------------------------ records
def legacy_jobs() -> pd.DataFrame:
    d = pd.read_csv(NYC / "dob_nb_all.csv", dtype=str).drop_duplicates("job__")
    d = d[d.job_type == "NB"]
    out = pd.DataFrame({
        "source": "legacy", "id": d.job__,
        "date": pd.to_datetime(d.pre__filing_date, format="%m/%d/%Y", errors="coerce"),
        "units": pd.to_numeric(d.proposed_dwelling_units, errors="coerce"),
        "bbl": d.borough.str.upper().map(BORO) * 10**9 + pd.to_numeric(d.block, errors="coerce") * 10**4 +
        pd.to_numeric(d.lot, errors="coerce"),
        "lat": pd.to_numeric(d.gis_latitude, errors="coerce"), "lon": pd.to_numeric(d.gis_longitude, errors="coerce")})
    return out


def dobnow_jobs() -> tuple[pd.DataFrame, dict]:
    d = pd.DataFrame(json.loads((D / "dobnow_nb.json").read_text()))
    n_all, n_altco = len(d), int((d.job_type != "New Building").sum())
    d = d[d.job_type == "New Building"].copy()                    # ALT-CO left out (lock)
    d["job"] = d.job_filing_number.str.split("-").str[0]
    d["init"] = d.job_filing_number.str.endswith("-I1")
    d["date"] = pd.to_datetime(d.filing_date, errors="coerce")
    d = d.sort_values(["job", "init", "date", "job_filing_number"], ascending=[True, False, True, True])
    d = d.drop_duplicates("job")
    bbl = pd.to_numeric(d.bbl, errors="coerce")
    alt = d.borough.str.upper().map(BORO) * 10**9 + pd.to_numeric(d.block, errors="coerce") * 10**4 + \
        pd.to_numeric(d.lot, errors="coerce")
    out = pd.DataFrame({"source": "dobnow", "id": d.job, "date": d.date,
                        "units": pd.to_numeric(d.proposed_dwelling_units, errors="coerce"),
                        "bbl": bbl.fillna(alt), "lat": pd.to_numeric(d.latitude, errors="coerce"),
                        "lon": pd.to_numeric(d.longitude, errors="coerce")})
    return out, dict(dobnow_rows_file=n_all, dobnow_altco_rows_dropped=n_altco,
                     dobnow_nb_jobs=int(len(out)), dobnow_nb_jobs_without_initial_filing=int((~d.init).sum()))


def hpd_records() -> tuple[pd.DataFrame, dict]:
    d = pd.DataFrame(json.loads((D / "hpd_affordable_by_building.json").read_text()))
    n = len(d)
    d = d[d.reporting_construction_type == "New Construction"].copy()
    units = sum(pd.to_numeric(d[c], errors="coerce").fillna(0) for c in HPD_INCOME)
    lat = pd.to_numeric(d.latitude, errors="coerce").fillna(pd.to_numeric(d.get("latitude_internal"), errors="coerce"))
    lon = pd.to_numeric(d.longitude, errors="coerce").fillna(pd.to_numeric(d.get("longitude_internal"), errors="coerce"))
    out = pd.DataFrame({"source": "hpd", "id": d.project_id.astype(str) + "/" + d.building_id.astype(str),
                        "date": pd.to_datetime(d.project_start_date, errors="coerce"), "units": units,
                        "bbl": pd.to_numeric(d.bbl, errors="coerce"), "lat": lat, "lon": lon})
    return out, dict(hpd_rows_file=n, hpd_new_construction_rows=int(len(out)))


def place(rec: pd.DataFrame, lots: pd.DataFrame) -> tuple[pd.Series, dict]:
    """16v1 lot index of each record (or -1): BBL unless > 100 m from the record's point, else nearest centroid < 40 m."""
    lut = pd.Series(np.arange(len(lots)), index=lots.bbl.to_numpy(float))
    lut = lut[~lut.index.duplicated()]
    i = lut.reindex(pd.to_numeric(rec.bbl, errors="coerce").round().to_numpy(float)).fillna(-1).astype(int).to_numpy(copy=True)
    has = rec.lat.notna().to_numpy() & rec.lon.notna().to_numpy()
    jx, jy = np.full(len(rec), np.nan), np.full(len(rec), np.nan)
    jx[has], jy[has] = G.transform(rec.lon.to_numpy()[has], rec.lat.to_numpy()[has], 4326, 2263)
    lx, ly = lots.XCoord.to_numpy(float), lots.YCoord.to_numpy(float)
    ok = i >= 0
    far = ok & has
    far[far] = np.hypot(lx[i[far]] - jx[far], ly[i[far]] - jy[far]) > BBL_MAX_FT
    i[far] = -1
    need = (i < 0) & has
    dd, nn = cKDTree(np.c_[lx, ly]).query(np.c_[jx[need], jy[need]])
    i[np.flatnonzero(need)[dd <= NEAR_MAX_FT]] = nn[dd <= NEAR_MAX_FT]
    return pd.Series(i, index=rec.index), dict(records=int(len(rec)), by_bbl=int((ok & ~far).sum()),
                                                bbl_rejected_far=int(far.sum()), by_point=int((dd <= NEAR_MAX_FT).sum()),
                                                unplaced=int((i < 0).sum()))


def placement_by_year(rec: pd.DataFrame) -> pd.DataFrame:
    """Whole-city records and not-placed share by year (never split by arm): rec needs date and lot (-1 = not placed)."""
    d = rec.assign(year=rec.date.dt.year, unplaced=(rec.lot < 0).astype(int))
    g = d.groupby("year").agg(records=("unplaced", "size"), not_placed=("unplaced", "sum")).reset_index()
    g["not_placed_share"] = (g.not_placed / g.records).round(4)
    g["year"] = g.year.astype(int)
    return g


# ------------------------------------------------------------------------------------------------ panels
def year_share_before(mih: pd.Series, year: int) -> np.ndarray:
    """Share of `year` before each lot's MIH adoption date (1 when no date)."""
    d = pd.to_datetime(mih)
    s = np.ones(len(d))
    has = d.notna().to_numpy()
    y = d.dt.year.to_numpy()
    s[has & (y < year)] = 0.0
    same = has & (y == year)
    if same.any():
        start = pd.Timestamp(year=year, month=1, day=1)
        days = 366 if pd.Timestamp(year=year, month=12, day=31).dayofyear == 366 else 365
        s[same] = (d[same] - start).dt.days.to_numpy() / days
    return s


def panel(lots: pd.DataFrame, rec: pd.DataFrame, years, drop_mih: bool, lot_mask: np.ndarray) -> pd.DataFrame:
    L = lots[lot_mask]
    parts = []
    for y in years:
        f = year_share_before(L.mih_date, y) if drop_mih else np.ones(len(L))
        parts.append(pd.DataFrame({"cluster": L.cluster.to_numpy(), "arm": L.arm.to_numpy(), "year": y,
                                   "acres": L.acres.to_numpy() * f}))
    A = pd.concat(parts).groupby(["cluster", "arm", "year"], as_index=False)["acres"].sum()
    r = rec[rec.lot.isin(np.flatnonzero(lot_mask))].copy()
    r["year"] = r.date.dt.year
    r = r[r.year.isin(list(years))]
    if drop_mih:
        md = lots.mih_date.to_numpy()[r.lot.to_numpy()]
        r = r[~(pd.notna(md) & (r.date.to_numpy() >= md))]
    r["cluster"] = lots.cluster.to_numpy()[r.lot.to_numpy()]
    r["arm"] = lots.arm.to_numpy()[r.lot.to_numpy()]
    U = r.groupby(["cluster", "arm", "year"], as_index=False).agg(units=("units", "sum"), jobs=("units", "size"))
    P = A.merge(U, on=["cluster", "arm", "year"], how="outer").fillna({"acres": 0.0, "units": 0.0, "jobs": 0})
    P["jobs"] = P.jobs.astype(int)
    P["year"] = P.year.astype(int)
    return P.sort_values(["cluster", "arm", "year"]).reset_index(drop=True)[["cluster", "arm", "year", "units", "jobs", "acres"]]


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "data/processed/t57"))
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp())
    try:
        lots, diag = lot_table(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    keep = (lots.arm.ne("") & lots.eligible).to_numpy()
    leg = legacy_jobs()
    now, dn = dobnow_jobs()
    hpd, dh = hpd_records()
    diag.update(dn, **dh, legacy_rows_file_unique_jobs=int(len(leg)))
    recs = {}
    for name, r in (("legacy", leg), ("dobnow", now), ("hpd", hpd)):
        r = r[(r.units > 0) & r.date.notna()].copy()
        r["lot"], pdg = place(r, lots)
        diag[f"placement_{name} (records with units > 0 and a date, whole file)"] = pdg
        if name == "hpd":   # audit code rulings 06:28 UTC: HPD not-placed share by year, whole city, for --first
            placement_by_year(r).to_csv(out / "hpd_placement_by_year.csv", index=False)
        recs[name] = r[r.lot >= 0]
    dob = pd.concat([recs["legacy"], recs["dobnow"]], ignore_index=True)
    same = lots.same_zone.to_numpy()
    spec = {"ny_dob": (dob, YEARS_DOB, True, keep), "ny_dob_keepmih": (dob, YEARS_DOB, False, keep),
            "ny_dob_samezone": (dob, YEARS_DOB, True, keep & same),
            "ny_dob_legacy2020": (recs["legacy"], range(C.FIRST_YEAR["New York"], 2021), True, keep),
            "ny_hpd": (recs["hpd"], YEARS_HPD, True, keep), "ny_hpd_keepmih": (recs["hpd"], YEARS_HPD, False, keep)}
    assert set(spec) == {k for k, r in C.RUNS.items() if r.city == "New York"}
    for k, (r, yrs, drop, mask) in spec.items():
        P = panel(lots, r, yrs, drop, mask)
        P.to_csv(out / f"panel_{k}.csv", index=False)
        print(f"wrote {out / f'panel_{k}.csv'}: {len(P):,} rows")
    (out / "build_ny_diag.json").write_text(json.dumps(diag, indent=1, default=str) + "\n")
    print(f"wrote {out / 'build_ny_diag.json'} (whole-file totals only)")


if __name__ == "__main__":
    main()
