"""Chicago station-area lot tables (docs/tod/STATION_AREA_PLAN.md, LOCKED section, audit section G, owner answers).

Cases
- chicago_2015: the 2015 transit-served location ordinance (lot-model case; reform year and windows read from the lot
  model's table, unit "chicago": before = window_first..eff-1, after = eff+1..window_last). Reform area: lots zoned
  B or C with a -3 or -5 bulk suffix in November 2012 within 1,320 ft (402 m) of a CTA or Metra station in Chicago
  (the lot model's treatment rule).
- chicago_2022: Connected Communities (adopted 20 Jul 2022): before 2016-21, after 2023-25. Reform area: 1/2 mile
  (805 m) of CTA and Metra rail stations inside Chicago (main version; the ordinance's bus corridors are not published
  as a list, so no bus version is built).

Stops: national transit map rail stops (platforms within 150 m merged), tagged to 2024 Census places. Reform = stops in
Chicago. Comparison = CTA stops in Evanston, Skokie, Oak Park, Forest Park, Cicero and Metra stops in the inner Cook
County suburbs listed in COMPARISON_PLACES. Each lot is matched to the nearest stop on its own side (Chicago lots to
Chicago stops, suburban lots to comparison stops), so no Chicago lot is counted as comparison or the reverse.

New homes: county year built on both sides (owner, 15:57), from three Cook County Assessor files (open data):
- residential characteristics (houses, townhouses, 2-6 flats; homes per card from the apartments field), 2026 file;
- condominium unit characteristics (one home per unit PIN, parking and common-area PINs left out), 2026 file;
- commercial valuation sheets (apartment buildings of 7+ homes and mixed use: total units and year built), latest
  sheet per building, 2021-2025.
Chicago's own permits (units parsed from text, staged-permit merge) are attached as a check column on Chicago lots only.
Lot = Assessor land parcel (first 10 digits of the PIN), placed at the mean of its PIN points (2026 parcel universe).
Parcel ids stay in data/ only.
"""
from __future__ import annotations

import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from missing_middleware import geom_extra_station as X  # noqa: E402
from missing_middleware.paths import RAW  # noqa: E402

CRS = 5070
QUARTER, HALF, MILE = 402.0, 805.0, 1609.0
COOK = RAW / "tod_radius_programs" / "cook"
CACHE = ROOT / "data" / "processed" / "tod_station_area"
SOCRATA = "https://datacatalog.cookcountyil.gov/resource"


def _lot_model_windows() -> dict:
    p = ROOT / "data" / "processed" / "tod_lot_model" / "lots_rebuilt_halfmile.parquet"
    d = pd.read_parquet(p, columns=["unit", "eff_year", "window_first", "window_last"])
    r = d[d.unit.astype(str) == "chicago"].iloc[0]
    e = int(r.eff_year)
    return {"eff": e, "before": (int(r.window_first), e - 1), "after": (e + 1, int(r.window_last))}


CASES = {
    "chicago_2015": _lot_model_windows(),
    "chicago_2022": {"eff": 2022, "before": (2016, 2021), "after": (2023, 2025)},
}

# Comparison cities: CTA (Evanston, Skokie, Oak Park, Forest Park, Cicero) plus Metra in inner Cook County suburbs
# (places touching or near Chicago). Own TOD rezoning in the window is listed in OWN_TOD.
COMPARISON_PLACES = ["Evanston", "Skokie", "Oak Park", "Forest Park", "Cicero", "Berwyn", "River Forest", "Maywood",
                     "Bellwood", "Melrose Park", "River Grove", "Franklin Park", "Schiller Park", "Rosemont",
                     "Park Ridge", "Des Plaines", "Morton Grove", "Wilmette", "Kenilworth", "Winnetka", "Glencoe",
                     "Niles", "Riverside", "Brookfield", "La Grange", "Western Springs", "Summit", "Oak Lawn",
                     "Evergreen Park", "Blue Island", "Calumet Park", "Riverdale", "Harvey", "Dolton",
                     "Hazel Crest", "Homewood", "Chicago Ridge", "Worth", "Palos Heights", "Hometown"]
OWN_TOD = {}
EVENTS: dict[str, pd.DataFrame] = {}   # case -> one row per new-building record (see build)   # filled in the report after checking sources (see module notes at the end)


