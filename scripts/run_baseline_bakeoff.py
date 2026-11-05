"""Baseline bake-off (docs/shared/BASELINE_BAKEOFF_PLAN.md, locked 2026-11-05). Part 1: the level; Part 2: shares.

    uv run python scripts/run_baseline_bakeoff.py --part 1
    uv run python scripts/build_baseline_bakeoff_links.py && uv run python scripts/run_baseline_bakeoff.py --part 2

Part 2 inputs: data/interim/baseline_bakeoff/{bps_place_1990_2025,xw,alloc}.parquet (link script),
data/raw/baseline_bakeoff/hu_1990/pl9417wi.dbf, hu_api/dec_{2000,2010,2020}_cousub55.json,
data/raw/milwaukee_mprop/mprop.csv, data/processed/foundation/areas.parquet, Part 1's rows file.
Part 2 outputs: reference/baseline_bakeoff_part2_{rows,summary,params,joint,shares_2025}.csv

Inputs: data/raw/census_bps_state/st{1990..2025}a.txt (all states), data/raw/baseline_bakeoff/ (fetch script:
hu_1990/st-98-51.txt, hu_api/dec_{2000,2010,2020}_state.json).
Outputs (committed): reference/baseline_bakeoff_part1_{rows,summary,params,by_group,range,coverage,wisconsin}.csv
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from missing_middleware import baseline_bakeoff as bb  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

BB = RAW / "baseline_bakeoff"
WI = "55"
V3_CENTRAL = 124_000
UNIT_COLS = {"1unit": 6, "2units": 9, "3_4units": 12, "5plus": 15}   # estimate columns (units) in state files
STATES = {f"{i:02d}" for i in range(1, 57)} - {"03", "07", "14", "43", "52"}   # 50 states + DC


def read_state_permits() -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, geo = [], {}
    for y in range(1990, 2026):
        for line in (RAW / "census_bps_state" / f"st{y}a.txt").read_text(errors="ignore").splitlines()[2:]:
            p = [x.strip() for x in line.split(",")]
            if len(p) < 16 or p[1] not in STATES:
                continue
            geo[p[1]] = dict(state=p[1], region=p[2], division=p[3], name=p[4])
            for z, c in UNIT_COLS.items():
                rows.append(dict(state=p[1], year=y, size=z, units=float(p[c])))
    u = pd.DataFrame(rows)
    if u.groupby(["state", "year"]).size().ne(4).any() or u["state"].nunique() != 51:
        raise SystemExit("state files: expected 51 states x 36 years x 4 sizes")
    return u, pd.DataFrame(geo.values())


def read_census() -> pd.DataFrame:
    rows = []
    lines = (BB / "hu_1990" / "st-98-51.txt").read_text(errors="ignore").splitlines()
    for ln in lines:
        t = ln.split()
        if len(t) > 12 and t[0] == "14" and t[1] in STATES and not ln.startswith("Block"):
            rows.append(dict(state=t[1], year=1990, homes=float(t[-3])))   # 4/1/90 census column
    for y in (2000, 2010, 2020):
        d = json.loads((BB / "hu_api" / f"dec_{y}_state.json").read_text())
        hdr = d[0]
        for r in d[1:]:
            rec = dict(zip(hdr, r))
            if rec["state"] in STATES:
                rows.append(dict(state=rec["state"], year=y, homes=float(rec[hdr[1]])))
    c = pd.DataFrame(rows).drop_duplicates(["state", "year"])
    if c.groupby("year")["state"].nunique().ne(51).any():
        raise SystemExit(f"census housing units: expected 51 states per year, got {c.groupby('year')['state'].nunique().to_dict()}")
    return c


def final_ranges(u, homes, division, W) -> pd.DataFrame:
    """Wisconsin 2027-2031 low/central/high for L0 and every candidate: multipliers (actual / predicted) from
    Wisconsin's start years (plan) and, as the sensitivity, from all states; at 10th-90th and at the widening stop
    (2.5th-97.5th). Published-file figures, and scaled to v3 by the ratio to L0 (plan log)."""
    w0 = W.set_index("candidate").loc["L0", "published_five_year"]
    out = []
    for c in bb.CANDIDATES:
        first = {"L1c": 1999, "L1b": 1996, "L1a": 1994, "L4a": 1999}.get(c, 1997 if c in bb.FITTED else 1992)
        ss = list(range(first, 2021))
        par = {t: bb.fit_param(c, u, homes, t, division) for t in ss} if c in bb.FITTED else None
        rr = bb.score_rows(c, u, homes, ss, division, par)
        p25 = bb.fit_param(c, u, homes, 2025, division) if c in bb.FITTED else None
        pr = bb.predict(c, u, homes, 2025, division, p25) * bb.HORIZON
        for scope, d in (("wisconsin", rr[rr.state == WI]), ("all_states", rr)):
            long = pd.concat([pd.DataFrame(dict(size=z, ratio=d[f"actual_{z}"] / d[f"pred_{z}"])) for z in bb.SIZES])
            long = long[np.isfinite(long["ratio"]) & (long["ratio"] > 0)]
            for lo, hi in ((0.10, 0.90), (0.025, 0.975)):
                q = long.groupby("size")["ratio"].quantile([lo, hi]).unstack()
                cen = float(pr.loc[WI].sum())
                low = float(sum(pr.loc[(WI, z)] * q.loc[z, lo] for z in bb.SIZES))
                high = float(sum(pr.loc[(WI, z)] * q.loc[z, hi] for z in bb.SIZES))
                f = V3_CENTRAL / w0
                out.append(dict(candidate=c, scope=scope, lo=lo, hi=hi, published_central=cen, published_low=low,
                                published_high=high, v3_central=cen * f, v3_low=low * f, v3_high=high * f))
    return pd.DataFrame(out)


# ---------------------------------------------------------------- Part 2
MKE_BPS_ID, MKE_TYPES = "572000", ("3_4units", "5plus")


def pl94_1990_cousub() -> dict:
    """1990 P.L. 94-171 Wisconsin county subdivisions (SUMLEV 060): geoid -> housing units (HU100)."""
    raw = (BB / "hu_1990" / "pl9417wi.dbf").read_bytes()
    n, hl, rl = (int.from_bytes(raw[a:b], "little") for a, b in ((4, 8), (8, 10), (10, 12)))
    flds, i, off = {}, 32, 1
    while raw[i] != 0x0D:
        flds[raw[i:i + 11].split(b"\x00")[0].decode()] = (off, raw[i + 16])
        off += raw[i + 16]
        i += 32
    g = lambda rec, k: rec[flds[k][0]:flds[k][0] + flds[k][1]].decode("latin-1").strip()  # noqa: E731
    out = {}
    for j in range(n):
        rec = raw[hl + j * rl: hl + (j + 1) * rl]
        if g(rec, "SUMLEV") == "060" and g(rec, "GEOCOMP") == "00":
            out["55" + g(rec, "CNTY") + g(rec, "COUSUBFP")] = float(g(rec, "HU100"))
    if abs(sum(out.values()) - 2_055_774) > 1:
        raise SystemExit(f"1990 county subdivisions do not add to the state's 2,055,774 homes: {sum(out.values()):,.0f}")
    return out


def api_cousub(y: int) -> dict:
    d = json.loads((BB / "hu_api" / f"dec_{y}_cousub55.json").read_text())
    h = d[0]
    return {r[h.index("state")] + r[h.index("county")] + r[h.index("county subdivision")]: float(r[1]) for r in d[1:]}


def mprop_estimate(years) -> pd.Series:
    """Milwaukee city 3-4 and 5+ units by permit year: MPROP units by year built, shifted one year earlier (as v3)."""
    m = pd.read_csv(RAW / "milwaukee_mprop" / "mprop.csv", usecols=["YR_BUILT", "NR_UNITS"], low_memory=False)
    m = m.apply(pd.to_numeric, errors="coerce").dropna()
    m = m[m["NR_UNITS"] >= 3]
    m["structure_type"] = pd.cut(m["NR_UNITS"], [2, 4, 1e9], labels=list(MKE_TYPES)).astype(str)
    m["year"] = m["YR_BUILT"].astype(int) - 1
    s = m[m["year"].isin(years)].groupby(["year", "structure_type"])["NR_UNITS"].sum()
    idx = pd.MultiIndex.from_product([list(years), MKE_TYPES], names=["year", "structure_type"])
    return s.reindex(idx).astype(float).fillna(0.0)


def part2() -> None:
    from missing_middleware import baseline_bakeoff_shares as sh
    from missing_middleware import housing_baseline as hb
    from missing_middleware.paths import PROCESSED, ROOT
    I = ROOT / "data" / "interim" / "baseline_bakeoff"
    b = pd.read_parquet(I / "bps_place_1990_2025.parquet")
    xw, alloc = pd.read_parquet(I / "xw.parquet"), pd.read_parquet(I / "alloc.parquet")
    gaps = {(MKE_BPS_ID, y): True for y in (2020, 2023, 2025)}
    hist = hb.allocate(hb.long_bps(b, gaps), xw, alloc)
    hist = hb.area_year_type(hist)
    # Milwaukee property-file fix, permit years 2000-2024 (plan: carried back to 2000; 2025 stays null)
    est = mprop_estimate(range(2000, 2025))
    pieces = xw[(xw["bps_id"] == MKE_BPS_ID) & xw["area_id"].notna()][["area_id", "alloc_share"]].drop_duplicates()
    if pieces.empty:
        raise SystemExit("Milwaukee city pieces not found in the crosswalk")
    for r in pieces.itertuples():
        for (y, t), v in est.items():
            m = (hist["area_id"] == r.area_id) & (hist["year"] == y) & (hist["structure_type"] == t)
            if m.any():
                hist.loc[m, "units"] = v * r.alloc_share
            else:
                hist = pd.concat([hist, pd.DataFrame([dict(area_id=r.area_id, year=y, structure_type=t,
                                                           units=v * r.alloc_share, allocation="mprop")])])
    hist = hist[hist["area_id"] != hb.UNALLOCATED]

    areas = pd.read_parquet(PROCESSED / "foundation" / "areas.parquet")
    mun = areas[areas["level"] == "municipality"].sort_values("area_id").reset_index(drop=True)
    ids, county = mun["area_id"].to_numpy(), mun["parent_county_id"].astype(str).to_numpy()
    acs = mun["housing_units_acs"].fillna(0).to_numpy(dtype=float)
    pos = {a: i for i, a in enumerate(ids)}
    arrays = {}
    for z in sh.SIZES:
        a = np.full((len(ids), len(sh.YEARS)), np.nan)
        d = hist[hist["structure_type"] == z]
        for area, y, v in zip(d["area_id"], d["year"], d["units"]):
            if area in pos and 1990 <= y <= 2025:
                a[pos[area], y - 1990] = v
        arrays[z] = a
    permits_all = np.nansum(np.stack([arrays[z] for z in sh.SIZES]), axis=0)
    geo = mun["geoid"].astype(str).to_numpy()
    cen = {1990: pl94_1990_cousub(), 2000: api_cousub(2000), 2010: api_cousub(2010), 2020: api_cousub(2020)}
    census = {y: np.array([c.get(g, np.nan) for g in geo]) for y, c in cen.items()}
    homes = {t: sh.homes_at(census, permits_all, t, acs) for t in range(1990, 2026)}
    large = acs >= 1000

    def preds_at(c, t, k=None, cap=2.0):
        return {z: sh.predict(c, arrays[z], county, t, homes[t], k, cap) for z in sh.SIZES}

    def fit_k(t):
        fs = range(sh.FIRST_FIT_START, t - sh.HORIZON + 1)
        best, bv = None, np.inf
        for k in sh.K_GRID:
            v = np.mean([sh.score_start(preds_at("S3", s, k), arrays, s) for s in fs])
            if v < bv - 1e-12:
                best, bv = k, v
        return best

    ks = {t: fit_k(t) for t in sh.SCORE_STARTS}
    rows = []
    for c in sh.CANDIDATES + ("S4_cap3",):
        for t in sh.SCORE_STARTS:
            cc, cap = ("S4", 3.0) if c == "S4_cap3" else (c, 2.0)
            p = preds_at(cc, t, ks[t] if cc == "S3" else None, cap)
            rows.append(dict(candidate=c, start=t, k=ks[t] if cc == "S3" else np.nan,
                             score=sh.score_start(p, arrays, t), score_large=sh.score_start(p, arrays, t, large),
                             score_small=sh.score_start(p, arrays, t, ~large)))
    R = pd.DataFrame(rows)
    draws = sh.block_bootstrap_starts(sh.SCORE_STARTS)
    base = R[R.candidate == "S0"].set_index("start")["score"]
    summ = []
    for c in R["candidate"].unique():
        r = R[R.candidate == c].set_index("start")
        d = r["score"] - base
        boot = np.array([d.loc[dr].mean() for dr in draws])
        summ.append(dict(candidate=c, score=r["score"].mean(), score_large=r["score_large"].mean(),
                         score_small=r["score_small"].mean(), diff_vs_s0=d.mean(),
                         boot_lo=np.quantile(boot, 0.05), boot_hi=np.quantile(boot, 0.95)))
    S = pd.DataFrame(summ)
    s0 = S.set_index("candidate").loc["S0", "score"]
    S["pass_margin"] = S["score"] <= 0.98 * s0
    S["pass_boot"] = S["boot_hi"] < 0
    winner = sh.pick(S[S.candidate.isin(sh.CANDIDATES)])
    S["winner"] = S["candidate"] == winner

    # joint check (reported only): Part 1 level x Part 2 shares on Wisconsin pieces, not scaled to the actual total
    p1 = pd.read_csv(REFERENCE / "baseline_bakeoff_part1_rows.csv", dtype={"state": str})
    p1s = pd.read_csv(REFERENCE / "baseline_bakeoff_part1_summary.csv")
    lw = p1s.loc[p1s["winner"], "candidate"].iloc[0]
    J = []
    for lev, shr in (("L0", "S0"), (lw, winner)):
        lv = p1[(p1.candidate == lev) & (p1.state == WI)].set_index("start")
        for t in sh.SCORE_STARTS:
            p = preds_at(shr, t, ks[t] if shr == "S3" else None)
            num = den = 0.0
            for z in sh.SIZES:
                act, ok = sh.actual(arrays[z], t)
                tot = p[z][ok].sum()
                pp = p[z][ok] / tot * lv.loc[t, f"pred_{z}"] if tot > 0 else p[z][ok] * 0
                num += np.abs(pp - act[ok]).sum()
                den += act[ok].sum()
            J.append(dict(level=lev, shares=shr, start=t, score_unscaled=num / den))
    J = pd.DataFrame(J)

    # 2025 shares, S0 and the winner, by piece and size
    k25 = fit_k(2025) if winner == "S3" else None
    out = []
    for c in ("S0", winner):
        p = preds_at(c, 2025, k25 if c == "S3" else None)
        for z in sh.SIZES:
            tot = p[z].sum()
            out.append(pd.DataFrame(dict(candidate=c, area_id=ids, name=mun["name"], size=z,
                                         share=p[z] / tot if tot else 0.0)))
    SH = pd.concat(out, ignore_index=True)
    R.round(5).to_csv(REFERENCE / "baseline_bakeoff_part2_rows.csv", index=False)
    S.round(5).to_csv(REFERENCE / "baseline_bakeoff_part2_summary.csv", index=False)
    pd.DataFrame(dict(start=list(ks), k=list(ks.values()))).to_csv(REFERENCE / "baseline_bakeoff_part2_params.csv", index=False)
    J.round(5).to_csv(REFERENCE / "baseline_bakeoff_part2_joint.csv", index=False)
    SH.round(7).to_csv(REFERENCE / "baseline_bakeoff_part2_shares_2025.csv", index=False)
    print(S.round(4).to_string(index=False))
    print("winner:", winner, "| k fitted:", {t: round(v) for t, v in ks.items()})
    print(J.groupby(["level", "shares"])["score_unscaled"].mean().round(4))


def main() -> None:
    part = sys.argv[sys.argv.index("--part") + 1] if "--part" in sys.argv else None
    if part == "2":
        return part2()
    if part != "1":
        raise SystemExit("usage: --part 1 | --part 2")
    u, geo = read_state_permits()
    census = read_census()
    allu = u.groupby(["state", "year"], as_index=False)["units"].sum()
    homes = bb.homes_by_year(census, allu, range(1990, 2026))
    division = geo.set_index("state")["division"]
    region = geo.set_index("state")["region"]

    starts = bb.SCORE_STARTS
    params, rows = {}, []
    for c in bb.CANDIDATES:
        if c in bb.FITTED:
            params[c] = {t: bb.fit_param(c, u, homes, t, division) for t in starts}
        rows.append(bb.score_rows(c, u, homes, starts, division, params.get(c)))
    R = pd.concat(rows, ignore_index=True)
    R["region"], R["division"] = R["state"].map(region), R["state"].map(division)

    draws = bb.block_bootstrap_starts(starts)
    base = R[R.candidate == "L0"]
    summ = []
    for c in bb.CANDIDATES:
        r = R[R.candidate == c]
        d = bb.paired_diff(r, base, draws) if c != "L0" else np.zeros(len(draws))
        point = r["abs_log"].mean() - base["abs_log"].mean()
        summ.append(dict(candidate=c, score=r["abs_log"].mean(), bias=r["log_ratio"].mean(),
                         crash_score=r[r.start.between(2005, 2009)]["abs_log"].mean(),
                         wi_score=r[r.state == WI]["abs_log"].mean(), wi_bias=r[r.state == WI]["log_ratio"].mean(),
                         diff_vs_l0=point, boot_lo=np.quantile(d, 0.05), boot_hi=np.quantile(d, 0.95)))
    S = pd.DataFrame(summ)
    l0 = S.set_index("candidate").loc["L0"]
    S["pass_margin"] = S["score"] <= 0.98 * l0["score"]
    S["pass_boot"] = S["boot_hi"] < 0
    S["pass_wi"] = S["wi_score"] <= 1.05 * l0["wi_score"]
    winner = bb.pick(S)
    S["winner"] = S["candidate"] == winner

    # by size, region and division (reported only)
    size_rows = []
    for c in bb.CANDIDATES:
        r = R[R.candidate == c]
        for z in bb.SIZES:
            size_rows.append(dict(candidate=c, group="size", value=z,
                                  score=np.abs(np.log(r[f"pred_{z}"].clip(lower=1e-9) / r[f"actual_{z}"].clip(lower=1e-9))).mean()))
        for g in ("region", "division"):
            for v, rr in r.groupby(g):
                size_rows.append(dict(candidate=c, group=g, value=v, score=rr["abs_log"].mean()))
    G = pd.DataFrame(size_rows)

    # range and coverage for every candidate (winner's is the one used); Wisconsin, start years 1992..2020
    rng_rows, cov_rows, wis = [], [], []
    wi_u = u[u.state == WI]
    for c in bb.CANDIDATES:
        first = {"L1c": 1999, "L1b": 1996, "L1a": 1994, "L4a": 1999}.get(c, 1992)
        ss = list(range(first, 2021))
        par = None
        if c in bb.FITTED:   # fitted per start year with the same no-look-ahead rule (fit years need s <= t-5)
            par = {t: bb.fit_param(c, u, homes, t, division) if t - 5 >= bb.FIRST_FIT_START else np.nan for t in ss}
            ss = [t for t in ss if not np.isnan(par[t])]
        rr = bb.score_rows(c, u, homes, ss, division, par)
        rr = rr[rr.state == WI]
        long = pd.concat([pd.DataFrame(dict(start=rr["start"], size=z, pred=rr[f"pred_{z}"], actual=rr[f"actual_{z}"]))
                          for z in bb.SIZES], ignore_index=True)
        long["ratio"] = long["actual"] / long["pred"]
        m = bb.range_multipliers(long).reset_index().assign(candidate=c, n_starts=len(ss))
        rng_rows.append(m)
        cov = bb.coverage_check(long[["start", "size", "ratio"]], long).assign(candidate=c)
        cov_rows.append(cov)
        # Wisconsin 2027-2031 at start year 2025 (plan log: ratio to L0 x 124,000)
        p25 = None if c not in bb.FITTED else bb.fit_param(c, u, homes, 2025, division)
        pr = bb.predict(c, u, homes, 2025, division, p25) * bb.HORIZON
        wis.append(dict(candidate=c, param=p25, published_five_year=float(pr.loc[WI].sum()),
                        **{f"published_{z}": float(pr.loc[(WI, z)]) for z in bb.SIZES}))
    W = pd.DataFrame(wis)
    w0 = W.set_index("candidate").loc["L0", "published_five_year"]
    W["ratio_to_l0"] = W["published_five_year"] / w0
    W["v3_scaled_central"] = W["ratio_to_l0"] * V3_CENTRAL
    RG, CV = pd.concat(rng_rows, ignore_index=True), pd.concat(cov_rows, ignore_index=True)
    covs = CV.groupby(["candidate", "lo", "hi"])["inside"].agg(["mean", "size"]).reset_index()

    P = pd.DataFrame([dict(candidate=c, start=t, param=v) for c, d in params.items() for t, v in d.items()])
    R.round(4).to_csv(REFERENCE / "baseline_bakeoff_part1_rows.csv", index=False)
    S.round(4).to_csv(REFERENCE / "baseline_bakeoff_part1_summary.csv", index=False)
    P.to_csv(REFERENCE / "baseline_bakeoff_part1_params.csv", index=False)
    G.round(4).to_csv(REFERENCE / "baseline_bakeoff_part1_by_group.csv", index=False)
    RG.round(4).to_csv(REFERENCE / "baseline_bakeoff_part1_range.csv", index=False)
    CV.round({"low": 1, "high": 1, "actual": 1}).to_csv(REFERENCE / "baseline_bakeoff_part1_coverage.csv", index=False)
    covs.round(4).to_csv(REFERENCE / "baseline_bakeoff_part1_coverage_summary.csv", index=False)
    W.round(1).to_csv(REFERENCE / "baseline_bakeoff_part1_wisconsin.csv", index=False)
    final_ranges(u, homes, division, W).round(1).to_csv(REFERENCE / "baseline_bakeoff_part1_final_ranges.csv", index=False)
    print(S.round(4).to_string(index=False))
    print("winner:", winner)
    print(W.round(1).to_string(index=False))
    print(covs.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
