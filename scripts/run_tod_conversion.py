"""Conversion rule: share of a city upzoned -> whole-city gain over five years (docs/tod/CONVERSION_PLAN.md).

    uv run --all-extras python scripts/run_tod_conversion.py

Measures four broad reforms as whole cities (matched-city method of CONTROL_CITIES_PLAN), assembles the measured
cities, fits two shapes, tests on Madison and Chicago, and reads Wisconsin municipalities off the chosen rule.
Writes reference/tod_conversion_points.csv, reference/tod_conversion_fit.csv, reference/tod_conversion_wisconsin.csv.
"""
from __future__ import annotations

import json
import math
import pickle
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from missing_middleware.paths import PROCESSED, RAW, REFERENCE  # noqa: E402
from missing_middleware.tod import control_cities as cc  # noqa: E402
from scripts import run_tod_census_cases as R  # noqa: E402
from scripts.fetch_tod_cases import Manifest  # noqa: E402
from scripts.fetch_tod_census_cases import arcgis_geojson  # noqa: E402

D = RAW / "tod_conversion"
OR_ZONING = "https://services8.arcgis.com/8PAo5HGmvRMlF2eU/arcgis/rest/services/Zoning/FeatureServer/0"
HOLD = ("Madison", "Chicago")
CAP = 0.25

BROAD = [  # (Reform, coverage function name)
    (cc.Reform("nyc_program_2005", "New York", "3651000", 2005, (2000, 2004), (2006, 2010), "", "New York"), "nyc"),
    (cc.Reform("seattle_mha_2019", "Seattle", "5363000", 2019, (2013, 2018), (2020, 2024), "", "Seattle"), "seattle"),
    (cc.Reform("minneapolis_2040_2020", "Minneapolis", "2743000", 2020, (2014, 2019), (2021, 2025), "", "Minneapolis"), "mpls"),
    (cc.Reform("portland_rip_2021", "Portland", "4159000", 2021, (2015, 2020), (2022, 2025), "", "Portland"), "pdx"),
]


def homes_share(st: str, geom, city_geom) -> float:
    p = R.block_points(st, 2010)
    inc = p[R.within(p, city_geom)]
    return float(inc[R.within(inc, geom)]["homes"].sum() / inc["homes"].sum())


def place(st: str, name: str):
    pl = gpd.read_file(R.D / f"tl_2020_{st}_place.zip") if (R.D / f"tl_2020_{st}_place.zip").exists() else None
    return pl[pl["NAME"] == name].to_crs(R.CRS).geometry.union_all()


def coverage(kind: str) -> float:
    if kind == "nyc":
        mem = pickle.loads((PROCESSED / "tod_net_effect" / "areas_nyc_pooled_2003_2013.pkl").read_bytes())
        u = unary_union([gpd.GeoSeries([m["upzoned_union"]], crs=m["crs"]).to_crs(R.CRS).iloc[0] for m in mem if m["effective_year"] <= 2009])
        return homes_share("36", u, place("36", "New York"))
    if kind == "seattle":
        z = gpd.read_file(RAW / "tod_cases" / "seattle" / "zoning_current.geojson").to_crs(R.CRS)
        m = z["ZONING"].astype(str).str.contains(r"\(M\d?\)", regex=True)
        return homes_share("53", z[m].geometry.make_valid().union_all(), place("53", "Seattle"))
    if kind == "mpls":
        z = gpd.read_file(RAW / "tod_cases" / "minneapolis" / "zoning_2017_01.geojson").to_crs(R.CRS)
        m = z["ZONE_CODE"].astype(str).str.match(r"^R\d")
        return homes_share("27", z[m].geometry.make_valid().union_all(), place("27", "Minneapolis"))
    if kind == "pdx":
        f = D / "portland_zoning.geojson"
        if not f.exists():
            man = Manifest(D, "tod_conversion", "Oregon GeoHUB statewide zoning (DLCD)")
            data, url = arcgis_geojson(OR_ZONING, "ownerName LIKE '%Portland%'")
            man.record("portland_zoning.geojson", data, url, licence="Oregon GeoHUB, public")
        z = gpd.read_file(f).to_crs(R.CRS)
        # Statewide layer carries Oregon classes only; "Res." = middle-housing residential (the single-dwelling zones RIP changed)
        m = z["orZCode"].astype(str).str.strip() == "Res."
        return homes_share("41", z[m].geometry.make_valid().union_all(), place("41", "Portland"))
    raise ValueError(kind)