# --------------------------------------------------------------------------- fetch (Cook County open data; local only)

def _socrata_csv(dataset: str, select: str, where: str, out: Path, order: str = "pin", page: int = 200_000) -> Path:
    """Fetch a Socrata query to CSV in pages (no owner or taxpayer fields are ever selected)."""
    if out.exists():
        return out
    parts, off = [], 0
    while True:
        q = urllib.parse.urlencode({"$select": select, "$where": where, "$order": order, "$limit": page, "$offset": off})
        url = f"{SOCRATA}/{dataset}.csv?{q}"
        for k in range(5):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "housing-policy-model/0.1"}), timeout=600) as r:
                    txt = r.read().decode()
                break
            except Exception:
                if k == 4:
                    raise
                time.sleep(10 * (k + 1))
        lines = txt.splitlines()
        if off == 0:
            parts.append(lines[0])
        body = lines[1:]
        parts.extend(body)
        print(f"  {dataset}: {off + len(body)} rows", flush=True)
        if len(body) < page:
            break
        off += page
    tmp = out.with_suffix(".part")
    tmp.write_text("\n".join(parts) + "\n")
    tmp.rename(out)
    return out


def fetch() -> dict[str, Path]:
    return {
        "universe": _socrata_csv("nj4t-kc8j", "pin,pin10,class,lon,lat,census_place_geoid", "year='2026'",
                                 COOK / "parcel_universe_2026.csv"),
        "res": _socrata_csv("x54s-btds", "pin,card,class,char_yrblt,char_apts,char_land_sf", "year='2026.0'",
                            COOK / "res_characteristics_2026.csv"),
        "condo": _socrata_csv("3r7i-mrz4", "pin,pin10,class,char_yrblt,is_parking_space,is_common_area,char_land_sf",
                              "year='2026.0'", COOK / "condo_characteristics_2026.csv"),
        "comm": _socrata_csv("csik-bsws", "keypin,pins,year,township,sheet,class_es,tot_units,studiounits,_1brunits,_2brunits,_3brunits,_4brunits,"
                             "finalmarketvalue,finalmarketvalue_unit,yearbuilt,landsf,property_type_use",
                             "year>='2021'", COOK / "commercial_valuation_2021_2025.csv", order="keypin,year"),
    }


# --------------------------------------------------------------------------- stops

def stations() -> pd.DataFrame:
    """CTA (NTD 50066) and Metra (NTD 50118) stops from the national transit map, platforms within 150 m merged into
    one station, tagged with their 2024 Census place."""
    import json
    s = pd.DataFrame(json.load(open(RAW / "tod_census_cases" / "ntm_rail_stops.json"))).dropna(subset=["stop_lat", "stop_lon"])
    s = s[s.stop_lon.between(-88.4, -87.5) & s.stop_lat.between(41.4, 42.5) & s.ntd_id.astype(str).isin(["50066", "50118"])]
    s["stop_type_text"] = np.where(s.ntd_id.astype(str) == "50066", "CTA rail", "Metra")
    g = s[["stop_name", "stop_type_text"]].copy()
    g["x"], g["y"] = X.transform(s.stop_lon.values.astype(float), s.stop_lat.values.astype(float), 4326, CRS)
    out = []
    for t, gg in g.groupby("stop_type_text"):   # merge platforms within one agency only
        cx, cy, i = X.merge_stops(gg.x.values, gg.y.values, 75.0)
        j = gg[["stop_name", "stop_type_text"]].iloc[i].reset_index(drop=True)
        j["x"], j["y"] = cx, cy
        out.append(j)
    S = pd.concat(out, ignore_index=True)
    p = X.read_vector(RAW / "census_cb_2024" / "cb_2024_us_place_500k.zip", dst=CRS, columns=["NAME", "STATEFP"])
    p = p[p.STATEFP == "17"].reset_index(drop=True)
    k = X.first_within(S.x.values, S.y.values, list(p.geometry))
    S["place"] = pd.Series(np.where(k >= 0, p.NAME.values[np.maximum(k, 0)], None), index=S.index, dtype=object).where(k >= 0)
    S["group"] = np.where(S.place == "Chicago", "reform", np.where(S.place.isin(COMPARISON_PLACES), "comparison", "other"))
    S = S[S.group != "other"].reset_index(drop=True)
    S["stop_id"] = np.arange(len(S))
    return S[["stop_id", "stop_name", "stop_type_text", "group", "place", "x", "y"]]


