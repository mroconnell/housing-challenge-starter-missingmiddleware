"""Test 51 (CAUSAL_FRAMEWORK_PLAN.md, audit fix 1): assign HUD LIHTC projects to BPS permit places by location.

Each project's latitude/longitude is placed in a Census 2024 place or county subdivision (cartographic boundary files,
geom point-in-polygon). A point inside a place that BPS reports goes to that place; otherwise to the county subdivision
if BPS reports it (towns and townships); otherwise it is unmatched (for example unincorporated county land). The
database's own place2020 field is used only as a check. Place first: a project in a
village counts for the village only, never also for the town around it.

    uv run python scripts/assign_parking_lihtc_places.py
Input: data/raw/hud_lihtc/lihtcpub.zip (hand-downloaded by Ryan; SHA-256 in data/raw/hud_lihtc/PROVENANCE.json).
Outputs (no coordinates, no addresses):
  reference/parking_lihtc_place_years.csv  BPS key x permit-proxy year: projects, all units, low-income units, units in
                                           100%-affordable projects (low-income >= 95% of units)
  reference/parking_lihtc_match.csv        match counts by state (place, county subdivision, unmatched, no location)
  reference/parking_lihtc_fallback_by_year.csv  matched projects whose permit year comes from placed-in-service - 1
"""
from __future__ import annotations

import io
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from missing_middleware import geom  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
import run_parking_method2 as m  # noqa: E402

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
FIELDS = ["hud_id", "latitude", "longitude", "st2020", "place2020", "n_units", "li_units", "yr_pis", "yr_alloc"]


