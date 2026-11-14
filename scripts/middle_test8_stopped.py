"""Middle housing Test 8: places with "stopped" middle housing (docs/middle/TEST8_PLAN_LOCKED.md). Post hoc.

Do law-state places with many pre-1980 2-4 unit homes and almost none since gain more (or fewer) 2-4 unit homes after
the law than places with none, each against Test 1's comparison places? Inference by 10,000 sets of 4 fake law states.

Inputs: Test 1's permit data and functions (scripts/middle_test1_states.py); data/raw/middle_tracts/ (fetch scripts
fetch_middle_tracts.py and fetch_middle_towns.py). Outputs: reference/middle_test8_*.csv.
Run: uv run python scripts/middle_test8_stopped.py
"""
from __future__ import annotations

import io
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import middle_power_check as pc  # noqa: E402
import middle_test1_states as m  # noqa: E402

RAW = ROOT / "data" / "raw" / "middle_tracts"
OUT = ROOT / "reference"
SEED, SETS = 20261113, 10_000
MIN_GROUP = 10                        # convention: at least 10 high and 10 low places per state
COLS = m.MEASURES["M2"]
# B25127 2-4 unit columns by band (owner, renter); labels checked against B25127_labels.json in check_labels()
OLD = ["026", "033", "040", "069", "076", "083"]          # built 1960-79, 1940-59, 1939 or earlier
NEW = ["012", "019", "055", "062"]                          # built 2000-19, 1980-99
PRE2000 = ["019", "026", "033", "040", "062", "069", "076", "083"]
BUILT_2020 = ["003", "046"]                                 # all homes built 2020 or later (owner, renter)


def check_labels() -> None:
    lab = json.loads((RAW / "B25127_labels.json").read_text())["variables"]
    for c in OLD + NEW + PRE2000:
        assert "2 to 4" in lab[f"B25127_{c}E"]["label"], c
    for c in OLD:
        assert any(b in lab[f"B25127_{c}E"]["label"] for b in ("1960 to 1979", "1940 to 1959", "1939 or earlier")), c
    for c in NEW:
        assert any(b in lab[f"B25127_{c}E"]["label"] for b in ("2000 to 2019", "1980 to 1999")), c
    for c in BUILT_2020:
        assert lab[f"B25127_{c}E"]["label"].endswith("Built 2020 or later:"), c


def tracts() -> pd.DataFrame:
    a = pd.read_csv(RAW / "acsdt5y2024-b25127.dat", sep="|", dtype=str)
    a = a[a["GEO_ID"].str.startswith("1400000US")].copy()
    a["tract"] = a["GEO_ID"].str[-11:]
    num = lambda cs: sum(pd.to_numeric(a[f"B25127_E{c}"], errors="coerce").fillna(0) for c in cs)  # noqa: E731
    out = pd.DataFrame({"tract": a["tract"], "old24": num(OLD), "new24": num(NEW), "pre2000_24": num(PRE2000),
                        "denom": pd.to_numeric(a["B25127_E001"], errors="coerce").fillna(0) - num(BUILT_2020)})
    return out.set_index("tract")


def stopped(t: pd.DataFrame, old_t: float = 0.10, new_t: float = 0.10) -> pd.Series:
    return (t["denom"] > 0) & (t["old24"] >= old_t * t["denom"]) & (t["old24"] > 0) & (t["new24"] <= new_t * t["old24"])


def links() -> pd.DataFrame:
    """Housing units (2020) by permit-unit key (Test 1's acs_geoid) and 2020 tract."""
    hu = []
    for f in sorted((RAW / "pl_blocks").glob("*.json")):
        rows = json.loads(f.read_text())[1:]
        hu.append(pd.DataFrame({"block": [r[1] + r[2] + r[3] + r[4] for r in rows], "hu": [int(r[0]) for r in rows]}))
    hu = pd.concat(hu).set_index("block")["hu"]
    parts = []
    for z in sorted(RAW.glob("BlockAssign_ST*.zip")):
        with zipfile.ZipFile(z) as zf:
            name = next(n for n in zf.namelist() if n.endswith("INCPLACE_CDP.txt"))
            b = pd.read_csv(io.BytesIO(zf.read(name)), sep="|", dtype=str).dropna()
        b["hu"] = b["BLOCKID"].map(hu).fillna(0)
        b["key"] = "160|" + b["BLOCKID"].str[:2] + b["PLACEFP"].str.zfill(5)
        b["tract"] = b["BLOCKID"].str[:11]
        parts.append(b.groupby(["key", "tract"], as_index=False)["hu"].sum())
    for f in sorted((RAW / "towns").glob("*.json")):
        rows = json.loads(f.read_text())
        if not rows:
            continue
        s, c, cs = f.stem[:2], f.stem[2:5], f.stem[5:]
        t = pd.DataFrame(rows)
        t["tract"] = s + c + t["tract"]
        t["key"] = "060|" + s + c + cs
        parts.append(t.groupby(["key", "tract"], as_index=False)["hu"].sum())
    return pd.concat(parts, ignore_index=True)


