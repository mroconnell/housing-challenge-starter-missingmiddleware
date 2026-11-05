"""Place traits: USDA RUCA commuting codes and Census principal-city status, for every BPS permit place.

No outcome is read. For each BPS place (or county subdivision), census tracts are assigned by their internal point
(Gazetteer) to the 2024 cartographic place / county-subdivision polygons, place first (as in the LIHTC script). The
place's traits are population-weighted shares of its tracts' primary RUCA codes, for 2010 (pre-repeal for every place
in the sample; main) and 2020 (check). A place with no tract point inside takes the nearest tract (flagged).

Classes (2010 codes; main):
  core      principal city of a metropolitan statistical area (Census list 2, July 2023)
  suburb    other place in a metro area (RUCA 1-3 dominant) whose dominant code is 1 (metro core)
  exurb     metro-area place whose dominant code is 2 or 3 (30%+ of workers commute to the metro core)
  non-metro dominant code 4-10 (micropolitan, small town, rural)

    uv run --all-extras python scripts/build_parking_ruca_traits.py
Inputs: data/raw/parking_ruca/ (scripts/fetch_parking_ruca.py). Output: reference/parking_place_ruca_traits.csv
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

R = RAW / "parking_ruca"
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def xlsx_rows(path, sheet="xl/worksheets/sheet1.xml"):
    z = zipfile.ZipFile(path)
    ss = [''.join(t.text or '' for t in si.iter(NS + 't')) for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall(NS + 'si')]
    for _, el in ET.iterparse(z.open(sheet)):
        if el.tag == NS + 'row':
            v = {}
            for c in el.findall(NS + 'c'):
                t = c.find(NS + 'v')
                x = None if t is None else t.text
                if x is not None and c.get('t') == 's':
                    x = ss[int(x)]
                v[re.match(r"[A-Z]+", c.get('r')).group(0)] = x
            yield v
            el.clear()


def ruca2010() -> pd.DataFrame:
    rows = list(xlsx_rows(R / "ruca2010_tracts.xlsx"))
    hdr_i = next(i for i, r in enumerate(rows) if (r.get("A") or "").startswith("State-County FIPS"))
    d = pd.DataFrame(rows[hdr_i + 1:])
    d = d.rename(columns={"D": "tract", "E": "ruca", "G": "pop"})[["tract", "ruca", "pop"]].dropna(subset=["tract"])
    d["ruca"] = pd.to_numeric(d["ruca"], errors="coerce")
    d["pop"] = pd.to_numeric(d["pop"], errors="coerce").fillna(0)
    return d


def ruca2020() -> pd.DataFrame:
    d = pd.read_csv(R / "ruca2020_tracts.csv", dtype={"TractFIPS20": str}, usecols=["TractFIPS20", "PrimaryRUCA", "Population"])
    return d.rename(columns={"TractFIPS20": "tract", "PrimaryRUCA": "ruca", "Population": "pop"})


def gaz(name) -> pd.DataFrame:
    with zipfile.ZipFile(R / name) as z:
        g = pd.read_csv(io.BytesIO(z.read(z.namelist()[0])), sep="\t", dtype={"GEOID": str})
    g.columns = [c.strip() for c in g.columns]
    return g[["GEOID", "INTPTLAT", "INTPTLONG"]].rename(columns={"GEOID": "tract"})


def assign(pts: pd.DataFrame, geo: pd.DataFrame, pl, cs) -> pd.Series:
    """BPS key for each tract point: place first, then county subdivision (Connecticut on state + MCD)."""
    px, py = pts["INTPTLONG"].astype(float).values, pts["INTPTLAT"].astype(float).values
    ip, ic = geom.points_in_polygons(px, py, pl.polys), geom.points_in_polygons(px, py, cs.polys)
    pg = np.where(ip >= 0, pl.attrs["GEOID"].values[np.maximum(ip, 0)], "")
    cg = np.where(ic >= 0, cs.attrs["GEOID"].values[np.maximum(ic, 0)], "")
    isplace = geo["fips_place"].str.strip("0") != ""
    by_place = {g[4:]: k for k, g in geo.loc[isplace, "acs_geoid"].items()}
    by_cs = {g[4:]: k for k, g in geo.loc[~isplace, "acs_geoid"].items()}
    ct = {g[4:6] + g[9:]: k for k, g in geo.loc[~isplace, "acs_geoid"].items() if g[4:6] == "09"}
    key = pd.Series(pg).map(by_place)
    csk = pd.Series(cg).map(by_cs)
    isct = pd.Series(cg).str.startswith("09")
    csk[isct] = (pd.Series(cg)[isct].str[:2] + pd.Series(cg)[isct].str[5:]).map(ct)
    return key.fillna(csk).values


def shares(t: pd.DataFrame, label: str) -> pd.DataFrame:
    t = t.dropna(subset=["key", "ruca"])
    t = t.assign(cls=np.select([t["ruca"] == 1, t["ruca"].isin([2, 3]), t["ruca"].between(4, 6)],
                               ["core", "commute", "micro"], "small_rural"))
    w = t.pivot_table(index="key", columns="cls", values="pop", aggfunc="sum", fill_value=0)
    for c in ("core", "commute", "micro", "small_rural"):
        if c not in w:
            w[c] = 0.0
    tot = w.sum(axis=1).replace(0, np.nan)
    out = pd.DataFrame({f"ruca{label}_share_core": w["core"] / tot, f"ruca{label}_share_commute": w["commute"] / tot,
                        f"ruca{label}_share_micro": w["micro"] / tot, f"ruca{label}_share_small_rural": w["small_rural"] / tot})
    dom = out.fillna(-1).idxmax(axis=1).str.replace(f"ruca{label}_share_", "", regex=False)
    out[f"ruca{label}_dominant"] = dom.where(tot.notna())
    out[f"ruca{label}_tracts"] = t.groupby("key").size()
    return out


def main() -> None:
    D = m.Data()
    geo = D.geo
    cb = RAW / "census_cb_2024"
    pl = geom.read_shapefile(cb / "cb_2024_us_place_500k.zip", columns=["GEOID"])
    cs = geom.read_shapefile(cb / "cb_2024_us_cousub_500k.zip", columns=["GEOID"])
    out = []
    for label, rr, gz in (("2010", ruca2010(), "gaz_tracts_2010.zip"), ("2020", ruca2020(), "gaz_tracts_2020.zip")):
        g = gaz(gz).merge(rr, on="tract", how="inner")
        g = g[np.isfinite(pd.to_numeric(g["INTPTLAT"], errors="coerce")) & np.isfinite(pd.to_numeric(g["INTPTLONG"], errors="coerce"))].reset_index(drop=True)
        g["key"] = assign(g, geo, pl, cs)
        s = shares(g, label)
        # places with no tract point inside: nearest tract internal point to the place's own internal point
        miss = [k for k in geo.index if k not in s.index]
        gp = pd.concat([pd.read_csv(io.BytesIO(zipfile.ZipFile(RAW / "census_gazetteer_2024" / f).read(zipfile.ZipFile(RAW / "census_gazetteer_2024" / f).namelist()[0])),
                                    sep="\t", dtype={"GEOID": str}) for f in ("2024_Gaz_place_national.zip", "2024_Gaz_cousubs_national.zip")])
        gp.columns = [c.strip() for c in gp.columns]
        gpt = gp.loc[:, ~gp.columns.duplicated()].drop_duplicates("GEOID").set_index("GEOID")[["INTPTLAT", "INTPTLONG"]].astype(float)
        mg = geo.loc[miss, "acs_geoid"].str[4:]
        fin = gpt.dropna()
        have = [k for k, x in zip(miss, mg.values) if x in fin.index]
        if have:
            q = fin.loc[geo.loc[have, "acs_geoid"].str[4:].values]
            idx, _ = geom.nearest(np.ravel(q["INTPTLONG"].to_numpy()), np.ravel(q["INTPTLAT"].to_numpy()),
                                  g["INTPTLONG"].astype(float).to_numpy(), g["INTPTLAT"].astype(float).to_numpy())
            nn = g.iloc[idx].assign(key=have)
            s2 = shares(nn.assign(pop=1.0), label)
            s2[f"ruca{label}_nearest_tract"] = True
            s = pd.concat([s, s2])
        out.append(s)
    T = out[0].join(out[1], how="outer")
    T.index.name = "key"
    # principal cities of metropolitan statistical areas (list 2, July 2023)
    rows = list(xlsx_rows(R / "cbsa_list2_2023.xlsx"))
    hi = next(i for i, r in enumerate(rows) if r.get("A") == "CBSA Code")
    P = pd.DataFrame(rows[hi + 1:]).rename(columns={"A": "cbsa", "B": "title", "C": "type", "D": "name", "E": "st", "F": "place"})
    P = P[P["type"] == "Metropolitan Statistical Area"].dropna(subset=["st", "place"])
    pg = set((P["st"].str.zfill(2) + P["place"].str.zfill(5)).values)
    pn = set(zip(P["st"].str.zfill(2), P["name"].str.lower()))
    isplace = geo["fips_place"].str.strip("0") != ""
    by_geoid = geo["acs_geoid"].str[4:]
    base_name = geo["name"].str.lower().str.replace(r"\s+(town|city|village|township|charter township|borough|plantation)$", "", regex=True)
    T = T.reindex(geo.index)
    T["principal_city"] = np.where(isplace, by_geoid.str[:7].isin(pg),
                                   [(s, n) in pn for s, n in zip(geo["state_fips"], base_name)])
    T["metro"] = [D.metro.get(k, 0.0) for k in geo.index]
    dom = T["ruca2010_dominant"]
    T["area_class"] = np.select(
        [(T["metro"] == 1) & T["principal_city"], (T["metro"] == 1) & (dom == "core"), (T["metro"] == 1) & (dom == "commute")],
        ["core", "suburb", "exurb"], np.where(dom.isna(), "unknown", np.where(T["metro"] == 1, "rural part of metro", "non-metro")))
    import run_parking_salvage as rps  # South Bend's combined-area row (St. Joseph County remainder): South Bend is a principal city
    if rps.SJ_KEY in T.index:
        T.loc[rps.SJ_KEY, ["principal_city", "area_class"]] = [True, "core"]
    T.insert(0, "name", geo["name"])
    T.insert(1, "state_fips", geo["state_fips"])
    T.round(4).to_csv(Path(__file__).resolve().parent.parent / "reference" / "parking_place_ruca_traits.csv")
    print(T["area_class"].value_counts().to_dict())
    print("nearest-tract fallback (2010):", int(T.get("ruca2010_nearest_tract", pd.Series(dtype=bool)).fillna(False).sum()))


if __name__ == "__main__":
    main()