# --------------------------------------------------------------------------- homes records (county year built)

APTS = {"Two": 2, "Three": 3, "Four": 4, "Five": 5, "Six": 6}


def _num(x) -> pd.Series:
    return pd.to_numeric(x, errors="coerce")


NOT_HOMES = r"hotel|motel|sro|nursing|hospital|hosp|health|psychiatric|treatment|assisted|skilled|parking|boat|storage|dorm|retirment|retirement"


def apartment_rows(m: pd.DataFrame) -> pd.Series:
    """Commercial-sheet rows whose units are homes: residential apartment classes (3xx; 9xx incentive apartments) or
    other classes (mixed use 5xx, 7xx, 8xx) whose use says multifamily, affordable or senior residences. Hotel rooms,
    nursing and hospital beds, assisted living, parking, storage and boat slips are left out (units there are not
    homes; e.g. class 529 motels carry about 39,000 "units"). Class 2xx rows are left to the residential file."""
    cls = m.class_es.fillna("").str.replace("-", "").str.split(",").str[0].str.strip()
    use = m.property_type_use.fillna("").str.lower()
    res_class = cls.str.match(r"^(3|9)\d\d$")
    res_use = use.str.contains("multifamily|multi-family|affordable|senior residences")
    return (res_class | (cls.str.match(r"^[578]\d\d$") & res_use)) & ~use.str.contains(NOT_HOMES)


def apartment_units(m: pd.DataFrame) -> pd.Series:
    """Homes in a commercial-sheet building: the total-units field where filled; else the sum of the unit-mix fields
    (studio to 4-bedroom; the north-triad sheets of 2022 and 2025 leave the total empty or 0); else market value over
    market value per unit (rounded)."""
    tot = _num(m.tot_units)
    mix = sum(_num(m[c]).fillna(0) for c in ("studiounits", "_1brunits", "_2brunits", "_3brunits", "_4brunits"))
    fmv, per = _num(m.finalmarketvalue), _num(m.finalmarketvalue_unit)
    ratio = (fmv / per.where(per > 1000)).round()
    out = tot.where(tot > 0, mix.where(mix > 0, ratio))
    return out.where(out > 0)


def records() -> pd.DataFrame:
    """One row per building record with homes: pin10, yb (year built, NaN unknown), units, src."""
    f = fetch()
    r = pd.read_csv(f["res"], dtype=str)
    r = r[r["class"] != "299"]
    u = r.char_apts.map(APTS)
    multi = r["class"].isin(["211", "212"])
    units = np.where(multi, u.fillna(pd.Series(np.where(r["class"] == "211", 2, 1), index=r.index)), 1)
    R1 = pd.DataFrame({"pin10": r.pin.str[:10], "yb": _num(r.char_yrblt), "units": units.astype(float), "src": "res"})
    c = pd.read_csv(f["condo"], dtype=str)
    c = c[(c.is_parking_space.str.lower() != "true") & (c.is_common_area.str.lower() != "true")].drop_duplicates("pin")
    R2 = pd.DataFrame({"pin10": c.pin.str[:10], "yb": _num(c.char_yrblt), "units": 1.0, "src": "condo"})
    m = pd.read_csv(f["comm"], dtype=str)
    m["units"] = apartment_units(m)
    m["yr"] = _num(m.year)
    m["yb"] = _num(m.yearbuilt).where(_num(m.yearbuilt).between(1800, 2026))
    m = m[(m.units > 0) & apartment_rows(m)].sort_values("yr")
    first_yb = m.groupby("keypin").yb.min()        # sheets disagree on year built for some new buildings (2020 vs 2022):
    m = m.drop_duplicates("keypin", keep="last")   # earliest year on any sheet; units from the latest sheet
    m["yearbuilt"] = m.keypin.map(first_yb)
    R3 = pd.DataFrame({"pin10": m.keypin.str.replace("-", "").str[:10], "yb": _num(m.yearbuilt), "units": m.units,
                       "src": "apartments", "sheet_year": m.yr})
    R = pd.concat([R1, R2, R3], ignore_index=True)
    R.loc[~R.yb.between(1800, 2026), "yb"] = np.nan
    return R


