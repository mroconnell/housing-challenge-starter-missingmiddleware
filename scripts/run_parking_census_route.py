"""Parking census-only route (docs/parking/CENSUS_ROUTE_PLAN.md).

    uv run --all-extras python scripts/run_parking_census_route.py

For each state with a repeal place effective before 1 April 2020: downloads Census 2010 and 2020 blocks and 2020
places (public domain) into data/raw/parking_census_route/ (kept; place counts are cached per state), places both years' blocks in 2020 place boundaries, and compares growth 2010-2020 in
repeal places with same-state places of 1/2-2x population, pro-rated by the share of the decade under repeal.
Outputs: reference/parking_census_route_places.csv, reference/parking_census_route_cases.csv,
reference/parking_census_route_results.csv
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
import run_parking_expanded as rpe  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
from scripts.fetch_tod_cases import Manifest, download_file  # noqa: E402

D = RAW / "parking_census_route"
KEEP = RAW / "parking_census_check"          # states already downloaded for the census-count check
PD = "US Census Bureau, public domain"
EA = 5070
SEED, DRAWS, SETS = 20261028, 2000, 500
DECADE_START, DECADE_END = pd.Timestamp("2010-04-01"), pd.Timestamp("2020-04-01")
CENSUS_TO_PERMITS = 0.86                     # census change / permits, all places summed (SALVAGE_RESULTS.md)
MIN_HOMES = 2500


def place_counts(st: str, man: Manifest) -> pd.DataFrame:
    out_csv = D / f"places_{st}.csv"
    if out_csv.exists():
        return pd.read_csv(out_csv, dtype={"GEOID": str})
    src = KEEP if (KEEP / f"tl_2020_{st}_tabblock20.zip").exists() else D
    files = {f"tabblock2010_{st}_pophu.zip": f"https://www2.census.gov/geo/tiger/TIGER2010BLKPOPHU/tabblock2010_{st}_pophu.zip",
             f"tl_2020_{st}_tabblock20.zip": f"https://www2.census.gov/geo/tiger/TIGER2020/TABBLOCK20/tl_2020_{st}_tabblock20.zip",
             f"tl_2020_{st}_place.zip": f"https://www2.census.gov/geo/tiger/TIGER2020/PLACE/tl_2020_{st}_place.zip"}
    if src is D:
        for n, u in files.items():
            download_file(man, n, u, False, PD)
    places = gpd.read_file(f"zip://{src}/tl_2020_{st}_place.zip")[["GEOID", "NAME", "geometry"]].to_crs(EA)
    b20 = gpd.read_file(f"zip://{src}/tl_2020_{st}_tabblock20.zip", columns=["INTPTLAT20", "INTPTLON20", "HOUSING20", "POP20"], ignore_geometry=True)
    b20 = gpd.GeoDataFrame(b20[["HOUSING20", "POP20"]], crs=4269,
                           geometry=gpd.points_from_xy(b20["INTPTLON20"].astype(float), b20["INTPTLAT20"].astype(float))).to_crs(EA)
    b10 = gpd.read_file(f"zip://{src}/tabblock2010_{st}_pophu.zip", columns=["HOUSING10", "POP10"]).to_crs(EA)
    b10["geometry"] = b10.geometry.representative_point()
    parts = []
    for b, cols in ((b20, ["HOUSING20", "POP20"]), (b10, ["HOUSING10", "POP10"])):
        j = gpd.sjoin(b[cols + ["geometry"]], places, predicate="within", how="inner")
        parts.append(j.groupby("GEOID")[cols].sum())
    r = pd.concat(parts, axis=1).fillna(0)
    r["name"] = places.set_index("GEOID")["NAME"]
    r["state_fips"] = st
    r = r.reset_index().rename(columns={"index": "GEOID"})
    r.to_csv(out_csv, index=False)
    return r


def cases() -> pd.DataFrame:
    c = rpe.all_checks()
    r = c["benchmark_rating_checked"].astype(str).str.lower()
    c = c[r.isin(["at", "near"]) & ~c["no_event"] & c["event_year"].notna()].copy()
    c["date"] = pd.to_datetime(c["effective_date"], errors="coerce").fillna(pd.to_datetime(c["adoption_date"], errors="coerce"))
    c["date"] = c["date"].fillna(pd.to_datetime(c["event_year"].astype(int).astype(str) + "-07-01"))
    c = c[["place", "state", "event_year", "date"]]
    pc = pd.read_csv(REFERENCE / "parking_partial_checks.csv")
    pc = pc[pc["use"] & (pc["group"] == "citywide benchmark")]
    pc = pc.assign(date=pd.to_datetime(pc["event_year"].astype(int).astype(str) + "-07-01"))[["place", "state", "event_year", "date"]]
    x = pd.concat([c, pc]).drop_duplicates(["place", "state"])
    x = x[x["date"] < DECADE_END].copy()
    x["exposure"] = ((DECADE_END - x["date"].clip(lower=DECADE_START)).dt.days / (DECADE_END - DECADE_START).days).clip(0, 1)
    x["state_fips"] = x["state"].map(rpc.STATE_FIPS)
    return x.reset_index(drop=True)


def match(places: pd.DataFrame, st: str, name: str) -> str | None:
    s = places[places["state_fips"] == st]
    n = name.lower().replace(" (city)", "")
    hit = s[s["name"].str.lower() == n]
    if hit.empty:
        hit = s[s["name"].str.lower().str.startswith(n)]
    return None if hit.empty else hit.sort_values("HOUSING10", ascending=False).iloc[0]["GEOID"]


def delta(d, e, w):
    return float((w * e * d).sum() / (w * e * e).sum())


def main() -> None:
    D.mkdir(parents=True, exist_ok=True)
    man = Manifest(D, "parking_census_route", "US Census Bureau")
    cs = cases()
    pl = pd.concat([place_counts(st, man) for st in sorted(cs["state_fips"].unique())], ignore_index=True)
    pl["growth"] = (pl["HOUSING20"] - pl["HOUSING10"]) / pl["HOUSING10"].where(pl["HOUSING10"] > 0) * 1000 / 10
    pl.to_csv(REFERENCE / "parking_census_route_places.csv", index=False)
    tax = pd.read_csv(REFERENCE / "parking_reform_taxonomy.csv")
    tax = tax[(tax["policy"] == "rm_min") & tax["scope"].fillna("").str.contains("citywide")]
    reformed = {g for r in tax.itertuples() if (g := match(pl, rpc.STATE_FIPS.get(r.state, "??"), r.place))}
    rows = []
    for c in cs.itertuples():
        g = match(pl, c.state_fips, c.place)
        if g is None:
            rows.append(dict(place=c.place, state=c.state, status="not found in 2020 places"))
            continue
        me = pl.set_index("GEOID").loc[g]
        comp = pl[(pl["state_fips"] == c.state_fips) & ~pl["GEOID"].isin(reformed | {g}) & (pl["HOUSING10"] > 0)
                  & pl["POP10"].between(0.5 * me["POP10"], 2 * me["POP10"])]
        if len(comp) < 5 or me["HOUSING10"] <= 0:
            rows.append(dict(place=c.place, state=c.state, GEOID=g, status=f"too few comparison places ({len(comp)})"))
            continue
        cg = (comp["HOUSING20"].sum() - comp["HOUSING10"].sum()) / comp["HOUSING10"].sum() * 1000 / 10
        rows.append(dict(place=c.place, state=c.state, GEOID=g, status="included", event_year=c.event_year, date=c.date.date(),
                         exposure=c.exposure, homes_2010=me["HOUSING10"], homes_2020=me["HOUSING20"], growth=me["growth"],
                         comparison_growth=cg, difference=me["growth"] - cg, comparison_places=len(comp),
                         comparison_ids=";".join(comp["GEOID"])))
    k = pd.DataFrame(rows)
    k.drop(columns=["comparison_ids"], errors="ignore").round(4).to_csv(REFERENCE / "parking_census_route_cases.csv", index=False)
    inc = k[k["status"] == "included"].reset_index(drop=True)
    rng = np.random.default_rng(SEED)
    res = []
    groups = (("Main: 2,500+ homes in 2010", inc[inc["homes_2010"] >= MIN_HOMES]),
              ("Small places (under 2,500 homes)", inc[inc["homes_2010"] < MIN_HOMES]),
              ("Repeals taking effect 2010-2020 only, 2,500+ homes", inc[(inc["homes_2010"] >= MIN_HOMES) & (inc["exposure"] < 1)]),
              ("All sizes", inc))
    pool = pl[~pl["GEOID"].isin(reformed) & (pl["HOUSING10"] > 0)]
    for lab, d in groups:
        d = d.reset_index(drop=True)
        if len(d) < 2:
            continue
        w, e, y = d["homes_2010"].values, d["exposure"].values, d["difference"].values
        est = delta(y, e, w)
        bs = []
        for _ in range(DRAWS):
            i = rng.integers(0, len(d), len(d))
            bs.append(delta(y[i], e[i], w[i]))
        # placebo: never-repealed places matched on state and population, same exposures
        pls = []
        for _ in range(SETS):
            yy = []
            for r in d.itertuples():
                cand = pool[(pool["state_fips"] == pl.set_index("GEOID").loc[r.GEOID, "state_fips"])
                            & pool["POP10"].between(0.5 * pl.set_index("GEOID").loc[r.GEOID, "POP10"], 2 * pl.set_index("GEOID").loc[r.GEOID, "POP10"])
                            & (pool["GEOID"] != r.GEOID)]
                if cand.empty:
                    yy.append(np.nan)
                    continue
                f = cand.iloc[rng.integers(0, len(cand))]
                comp_ids = set(k.loc[k["GEOID"] == r.GEOID, "comparison_ids"].iloc[0].split(";")) - {f["GEOID"]}
                cc = pool[pool["GEOID"].isin(comp_ids)]
                yy.append(f["growth"] - (cc["HOUSING20"].sum() - cc["HOUSING10"].sum()) / cc["HOUSING10"].sum() * 100)
            yy = np.array(yy)
            ok = ~np.isnan(yy)
            pls.append(delta(yy[ok], e[ok], w[ok]))
        pls = np.array(pls)
        res.append(dict(case=lab, places=len(d), delta=est, p05=np.percentile(bs, 5), p95=np.percentile(bs, 95),
                        delta_permit_equivalent=est / CENSUS_TO_PERMITS, placebo_p05=np.percentile(pls, 5),
                        placebo_p50=np.percentile(pls, 50), placebo_p95=np.percentile(pls, 95),
                        share_placebo_at_or_below=float((pls <= est).mean()), mean_exposure=float(np.average(e, weights=w))))
    r = pd.DataFrame(res)
    r.round(4).to_csv(REFERENCE / "parking_census_route_results.csv", index=False)
    pd.set_option("display.width", 250)
    print(inc[["place", "state", "date", "exposure", "homes_2010", "growth", "comparison_growth", "difference", "comparison_places"]].round(2).to_string(index=False))
    print(k[k["status"] != "included"][["place", "state", "status"]].to_string(index=False))
    print(r.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
