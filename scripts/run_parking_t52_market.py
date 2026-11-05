"""Test 52a, market demand, and audit fix 8, denominator check (docs/parking/CAUSAL_FRAMEWORK_PLAN.md, "Test 52").

Nothing here edits the batch scripts: each override is applied in this process (or a child of it) before the batch
code runs, on a working copy of reference/ with the batch 2026-11-05 outputs laid over it.

    uv run --all-extras python scripts/run_parking_t52_market.py traits         # market traits for every place x repeal year
    uv run --all-extras python scripts/run_parking_t52_market.py main market    # main pipeline, pools trimmed on market traits
    uv run --all-extras python scripts/run_parking_t52_market.py main hu10      # main pipeline, Census 2010 homes denominator
    uv run --all-extras python scripts/run_parking_t52_market.py d              # method D: batch check, market, hu10; balance
    uv run --all-extras python scripts/run_parking_t52_market.py summarise      # results, paired shifts -> reference/

Traits (52a, audit fix 6), for repeal year ey (a pool place takes its matched repeal's ey):
- rent growth = log(ACS 5-year B25064, release ending ey-1) - log(release ending ey-6). Where the place's margin of
  error is above 20% of its estimate in either release (20% is a convention), both releases use the county's values.
  A place with no published estimate in either release is left missing (not filled from the county).
- job growth = log(QCEW county employment, ey-1) - log(ey-6). County-level only.

Method D (corrected method 2, candidate D): the two traits are added to the Mahalanobis traits (crowding, density, age)
by overriding run_parking_method2.traits.
Main (cmp.controls matched DiD): the main has no matching traits. Its rerun keeps the main ladder's pool and, where
the pool has more than 10 places, keeps the 10 nearest on Mahalanobis distance over the two market traits (method 2's
mahal() and nearest(), N_MATCH = 10). The placebo spread is rebuilt with the same rule.
HU10 (fix 8): Census 2010 housing units (2010 Gazetteer, HU10) replace ACS 2020-2024 homes as the denominator.
"""
from __future__ import annotations

import concurrent.futures as cf
import importlib
import multiprocessing as mp
import os
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

T52 = ROOT / "data" / "processed" / "t52"
BATCH = ROOT / "reference" / "batch_2026-11-05"
EYS = range(2016, 2025)
MOE_CUT = 0.20
N_TRIM = 10
WI_K = 2_668_677 * 5 / 1000
SEED, DRAWS = 20261105, 2000
WORKERS = 4
ENV = dict(VECLIB_MAXIMUM_THREADS="1", OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
           MM_GATE_TIME="15:50", MM_BATCH_COMMITTED_DIR="reference/batch_2026-11-05", MM_BPS_LAST_YEAR="2025")


def workdir(name: str) -> Path:
    return T52 / f"a_{name}_ref"


def make_workdir(name: str) -> Path:
    w = workdir(name)
    subprocess.run(["rm", "-rf", str(w)], check=True)
    w.mkdir(parents=True)
    subprocess.run(["rsync", "-a", "--exclude", "batch_2026-11-05/", str(ROOT / "reference") + "/", str(w) + "/"], check=True)
    subprocess.run(["rsync", "-a", str(BATCH) + "/", str(w) + "/"], check=True)
    return w


# ---------------------------------------------------------------- traits --------------------------------------------
def ct_norm(g):
    g = str(g)
    return "060|09" + g[-5:] if g.startswith("060|09") and len(g) == 14 else g


def bps_panel() -> pd.DataFrame:
    import run_parking_comparison as rpc
    from missing_middleware.parking import comparison as cmp
    bps = rpc.read_bps_us()
    p = cmp.panel(bps)
    sj = bps[(bps["state_fips"].astype(str).str.strip() == "18") & (bps["bps_id"].astype(str).str.strip() == "687500")].copy()
    sj["fips_place"] = "00001"
    return pd.concat([p, cmp.panel(sj)], ignore_index=True)


