"""TOD "today" screen, second measure (owner 2026-11-02 13:41): density near transit relative to the rest of the city.

For each city: homes per acre of land within 1/2 mile (and 1/4 mile) of the stops, divided by homes per acre in the
rest of the same city (blocks whose internal point is inside the city but beyond 1/2 mile of those stops). City size,
age and market affect both, so the ratio shows how much a city has concentrated homes around its transit.
Stops as in scripts/build_tod_today_density.py (Wisconsin: rail and rapid stops of each system; the six older
reforms: their reform stops). City limits: Census 2024 cartographic boundary places. Blocks: 2020 Census.

    .venv/bin/python scripts/build_tod_today_ratio.py      -> reference/tod_today_ratio.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
import build_tod_today_density as TD  # noqa: E402
from missing_middleware import geom as G  # noqa: E402
from missing_middleware import geom_extra_station as X  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
from missing_middleware.tod import transit as T  # noqa: E402

PLACES = [  # label, Census place name, state FIPS, stop selector
    ("Milwaukee (BRT and streetcar)", "Milwaukee", "55", ("wi", ["Milwaukee County", "City of Milwaukee"])),
    ("Madison (BRT)", "Madison", "55", ("wi", ["City of Madison"])),
    ("Kenosha (streetcar)", "Kenosha", "55", ("wi", ["City of Kenosha"])),
    ("Austin (2009 reform)", "Austin", "48", ("rf", ["austin_2009"])),
    ("Bellevue BelRed (2009 reform)", "Bellevue", "53", ("rf", ["bellevue_belred_2009"])),
    ("Salt Lake City (2010 reform)", "Salt Lake City", "49", ("rf", ["slc_2010"])),
    ("Saint Paul (2011 reform)", "St. Paul", "27", ("rf", ["stpaul"])),
    ("Seattle Othello and Mount Baker (2012, 2014 reforms)", "Seattle", "53",
     ("rf", ["seattle_nbh_othello_2012", "seattle_mount_baker_2014"])),
]


def main() -> None:
    wi = pd.read_csv(REFERENCE / "tod_stops.csv")
    wi = wi[wi.flag_a_rapid == 1]
    st = pd.read_csv(REFERENCE / "tod_station_area_stations.csv")
    pl = X.read_vector(RAW / "census_cb_2024" / "cb_2024_us_place_500k.zip", dst=4269, columns=["NAME", "STATEFP"])
    blocks, rows = {}, []
    for label, name, fips, (kind, sel) in PLACES:
        s = wi[wi.agency.isin(sel)] if kind == "wi" else st[st.case.isin(sel) & (st.role == "reform")]
        s = s.drop_duplicates(["lat", "lon"]) if "lat" in s else s
        if fips not in blocks:
            blocks[fips] = TD.read_blocks(fips)
        b = blocks[fips]
        poly = pl[(pl.STATEFP == fips) & (pl.NAME == name)]
        if len(poly) != 1:
            raise SystemExit(f"place {name} ({fips}): {len(poly)} matches")
        bb = X.feature_bounds(list(poly.geometry))[0]
        b = b[(b.lon >= bb[0]) & (b.lon <= bb[2]) & (b.lat >= bb[1]) & (b.lat <= bb[3])]
        inside = G.points_in_any(b.lon.values, b.lat.values, list(poly.geometry), union=True)
        b = b[inside]
        proj = 3071 if fips == "55" else TD.local_tm(s)
        bp = np.c_[G.transform(b.lon.values, b.lat.values, 4269, proj)]
        sp = np.c_[G.transform(s.lon.values, s.lat.values, 4326, proj)]
        homes, land = b.homes.values, b.land_m2.values / TD.ACRE_M2
        half = T.blocks_within(bp, sp, TD.BANDS["half_mile"])
        quarter = T.blocks_within(bp, sp, TD.BANDS["quarter_mile"])
        rest = (homes[~half].sum(), land[~half].sum())
        d_rest = rest[0] / rest[1]
        for band, m in (("quarter_mile", quarter), ("half_mile", half)):
            d = homes[m].sum() / land[m].sum()
            rows.append({"place": label, "band": band, "stops": len(s), "homes_near": int(homes[m].sum()),
                         "land_acres_near": round(land[m].sum(), 1), "homes_per_acre_near": round(d, 2),
                         "homes_rest_of_city": int(rest[0]), "land_acres_rest_of_city": round(rest[1], 1),
                         "homes_per_acre_rest_of_city": round(d_rest, 2), "ratio_near_to_rest": round(d / d_rest, 2)})
    out = pd.DataFrame(rows)
    out.to_csv(REFERENCE / "tod_today_ratio.csv", index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