def broad_points() -> list[dict]:
    bps = cc.read_bps(RAW / "tod_control_cities" / "bps")
    gaz = cc.read_gazetteer(RAW / "tod_control_cities" / "Gaz_places_national.zip")
    panel, places = cc.link(bps, gaz, cc.read_county_hu(RAW / "tod_control_cities" / "Gaz_counties_national.zip"))
    inv = cc.inventory_geoids(pd.read_csv(REFERENCE / "tod_cases.csv"), gaz)
    Rt = cc.rates(panel, places)
    P = places.set_index("geoid")
    cc.REFORMS = [b[0] for b in BROAD]      # so each broad city is excluded from the others' controls
    out = []
    for rf, kind in BROAD:
        pool = list(cc.eligible(rf, Rt, places, inv).index)
        est = cc.estimate(Rt, rf.geoid, pool, rf.before, rf.after, "matched", 10)
        pl = cc.placebos(Rt, pool, places, rf.before, rf.after, "matched", 10)
        lo, hi = est - pl.quantile(0.95), est - pl.quantile(0.05)
        cov = coverage(kind)
        out.append({"city": rf.city, "case": rf.test, "source": "whole city vs 10 matched cities (permit survey)",
                    "coverage_homes": cov, "gain_5yr_pct": cc.to_5yr_share(est), "low": cc.to_5yr_share(lo), "high": cc.to_5yr_share(hi),
                    "pool": len(pool)})
        print(rf.test, round(cov, 3), round(cc.to_5yr_share(est), 2), flush=True)
    return out


def measured_points() -> list[dict]:
    pts = []
    n = pd.read_csv(REFERENCE / "tod_net_effect_by_case.csv").set_index("case")
    for case, city in [("nyc_pooled_2003_2013", "New York"), ("philadelphia_2012_remapping", "Philadelphia"),
                       ("charlotte_tod_2019", "Charlotte"), ("stpaul_green_line_2011", "Saint Paul"),
                       ("los_angeles_all_cases", "Los Angeles"), ("seattle_all_cases", "Seattle"),
                       ("chicago_tod_2013_2015", "Chicago"), ("madison_tod_overlay_2023", "Madison")]:
        r = n.loc[case]
        pts.append({"city": city, "case": case, "source": "permits, upzoned land net of building moved in the city",
                    "coverage_homes": r["treated_area_share_of_city_homes"], "gain_5yr_pct": r["net_share_5yr_pct"],
                    "low": r["net_share_5yr_low_pct"], "high": r["net_share_5yr_high_pct"]})
    s = pd.read_csv(REFERENCE / "tod_census_share.csv").set_index("case")
    for case, city in [("jersey_city_journal_square_2010", "Jersey City"), ("milpitas_tasp_2008", "Milpitas"),
                       ("bellevue_belred_2009", "Bellevue"), ("austin_tod_station_plans", "Austin"),
                       ("tysons_2010", "Fairfax County"), ("salt_lake_city_tsa_2010", "Salt Lake City")]:
        r = s.loc[case]
        pts.append({"city": city, "case": case, "source": "census 2010-2020, upzoned land vs its 1/2-mile ring",
                    "coverage_homes": r["area_share_upzoned_homes_2010"] / r["jurisdiction_homes_2010"],
                    "gain_5yr_pct": r["city_share_per_1000_five_years_area_share"] / 10,
                    "low": r["city_share_per_1000_decade_area_share_low"] / 20, "high": r["city_share_per_1000_decade_area_share_high"] / 20})
    pts.append({"city": "Auckland", "case": "auckland_aup_2016", "source": "published (Greenaway-McGrevy and coauthors), AQ-050",
                "coverage_homes": 0.752, "gain_5yr_pct": 21808 / 530300 * 100, "low": np.nan, "high": np.nan})
    pts.append({"city": "Los Angeles TOC", "case": "la_toc_2017", "source": "published (Kestelman, Harvard JCHS), AQ-050",
                "coverage_homes": 0.61, "gain_5yr_pct": 0.04 * 5 / 6, "low": np.nan, "high": np.nan})
    return pts


