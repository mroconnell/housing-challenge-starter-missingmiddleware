"""Chicago B/C/D lots with home and acre denominators (post hoc; owner 2026-11-03 14:29).
docs/parking/CAUSAL_FRAMEWORK_PLAN.md ("Chicago B/C/D with home and acre denominators").

    uv run --all-extras python scripts/run_parking_ws_chicago_denom.py
Output: reference/parking_ws_chicago_denom.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from missing_middleware import geom  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
from scripts import run_parking_lot_cities as LC  # noqa: E402
from scripts import run_parking_lot_test as LT  # noqa: E402

SEED, DRAWS = 20261104, 2000


def main() -> None:
    d = LT.lots()
    d = d[(d["city"] == "Chicago") & (d["acres"] > 0) & (d["dist_station_m"] <= 805)].copy()
    lay = geom.read_shapefile(RAW / "tod_cases" / "chicago" / "zoning_nov2012.zip")
    lon, lat = geom.transform(d["x5070"].values, d["y5070"].values, 5070, 4326)
    x, y = geom.transform(lon, lat, 4326, lay.crs)
    hit = geom.points_in_polygons(x, y, lay.polys)
    zc = pd.Series(np.where(hit >= 0, lay.attrs["ZONE_CLASS"].astype(str).values[np.clip(hit, 0, None)], ""), index=d.index)
    old = zc.str.match(r"^[BCD]\d|^D[XRS]")
    new = zc.str.match(r"^[BC]\d|^D[CXRS]")
    added_dc = int((new & ~old).sum())
    d = d[new].copy()
    d["pinched"] = (d["dist_station_m"] <= 402.336).astype(float)
    d["permits_main"] = d["permits"]
    d["cell"] = "Chicago:" + (d["x5070"] // LC.CELL).astype(int).astype(str) + "_" + (d["y5070"] // LC.CELL).astype(int).astype(str)
    L = LC.add_rates(d, "permits_main")
    # existing homes: 2010 census block housing units (block internal point inside a kept lot's 2012 zone polygon is not
    # available per lot, so each block's homes go to the nearest kept lot within 100 m); homes_on_lot is empty for Chicago
    from scipy.spatial import cKDTree
    blk = geom.read_shapefile(RAW / "tod_cases" / "census_2010_blocks" / "tabblock2010_17_pophu.zip")
    cx, cy = geom.representative_points(blk.polys)
    bx, by = geom.transform(cx, cy, 4326, 5070)
    hu = blk.attrs["HOUSING10"].astype(float).values
    tree = cKDTree(np.column_stack([L["x5070"].values, L["y5070"].values]))
    dist, idx = tree.query(np.column_stack([bx, by]), distance_upper_bound=100)
    ok = np.isfinite(dist) & (idx < len(L))
    h = np.zeros(len(L))
    np.add.at(h, idx[ok], hu[ok])
    L["homes0"] = h
    L["res_lot"] = L["use"].isin(["res", "mixed"])

    def per_home(g):
        t, c = g[g["pinched"] == 1], g[g["pinched"] == 0]
        f = lambda x: (x["after_py"] - x["before_py"]).sum() / x["homes0"].sum() * 1000  # noqa: E731
        return f(t) - f(c)

    def per_acre(g):
        t, c = g[g["pinched"] == 1], g[g["pinched"] == 0]
        f = lambda x: (x["after_py"] - x["before_py"]).sum() / x["acres"].sum() * 100  # noqa: E731
        return f(t) - f(c)

    rng = np.random.default_rng(SEED)
    cells = L["cell"].unique()
    grp = {c: x for c, x in L.groupby("cell")}
    rows = []
    def per_res_acre(g):
        t, c = g[g["pinched"] == 1], g[g["pinched"] == 0]
        f = lambda x: (x["after_py"] - x["before_py"]).sum() / x.loc[x["res_lot"], "acres"].sum() * 100  # noqa: E731
        return f(t) - f(c)

    for lab, f, unit in (("per existing home (2010 census block homes)", per_home, "net new homes per 1,000 existing homes (2010) a year"),
                         ("per lot acre", per_acre, "net new homes per 100 lot acres a year"),
                         ("per residential lot acre (lots in residential or mixed use)", per_res_acre, "net new homes per 100 residential lot acres a year")):
        bs = []
        for _ in range(DRAWS):
            s = pd.concat([grp[c] for c in rng.choice(cells, len(cells))])
            if (s["pinched"] == 1).any() and (s["pinched"] == 0).any():
                bs.append(f(s))
        t, c = L[L["pinched"] == 1], L[L["pinched"] == 0]
        rows.append(dict(denominator=lab, estimate=f(L), p05=np.percentile(bs, 5), p95=np.percentile(bs, 95),
                         p0125=np.percentile(bs, 1.25), p9875=np.percentile(bs, 98.75), reform_lots=len(t), comparison_lots=len(c),
                         reform_homes_before=float(t["homes0"].sum()), comparison_homes_before=float(c["homes0"].sum()),
                         reform_acres=float(t["acres"].sum()), comparison_acres=float(c["acres"].sum()),
                         reform_res_acres=float(t.loc[t["res_lot"], "acres"].sum()), comparison_res_acres=float(c.loc[c["res_lot"], "acres"].sum()),
                         dc_lots_added=added_dc, unit=unit))
    out = pd.DataFrame(rows)
    out["label"] = "POST HOC: Chicago 2015, B/C/D lots only (reform <= 402 m, comparison 402-805 m)"
    out.to_csv(REFERENCE / "parking_ws_chicago_denom.csv", index=False)
    pd.set_option("display.width", 250)
    print(out.drop(columns=["unit", "label"]).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