def read_lihtc() -> pd.DataFrame:
    """LIHTCPUB.xlsx read with the standard library (no new dependency)."""
    with zipfile.ZipFile(RAW / "hud_lihtc" / "lihtcpub.zip") as outer:
        z = zipfile.ZipFile(io.BytesIO(outer.read("LIHTCPUB.xlsx")))
    ss = ["".join(t.text or "" for t in si.iter(NS + "t")) for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall(NS + "si")]
    hdr, rows = None, []
    for _, el in ET.iterparse(z.open("xl/worksheets/sheet1.xml")):
        if el.tag == NS + "row":
            vals = {}
            for c in el.findall(NS + "c"):
                v = c.find(NS + "v")
                x = None if v is None else v.text
                if x is not None and c.get("t") == "s":
                    x = ss[int(x)]
                vals[re.match(r"[A-Z]+", c.get("r")).group(0)] = x
            if hdr is None:
                hdr = {v: k for k, v in vals.items()}
            else:
                rows.append({f: vals.get(hdr[f]) for f in FIELDS})
            el.clear()
    d = pd.DataFrame(rows)
    for c in ("latitude", "longitude", "n_units", "li_units", "yr_pis", "yr_alloc"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    for c in ("yr_pis", "yr_alloc"):  # 8888 / 9999 = missing
        d.loc[~d[c].between(1980, 2100), c] = np.nan
    return d


def main() -> None:
    d = read_lihtc()
    d["st"] = d["st2020"].astype(str).str.zfill(2)
    ok = d["latitude"].between(-90, 90) & d["longitude"].between(-180, 180) & d["latitude"].ne(0)
    px, py = d.loc[ok, "longitude"].values, d.loc[ok, "latitude"].values
    cb = RAW / "census_cb_2024"
    pl = geom.read_shapefile(cb / "cb_2024_us_place_500k.zip", columns=["GEOID"])
    cs = geom.read_shapefile(cb / "cb_2024_us_cousub_500k.zip", columns=["GEOID"])
    ip = geom.points_in_polygons(px, py, pl.polys)
    ic = geom.points_in_polygons(px, py, cs.polys)
    d["place_geoid"], d["cousub_geoid"] = None, None
    d.loc[ok, "place_geoid"] = np.where(ip >= 0, pl.attrs["GEOID"].values[np.maximum(ip, 0)], None)
    d.loc[ok, "cousub_geoid"] = np.where(ic >= 0, cs.attrs["GEOID"].values[np.maximum(ic, 0)], None)
    geo = m.Data().geo  # BPS keys with their place / county-subdivision codes
    isplace = geo["fips_place"].str.strip("0") != ""
    by_place = {g[4:]: k for k, g in geo.loc[isplace, "acs_geoid"].items()}
    by_cousub = {g[4:]: k for k, g in geo.loc[~isplace, "acs_geoid"].items()}
    # Connecticut: the 2024 boundary file uses the 2022 planning-region county codes, BPS the old county codes, so
    # Connecticut county subdivisions are matched on state + MCD code (unique within the state)
    ct = {g[4:6] + g[9:]: k for g, k in ((g, k) for k, g in geo.loc[~isplace, "acs_geoid"].items()) if g[4:6] == "09"}
    d["key"] = d["place_geoid"].map(by_place)
    d["how"] = np.where(d["key"].notna(), "place", None)
    cs_key = d["cousub_geoid"].map(by_cousub)
    isct = d["cousub_geoid"].fillna("").str.startswith("09")
    cs_key[isct] = (d.loc[isct, "cousub_geoid"].str[:2] + d.loc[isct, "cousub_geoid"].str[5:]).map(ct)
    fill = d["key"].isna() & cs_key.notna()
    d.loc[fill, "key"], d.loc[fill, "how"] = cs_key[fill], "county subdivision"
    d.loc[d["key"].isna() & ok, "how"] = "unmatched"
    d.loc[~ok, "how"] = "no location"
    # check against the database's own place field (place2020 = place FIPS within st2020)
    pf = d["st"] + d["place2020"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(5)
    both = (d["how"] == "place") & d["place2020"].notna() & ~pf.str.endswith("99999")
    d["place_field_agrees"] = np.where(both, pf == d["place_geoid"], np.nan)
    d["full_affordable"] = d["li_units"] >= 0.95 * d["n_units"]
    d["permit_year"] = np.where(d["yr_alloc"].notna(), d["yr_alloc"] + 1, d["yr_pis"] - 1)  # lock: allocation + 1
    d["fallback"] = d["yr_alloc"].isna() & d["yr_pis"].notna()  # permit year from placed-in-service - 1
    d["permit_year_alt"] = np.where(d["yr_alloc"].notna(), d["yr_alloc"], d["yr_pis"] - 2)  # sensitivity: allocation year
    d["units_100"] = np.where(d["full_affordable"], d["n_units"], 0)
    match = d.groupby(["st", "how"]).size().unstack(fill_value=0)
    match.to_csv(REFERENCE / "parking_lihtc_match.csv")
    keep = d[d["key"].notna()]
    out = []
    for col, label in (("permit_year", "allocation + 1"), ("permit_year_alt", "allocation year")):
        g = keep.dropna(subset=[col]).groupby(["key", col]).agg(
            projects=("hud_id", "size"), units=("n_units", "sum"), li_units=("li_units", "sum"),
            units_100pct=("units_100", "sum"), fallback_projects=("fallback", "sum")).reset_index().rename(columns={col: "year"})
        out.append(g.assign(timing=label))
    o = pd.concat(out, ignore_index=True)
    o["year"] = o["year"].astype(int)
    o.to_csv(REFERENCE / "parking_lihtc_place_years.csv", index=False)
    # each project carries one key (place first, then county subdivision), so no project counts in both a village and
    # the town around it
    assert d["hud_id"].is_unique
    fb = d[d["fallback"] & d["key"].notna()].groupby("permit_year").size()
    fb.rename("fallback_projects").to_csv(REFERENCE / "parking_lihtc_fallback_by_year.csv")
    pd.set_option("display.width", 200)
    mt = match.assign(total=match.sum(axis=1))
    mt["unmatched_share"] = (mt.get("unmatched", 0) / mt["total"]).round(3)
    print(mt.to_string())
    print("fallback (placed-in-service - 1) projects by permit year, matched:", fb[fb.index >= 2010].astype(int).to_dict())
    print("projects", len(d), d["how"].value_counts().to_dict())
    print("place field agrees:", int((d["place_field_agrees"] == 1).sum()), "of", int(d["place_field_agrees"].notna().sum()))
    print("100% affordable share of projects:", round(d["full_affordable"].mean(), 3),
          "no year:", int(d["permit_year"].isna().sum()))


if __name__ == "__main__":
    main()