def lots() -> pd.DataFrame:
    """Lots (Assessor land parcels, PIN10) with points, place, class, values, acres, year built (cached in data/)."""
    cache = CACHE / "_cook_lots.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    f = fetch()
    U = pd.read_csv(f["universe"], dtype=str)
    U["lon"], U["lat"] = _num(U.lon), _num(U.lat)
    U["pin10"] = U.pin10.fillna(U.pin.str[:10])
    g = U.groupby("pin10")
    L = pd.DataFrame({"lon": g.lon.mean(), "lat": g.lat.mean(), "use": g["class"].agg(lambda x: x.mode().iat[0] if len(x.mode()) else ""),
                      "place_geoid": g.census_place_geoid.first(), "pins": g.size()})
    pl = X.read_vector(RAW / "census_cb_2024" / "cb_2024_us_place_500k.zip", columns=["GEOID", "NAME", "STATEFP"], geometry=False)
    pl = pl[pl.STATEFP == "17"]
    L["city_name"] = L.place_geoid.map(dict(zip(pl.GEOID, pl.NAME))).fillna("Unincorporated")
    L["public"] = L.use.eq("EX")
    # values: certified assessed values (level differs by class: about 10% of market for homes, 25% commercial)
    for yr in (2016, 2024):
        v = pd.read_csv(COOK / f"assessed_values_{yr}.csv", dtype={"pin": str})
        v["pin10"] = v.pin.str[:10]
        vv = v.groupby("pin10")[["certified_land", "certified_bldg"]].sum()
        L[f"land_value_{yr}"] = vv.certified_land.reindex(L.index)
        L[f"bldg_value_{yr}"] = vv.certified_bldg.reindex(L.index)
    # acres: land square feet from the characteristic files (res per PIN summed; condo and apartment per building)
    r = pd.read_csv(f["res"], dtype=str, usecols=["pin", "char_land_sf"])
    r = r.assign(sf=_num(r.char_land_sf), pin10=r.pin.str[:10]).groupby("pin").agg(pin10=("pin10", "first"), sf=("sf", "max"))
    a1 = r.groupby("pin10").sf.sum()
    c = pd.read_csv(f["condo"], dtype=str, usecols=["pin", "char_land_sf"])
    a2 = c.assign(sf=_num(c.char_land_sf), pin10=c.pin.str[:10]).groupby("pin10").sf.max()
    m = pd.read_csv(f["comm"], dtype=str, usecols=["keypin", "landsf"])
    a3 = m.assign(sf=_num(m.landsf), pin10=m.keypin.str.replace("-", "").str[:10]).groupby("pin10").sf.max()
    L["acres"] = pd.concat([a1, a2, a3], axis=1).max(axis=1).reindex(L.index) / 43560.0
    # land areas under 200 sq ft (condo records with a prorated or placeholder 1 sq ft) or over 2,000 acres are errors
    L.loc[(L.acres < 200 / 43560.0) | (L.acres > 2000), "acres"] = np.nan
    # township (2024 universe) and the last commercial (apartment) sheet year of its assessment triad: apartments
    # finished after that sheet are not yet in the county file (Chicago 2024, north suburbs 2025, south suburbs 2023)
    t = pd.read_csv(COOK / "parcel_universe_2024.csv", dtype=str, usecols=["pin", "township_name"])
    L["township"] = t.assign(pin10=t.pin.str[:10]).drop_duplicates("pin10").set_index("pin10").township_name.reindex(L.index)
    m = pd.read_csv(f["comm"], dtype=str, usecols=["township", "year"])
    L["apt_sheet_last"] = L.township.map(m.assign(y=_num(m.year)).groupby("township").y.max())
    L = L.dropna(subset=["lon", "lat"])
    G = L.copy()
    G["x"], G["y"] = X.transform(L.lon.values.astype(float), L.lat.values.astype(float), 4326, CRS)
    CACHE.mkdir(parents=True, exist_ok=True)
    G.to_parquet(cache)
    return G


# --------------------------------------------------------------------------- Chicago permits (check, Chicago lots only)

