"""Chicago lot tests rerun on B/C/D lots only (2015 parking relief scope, SO2015-5334). Post hoc; rule in
docs/parking/CAUSAL_FRAMEWORK_PLAN.md ("Chicago lot rerun rule").

    uv run --all-extras python scripts/run_parking_ws_chicago_bcd.py
Output: reference/parking_ws_chicago_bcd.csv
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


def boot(g, f, rng):
    cells = g["cell"].unique()
    grp = {c: x for c, x in g.groupby("cell")}
    bs = []
    for _ in range(DRAWS):
        s = pd.concat([grp[c] for c in rng.choice(cells, len(cells))])
        if (s["pinched"] == 1).any() and (s["pinched"] == 0).any():
            bs.append(f(s))
    return np.percentile(bs, [5, 95, 1.25, 98.75])


def per_acre(g):
    t, c = g[g["pinched"] == 1], g[g["pinched"] == 0]
    r = lambda x: ((x["after_py"] - x["before_py"]).sum() / x["acres"].sum()) * 100  # noqa: E731
    return r(t) - r(c)


def main() -> None:
    d = LT.lots()
    d = d[(d["city"] == "Chicago") & (d["acres"] > 0) & (d["dist_station_m"] <= 805)].copy()
    lay = geom.read_shapefile(RAW / "tod_cases" / "chicago" / "zoning_nov2012.zip")
    lon, lat = geom.transform(d["x5070"].values, d["y5070"].values, 5070, 4326)
    x, y = geom.transform(lon, lat, 4326, lay.crs)
    hit = geom.points_in_polygons(x, y, lay.polys)
    zc = np.where(hit >= 0, lay.attrs["ZONE_CLASS"].astype(str).values[np.clip(hit, 0, None)], "")
    d["zone"] = zc
    d = d[pd.Series(zc, index=d.index).str.match(r"^[BC]\d|^D[CXRS]")].copy()
    d["pinched"] = (d["dist_station_m"] <= 402.336).astype(float)
    d["permits_main"] = d["permits"]
    d["cell"] = "Chicago:" + (d["x5070"] // LC.CELL).astype(int).astype(str) + "_" + (d["y5070"] // LC.CELL).astype(int).astype(str)
    L = LC.add_rates(d, "permits_main")
    rng = np.random.default_rng(SEED)
    rows = []
    for lab, sub in (("B/C/D, density-bonus lots kept (main)", L), ("B/C/D, density-bonus lots dropped", L[L["treated"] == 0])):
        q = boot(sub, LC.effect, rng)
        rows.append(dict(test="FU7-style all lots", case=lab, reform_lots=int((sub["pinched"] == 1).sum()), comparison_lots=int((sub["pinched"] == 0).sum()),
                         estimate=LC.effect(sub), p05=q[0], p95=q[1], p0125=q[2], p9875=q[3], unit="net new homes per 1,000 lots a year"))
        s2 = sub[sub["far_before"] >= 1.2]
        q = boot(s2, per_acre, rng)
        rows.append(dict(test="B1 (FAR >= 1.2)", case=lab, reform_lots=int((s2["pinched"] == 1).sum()), comparison_lots=int((s2["pinched"] == 0).sum()),
                         estimate=per_acre(s2), p05=q[0], p95=q[1], p0125=q[2], p9875=q[3], unit="net new homes per 100 lot acres a year"))
    out = pd.DataFrame(rows)
    out["label"] = "POST HOC: reform side limited to B/C/D lots within 402 m (Nov 2012 map); comparison B/C/D lots 402-805 m"
    out["unmatched_lots"] = int((hit < 0).sum())
    out.to_csv(REFERENCE / "parking_ws_chicago_bcd.csv", index=False)
    pd.set_option("display.width", 250)
    print(out.drop(columns=["label", "unit"]).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