def build_traits() -> None:
    import run_parking_salvage as rps
    p = bps_panel()
    last = p.sort_values("year").drop_duplicates("key", keep="last").set_index("key")
    pre22 = p[p["year"] <= 2022].sort_values("year").drop_duplicates("key", keep="last").set_index("key")
    county = last["state_fips"] + last["county_fips"].str.zfill(3)
    ct = county.index[last["state_fips"] == "09"]  # Connecticut: the old county (planning regions from 2023 in BPS)
    county.loc[ct] = (pre22["state_fips"] + pre22["county_fips"].str.zfill(3)).reindex(ct)
    geoid = last["acs_geoid"].map(ct_norm)
    geoid[rps.SJ_KEY] = rps.SOUTH_BEND  # St. Joseph County remainder row: South Bend's own rent
    A = pd.read_csv(T52 / "acs_b25064.csv", dtype={"acs_geoid": str})
    A["acs_geoid"] = A["acs_geoid"].map(ct_norm)
    A = A[~A["acs_geoid"].str.endswith("00000")].drop_duplicates(["acs_geoid", "year"])
    R = A.pivot(index="acs_geoid", columns="year", values="rent")
    M = A.pivot(index="acs_geoid", columns="year", values="rent_moe")
    Q = pd.read_csv(T52 / "qcew_county.csv", dtype={"county": str})
    E = Q[Q["employment"] > 0].pivot(index="county", columns="year", values="employment")
    out = []
    for ey in EYS:
        lt, er = ey - 1, ey - 6
        pl, pe = R[lt].reindex(geoid.values).values, R[er].reindex(geoid.values).values
        ml, me = M[lt].reindex(geoid.values).values, M[er].reindex(geoid.values).values
        cg = ("050|" + county).values
        cl, ce = R[lt].reindex(cg).values, R[er].reindex(cg).values
        have = np.isfinite(pl) & np.isfinite(pe)
        with np.errstate(invalid="ignore", divide="ignore"):
            big = have & ((ml / pl > MOE_CUT) | (me / pe > MOE_CUT))
            place_g = np.log(pl / pe)
            county_g = np.log(cl / ce)
            job = np.log(E[lt].reindex(county.values).values / E[er].reindex(county.values).values)
        rent = np.where(have & ~big, place_g, np.where(big, county_g, np.nan))
        src = np.where(~have, "missing: no place estimate", np.where(~big, "place",
                       np.where(np.isfinite(county_g), "county (margin of error > 20%)", "missing: county fallback unavailable")))
        out.append(pd.DataFrame({"key": last.index, "event_year": ey, "acs_geoid": geoid.values, "county": county.values,
                                 "rent_growth": rent, "rent_source": src, "job_growth": job}))
    T = pd.concat(out, ignore_index=True)
    T.to_csv(T52 / "market_traits.csv", index=False)
    print(T.groupby("event_year")["rent_source"].value_counts().unstack().to_string())
    print(T.groupby("event_year")["job_growth"].apply(lambda s: s.notna().mean()).round(4).to_string())


@lru_cache(maxsize=None)
def mkt() -> dict:
    T = pd.read_csv(T52 / "market_traits.csv", dtype={"key": str, "county": str})
    return {ey: g.set_index("key")[["rent_growth", "job_growth"]] for ey, g in T.groupby("event_year")}


def mkt_for(ey: int) -> pd.DataFrame:
    m = mkt()
    return m.get(int(ey), pd.DataFrame(columns=["rent_growth", "job_growth"], dtype=float))


# ---------------------------------------------------------------- main overrides ------------------------------------
def make_trimmed_controls(orig):
    """Main ladder unchanged; pools of more than 10 keep the 10 nearest on the two market traits."""
    import run_parking_method2 as m2

    def trimmed(p, key, event_year, excluded, homes, population=None):
        c, label = orig(p, key, event_year, excluded, homes, population)
        if len(c) <= N_TRIM:
            return c, label
        T = mkt_for(event_year).reindex([key] + list(c))
        if not T.loc[key].notna().any():  # no market trait for the repeal place: pool unchanged
            return c, label + " | t52a: no trait, untrimmed"
        dist, _ = m2.mahal(T, key, list(c))
        if population is not None:
            pop = population
        else:
            pop = p[p["year"] == int(event_year) - 1].drop_duplicates("key").set_index("key")["pop"]
        pick = m2.nearest(dist, pop, float(pop.get(key, np.nan)), N_TRIM)
        return pick, label + f" | t52a: nearest {N_TRIM} of {len(c)}"
    return trimmed


