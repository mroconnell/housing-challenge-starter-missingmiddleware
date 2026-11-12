"""Test 57 (CAUSAL_FRAMEWORK_PLAN.md, Test 57 LOCK): San Francisco wave A panel (a case, not a headline cell).

    uv run python scripts/build_parking_t57_sf_panel.py [--out data/processed/t57]

WRITES THE PANEL ONLY. Nothing is printed by arm or by year. Stdout: file name, panel rows, whole-file totals.

Inputs (git-ignored):
  data/raw/parking_lot_cities/sf_parcels.geojson      DataSF active parcels (acdm-wktn, PDDL), centroid and shape
  data/raw/parking_t57/sf_zoning_districts.geojson    DataSF Zoning Districts (3i4a-hu95, PDDL), 2026 vintage
  data/raw/parking_t57/sf_zoning_2009.geojson         DataSF Historic Zoning Districts - 2009 (jud5-ja46)
  data/raw/parking_t57/sf_planning_areas_datasf.geojson  DataSF Planning Areas (bkzf-eahq): MASK ONLY
  data/raw/parking_t57/sf_sud.geojson                 DataSF Special Use Districts (5yf5-ms5f)
  data/raw/parking_t57/sf_permits_2003.json           DataSF Building Permits (i98e-djp9, PDDL), issued 2003 on
  reference/parking_t57_sf_districts.csv              district roles (41 'control' rows; treated A lists)

Lots: active parcels, condominium sub-lots folded into one lot (parcels sharing a centroid; the first is kept).
Acres from the parcel polygon (EPSG:3310). The lot's point is its centroid (DataSF centroid fields).
Arms (rules block and LOCK):
- Treated, Market-Octavia (Ord. 72-08, 2008-05-30): 2009 historic district RTO, NCT-3, Hayes NCT or Upper Market NCT
  (the 2008 part; the Upper Market NCD remnant is 'NCD' in 2009 and is not treated), inside the Market and Octavia
  planning area. The current layer is not used for these (RTO-1 has 2026 additions; Upper Market has a 2011 remnant).
- Treated, Eastern Neighborhoods (Ord. 298-08, about 2009-01-19): current district UMU, MUG, MUR, MUO, SPD, RTO-M,
  NCT-MISSION or NCT-24TH-MISSION, inside the 2008 EN planning areas (Mission, Showplace Square/Potrero Hill, Central
  Waterfront, East SoMa, and Central SoMa, which was East SoMa in 2009), not in the Visitacion Valley/Schlage SUD.
  Undated NCT districts are dropped (NCT-Valencia, NCT-SoMa, NCT-1, NCT-2). C-3-G, Downtown C-3 and Rincon
  Hill/Transbay (DTR) lots are in neither list.
- Controls: the clean districts of reference/parking_t57_sf_districts.csv (role 'control') except NCD-BAYVIEW (the
  rules block puts Bayview out), with all of: the 2009 district was a control-type district (RH, RM, NC-1/2/3/S, NCD
  or C-2; this drops lots moved into these districts in 2026); outside the Market and Octavia planning area and every
  EN planning area (EN RH/RM lots out of both arms); outside the Telegraph Hill-North Beach Residential, North of
  Market Residential 1 and 2, Bernal Heights, Washington-Broadway and Visitacion Valley/Schlage SUDs.
- Every lot in an arm is in a residential, mixed-use or commercial district, so all are eligible land (the parcel
  layer has no land-use field to remove parks or institutions inside these districts).
Clusters: 500 m grid cells (EPSG:3310); a cell holding lots of both arms is one cluster with a part in each.
Outcome (measure: permits ISSUED): new-construction permits (types 1 and 2), not cancelled, with proposed units > 0;
units = proposed units (gross); year = issue year. Placed by block-lot, else the nearest lot centroid within 40 m of
the permit's point; the permit takes its lot's arm and cluster.
Output: <out>/panel_sf_a.csv, <out>/build_sf_diag.json.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import parking_t57_common as C  # noqa: E402
from missing_middleware import geom as G  # noqa: E402
from missing_middleware import geom_extra_station as X  # noqa: E402
from missing_middleware.paths import RAW  # noqa: E402

D = RAW / "parking_t57"
CRS_M = 3310
CELL_M, NEAR_M = 500.0, 40.0
YEARS = range(C.FIRST_YEAR["San Francisco"], 2019)
MO_2009 = {"RTO", "NCT-3"}
MO_2009_NCT = {"HAYES NCT", "UPPER MARKET STREET NEIGHBORHOOD COMMERCIAL"}
EN_CURRENT = {"UMU", "MUG", "MUR", "MUO", "SPD", "RTO-M", "NCT-MISSION", "NCT-24TH-MISSION"}
EN_2008_AREAS = {"Mission (EN)", "Showplace Square/Potrero Hill (EN)", "Central Waterfront (EN)", "East SoMa (EN)", "Central SoMa"}
EN_ALL_AREAS = EN_2008_AREAS | {"Western SoMa (EN)", "Eastern Neighborhoods (Complete)", "Eastern Neighborhoods w/Valencia"}
MO_AREA = "Market and Octavia"
CONTROL_2009 = {"RH-1", "RH-1(D)", "RH-1(S)", "RH-2", "RH-3", "RM-1", "RM-2", "RM-3", "RM-4", "NC-1", "NC-2", "NC-3",
                "NC-S", "NCD", "C-2"}
SUD_OUT = {"Telegraph Hill-NB Residential", "North of Market Residential 1", "North of Market Residential 2",
           "Bernal Heights", "Washington-Broadway SUD", "Visitacion Valley/Schlage SUD"}
CONTROL_DROP = {"NCD-BAYVIEW"}


def layer(name: str, cols):
    L = G.read_geojson(D / name, columns=cols)
    return L.attrs.reset_index(drop=True), X.polys_to_crs(L.polys, L.crs, X.crs(CRS_M))


def lots_table() -> tuple[pd.DataFrame, dict, pd.Series]:
    P = G.read_geojson(RAW / "parking_lot_cities/sf_parcels.geojson",
                       columns=["blklot", "zoning_code", "centroid_latitude", "centroid_longitude"])
    a = P.attrs.reset_index(drop=True)
    lat, lon = pd.to_numeric(a.centroid_latitude, errors="coerce"), pd.to_numeric(a.centroid_longitude, errors="coerce")
    ok = (lat.notna() & lon.notna()).to_numpy()
    key = lat.round(9).astype(str) + "," + lon.round(9).astype(str)
    base = ok & ~key.duplicated().to_numpy()
    idx = np.flatnonzero(base)
    polys = X.polys_to_crs([P.polys[i] for i in idx], P.crs, X.crs(CRS_M))
    x, y = G.transform(lon.to_numpy()[idx], lat.to_numpy()[idx], 4326, CRS_M)
    L = pd.DataFrame({"blklot": a.blklot.to_numpy()[idx], "x": x, "y": y, "acres": G.areas(polys) / 4046.8564224})
    # every active blklot (condo sub-lots too) -> its base lot
    base_of = pd.Series(np.arange(len(idx)), index=key.to_numpy()[idx])
    blk = pd.Series(key[ok].map(base_of).to_numpy(), index=a.blklot.to_numpy()[ok])
    za, zp = layer("sf_zoning_districts.geojson", ["zoning"])
    h9a, h9p = layer("sf_zoning_2009.geojson", ["zoning_sim", "districtna"])
    pa, pp = layer("sf_planning_areas_datasf.geojson", ["planarea"])
    sa, sp = layer("sf_sud.geojson", ["name"])
    k = X.first_within(x, y, zp)
    L["cur"] = np.where(k >= 0, za.zoning.to_numpy()[np.clip(k, 0, None)], "")
    k = X.first_within(x, y, h9p)
    L["z09"] = np.where(k >= 0, h9a.zoning_sim.to_numpy()[np.clip(k, 0, None)], "")
    L["z09name"] = np.where(k >= 0, h9a.districtna.to_numpy()[np.clip(k, 0, None)], "")

    def in_named(attrs, polys, col, names):
        sel = [polys[i] for i in np.flatnonzero(attrs[col].isin(names).to_numpy())]
        return G.points_in_any(x, y, sel, union=True) if sel else np.zeros(len(x), bool)
    mo_area = in_named(pa, pp, "planarea", {MO_AREA})
    en08 = in_named(pa, pp, "planarea", EN_2008_AREAS)
    en_all = in_named(pa, pp, "planarea", EN_ALL_AREAS)
    sud = in_named(sa, sp, "name", SUD_OUT)
    schlage = in_named(sa, sp, "name", {"Visitacion Valley/Schlage SUD"})
    roles = pd.read_csv(ROOT / "reference/parking_t57_sf_districts.csv")
    clean = set(roles.loc[roles.role == "control", "zoning"]) - CONTROL_DROP
    mo = (L.z09.isin(MO_2009) | ((L.z09 == "NCT") & L.z09name.isin(MO_2009_NCT))).to_numpy() & mo_area
    en = L.cur.isin(EN_CURRENT).to_numpy() & en08 & ~schlage
    ctrl = L.cur.isin(clean).to_numpy() & L.z09.isin(CONTROL_2009).to_numpy() & ~mo_area & ~en_all & ~sud
    assert not (mo & en).any() and not ((mo | en) & ctrl).any()
    L["arm"] = np.where(mo | en, "T", np.where(ctrl, "C", ""))
    L["wave_area"] = np.where(mo, "Market-Octavia (2008)", np.where(en, "Eastern Neighborhoods (2009)", ""))
    for bad in ("C-3-G", "RH DTR", "SB-DTR", "TB DTR", "NCT-VALENCIA", "NCT-SOMA", "NCT-1", "NCT-2"):
        assert not (L.arm.eq("T") & L.cur.eq(bad) & ~mo).any(), bad
    x0, y0 = np.floor(x.min() / CELL_M) * CELL_M, np.floor(y.min() / CELL_M) * CELL_M
    L["cluster"] = ((y - y0) // CELL_M).astype(int) * 10000 + ((x - x0) // CELL_M).astype(int)
    diag = dict(parcels_file=int(len(a)), parcels_without_centroid=int((~ok).sum()), lots_after_condo_fold=int(len(L)),
                lots_treated_market_octavia=int(mo.sum()), lots_treated_eastern_neighborhoods=int(en.sum()),
                lots_control=int(ctrl.sum()), control_districts_used=sorted(clean))
    return L, diag, blk


def permits(L: pd.DataFrame, blk: pd.Series) -> tuple[pd.DataFrame, dict]:
    p = pd.DataFrame(json.loads((D / "sf_permits_2003.json").read_text()))
    n = len(p)
    p = p[(p.status != "cancelled") & p.permit_type.isin(["1", "2"])].copy()
    p["units"] = pd.to_numeric(p.proposed_units, errors="coerce").fillna(0)
    p["year"] = pd.to_datetime(p.issued_date, errors="coerce").dt.year
    p = p[(p.units > 0) & p.year.notna()].copy()
    p["year"] = p.year.astype(int)
    i = (p.block.astype(str) + p.lot.astype(str)).map(blk).fillna(-1).astype(int).to_numpy()
    lon = p.location.map(lambda g: g["coordinates"][0] if isinstance(g, dict) else np.nan).to_numpy(float)
    lat = p.location.map(lambda g: g["coordinates"][1] if isinstance(g, dict) else np.nan).to_numpy(float)
    need = (i < 0) & np.isfinite(lon) & np.isfinite(lat)
    by_id = int((i >= 0).sum())
    if need.any():
        px, py = G.transform(lon[need], lat[need], 4326, CRS_M)
        dd, nn = cKDTree(np.c_[L.x, L.y]).query(np.c_[px, py])
        i[np.flatnonzero(need)[dd <= NEAR_M]] = nn[dd <= NEAR_M]
    p["lot"] = i
    return p[p.lot >= 0], dict(permits_file_rows=n, new_construction_with_units=int(len(p)), placed_by_blocklot=by_id,
                               placed_by_point=int((i >= 0).sum()) - by_id, unplaced=int((i < 0).sum()))


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "data/processed/t57"))
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    L, diag, blk = lots_table()
    p, dp = permits(L, blk)
    diag.update(dp)
    arm = L.arm.to_numpy()
    p = p[arm[p.lot.to_numpy()] != ""]
    p = p[p.year.isin(list(YEARS))]
    T = L[L.arm != ""]
    A = pd.concat([pd.DataFrame({"cluster": T.cluster, "arm": T.arm, "year": y, "acres": T.acres}) for y in YEARS])
    A = A.groupby(["cluster", "arm", "year"], as_index=False)["acres"].sum()
    p["cluster"], p["arm"] = L.cluster.to_numpy()[p.lot.to_numpy()], arm[p.lot.to_numpy()]
    U = p.groupby(["cluster", "arm", "year"], as_index=False).agg(units=("units", "sum"), jobs=("units", "size"))
    P = A.merge(U, on=["cluster", "arm", "year"], how="outer").fillna({"acres": 0.0, "units": 0.0, "jobs": 0})
    P["jobs"], P["year"] = P.jobs.astype(int), P.year.astype(int)
    P = P.sort_values(["cluster", "arm", "year"])[["cluster", "arm", "year", "units", "jobs", "acres"]]
    P.to_csv(out / "panel_sf_a.csv", index=False)
    (out / "build_sf_diag.json").write_text(json.dumps(diag, indent=1, default=str) + "\n")
    print(f"wrote {out / 'panel_sf_a.csv'}: {len(P):,} rows; {out / 'build_sf_diag.json'} (whole-file totals only)")


if __name__ == "__main__":
    main()