def scores(lk: pd.DataFrame, st_flag: pd.Series) -> pd.Series:
    lk = lk.assign(stop=lk["tract"].map(st_flag).fillna(False).astype(bool))
    g = lk.groupby("key")
    return (g.apply(lambda x: x.loc[x["stop"], "hu"].sum()) / g["hu"].sum()).fillna(0)


def split(units: pd.DataFrame, info: pd.DataFrame, score: pd.Series):
    s = info.loc[units.index, "acs_geoid"].map(score)
    pos = s[s > 0]
    if s.isna().all() or len(pos) == 0:
        return None, None
    med = pos.median()
    hi, lo = units[(s >= med) & (s > 0)], units[s == 0]
    return hi, lo


def contrast(tr, cm, info, score):
    hi, lo = split(tr, info, score)
    if hi is None or len(hi) < MIN_GROUP or len(lo) < MIN_GROUP:
        return None
    rh, rl = m.state_stat(hi, cm, info), m.state_stat(lo, cm, info)
    if not rh or not rl or not np.isfinite(rh["log_ratio"]) or not np.isfinite(rl["log_ratio"]):
        return None
    return dict(log=rh["log_ratio"] - rl["log_ratio"], diff=rh["diff"] - rl["diff"], n_high=len(hi), n_low=len(lo),
                unmatched_high=rh["unmatched_share"], unmatched_low=rl["unmatched_share"])


def run_windows(d, homes, info, pool_ok, score, windows_by_state, label):
    """Real contrasts per law state and fake contrasts per (windows_of, fake state)."""
    real, fake, fails = {}, [], []
    fake_states = sorted(info.loc[pool_ok, "state_fips"].unique())
    for st in m.TREATED:
        pw = m.place_windows(d, homes, windows_by_state[st], COLS, True)
        pw = pw[pw.index.isin(info.index)]
        tr = pw[(info.loc[pw.index, "state_fips"] == st).to_numpy()]
        region = info.loc[tr.index, "region"].mode().iat[0]
        ok = pool_ok.reindex(pw.index).fillna(False).to_numpy()
        cm = pw[ok & (info.loc[pw.index, "region"] == region).to_numpy()]
        real[st] = contrast(tr, cm, info, score)
        for fs in fake_states:
            ftr = pw[(info.loc[pw.index, "state_fips"] == fs).to_numpy() & ok]
            if len(ftr) < 3:
                continue
            freg = info.loc[ftr.index, "region"].mode().iat[0]
            fcm = pw[ok & (info.loc[pw.index, "region"] == freg).to_numpy() & (info.loc[pw.index, "state_fips"] != fs).to_numpy()]
            r = contrast(ftr, fcm, info, score)
            fails.append(dict(windows=label, windows_of=m.TREATED[st], fake_state=fs, passed=r is not None))
            if r:
                fake.append(dict(windows_of=m.TREATED[st], fake_state=fs, **r))
    return real, pd.DataFrame(fake), pd.DataFrame(fails)


def fake_sets(fk: pd.DataFrame, slots: list[str], rng) -> tuple[np.ndarray, np.ndarray]:
    logs, diffs = [], []
    for _ in range(SETS):
        used, lv, dv = set(), [], []
        for s in slots:
            cand = fk[(fk["windows_of"] == s) & ~fk["fake_state"].isin(used)]
            p = cand.iloc[int(rng.integers(len(cand)))]
            used.add(p["fake_state"]); lv.append(p["log"]); dv.append(p["diff"])
        logs.append(np.mean(lv)); diffs.append(np.mean(dv))
    return np.array(logs), np.array(diffs)