def fit(df: pd.DataFrame, shape: str) -> float:
    x = df["coverage_homes"].to_numpy() if shape == "A" else np.sqrt(df["coverage_homes"].to_numpy())
    w = df["w"].to_numpy()
    return float(np.sum(w * x * df["gain_5yr_pct"]) / np.sum(w * x * x))


def predict(b: float, c, shape: str):
    return b * (np.asarray(c) if shape == "A" else np.sqrt(np.asarray(c)))


def main() -> None:
    pts = pd.DataFrame(measured_points() + broad_points())
    width = (pts["high"] - pts["low"]).abs()
    w = 1 / width.clip(lower=0.05) ** 2
    w = w.fillna(np.inf)
    pts["w"] = w
    fitpts = pts[~pts["city"].isin(HOLD)].copy()
    # cap: no city above 25% of total weight (iterative), points with no interval take the cap
    for _ in range(20):
        tot = fitpts.loc[np.isfinite(fitpts["w"]), "w"].sum()
        n_inf = (~np.isfinite(fitpts["w"])).sum()
        capw = CAP * (tot / (1 - CAP * n_inf)) if n_inf else CAP * tot
        fitpts["w"] = np.where(~np.isfinite(fitpts["w"]), capw, np.minimum(fitpts["w"], capw))
        if (fitpts["w"] / fitpts["w"].sum()).max() <= CAP + 1e-6:
            break
    rows = []
    for shape in ("A", "B"):
        b = fit(fitpts, shape)
        errs = []
        for city in fitpts["city"].unique():
            tr, te = fitpts[fitpts["city"] != city], fitpts[fitpts["city"] == city]
            errs.append(float(np.average(np.abs(predict(fit(tr, shape), te["coverage_homes"], shape) - te["gain_5yr_pct"]))))
        hold = {}
        for city in HOLD:
            h = pts[pts["city"] == city].iloc[0]
            p = float(predict(b, h["coverage_homes"], shape))
            hold[city] = (p, bool(h["low"] <= p <= h["high"]))
        rows.append({"shape": "A proportional" if shape == "A" else "B diminishing (square root)", "b": b,
                     "loco_mean_abs_error_pct": float(np.mean(errs)),
                     **{f"pred_{c.lower()}": hold[c][0] for c in HOLD}, **{f"inside_{c.lower()}": hold[c][1] for c in HOLD}})
    F = pd.DataFrame(rows)
    best = F.loc[F["loco_mean_abs_error_pct"].idxmin()]
    F["chosen"] = F["shape"] == best["shape"]
    F["offered_to_owner"] = F["chosen"] & F["inside_madison"] & F["inside_chicago"]
    shape = "A" if best["shape"].startswith("A") else "B"
    # Wisconsin, municipality by municipality
    m = pd.read_csv(REFERENCE / "tod_near_stop_homes_by_muni.csv")
    out = []
    for col, label in (("share_near_main", "current definition"), ("share_near_rapid_half", "rail and rapid only, 1/2 mile")):
        for sh in ("A", "B"):
            bb = float(F.loc[F["shape"].str.startswith(sh), "b"].iloc[0])
            extra = predict(bb, m[col].fillna(0), sh) / 100 * m["homes_2020"]
            out.append({"definition": label, "shape": "A" if sh == "A" else "B", "chosen_shape": sh == shape,
                        "extra_homes_2027_2031": float(extra.sum()),
                        "milwaukee": float(extra[m["name"] == "Milwaukee city"].sum()), "madison": float(extra[m["name"] == "Madison city"].sum()),
                        "homes_covered": float((m[col].fillna(0) * m["homes_2020"]).sum())})
    W = pd.DataFrame(out)
    pts.drop(columns=["w"]).round(5).to_csv(REFERENCE / "tod_conversion_points.csv", index=False)
    F.round(5).to_csv(REFERENCE / "tod_conversion_fit.csv", index=False)
    W.round(1).to_csv(REFERENCE / "tod_conversion_wisconsin.csv", index=False)
    pd.set_option("display.width", 250)
    print(pts.drop(columns=["w"]).round(3).to_string())
    print(F.round(4).to_string())
    print(W.round(0).to_string())


if __name__ == "__main__":
    main()