def hu10_by_geoid(panel_geoids) -> pd.Series:
    """HU10 keyed by acs_geoid: 2010 Gazetteer places and county subdivisions; counties as the sum of their county
    subdivisions; Connecticut town geoids matched on state + town code (the 2022 planning regions)."""
    import run_parking_method2 as m2
    from missing_middleware.paths import RAW
    pl = m2.gaz(RAW / "parking_older_reforms" / "Gaz_places_national.zip", "Gaz_places_national.txt", "160")["HU10"]
    cs = m2.gaz(RAW / "census_gazetteer_2010" / "Gaz_cousubs_national.zip", "Gaz_cousubs_national.txt", "060")["HU10"]
    co = cs.groupby(cs.index.str[4:9]).sum()
    co.index = "050|" + co.index
    cs = cs[~cs.index.str.endswith("00000")]
    s = pd.concat([pl, cs, co]).astype(float)
    s = s[~s.index.duplicated()]
    ctmap = {ct_norm(i): v for i, v in s.items() if i.startswith("060|09")}
    extra = {g: ctmap[ct_norm(g)] for g in set(panel_geoids) if str(g).startswith("060|09") and g not in s.index
             and ct_norm(g) in ctmap}
    return pd.concat([s, pd.Series(extra, dtype=float)])


def apply_hu10_main() -> None:
    import run_parking_comparison as rpc
    import run_parking_salvage as rps
    hu = hu10_by_geoid(bps_panel()["acs_geoid"].unique())
    o_tab, o_acs = rpc.acs_table, rps.acs

    def acs_table(path, col):
        return hu.copy() if "b25002" in str(path) else o_tab(path, col)

    def acs(path, col, sumlevels=("050", "160")):
        return hu[hu.index.str[:3].isin(sumlevels)].copy() if "b25002" in str(path) else o_acs(path, col, sumlevels)
    rpc.acs_table, rps.acs = acs_table, acs


def exec_script(variant: str, module: str, args: list) -> None:
    """Child process: apply the variant's override, then run one batch script's main()."""
    from missing_middleware.parking import comparison as cmp
    if variant == "market":
        cmp.controls = make_trimmed_controls(cmp.controls)
    elif variant == "hu10":
        apply_hu10_main()
    else:
        raise SystemExit(variant)
    mod = importlib.import_module(module)
    sys.argv = [module + ".py"] + args
    mod.main()


def run_main(variant: str) -> None:
    w = make_workdir(variant)
    env = {**os.environ, **ENV, "MM_REFERENCE_DIR": str(w)}
    logs = T52 / f"a_{variant}_logs"
    logs.mkdir(parents=True, exist_ok=True)
    for module, args in (("run_parking_salvage", []), ("run_parking_partial", []), ("run_parking_expanded", []),
                         ("run_parking_placebo", ["--full", "--save-draws"])):
        print("==", variant, module, flush=True)
        with open(logs / f"{module}.log", "w") as f:
            r = subprocess.run(["uv", "run", "--all-extras", "python", __file__, "_exec", variant, module, *args],
                               cwd=ROOT, env=env, stdout=f, stderr=subprocess.STDOUT)
        if r.returncode:
            raise SystemExit(f"FAILED {variant} {module}; see {logs / (module + '.log')}")
    print("==", variant, "done", flush=True)