def chicago_permits() -> pd.DataFrame:
    """City of Chicago new-construction permits: units parsed from the work description, staged permits merged
    (lot model rule: same point within 1 m, issued within 18 months, unit counts within 10%; larger count kept)."""
    from missing_middleware.tod import case_chicago as CH
    d = pd.read_csv(RAW / "tod_cases" / "chicago" / "permits_new_construction.csv", dtype=str).drop_duplicates("permit_")
    d["units"] = d.work_description.map(CH.parse_units)
    d["year"] = _num(d.issue_date.str[:4])
    d = d[(d.units > 0) & d.year.notna()].dropna(subset=["latitude", "longitude"])
    g = d.copy()
    g["x"], g["y"] = X.transform(_num(d.longitude).values, _num(d.latitude).values, 4326, CRS)
    n0, u0 = len(g), g.units.sum()
    g = CH.dedupe_staged_relaxed(g)
    # second pass (fit-and-fix, round 3): partial-stage permits (caissons, piles, foundation, "superstructure through",
    # "phase 1") at the same point as another permit for 20+ homes within 4 years are the same building; the stage
    # permit is merged into its partner whatever the unit counts (the lot-model merge needs counts within 10% and 18
    # months). The merged record keeps the earlier issue year (construction start, as the Census survey dates it)
    # and the larger home count.
    stage = g.work_description.str.upper().str.contains(r"CAISSON|PILES|FOUNDATION|SUPERSTRUCTURE|PHASE 1|EXCAVATION", na=False)
    g["_pt"] = g.x.round().astype(int).astype(str) + "_" + g.y.round().astype(int).astype(str)
    drop = set()
    for _, q in g[g.units >= 20].groupby("_pt"):
        if len(q) < 2:
            continue
        for i in q.index[stage.loc[q.index]]:
            if i in drop:
                continue
            o = q.drop(index=[i, *drop], errors="ignore")
            o = o[(o.year - q.at[i, "year"]).abs() <= 4]
            if o.empty:
                continue
            j = (o.year - q.at[i, "year"]).abs().sort_values().index[0]
            g.at[j, "year"] = min(g.at[i, "year"], g.at[j, "year"])
            g.at[j, "units"] = max(g.at[i, "units"], g.at[j, "units"])
            drop.add(i)
    g = g.drop(index=list(drop))
    g.attrs["staged_removed"] = (n0 - len(g), float(u0 - g.units.sum()))
    return g[["year", "units", "work_description", "x", "y"]]


# --------------------------------------------------------------------------- build