def summarize(name, real, fk, rng):
    slots = [m.TREATED[s] for s, r in real.items() if r is not None]
    dropped = [m.TREATED[s] for s, r in real.items() if r is None]
    if not slots:
        return dict(version=name, note="no law state passes the size rule", dropped=", ".join(dropped))
    rl = np.mean([real[s]["log"] for s in real if real[s]])
    rd = np.mean([real[s]["diff"] for s in real if real[s]])
    fl, fd = fake_sets(fk, slots, rng)
    q05, q50, q95 = np.quantile(fl, [0.05, 0.5, 0.95])
    d05, d50, d95 = np.quantile(fd, [0.05, 0.5, 0.95])
    reading = ("stopped places gained more" if rl > q95 else "stopped places gained fewer" if rl < q05
               else "we do not know (range includes 0)")
    return dict(version=name, states=", ".join(slots), dropped=", ".join(dropped), real_log=rl, fake_log_q05=q05,
                fake_log_median=q50, fake_log_q95=q95, point_log=rl - q50, range_log_low=rl - q95, range_log_high=rl - q05,
                pct_point=100 * (np.exp(rl - q50) - 1), pct_low=100 * (np.exp(rl - q95) - 1), pct_high=100 * (np.exp(rl - q05) - 1),
                real_diff=rd, fake_diff_median=d50, point_diff=rd - d50, range_diff_low=rd - d95, range_diff_high=rd - d05,
                percentile=float((fl < rl).mean() * 100), reading=reading, fake_log_sd=float(fl.std()),
                detectable_log=2.486 * float(fl.std()))


def survival(t: pd.DataFrame) -> pd.DataFrame:
    """Occupied 2-4 unit homes in 2000 (SF3 H032) on 2020 tracts vs ACS 2-4 homes built before 2000."""
    rows = []
    for f in sorted(RAW.glob("sf3_2000_h032_*.json")):
        r = json.loads(f.read_text())
        h = pd.DataFrame(r[1:], columns=r[0])
        h["t00"] = h["state"] + h["county"] + h["tract"].where(h["tract"].str.len() == 6, h["tract"].str.ljust(6, "0"))
        h["v"] = sum(pd.to_numeric(h[c], errors="coerce").fillna(0) for c in ("H032005", "H032006", "H032016", "H032017"))
        rows.append(h[["t00", "v"]])
    h = pd.concat(rows)
    trf = pd.read_csv(RAW / "us2010trf.txt", header=None, dtype=str)
    trf = pd.DataFrame({"t00": trf[3], "t10": trf[12], "w": pd.to_numeric(trf[28], errors="coerce").fillna(0) / 100})
    x = h.merge(trf, on="t00")
    x = (x.assign(v=x["v"] * x["w"]).groupby("t10")["v"].sum())
    r20 = pd.read_csv(RAW / "tab20_tract20_tract10_natl.txt", sep="|", dtype=str, encoding="utf-8-sig")
    r20["w"] = pd.to_numeric(r20["AREALAND_PART"], errors="coerce") / pd.to_numeric(r20["AREALAND_TRACT_10"], errors="coerce")
    r20 = r20[r20["w"].notna()]
    y = r20.assign(v=r20["GEOID_TRACT_10"].map(x).fillna(0) * r20["w"]).groupby("GEOID_TRACT_20")["v"].sum()
    s = pd.DataFrame({"y2000": y}).join(t[["pre2000_24"]], how="inner")
    s["state"] = s.index.str[:2]
    s = s[s["state"].isin(set(f.stem[-2:] for f in RAW.glob("sf3_2000_h032_*.json")))]
    g = s.groupby("state")[["y2000", "pre2000_24"]].sum()
    g["loss_share"] = 1 - g["pre2000_24"] / g["y2000"]
    big = s[s["y2000"] >= 20]
    g["tracts_loss_over_half"] = (big["pre2000_24"] < 0.5 * big["y2000"]).groupby(big["state"]).sum()
    g["tracts_checked"] = big.groupby("state").size()
    return g.reset_index()