# ---------------------------------------------------------------- method D ------------------------------------------
def d_run() -> None:
    """Method D (corrected method 2, candidate D) in a batch working copy: the batch check, the market-trait rerun and
    the HU10 rerun; the balance table for main and D pools."""
    if os.environ.get("MM_REFERENCE_DIR") is None:
        w = make_workdir("d")
        env = {**os.environ, **ENV, "MM_REFERENCE_DIR": str(w)}
        r = subprocess.run(["uv", "run", "--all-extras", "python", __file__, "d"], cwd=ROOT, env=env)
        raise SystemExit(r.returncode)
    import run_parking_method2 as m2
    import run_parking_salvage as rps
    import run_parking_t45_t46 as t46
    from missing_middleware.parking import comparison as cmp
    from missing_middleware.paths import REFERENCE
    m2.SUF, m2.CORRECTED = "_corrected", True
    m2.WORKERS = WORKERS
    D = m2.Data()
    real, cases = m2.real_cases()
    main_calls = t46.rebuild(real, t46.collect())
    # main pools under the market trim (same recording, with the trimmed ladder)
    o = t46._orig_controls
    t46._orig_controls = make_trimmed_controls(o)
    try:
        trim_calls = t46.rebuild(real, t46.collect())
    finally:
        t46._orig_controls = o
    v = m2.placebo_v(len(real))
    ev = pd.DataFrame({"v": v, "homes": real["homes"].values, "n_post": real["n_post"].values,
                       "band": m2.band_of(real["population"].fillna(0)), "metro": [D.metro.get(c["key"], 0.0) for c in cases]})
    ev["base"] = ev["homes"] * ev["n_post"]
    wi = m2.target_cells(D, "55")

    # HU10 by BPS key (South Bend: the combined area, as in the salvage script)
    hu = hu10_by_geoid(D.geo["acs_geoid"].unique())
    hk = D.geo["acs_geoid"].map(hu)
    others = [k for k in D.geo.index if k.startswith("18|") and D.geo.loc[k, "county_fips"] == "141"
              and D.geo.loc[k, "name"].replace(" town", "") in rps.SJ_OTHER_PLACES]
    hk[rps.SJ_KEY] = hu.get(rps.SJ_COUNTY, np.nan) - hk.reindex(others).sum()
    hk = hk[hk > 0].astype(float)
    sb_scale_hu10 = float(hu.get(rps.SOUTH_BEND, np.nan) / hk.get(rps.SJ_KEY, np.nan))

    o_traits, o_rates, o_pool_rate, o_eligible = m2.traits, m2.rates, m2.pool_rate, m2.eligible

    def traits_mkt(D_, keys, pre, ey, h, with_pace, with_pop):
        t = o_traits(D_, keys, pre, ey, h, with_pace, with_pop)
        M = mkt_for(ey).reindex(t.index)
        t["rent_growth"], t["job_growth"] = M["rent_growth"].values, M["job_growth"].values
        return t

    def rates_hu10(D_, keys, years, h):
        return D_.P.loc[keys, list(years)].div(hk.reindex(keys), axis=0) * 1000

    def pool_rate_hu10(D_, pool, years, h, wins):
        R = m2.winsor_cols(rates_hu10(D_, pool, years, h), wins)
        w = hk.reindex(pool).values
        return pd.Series((R.values * w[:, None]).sum(axis=0) / w.sum(), index=list(years))

    def eligible_hu10(D_, target, years, mode_exc, shock_on, h):
        return [k for k in o_eligible(D_, target, years, mode_exc, shock_on, h) if k in hk.index]

    def restore():
        m2.traits, m2.rates, m2.pool_rate, m2.eligible = o_traits, o_rates, o_pool_rate, o_eligible

    runs = {}
    for name in ("batch", "market", "hu10"):
        restore()
        cs = cases
        if name == "market":
            m2.traits = traits_mkt
        elif name == "hu10":
            m2.rates, m2.pool_rate, m2.eligible = rates_hu10, pool_rate_hu10, eligible_hu10
            cs = [dict(c, scale=sb_scale_hu10) if c["key"] == rps.SJ_KEY else c for c in cases]
        m2._G = dict(D=D, cases=cs)
        with cf.ProcessPoolExecutor(WORKERS, mp_context=mp.get_context("fork")) as ex:
            res = list(ex.map(m2._variant, [("D", m2.OPT_MAIN)]))[0]
        runs[name] = res
        print("D run", name, "done", flush=True)
    restore()

    # per-place effects and results for every weighting
    rows, places = [], []
    for name, res in runs.items():
        y = np.array([r["effect"] for r in res], dtype=float)
        ok = np.isfinite(y)
        for kind in m2.WEIGHTS:
            a = m2.weighted_avg(kind, y[ok], ev[ok].reset_index(drop=True), wi, True)
            lo, hi = m2.boot_range(kind, y[ok], ev[ok].reset_index(drop=True), wi, m2.BOOT, m2.SEED, True)
            rows.append(dict(run=name, weights=kind, places=int(ok.sum()), average=a, p05=lo, p95=hi,
                             wi_homes=a * WI_K, wi_p05=lo * WI_K, wi_p95=hi * WI_K))
        for c, r in zip(cases, res):
            places.append(dict(run=name, i=c["i"], key=c["key"], place=c["place"], state=c["state"], event_year=c["event_year"],
                               effect=r["effect"], step=r["step"], n_pool=r["n_pool"], missing_share=r["missing_share"]))
    pd.DataFrame(rows).to_csv(T52 / "d_results_all_weights.csv", index=False)
    P = pd.DataFrame(places)
    P.to_csv(T52 / "d_places.csv", index=False)
    ev.assign(key=[c["key"] for c in cases]).to_csv(T52 / "d_ev.csv", index=False)

    # batch check: the reproduced batch effects must equal the committed batch places
    bp = pd.read_csv(BATCH / "parking_method2_corrected_places.csv")
    bp = bp[bp["variant"] == "method 2, D"].reset_index(drop=True)
    mine = P[P["run"] == "batch"].reset_index(drop=True)
    gap = float(np.nanmax(np.abs(mine["effect"].values - bp["effect"].values)))
    print("batch check: largest |effect gap| vs committed batch places =", gap, flush=True)

    # paired shifts for D (target-state mix), paired place bootstrap
    yb = np.array([r["effect"] for r in runs["batch"]], dtype=float)
    shift = []
    for name in ("market", "hu10"):
        yn = np.array([r["effect"] for r in runs[name]], dtype=float)
        ok = np.isfinite(yb) & np.isfinite(yn)
        e2 = ev[ok].reset_index(drop=True)
        a, b = yn[ok], yb[ok]
        d0 = m2.weighted_avg("target-state mix", a, e2, wi) - m2.weighted_avg("target-state mix", b, e2, wi)
        rng = np.random.default_rng(SEED)
        bd = []
        for _ in range(DRAWS):
            i = rng.integers(0, len(a), len(a))
            ei = e2.iloc[i].reset_index(drop=True)
            bd.append(m2.weighted_avg("target-state mix", a[i], ei, wi) - m2.weighted_avg("target-state mix", b[i], ei, wi))
        lo, hi = np.nanpercentile(bd, [5, 95])
        shift.append(dict(method="D", run=name, places_paired=int(ok.sum()), shift=d0, shift_p05=lo, shift_p95=hi))
    pd.DataFrame(shift).to_csv(T52 / "d_shifts.csv", index=False)

    # balance: repeal places vs their pools (pool traits at the matched repeal's year)
    def trait_frame(keys, ey):
        t = pd.DataFrame({"crowding": D.crowd_for(ey).reindex(keys).values, "density": D.density.reindex(keys).values,
                          "age": D.age.reindex(keys).values}, index=keys)
        M = mkt_for(ey).reindex(keys)
        t["rent_growth"], t["job_growth"] = M["rent_growth"].values, M["job_growth"].values
        return t
    pools = {"main (batch)": [list(x["call"]["pool"]) for _, x in main_calls.iterrows()],
             "main (market trim)": [list(x["call"]["pool"]) for _, x in trim_calls.iterrows()],
             "D (batch)": [r.get("pool", []) for r in runs["batch"]],
             "D (market traits)": [r.get("pool", []) for r in runs["market"]]}
    tr_rows, pool_rows = [], []
    for c in cases:
        t = trait_frame([c["key"]], c["event_year"]).iloc[0]
        tr_rows.append(dict(i=c["i"], key=c["key"], place=c["place"], state=c["state"], event_year=c["event_year"], **t.to_dict()))
    TR = pd.DataFrame(tr_rows)
    for label, pl in pools.items():
        for c, pool in zip(cases, pl):
            if not pool:
                continue
            t = trait_frame(list(pool), c["event_year"])
            t["w"] = 1.0 / len(pool)
            t["i"], t["method"] = c["i"], label
            pool_rows.append(t.reset_index(names="key"))
    PL = pd.concat(pool_rows, ignore_index=True)
    PL.to_csv(T52 / "balance_pool_members.csv", index=False)
    TR.to_csv(T52 / "balance_repeal_places.csv", index=False)
    bal = []
    for label in pools:
        g = PL[PL["method"] == label]
        for tr in ("rent_growth", "job_growth", "crowding", "density", "age"):
            xt = TR.loc[TR["i"].isin(g["i"].unique()), tr].dropna()
            gc = g.dropna(subset=[tr])
            mt, vt = xt.mean(), xt.var(ddof=1)
            mc = np.average(gc[tr], weights=gc["w"])
            vc = np.average((gc[tr] - mc) ** 2, weights=gc["w"])
            smd = (mt - mc) / np.sqrt((vt + vc) / 2)
            bal.append(dict(pools=label, trait=tr, repeal_places=len(xt), repeal_mean=mt, pool_members=len(gc),
                            pool_cases=gc["i"].nunique(), pool_mean=mc, standardised_difference=smd,
                            flag_over_0_25=bool(abs(smd) > 0.25)))
    pd.DataFrame(bal).to_csv(T52 / "balance.csv", index=False)
    print(pd.DataFrame(bal).round(3).to_string(), flush=True)
    print(pd.DataFrame(rows).round(3).to_string(), flush=True)
    print(pd.DataFrame(shift).round(3).to_string(), flush=True)
    _ = (cmp, REFERENCE)