def build(case: str):
    c = CASES[case]
    (b0, b1), (a0, a1) = c["before"], c["after"]
    S = stations()
    L = lots()
    R = records()
    chi = L.city_name.eq("Chicago")
    parts = []
    for side, mask in (("reform", chi), ("comparison", ~chi)):
        st = S[S.group == side]
        lm = L.loc[mask]
        i, d = X.nearest_lowest(lm.x.values, lm.y.values, st.x.values, st.y.values, MILE)
        ok = i >= 0
        parts.append(pd.DataFrame({"stop_id": st.stop_id.values[i[ok]], "group": st.group.values[i[ok]], "dist_m": d[ok]},
                                  index=lm.index[ok]))
    near = pd.concat(parts)
    D = L.loc[near.index].copy()
    D[["stop_id", "group", "dist_m"]] = near
    D["band"] = pd.cut(D.dist_m, [-1, QUARTER, HALF, MILE], labels=["0-1/4", "1/4-1/2", "1/2-1"]).astype(str)
    D["place_of_stop"] = D.stop_id.map(S.set_index("stop_id").place)

    # homes from county year built (same source both sides)
    R = R[R.pin10.isin(D.index)]
    yb = R.yb
    D["homes_before_win"] = R[yb.between(b0, b1)].groupby("pin10").units.sum().reindex(D.index).fillna(0)
    D["homes_after_win"] = R[yb.between(a0, a1)].groupby("pin10").units.sum().reindex(D.index).fillna(0)
    D["homes_existing"] = R[~(yb >= b0)].groupby("pin10").units.sum().reindex(D.index).fillna(0)
    D["homes_now"] = R.groupby("pin10").units.sum().reindex(D.index).fillna(0)
    for src in ("res", "condo", "apartments"):
        w = R[(R.src == src)]
        D[f"after_{src}"] = w[w.yb.between(a0, a1)].groupby("pin10").units.sum().reindex(D.index).fillna(0)
        D[f"before_{src}"] = w[w.yb.between(b0, b1)].groupby("pin10").units.sum().reindex(D.index).fillna(0)
    D["year_built"] = R.groupby("pin10").yb.min().reindex(D.index)
    vy = 2016   # earliest values on file (after the 2015 reform year; before the 2022 one)
    D["land_value"], D["bldg_value"] = D[f"land_value_{vy}"], D[f"bldg_value_{vy}"]
    D["source"] = "county year built (both sides): Cook res characteristics, condo units, commercial apartment sheets"

    # Chicago permits as a check column (Chicago lots only; nearest lot within 60 m)
    P = chicago_permits()
    Lc = L.loc[chi, ["x", "y"]]
    ni, _ = X.nearest_lowest(P.x.values, P.y.values, Lc.x.values, Lc.y.values, 60.0)
    pj = P.copy()
    pj["index_right"] = pd.Series(np.where(ni >= 0, Lc.index.values[np.maximum(ni, 0)], None), index=P.index, dtype=object).where(ni >= 0)
    for lab, (x, y) in {"permits_before_win": (b0, b1), "permits_after_win": (a0, a1)}.items():
        w = pj[pj.year.between(x, y)]
        D[lab] = w.groupby("index_right").units.sum().reindex(D.index)
        D.loc[D.city_name.eq("Chicago"), lab] = D.loc[D.city_name.eq("Chicago"), lab].fillna(0)

    # reform area
    if case == "chicago_2022":
        D["in_reform_area"] = D.group.eq("reform") & (D.dist_m <= HALF)
    else:
        from missing_middleware.tod import case_chicago as CH
        z = X.read_vector(RAW / "tod_cases" / "chicago" / "zoning_nov2012.zip", dst=CRS)
        zcol = next(k for k in z.columns if k.upper() in ("ZONE_CLASS", "ZONING", "ZONE_TYPE_CLASS", "ZONING_CLA", "ZONE_CLA"))
        k = X.first_within(D.x.values, D.y.values, list(z.geometry))
        D["zoning_2012"] = pd.Series(np.where(k >= 0, z[zcol].values[np.maximum(k, 0)], None), index=D.index, dtype=object).where(k >= 0)
        D["in_reform_area"] = D.group.eq("reform") & (D.dist_m <= QUARTER) & D.zoning_2012.map(CH.tod_far_gain).notna()

    D["case"] = case
    D["implausible"] = False
    D["_yb"] = [()] * len(D)
    D["_un"] = [()] * len(D)
    D["lot_key"] = D.index          # PIN10: stays in data/ (the builder writes the table to data/processed)
    D = D.reset_index(drop=True)
    pos = pd.Series(D.index, index=D.lot_key)
    # events: one row per new-building record placed on a lot, any year from 2000 on (windows can be shifted later)
    e1 = R[R.yb >= 2000]
    E1 = pd.DataFrame({"lot_index": e1.pin10.map(pos).values, "homes": e1.units.values, "permit_year": np.nan,
                       "completed_year": e1.yb.values, "preferred": "completed",
                       "source": ("county year built: " + e1.src).values})
    e2 = pj[(pj.year >= 2000) & pj.index_right.isin(pos.index)]
    E2 = pd.DataFrame({"lot_index": e2.index_right.map(pos).values, "homes": e2.units.values,
                       "permit_year": e2.year.values.astype(float), "completed_year": np.nan, "preferred": "permit",
                       "source": "Chicago permits, staged merged (check; Chicago lots only)"})
    EVENTS[case] = pd.concat([E1, E2], ignore_index=True)
    D.attrs["permits_unplaced"] = float(pj[pj.index_right.isna() & pj.year.between(b0, a1)].units.sum())
    keep = ["case", "city_name", "group", "stop_id", "place_of_stop", "dist_m", "band", "in_reform_area", "acres", "township", "apt_sheet_last",
            "land_value", "bldg_value", "year_built", "use", "public", "homes_existing", "homes_now", "homes_before_win",
            "homes_after_win", "before_res", "before_condo", "before_apartments", "after_res", "after_condo",
            "after_apartments", "permits_before_win", "permits_after_win", "source", "implausible", "lot_key", "_yb", "_un", "x", "y"]
    return D[keep + (["zoning_2012"] if "zoning_2012" in D else [])].copy(), S


