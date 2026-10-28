"""Census-count check (docs/parking/SALVAGE_PLAN.md, section 4): does the change in homes between the 2010 and
2020 censuses match the permits a place issued over the same years?

    uv run python scripts/fetch_parking_census_check.py
    uv run python scripts/run_parking_census_check.py

Both years' blocks are placed in 2020 place boundaries by internal point. Permits from the Census permit place
files. Outputs: reference/parking_census_check_places.csv, reference/parking_census_check_summary.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_parking_comparison as rpc  # noqa: E402
from missing_middleware.foundation import parsers  # noqa: E402
from missing_middleware.parking import comparison as cmp  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

D = RAW / "parking_census_check"
CHECK_STATES = ("18", "27", "37", "55")
ALL_STATES = ("18", "27", "37", "45", "46", "42", "55")
EQUAL_AREA = 5070


def place_homes(st: str) -> pd.DataFrame:
    places = gpd.read_file(f"zip://{D}/tl_2020_{st}_place.zip")[["GEOID", "NAME", "geometry"]].to_crs(EQUAL_AREA)
    b20 = gpd.read_file(f"zip://{D}/tl_2020_{st}_tabblock20.zip", columns=["INTPTLAT20", "INTPTLON20", "HOUSING20"], ignore_geometry=True)
    b20 = gpd.GeoDataFrame(b20[["HOUSING20"]], geometry=gpd.points_from_xy(b20["INTPTLON20"].astype(float), b20["INTPTLAT20"].astype(float)),
                           crs=4269).to_crs(EQUAL_AREA)
    b10 = gpd.read_file(f"zip://{D}/tabblock2010_{st}_pophu.zip", columns=["HOUSING10"])
    b10 = b10.to_crs(EQUAL_AREA)
    b10["geometry"] = b10.geometry.representative_point()
    out = []
    for b, col in ((b20, "HOUSING20"), (b10, "HOUSING10")):
        j = gpd.sjoin(b[[col, "geometry"]], places, predicate="within", how="inner")
        out.append(j.groupby("GEOID")[col].sum())
    r = pd.concat(out, axis=1).fillna(0)
    r["name"] = places.set_index("GEOID")["NAME"]
    return r


def permits() -> pd.DataFrame:
    frames = []
    for f in sorted(list(D.glob("*a.txt")) + list(rpc.BPS_DIR.glob("*a.txt"))):
        y = int(f.name[2:6])
        if 2009 <= y <= 2019:
            d = parsers.read_bps(f, "place", state_fips=None)
            d["year"] = y
            frames.append(d)
    p = cmp.panel(pd.concat(frames, ignore_index=True))
    p = p[p["acs_geoid"].str.startswith("160|")]
    p["GEOID"] = p["acs_geoid"].str[4:]
    return p


def main() -> None:
    p = permits()
    rows = []
    for st in ALL_STATES:
        h = place_homes(st)
        s = p[p["state_fips"] == st]
        for lab, yrs in (("2010-2019", range(2010, 2020)), ("2009-2018", range(2009, 2019))):
            g = s[s["year"].isin(yrs)].groupby("GEOID").agg(units=("units_total", "sum"), years=("year", "nunique"))
            h[f"permits_{lab}"] = g["units"]
            h[f"years_{lab}"] = g["years"]
        h["state_fips"] = st
        rows.append(h.reset_index().rename(columns={"index": "GEOID"}))
        print(st, len(h), flush=True)
    d = pd.concat(rows, ignore_index=True)
    d["census_change"] = d["HOUSING20"] - d["HOUSING10"]
    d.to_csv(REFERENCE / "parking_census_check_places.csv", index=False)

    c = d[d["state_fips"].isin(CHECK_STATES) & (d["years_2010-2019"] == 10) & (d["HOUSING10"] >= 100)].copy()
    out = []
    for lab in ("2010-2019", "2009-2018"):
        k = c[c[f"years_{lab}"] == 10] if lab == "2009-2018" else c
        perm = k[f"permits_{lab}"]
        for band, m in (("all", np.ones(len(k), bool)), ("under 2,500 homes", k["HOUSING10"] < 2500),
                        ("2,500-25,000 homes", (k["HOUSING10"] >= 2500) & (k["HOUSING10"] < 25000)),
                        ("over 25,000 homes", k["HOUSING10"] >= 25000)):
            x, y = perm[m], k["census_change"][m]
            ok = x > 0
            gx, gy = x / k["HOUSING10"][m], y / k["HOUSING10"][m]
            out.append(dict(permit_years=lab, band=band, places=int(m.sum()),
                            correlation=float(np.corrcoef(x, y)[0, 1]) if m.sum() > 2 else np.nan,
                            correlation_rates=float(np.corrcoef(gx, gy)[0, 1]) if m.sum() > 2 else np.nan,
                            median_ratio=float((y[ok] / x[ok]).median()), total_ratio=float(y.sum() / x.sum()),
                            share_disagree=float(((y - x).abs() > np.maximum(0.5 * x, 50)).mean()),
                            share_agree_above_median=float(((gx > gx.median()) == (gy > gy.median())).mean())))
    s = pd.DataFrame(out)
    s.round(4).to_csv(REFERENCE / "parking_census_check_summary.csv", index=False)
    print(s.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
