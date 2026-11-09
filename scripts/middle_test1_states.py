"""Middle housing Test 1 (primary) and its Test 4 fake-year version. Locked plan:
docs/middle/TEST_PLAN_LOCKED.md (commit 8767525c). Committed before any run.

Treated states: Oregon, California, Maine, Vermont. Comparison places: Census permit-issuing places in the same Census
region, in states that pass the comparison screen (no state law of the screened kinds first binding 2015-2025), never a
candidate city or screened place, never in a county bordering Oregon or California. Each treated place is matched to
comparison places at 1/2-2x its population; unmatched treated places are left out (their share of single-family homes
is reported) and, as a sensitivity, matched from the screened national pool.

Rates: homes permitted per 1,000 single-family homes per year. Single-family homes = ACS 2020-2024 B25024 rows 2+3,
moved to each year by the place's one-unit permits (as in homes_by_year.py), anchored at 2022.
Statistic per state: log(treated after / treated before) - log(comparison after / comparison before), pooled rates,
comparison side = treated places' matched comparison rates weighted by treated places' single-family homes.
Second unit: the same difference in rates (per 1,000 per year).
Set statistic: unweighted mean over the treated states.
Main inference: rank among 10,000 sets of fake law states (each untested, screened state run through the same
statistic with one real state's windows, its own region's pool), seed 20261103. Reading: above the fake sets'
95th percentile = a rise relative to comparison places; below the 5th = a fall; otherwise = we do not know.
The 90% range is [real - fake 95th, real - fake 5th].
Data columns: reported only, places reporting 12 months in every window year (main); Census filled-in (sensitivity).

Usage: python scripts/middle_test1_states.py [real|fake]   (fake = Test 4 windows 2012-2014 vs 2016-2018)
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from missing_middleware.foundation import parsers  # noqa: E402
import middle_power_check as pc  # noqa: E402  (screen lists and place filters)

RAW, OUT = ROOT / "data" / "raw", ROOT / "reference"
SEED, SETS, BOOT = 20261103, 10_000, 2_000
TREATED = {"41": "Oregon", "06": "California", "23": "Maine", "50": "Vermont"}
REAL_WINDOWS = {"41": ((2015, 2016, 2017, 2018, 2019), (2023, 2024, 2025)),
                "06": ((2018, 2019, 2020, 2021), (2023, 2024, 2025)),
                "23": ((2019, 2020, 2021, 2022, 2023), (2024, 2025)),
                "50": ((2019, 2020, 2021, 2022), (2024, 2025))}
FAKE_WINDOWS = {k: ((2012, 2013, 2014), (2016, 2017, 2018)) for k in TREATED}
OR_SENS_WINDOWS = ((2015, 2016, 2017, 2018), (2023, 2024, 2025))
MEASURES = {"M2": ["2units", "3_4units"], "M1": ["1unit", "2units", "3_4units"],
            "M3": ["1unit", "2units", "3_4units", "5plus"], "M4": ["5plus"], "one_unit": ["1unit"]}
LAW_STATES_ALL = {"06", "41", "53", "23", "50", "30", "04"}


def load_all(last_year: int) -> pd.DataFrame:
    frames = []
    for f in sorted((RAW / "census_bps_place_us").glob("*a.txt")):
        y = int(f.name[2:6])
        if y > last_year:
            continue
        d = parsers.read_bps(f, "place", state_fips=None)
        d["year"] = y
        frames.append(d)
    d = pd.concat(frames, ignore_index=True)
    for c in ("state_fips", "bps_id", "county_fips", "fips_place", "fips_mcd", "name", "region"):
        d[c] = d[c].astype(str).str.strip()
    keep_names = {"Mecklenburg County", "Arlington County"}
    d = d[(d["fips_place"] != "99990") & (~d["name"].str.contains("County|Balance") | d["name"].isin(keep_names))]
    d["key"] = d["state_fips"] + "|" + d["bps_id"]
    d["acs_geoid"] = np.where(d["fips_place"].str.strip("0") != "",
                              "160|" + d["state_fips"] + d["fips_place"].str.zfill(5),
                              "060|" + d["state_fips"] + d["county_fips"].str.zfill(3) + d["fips_mcd"].str.zfill(5))
    d["county5"] = d["state_fips"] + d["county_fips"].str.zfill(3)
    return d


def border_counties() -> set[str]:
    adj = set()
    with open(RAW / "census_county_adjacency" / "county_adjacency2023.txt") as f:
        for r in csv.DictReader(f, delimiter="|"):
            a, b = r["County GEOID"], r["Neighbor GEOID"]
            if a[:2] in ("41", "06") and b[:2] not in ("41", "06"):
                adj.add(b)
    return adj


def screened_flags(info: pd.DataFrame) -> pd.Series:
    nm = info["name"].str.replace(r" (city|town|village|borough|township|municipality)$", "", regex=True)
    cand = {s + "|" + n for s, n in pc.CANDIDATE_CITIES} | {s + "|" + n for s, n in pc.SCREENED_PLACES}
    return (info["state_fips"] + "|" + info["name"]).isin(cand) | (info["state_fips"] + "|" + nm).isin(cand)


def place_windows(d: pd.DataFrame, homes_acs: pd.Series, windows: tuple, cols: list[str], reported_only: bool,
                  keys: pd.Index | None = None) -> pd.DataFrame:
    """Per place: permits and single-family homes summed over the before and after windows."""
    before, after = windows
    yrs = sorted(set(before) | set(after))
    suf = "_units_rep" if reported_only else "_units"
    w = d if keys is None else d[d["key"].isin(keys)]
    span = range(min(yrs), max(max(yrs), 2022) + 1)
    w = w[w["year"].isin(span)]
    g = w.pivot_table(index="key", columns="year", values=[c + suf for c in cols] + ["1unit" + suf, "months_reported"],
                      aggfunc="first")
    out = pd.DataFrame(index=g.index)
    have = g["months_reported"].reindex(columns=yrs).notna().all(axis=1)
    if reported_only:
        have &= (g["months_reported"].reindex(columns=yrs) == 12).all(axis=1)
    one = g["1unit" + suf].reindex(columns=list(span)).fillna(0)
    meta = w.sort_values("year").groupby("key").last()
    h22 = meta["acs_geoid"].map(homes_acs)
    homes = {}
    for y in yrs:
        if y <= 2022:
            homes[y] = h22 - one[[t for t in span if y < t <= 2022]].sum(axis=1)
        else:
            homes[y] = h22 + one[[t for t in span if 2023 <= t <= y]].sum(axis=1)
    perm = sum(g[c + suf].reindex(columns=yrs).fillna(0) for c in cols)
    out["p_b"] = perm[list(before)].sum(axis=1)
    out["p_a"] = perm[list(after)].sum(axis=1)
    out["h_b"] = sum(homes[y] for y in before)
    out["h_a"] = sum(homes[y] for y in after)
    out["ok"] = have & (h22 >= 100) & out["h_b"].gt(0)
    return out[out["ok"]]


def state_stat(tr: pd.DataFrame, cmp_: pd.DataFrame, info: pd.DataFrame, national: pd.DataFrame | None = None):
    """Log rate ratio and rate difference for one treated (or fake) state."""
    cp = info.loc[cmp_.index, "pop"].to_numpy()
    cpb, cpa, chb, cha = (cmp_[c].to_numpy() for c in ("p_b", "p_a", "h_b", "h_a"))
    if national is not None:
        np_ = info.loc[national.index, "pop"].to_numpy()
        npb, npa, nhb, nha = (national[c].to_numpy() for c in ("p_b", "p_a", "h_b", "h_a"))
    wsum = cb = ca = 0.0
    unmatched_h = 0.0
    for key, row in tr.iterrows():
        p = info.at[key, "pop"]
        k = (cp >= p / 2) & (cp <= p * 2)
        src = (cpb, cpa, chb, cha)
        if not k.any() and national is not None:
            k = (np_ >= p / 2) & (np_ <= p * 2)
            src = (npb, npa, nhb, nha)
        if not k.any() or src[2][k].sum() == 0:
            unmatched_h += row["h_b"]
            continue
        wt = row["h_b"]
        cb += wt * src[0][k].sum() / src[2][k].sum()
        ca += wt * src[1][k].sum() / src[3][k].sum()
        wsum += wt
    tb, ta = 1000 * tr["p_b"].sum() / tr["h_b"].sum(), 1000 * tr["p_a"].sum() / tr["h_a"].sum()
    if wsum == 0:
        return None
    cb, ca = 1000 * cb / wsum, 1000 * ca / wsum
    logr = np.log(ta / tb) - np.log(ca / cb) if min(ta, tb, ca, cb) > 0 else np.nan
    return dict(treated_before=tb, treated_after=ta, comp_before=cb, comp_after=ca, log_ratio=logr,
                diff=(ta - tb) - (ca - cb), unmatched_share=unmatched_h / tr["h_b"].sum(), places=len(tr))


def run(mode: str) -> None:
    last = 2025 if mode == "real" else 2018
    d = load_all(last)
    homes_acs = pc.sf_homes()
    info = d.sort_values("year").groupby("key").last()[["state_fips", "region", "name", "pop", "acs_geoid", "county5"]]
    info["pop"] = pd.to_numeric(info["pop"], errors="coerce")
    info = info[info["pop"].gt(0)]
    info["screened_place"] = screened_flags(info)
    border = border_counties()
    pool_ok = (~info["state_fips"].isin(LAW_STATES_ALL | set(pc.SCREENED_STATES)) & ~info["screened_place"]
               & ~info["county5"].isin(border))
    fake_states = sorted(info.loc[pool_ok, "state_fips"].unique())
    windows_by_state = REAL_WINDOWS if mode == "real" else FAKE_WINDOWS
    rows, fake_rows = [], []
    boot_inputs = {}
    for reported_only in (True, False):
        data = "reported only (main)" if reported_only else "Census filled-in (sensitivity)"
        for mname, cols in MEASURES.items():
            per_state = {}
            for st in TREATED:
                win = windows_by_state[st]
                pw = place_windows(d, homes_acs, win, cols, reported_only)
                pw = pw[pw.index.isin(info.index)]
                tr = pw[(info.loc[pw.index, "state_fips"] == st).to_numpy()]  # every place in the law state
                region = info.loc[tr.index, "region"].mode().iat[0] if len(tr) else None
                cm = pw[pool_ok.reindex(pw.index).fillna(False).to_numpy() & (info.loc[pw.index, "region"] == region).to_numpy()]
                nat = pw[pool_ok.reindex(pw.index).fillna(False).to_numpy()]
                r = state_stat(tr, cm, info)
                rn = state_stat(tr, cm, info, national=nat)
                per_state[st] = r
                rows.append(dict(mode=mode, data=data, measure=mname, state=TREATED[st], version="main", **(r or {})))
                if rn:
                    rows.append(dict(mode=mode, data=data, measure=mname, state=TREATED[st],
                                     version="unmatched matched nationally", **rn))
                # fake states with this state's windows
                for fs in fake_states:
                    ftr = pw[(info.loc[pw.index, "state_fips"] == fs).to_numpy() & pool_ok.reindex(pw.index).fillna(False).to_numpy()]
                    if len(ftr) < 3:
                        continue
                    freg = info.loc[ftr.index, "region"].mode().iat[0]
                    fcm = pw[pool_ok.reindex(pw.index).fillna(False).to_numpy()
                             & (info.loc[pw.index, "region"] == freg).to_numpy()
                             & (info.loc[pw.index, "state_fips"] != fs).to_numpy()]
                    fr = state_stat(ftr, fcm, info)
                    if fr and np.isfinite(fr["log_ratio"]):
                        fake_rows.append(dict(mode=mode, data=data, measure=mname, windows_of=TREATED[st],
                                              fake_state=fs, **fr))
                if mode == "real" and st == "06" and mname == "M1":
                    adj = tr.copy()
                    ab, aa = apr_adus(info, adj.index, win)
                    adj["p_b"] = (adj["p_b"] - ab.reindex(adj.index).fillna(0)).clip(lower=0)
                    adj["p_a"] = (adj["p_a"] - aa.reindex(adj.index).fillna(0)).clip(lower=0)
                    r3 = state_stat(adj, cm, info)
                    if r3:
                        rows.append(dict(mode=mode, data=data, measure=mname, state="California",
                                         version="California without progress-report ADUs (bound)", **r3))
                if len(tr) and len(cm) and reported_only and mname in ("M2", "M1", "M3"):
                    boot_inputs[(data, mname, st)] = (tr, cm)  # bootstrap: main data, three lead measures
                if mode == "real" and st == "41":
                    pw2 = place_windows(d, homes_acs, OR_SENS_WINDOWS, cols, reported_only)
                    pw2 = pw2[pw2.index.isin(info.index)]
                    tr2 = pw2[(info.loc[pw2.index, "state_fips"] == "41").to_numpy()]
                    cm2 = pw2[pool_ok.reindex(pw2.index).fillna(False).to_numpy() & (info.loc[pw2.index, "region"] == region).to_numpy()]
                    r2 = state_stat(tr2, cm2, info)
                    if r2:
                        rows.append(dict(mode=mode, data=data, measure=mname, state="Oregon",
                                         version="Oregon before 2015-2018", **r2))
    res = pd.DataFrame(rows)
    fk = pd.DataFrame(fake_rows)
    tag = "" if mode == "real" else "_fakeyears"
    res.to_csv(OUT / f"middle_test1_states{tag}.csv", index=False)
    fk.to_csv(OUT / f"middle_test1_fakestates{tag}.csv", index=False)
    summarize(res, fk, tag)
    bootstrap(boot_inputs, info, tag)


def apr_adus(info: pd.DataFrame, keys, windows) -> tuple[pd.Series, pd.Series]:
    """California progress-report ADU permits (Table A2, UNIT_CAT ADU, NO_BUILDING_PERMITS) summed over each window,
    matched to Census places by name (upper case, without ' city'/' town')."""
    before, after = windows
    tot = {}
    with open(RAW / "hcd_apr_a2" / "tablea2.csv", encoding="utf-8-sig", errors="replace") as f:
        for r in csv.DictReader(f):
            if r["UNIT_CAT"] != "ADU":
                continue
            try:
                y, u = int(r["YEAR"]), float(r["NO_BUILDING_PERMITS"] or 0)
            except ValueError:
                continue
            tot[(r["JURIS_NAME"].strip().upper(), y)] = tot.get((r["JURIS_NAME"].strip().upper(), y), 0) + u
    nm = info.loc[list(keys), "name"].str.replace(r" (city|town)$", "", regex=True).str.upper()
    b = pd.Series({k: sum(tot.get((n, y), 0) for y in before) for k, n in nm.items()})
    a = pd.Series({k: sum(tot.get((n, y), 0) for y in after) for k, n in nm.items()})
    print(f"APR ADU match: {int((b + a > 0).sum())} of {len(nm)} California places")
    return b, a


def bootstrap(inputs: dict, info: pd.DataFrame, tag: str) -> None:
    """Second inference: resample treated places within each state and comparison places within each pool,
    1,000 draws, seed 20261103; four-state mean of the rate difference and log ratio."""
    rng = np.random.default_rng(SEED)
    out = []
    keys = sorted({(dt, m) for dt, m, _ in inputs})
    for dt, m in keys:
        sts = [s for s in TREATED if (dt, m, s) in inputs]
        if len(sts) < 4:
            continue
        logs, diffs = [], []
        for _ in range(1000):
            lv, dv = [], []
            for s in sts:
                tr, cm = inputs[(dt, m, s)]
                trb = tr.iloc[rng.integers(0, len(tr), len(tr))]
                trb = trb[~trb.index.duplicated()] if False else trb
                cmb = cm.iloc[rng.integers(0, len(cm), len(cm))]
                cmb = cmb.groupby(level=0).sum()
                trb = trb.groupby(level=0).sum()
                r = state_stat(trb, cmb, info)
                if r is None or not np.isfinite(r["log_ratio"]):
                    break
                lv.append(r["log_ratio"]); dv.append(r["diff"])
            if len(lv) == len(sts):
                logs.append(np.mean(lv)); diffs.append(np.mean(dv))
        out.append(dict(data=dt, measure=m, draws=len(logs), log_q05=np.quantile(logs, 0.05), log_q95=np.quantile(logs, 0.95),
                        diff_q05=np.quantile(diffs, 0.05), diff_q95=np.quantile(diffs, 0.95)))
    pd.DataFrame(out).to_csv(OUT / f"middle_test1_bootstrap{tag}.csv", index=False)
    print(pd.DataFrame(out).round(3).to_string(index=False))


def summarize(res: pd.DataFrame, fk: pd.DataFrame, tag: str) -> None:
    rng = np.random.default_rng(SEED)
    out = []
    for (data, m), g in res[res["version"] == "main"].groupby(["data", "measure"]):
        for label, states in (("four states", ["Oregon", "California", "Maine", "Vermont"]),
                              ("Oregon + California", ["Oregon", "California"])):
            gg = g.set_index("state").reindex(states)
            if gg["log_ratio"].isna().any():
                out.append(dict(data=data, measure=m, set=label, note="a state has no finite statistic"))
                continue
            real_log, real_diff = gg["log_ratio"].mean(), gg["diff"].mean()
            f = fk[(fk["data"] == data) & (fk["measure"] == m)]
            sets_log, sets_diff = [], []
            for _ in range(SETS):
                picks, used = [], set()
                for s in states:
                    cand = f[(f["windows_of"] == s) & ~f["fake_state"].isin(used)]
                    pick = cand.iloc[int(rng.integers(len(cand)))]
                    used.add(pick["fake_state"])
                    picks.append(pick)
                sets_log.append(np.mean([p["log_ratio"] for p in picks]))
                sets_diff.append(np.mean([p["diff"] for p in picks]))
            q05, q95 = np.quantile(sets_log, [0.05, 0.95])
            d05, d95 = np.quantile(sets_diff, [0.05, 0.95])
            reading = ("rise relative to comparison places" if real_log > q95 else
                       "fall relative to comparison places" if real_log < q05 else "we do not know (range includes 0)")
            loo = [gg.drop(s)["diff"].mean() for s in states] if len(states) > 2 else []
            out.append(dict(data=data, measure=m, set=label, real_log=real_log, fake_q05=q05, fake_q95=q95,
                            range_log_low=real_log - q95, range_log_high=real_log - q05,
                            pct_low=100 * (np.exp(real_log - q95) - 1), pct_high=100 * (np.exp(real_log - q05) - 1),
                            real_diff_per_1000=real_diff, range_diff_low=real_diff - d95, range_diff_high=real_diff - d05,
                            percentile=float((np.array(sets_log) < real_log).mean() * 100), reading=reading,
                            leave_one_out_diff=", ".join(f"{x:.2f}" for x in loo),
                            comparison_change_per_1000=float((gg["comp_after"] - gg["comp_before"]).mean()),
                            treated_change_per_1000=float((gg["treated_after"] - gg["treated_before"]).mean()),
                            unmatched_share_by_state=", ".join(f"{s}: {u:.0%}" for s, u in gg["unmatched_share"].items())))
    s = pd.DataFrame(out)
    s.to_csv(OUT / f"middle_test1_summary{tag}.csv", index=False)
    pd.set_option("display.width", 260)
    print(s.round(3).to_string(index=False))


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "real")