# --------------------------------------------------------------------------- checks (approach test; Census ratios)

def checks() -> None:
    """(a) new PINs between the 2016 and 2024 parcel universes vs (c) county year built; (b) Chicago permits vs
    county year built vs the Census permit survey, by year, citywide."""
    pd.set_option("display.width", 200)
    pl = X.read_vector(RAW / "census_cb_2024" / "cb_2024_us_place_500k.zip", columns=["GEOID", "NAME", "STATEFP"], geometry=False)
    name = dict(zip(pl[pl.STATEFP == "17"].GEOID, pl[pl.STATEFP == "17"].NAME))
    u16 = pd.read_csv(COOK / "parcel_universe_2016.csv", dtype=str, usecols=["pin", "class", "census_place_geoid"])
    u24 = pd.read_csv(COOK / "parcel_universe_2024.csv", dtype=str, usecols=["pin", "class", "census_place_geoid"])
    new = u24[~u24.pin.isin(u16.pin)].copy()
    new["place"] = new.census_place_geoid.map(name)
    new["side"] = np.where(new.place == "Chicago", "Chicago", np.where(new.place.isin(COMPARISON_PLACES), "comparison suburbs", "other"))
    new["kind"] = np.where(new["class"] == "299", "condo 299", np.where(new["class"].str.startswith("3"), "apartment 3xx",
                  np.where(new["class"].str.startswith("2"), "other residential 2xx", "non-residential")))
    print("(a) PINs new in the 2024 parcel universe (absent in 2016), by kind:")
    print(new.groupby(["side", "kind"]).size().unstack().fillna(0).astype(int).to_string())
    R = records()
    U = pd.read_csv(fetch()["universe"], dtype=str, usecols=["pin10", "census_place_geoid"]).drop_duplicates("pin10")
    R["place"] = R.pin10.map(dict(zip(U.pin10, U.census_place_geoid))).map(name)
    R["side"] = np.where(R.place == "Chicago", "Chicago", np.where(R.place.isin(COMPARISON_PLACES), "comparison suburbs", "other"))
    w = R[R.yb.between(2016, 2023)]
    print("(c) county year built 2016-2023, homes by source:")
    print(w.groupby(["side", "src"]).units.sum().unstack().round(0).to_string())
    print("year built missing (records with homes):", R.groupby("src").yb.apply(lambda s: round(s.isna().mean(), 3)).to_dict())
    # Chicago: county year built vs permits vs Census permit survey
    from missing_middleware.tod.control_cities import read_bps
    bps = read_bps(RAW / "tod_control_cities" / "bps", years=range(2006, 2026))
    bps = bps[(bps.state == "17") & bps.name.str.fullmatch(r"Chicago(\s*city)?", case=False)].groupby("year").units.sum()
    P = chicago_permits()
    print("staged permits removed (records, homes):", P.attrs.get("staged_removed"))
    yb = R[R.side == "Chicago"].groupby("yb").units.sum()
    pm = P.groupby("year").units.sum()
    T = pd.DataFrame({"census_permits": bps, "city_permits": pm, "county_year_built": yb}).loc[2006:2025]
    T["permits/census"] = T.city_permits / T.census_permits
    T["yearbuilt/census"] = T.county_year_built / T.census_permits
    print(T.round(2).to_string())
    for lab, (a, b) in {"2009-14": (2009, 2014), "2016-20": (2016, 2020), "2016-21": (2016, 2021), "2023-25": (2023, 2025)}.items():
        t = T.loc[a:b].sum()
        print(f"Chicago {lab}: Census {t.census_permits:.0f}; permits {t.city_permits:.0f} ({t.city_permits / t.census_permits:.2f}); "
              f"county year built {t.county_year_built:.0f} ({t.county_year_built / t.census_permits:.2f})")


if __name__ == "__main__":
    fetch() if "--fetch" in sys.argv else checks()