def main() -> None:
    check_labels()
    t = tracts()
    lk = links()
    d = m.load_all(2025)
    homes = pc.sf_homes()
    info = d.sort_values("year").groupby("key").last()[["state_fips", "region", "name", "pop", "acs_geoid", "county5"]]
    info["pop"] = pd.to_numeric(info["pop"], errors="coerce")
    info = info[info["pop"].gt(0)]
    info["screened_place"] = m.screened_flags(info)
    pool_ok = (~info["state_fips"].isin(m.LAW_STATES_ALL | set(pc.SCREENED_STATES)) & ~info["screened_place"]
               & ~info["county5"].isin(m.border_counties()))
    linked = info["acs_geoid"].isin(set(lk["key"]))
    print(f"permit units linked to tracts: {int(linked.sum())} of {len(info)}", flush=True)

    rows, fails_all = [], []
    variants = {"main (10% / 10%)": (0.10, 0.10), "old 5%": (0.05, 0.10), "old 20%": (0.20, 0.10),
                "new 5%": (0.10, 0.05), "new 20%": (0.10, 0.20)}
    ts, ps = [], []
    for name, (o, n) in variants.items():
        flag = stopped(t, o, n)
        score = scores(lk, flag)
        if name.startswith("main"):
            ts = t.assign(stopped=flag)
            ps = score.rename("score")
            # power first: fake windows (2012-14 vs 2016-18), fakes only
            _, fkp, flp = run_windows(d, homes, info, pool_ok, score, m.FAKE_WINDOWS, "fake years")
            rng = np.random.default_rng(SEED)
            slots = list(m.TREATED.values())
            fl, _ = fake_sets(fkp, slots, rng)
            rows.append(dict(version="power: fake windows, fakes only", fake_log_sd=float(fl.std()),
                             detectable_log=2.486 * float(fl.std())))
            print(f"power: detectable log contrast = {2.486 * fl.std():.3f}", flush=True)
            # pre-trend: law states on the fake windows
            realp, _, _ = run_windows(d, homes, info, pool_ok, score, m.FAKE_WINDOWS, "fake years")
            rows.append(summarize("pre-trend: law states on fake years", realp, fkp, np.random.default_rng(SEED)))
            fails_all.append(flp)
        real, fk, fl_ = run_windows(d, homes, info, pool_ok, score, m.REAL_WINDOWS, "real")
        r = summarize(name, real, fk, np.random.default_rng(SEED))
        r["fake_state_fail_share"] = float(1 - fl_["passed"].mean()) if len(fl_) else np.nan
        for s, v in real.items():
            if v:
                r[f"{m.TREATED[s]}_log"] = v["log"]; r[f"{m.TREATED[s]}_high_low"] = f"{v['n_high']}/{v['n_low']}"
                r[f"{m.TREATED[s]}_unmatched_high_low"] = f"{v['unmatched_high']:.0%}/{v['unmatched_low']:.0%}"
        rows.append(r)
        fails_all.append(fl_)
        pd.DataFrame(rows).to_csv(OUT / "middle_test8_summary.csv", index=False)  # saved as it goes
        print(name, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items() if k in ("real_log", "point_log", "range_log_low", "range_log_high", "reading", "dropped")}, flush=True)
    # size check: contrast within population terciles (main thresholds), real and fakes
    score = ps
    tert = info.groupby("state_fips")["pop"].transform(lambda x: np.minimum((x.rank(method="first", pct=True) * 3).apply(np.ceil) - 1, 2))
    sz = []
    for k in range(3):
        sub_info_ok = tert == k
        sc = score.copy()
        keep = set(info.loc[sub_info_ok, "acs_geoid"])
        sc = sc[sc.index.isin(keep)]
        real, fk, _ = run_windows(d, homes, info, pool_ok, sc, m.REAL_WINDOWS, f"size {k}")
        sz.append(summarize(f"size tercile {k + 1}", real, fk, np.random.default_rng(SEED)))
    rows += sz
    pd.DataFrame(rows).to_csv(OUT / "middle_test8_summary.csv", index=False)
    pd.concat(fails_all).to_csv(OUT / "middle_test8_fake_state_rule.csv", index=False)
    ts.reset_index().assign(state=lambda x: x["tract"].str[:2]).to_csv(OUT / "middle_test8_tract_scores.csv", index=False)
    info.assign(score=info["acs_geoid"].map(ps)).reset_index()[["key", "state_fips", "name", "acs_geoid", "pop", "score"]] \
        .to_csv(OUT / "middle_test8_place_scores.csv", index=False)
    survival(t).to_csv(OUT / "middle_test8_survival.csv", index=False)
    print(pd.read_csv(OUT / "middle_test8_survival.csv").round(3).to_string(index=False))


if __name__ == "__main__":
    main()