# ---------------------------------------------------------------- summary -------------------------------------------
def summarise() -> None:
    out = []
    # main: estimate with placebo spread; paired shift by prn_key (each run's own weights, as in Test 51)
    eb = pd.read_csv(BATCH / "parking_expanded_effects.csv")
    eb = eb[(eb["status"] == "included") & (eb["outcome"] == "all")].dropna(subset=["effect"]).set_index("prn_key")
    pb = pd.read_csv(BATCH / "parking_placebo_full_summary.csv").iloc[0]
    out.append(dict(method="main", run="batch", places=len(eb), estimate=pb["real_average"], p05=pb["range_from_placebo_low"],
                    p95=pb["range_from_placebo_high"]))
    for name in ("market", "hu10"):
        w = workdir(name)
        e = pd.read_csv(w / "parking_expanded_effects.csv")
        e = e[(e["status"] == "included") & (e["outcome"] == "all")].dropna(subset=["effect"]).set_index("prn_key")
        ps = pd.read_csv(w / "parking_placebo_full_summary.csv").iloc[0]
        both = eb.index.intersection(e.index)
        yb, yn = eb.loc[both, "effect"].values, e.loc[both, "effect"].values
        for wlab, wb, wn in (("own weights", eb.loc[both, "weight"].values, e.loc[both, "weight"].values),
                             ("batch weights", eb.loc[both, "weight"].values, eb.loc[both, "weight"].values)):
            if name == "market" and wlab == "batch weights":
                continue  # same homes, same weights
            d0 = np.average(yn, weights=wn) - np.average(yb, weights=wb)
            rng = np.random.default_rng(SEED)
            bd = []
            for _ in range(DRAWS):
                i = rng.integers(0, len(both), len(both))
                bd.append(np.average(yn[i], weights=wn[i]) - np.average(yb[i], weights=wb[i]))
            lo, hi = np.percentile(bd, [5, 95])
            row = dict(method="main", run=name, places=len(e), places_paired=len(both), shift=d0, shift_p05=lo, shift_p95=hi,
                       shift_weights=wlab)
            if wlab == "own weights":
                row.update(estimate=ps["real_average"], p05=ps["range_from_placebo_low"], p95=ps["range_from_placebo_high"],
                           placebo_places=int(ps["placebo_places"]), real_places_matched=int(ps["real_places_matched"]))
            out.append(row)
    # method D
    dr = pd.read_csv(T52 / "d_results_all_weights.csv")
    ds = pd.read_csv(T52 / "d_shifts.csv").set_index("run")
    for name in ("batch", "market", "hu10"):
        r = dr[(dr["run"] == name) & (dr["weights"] == "target-state mix")].iloc[0]
        row = dict(method="D (target-state mix)", run=name, places=int(r["places"]), estimate=r["average"], p05=r["p05"], p95=r["p95"])
        if name in ds.index:
            s = ds.loc[name]
            row.update(places_paired=int(s["places_paired"]), shift=s["shift"], shift_p05=s["shift_p05"], shift_p95=s["shift_p95"],
                       shift_weights="target-state mix")
        out.append(row)
    R = pd.DataFrame(out)
    for c in ("estimate", "p05", "p95", "shift", "shift_p05", "shift_p95"):
        R[f"wi_{c}"] = R[c] * WI_K
    R["reading"] = np.where(R["shift"].isna(), "", np.where((R["shift_p05"] > 0) | (R["shift_p95"] < 0),
                                                            "counts: paired range excludes 0", "does not count: paired range includes 0"))
    R["run"] = R["run"].map({"batch": "batch 2026-11-05", "market": "52a: rent and job growth added",
                             "hu10": "fix 8: Census 2010 homes (HU10) denominator"})
    R.round(4).to_csv(ROOT / "reference" / "parking_t52_a_results.csv", index=False)
    B = pd.read_csv(T52 / "balance.csv")
    B.round(4).to_csv(ROOT / "reference" / "parking_t52_a_balance.csv", index=False)
    # repeal-place traits and per-place effects
    TR = pd.read_csv(T52 / "balance_repeal_places.csv")
    P = pd.read_csv(T52 / "d_places.csv").pivot(index="i", columns="run", values="effect").add_prefix("d_effect_")
    TR = TR.merge(P, left_on="i", right_index=True, how="left")
    mt = pd.read_csv(T52 / "market_traits.csv", dtype={"key": str})
    TR = TR.merge(mt[["key", "event_year", "rent_source", "county"]], on=["key", "event_year"], how="left")
    TR.round(5).to_csv(ROOT / "reference" / "parking_t52_a_places.csv", index=False)
    # coverage and margin-of-error fallbacks
    PL = pd.read_csv(T52 / "balance_pool_members.csv", dtype={"key": str})
    cov = []
    ey_of = dict(zip(TR["i"], TR["event_year"]))
    PL["event_year"] = PL["i"].map(ey_of)
    groups = {"repeal places": TR[["key", "event_year"]]}
    for m in PL["method"].unique():
        groups[f"pool members, {m} (place x repeal year)"] = PL.loc[PL["method"] == m, ["key", "event_year"]]
    groups["all BPS places, all repeal years 2016-2024"] = mt[["key", "event_year"]]
    for lab, g in groups.items():
        x = g.merge(mt, on=["key", "event_year"], how="left")
        vc = x["rent_source"].value_counts()
        cov.append(dict(group=lab, rows=len(x), rent_from_place=int(vc.get("place", 0)),
                        rent_from_county_moe_over_20pct=int(vc.get("county (margin of error > 20%)", 0)),
                        rent_missing_no_place_estimate=int(vc.get("missing: no place estimate", 0)),
                        rent_missing_county_unavailable=int(vc.get("missing: county fallback unavailable", 0)),
                        rent_growth_available=int(x["rent_growth"].notna().sum()),
                        job_growth_available=int(x["job_growth"].notna().sum())))
    C = pd.DataFrame(cov)
    C.to_csv(ROOT / "reference" / "parking_t52_a_coverage.csv", index=False)
    pd.set_option("display.width", 250)
    print(C.to_string())
    print(B.round(3).to_string())
    print(R.round(3).T.to_string())


def main() -> None:
    a = sys.argv[1:]
    if not a:
        raise SystemExit(__doc__)
    if a[0] == "traits":
        build_traits()
    elif a[0] == "main":
        run_main(a[1])
    elif a[0] == "_exec":
        exec_script(a[1], a[2], a[3:])
    elif a[0] == "d":
        d_run()
    elif a[0] == "summarise":
        summarise()
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
