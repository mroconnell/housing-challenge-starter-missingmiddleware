"""WRITTEN AFTER THE MAIN RESULTS WERE SEEN (2026-11-05); it follows the spec fixed before the first run.

CA AB 2097 study: side checks from the spec fixed in the plan before the first estimate run (plan section 9, entry
"exact spec of the bus side checks"). Parts 2, 3 and 5 of that spec; part 1 (dated 2022 bus map from archived
schedules) is a separate script. Written after the main results were seen; it follows the pre-written spec, and any
choice not in that spec is marked "not in the spec".

    uv run python scripts/ca_ab2097_side_checks.py --fetch   # city map layers (features) and MTC 2017 item metadata
    uv run python scripts/ca_ab2097_side_checks.py --run

Part 5, city maps (Ryan 2026-11-05 16:42: unlicensed city layers may be used as research inputs, kept out of git).
- Oakland: "Parking Reduction Near Major Transit - AB 2097", stops as of Spring 2023, 15-minute rule
  (gisapps1.mapoakland.com MapServer/22). Truckee: Train Depot half-mile layer. Sacramento (placebo city): city
  "AB 2097 Parking" layer. Palo Alto: rebuilt as 1/2-mile circles around its Caltrain stations (Palo Alto,
  California Ave, San Antonio) from reference/ca_ab2097_rail_stations.csv. Santa Cruz (PDF of circles around many bus
  stops): NOT done here; it needs the PDF's stops matched by hand, listed as pending.
- Per city: 2020 homes inside the city map, inside our main map's 1/2-mile area, in both, in either; agreement =
  both / either (blocks by internal point, as elsewhere).
- Edge on each city's own line: blocks and permits 25-150 m inside the line vs 25-150 m outside it (= the spec's
  "0-150 m with a 25 m donut"), homes other than
  ADUs per 1,000 existing homes a year, 2023-2025 vs 2018-2022, 90% range from 2,000 resamples of projects (one city).
  The city's own jurisdiction only.

Part 2, MTC 2017 (Bay Area, earlier map): reads MTC's ArcGIS item metadata for the 2017 layers and records the licence
  text. The data are fetched and used only if the licence text allows reuse; otherwise this part stops at the record.

Part 3, National Transit Database service: from the monthly file already on disk
  (data/raw/tod_stop_table/ntd/ntd_complete_monthly_ridership_8bui-9xvu.csv, public domain): California agencies'
  bus vehicle revenue hours (modes MB, RB, CB), calendar 2022 and the latest full calendar year, and the ratio.
  Described only. Matching NTD agencies to the archive's "qualifying 2022 copy" list is done by hand in the review.

Outputs (no addresses): reference/ca_ab2097_side_city_maps.csv, reference/ca_ab2097_side_ntd_bus_hours.csv,
reference/ca_ab2097_side_mtc_licence.json. Layers cached in data/raw/ca_ab2097/city_maps/ (git-ignored).
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import ca_ab2097_estimate as E  # noqa: E402
import run_ab2097_test as run  # noqa: E402
from missing_middleware import geom as G  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
from missing_middleware.tod import ab2097 as ab  # noqa: E402

UA = {"User-Agent": "missing-middleware-research/1.0 (public data)"}
MAPS = RAW / "ca_ab2097" / "city_maps"
CITY_LAYERS = {
    "OAKLAND": "https://gisapps1.mapoakland.com/oakgis/rest/services/Prod/CEDA_App_PRODGIS/MapServer/22",
    "TRUCKEE": "https://services5.arcgis.com/i75zh9vlhYUpqwjr/arcgis/rest/services/TraiinDepot_AB2097/FeatureServer/0",
    "SACRAMENTO": "https://services5.arcgis.com/54falWtcpty3V47Z/arcgis/rest/services/AB_2097_Parking/FeatureServer/0",
}
MTC_ITEMS = {"High Quality Transit Corridors - 1/2 Mile (2017)": "3ed055a3cff0415384bf4ce744b6f52b",
             "Major Transit Stops 2017 (item linked from MTC's GitHub)": "561dc5b42fa9451b95faf615a3054260",
             "Transit Priority Project Eligible Areas (2017)": "165d990e3d1341c4942b79e526eafe0f"}
PALO_ALTO_STATIONS = ("Palo Alto", "California Ave", "San Antonio")
# Santa Cruz (Ryan 2026-11-06 "you can rebuild that map"): the city's PDF (Coastal Commission exhibit 2, LCP-3-STC-23-0047-2
# Part C, hearing 2024-03-15) shows 1/2-mile circles around about 45 bus stops in five clusters. Rebuilt by matching the
# PDF's stop icons by eye to named Santa Cruz Metro stops (National Transit Map, NTD 90006, CC BY 3.0); approximate.
SANTA_CRUZ_RULES = [r"UCSC", r"^Bay Dr & (Meder|Iowa|Nobel|High)", r"^(High & Bay|Bay & High)", r"^Western Dr",
                    r"^High & Western", r"^Bay & (Escalona|King|Mission)",
                    r"^Mission & (Laurel|Trescony|Olive|Palm|Miramar|King|Swift)",
                    r"^(Laurel & (Center|Chestnut)|Front & Laurel)", r"^Water & (N Branciforte|Seabright|Poplar)"]
SANTA_CRUZ_STOPS = MAPS / "santa_cruz_metro_ntm_stops.json"
NTD = RAW / "tod_stop_table" / "ntd" / "ntd_complete_monthly_ridership_8bui-9xvu.csv"


def get(url: str, params: dict | None = None) -> bytes:
    q = ("?" + urllib.parse.urlencode(params)) if params else ""
    with urllib.request.urlopen(urllib.request.Request(url + q, headers=UA), timeout=180) as r:
        return r.read()


def fetch() -> None:
    MAPS.mkdir(parents=True, exist_ok=True)
    for city, url in CITY_LAYERS.items():
        f = MAPS / f"{city.lower()}.geojson"
        if not f.exists():
            f.write_bytes(get(url + "/query", {"where": "1=1", "outFields": "*", "outSR": "4326", "f": "geojson"}))
            print(f"{city}: {len(json.loads(f.read_text()).get('features', []))} features")
    rec = {}
    for name, item in MTC_ITEMS.items():
        try:
            j = json.loads(get(f"https://www.arcgis.com/sharing/rest/content/items/{item}", {"f": "json"}))
            rec[name] = {"item": item, "licenseInfo": j.get("licenseInfo"), "accessInformation": j.get("accessInformation"),
                         "modified": j.get("modified")}
        except Exception as e:  # noqa: BLE001 - record and move on
            rec[name] = {"item": item, "error": str(e)}
    (REFERENCE / "ca_ab2097_side_mtc_licence.json").write_text(json.dumps(rec, indent=1))
    print(json.dumps(rec, indent=1)[:2000])


def seg_distance(px, py, polys: list) -> np.ndarray:
    """Distance (m) from each point to the nearest polygon boundary segment, brute force in chunks."""
    seg, _ = G._segments(polys)
    ax, ay, bx, by = seg[:, 0], seg[:, 1], seg[:, 2], seg[:, 3]
    dx, dy = bx - ax, by - ay
    ll = np.maximum(dx * dx + dy * dy, 1e-12)
    out = np.empty(len(px))
    for i in range(0, len(px), 500):
        x, y = px[i:i + 500, None], py[i:i + 500, None]
        t = np.clip(((x - ax) * dx + (y - ay) * dy) / ll, 0, 1)
        out[i:i + 500] = np.min(np.hypot(x - (ax + t * dx), y - (ay + t * dy)), axis=1)
    return out


def city_polys(city: str, rail: pd.DataFrame):
    """City map as polygons in EPSG:3310, or None. Palo Alto is circles (64-gons) around its Caltrain stations."""
    if city == "SANTA CRUZ":
        import re
        from missing_middleware.geom_extra_station import _circle
        r = pd.DataFrame([x["attributes"] for x in json.loads(SANTA_CRUZ_STOPS.read_text())["features"]])
        s = r[r.stop_name.apply(lambda n: any(re.search(p_, n) for p_ in SANTA_CRUZ_RULES)) & (r.stop_lat < 37.002)]
        s = run.lonlat_points(s.reset_index(drop=True), s.stop_lon, s.stop_lat)
        return [[[_circle(x, y, E.MILE / 2)]] for x, y in zip(s.x, s.y)], len(s)
    if city == "PALO ALTO":
        from missing_middleware.geom_extra_station import _circle
        s = rail[rail["name"].str.contains("|".join(PALO_ALTO_STATIONS), case=False, na=False)
                 & (rail["mode"] == "commuter_rail")]
        s = run.lonlat_points(s.reset_index(drop=True), s.lon, s.lat)
        stations = s["name"].str.extract("(" + "|".join(PALO_ALTO_STATIONS) + ")", expand=False).nunique()
        return [[[_circle(x, y, E.MILE / 2)]] for x, y in zip(s.x, s.y)], stations
    f = MAPS / f"{city.lower()}.geojson"
    L = G.read_geojson(str(f)).to_crs(G.crs(run.CRS))
    return L.polys, len(L.polys)


def city_maps() -> pd.DataFrame:
    b = pd.read_parquet(E.CACHE / "blocks.parquet")
    bx = run.read_blocks(["GEOID20", "INTPTLAT20", "INTPTLON20"])[["GEOID20", "x", "y"]]
    b = b.merge(bx, on="GEOID20", how="left")
    a2 = pd.read_csv(RAW / "hcd_apr_a2" / "tablea2.csv", usecols=E.A2_COLS, low_memory=False)
    p = E.add_census_points(E.clean_permits_full(a2), set(E.raw_keys(a2)))
    p = p[p.lat.notna()].copy()
    p = run.lonlat_points(p, p.lon, p.lat)
    rail = pd.read_csv(REFERENCE / "ca_ab2097_rail_stations.csv")
    rows = []
    for city in ("OAKLAND", "TRUCKEE", "SACRAMENTO", "PALO ALTO", "SANTA CRUZ"):
        polys, n = city_polys(city, rail)
        bc, pc = b[b.juris == city].copy(), p[p.juris == city].copy()
        bin_ = G.points_in_any(bc.x.to_numpy(), bc.y.to_numpy(), polys)
        ours = (bc.zone_main == "near").to_numpy()
        h = bc.homes.to_numpy()
        both, either = h[bin_ & ours].sum(), h[bin_ | ours].sum()
        # edge on the city's own line
        for frame in (bc, pc):
            inside = G.points_in_any(frame.x.to_numpy(), frame.y.to_numpy(), polys)
            d = seg_distance(frame.x.to_numpy(), frame.y.to_numpy(), polys)
            frame["zone"] = np.where((d >= 25) & (d < 150), np.where(inside, "inside", "outside"), "other")
            frame["upz"] = False
        cells = bc.groupby(["juris", "upz", "zone"])[["homes", "acres"]].sum().reset_index()
        g = ab.Group(city, [city], ("inside", False), ("outside", False))
        r = ab.estimate(g, cells, pc, "homes_non_adu", "per_1000_homes", E.BEFORE, E.AFTER, draws=10)
        lo, hi, _ = ab.project_interval(g, cells, pc, "homes_non_adu", "per_1000_homes", E.BEFORE, E.AFTER)
        rows.append({"city": city, "role": "placebo city" if city in E.PLACEBO else "main",
                     "map_parts": n, "map_note": ("3 Caltrain stations, rebuilt from our station list, not the PDF; "
                                                  "agreement tests only bus-stop differences") if city == "PALO ALTO"
                     else ("rebuilt from the city's PDF by matching stop icons by eye to named stops; approximate"
                           if city == "SANTA CRUZ" else "city's own layer"), "homes_2020_city": float(h.sum()), "homes_in_city_map": float(h[bin_].sum()),
                     "homes_in_our_main_map": float(h[ours].sum()), "homes_in_both": float(both),
                     "homes_in_either": float(either), "agreement_both_over_either": both / either if either else np.nan,
                     "edge_estimate": r["estimate"], "edge_low": lo, "edge_high": hi,
                     "edge_inside_homes": r["treat_denominator"], "edge_outside_homes": r["comp_denominator"],
                     "edge_inside_units_before": r["treat_units_before"], "edge_inside_units_after": r["treat_units_after"],
                     "edge_outside_units_before": r["comp_units_before"], "edge_outside_units_after": r["comp_units_after"],
                     "edge_unit": "homes other than ADUs per 1,000 existing homes a year, 2023-2025 vs 2018-2022; "
                                  "25-150 m inside vs outside the city's line; projects resampled",
                     "edge_interval": f"projects, {ab.N_DRAWS} resamples, seed {ab.SEED}"})
    return pd.DataFrame(rows)


def ntd_hours() -> pd.DataFrame:
    d = pd.read_csv(NTD, dtype=str)
    d = d[(d.State == "CA") & d.Mode.isin(["MB", "RB", "CB"])].copy()
    d["year"] = d.Date.str[-4:].astype(int)
    d["VRH"] = pd.to_numeric(d.VRH.str.replace(",", ""), errors="coerce")
    full = d.groupby("year").Date.nunique()
    latest = int(max(y for y, n in full.items() if n >= 12))
    t = d[d.year.isin([2022, latest])].groupby(["NTD ID", "Agency", "year"]).VRH.sum().unstack(fill_value=0)
    t.columns = [f"bus_vrh_{c}" for c in t.columns]
    t["ratio_latest_over_2022"] = t[f"bus_vrh_{latest}"] / t["bus_vrh_2022"].replace(0, np.nan)
    t = t.reset_index()
    t["unit"] = f"annual bus vehicle revenue hours (modes MB, RB, CB), calendar 2022 and {latest}"
    return t


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.fetch:
        fetch()
    if a.run:
        cm = city_maps()
        cm.to_csv(REFERENCE / "ca_ab2097_side_city_maps.csv", index=False)
        print(cm.round(3).to_string(index=False))
        nt = ntd_hours()
        nt.to_csv(REFERENCE / "ca_ab2097_side_ntd_bus_hours.csv", index=False)
        print(nt.sort_values("bus_vrh_2022", ascending=False).head(25).round(2).to_string(index=False))


if __name__ == "__main__":
    main()
