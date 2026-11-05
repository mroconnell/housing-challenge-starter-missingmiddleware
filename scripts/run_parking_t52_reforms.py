"""Test 52b reruns (docs/parking/CAUSAL_FRAMEWORK_PLAN.md, "Test 52", 52b with audit fixes 1, 2, 7, 13): other housing
reforms as dated events, on the main estimate and on method D. Uses the committed events table
reference/parking_t52_b_events.csv (scripts/run_parking_t52_events.py, commit c1eedd17, before any join).

    uv run --all-extras python scripts/run_parking_t52_reforms.py all <variant>     # prep + main pipeline + method D
    uv run --all-extras python scripts/run_parking_t52_reforms.py summary          # reading table (all variants run)

Variants (E = the repeal place's event year; for a pool place, the matched repeal's year):
  base          no change (same working copy and code; the paired shifts are read against it, and it is checked against
                the committed batch)
  pool          52b.1: a pool place is left out of a repeal place's pool if it has a counted place-level event in E-3..E-1
  repeal        52b.2: repeal places with a separate counted reform in E-3..E-1 are dropped
  state         52b.3: out-of-state pool places (division / nation steps of the ladder) are left out if their state has a
                coded state law in E-3..E-1
  pool_after    sensitivity (fix 1): as pool, events in E..E+3 (may be caused by the repeal; post-treatment)
  repeal_after  sensitivity (fix 1): as repeal, separate reforms in E..E+3
  (52b.4, the indicator version, keeps every place and is computed from base in `summary`.)
"Counted" events: place-scope rows of the events table with counted = True and a BPS key; prior parking dose rows (PRN and
coded partial parking cuts, repeal places only) never count, and PRN reforms of pool places are not in the table (52h).
Each variant runs on its own working copy, data/processed/t52/b_<variant>_ref (reference/ without batch_2026-11-05/, the
batch outputs laid over it); the existing scripts are run unchanged, with cmp.controls (main) or method 2's select_pool
(D) wrapped to add the variant's exclusions.
Main = salvage -> partial -> expanded -> placebo --full --save-draws (real average, placebo-spread range).
D = method 2 corrected, candidate D, target-state mix (the stage-2 row "method 2, D" / "target-state mix", recomputed here
for D only with the same functions, draws and seed).
"""
from __future__ import annotations

import atexit
import os
import runpy
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
T52 = ROOT / "data" / "processed" / "t52"
EVENTS = ROOT / "reference" / "parking_t52_b_events.csv"
OUT = ROOT / "reference" / "parking_t52_b_results.csv"
OUT_STATE = ROOT / "reference" / "parking_t52_b_by_state.csv"
VARIANTS = ("base", "pool", "repeal", "state", "pool_after", "repeal_after")
WI_K = 2_668_677 * 5 / 1000
SEED, DRAWS = 20261105, 2000
THREADS = dict(VECLIB_MAXIMUM_THREADS="1", OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")


def work(variant: str) -> Path:
    return T52 / f"b_{variant}_ref"


# ---------------------------------------------------------------- events -> exclusions --------------------------------
def load_events():
    e = pd.read_csv(EVENTS, dtype={"bps_key": str, "state_fips": str})
    e = e[e["event_year"].notna()]
    pl = e[(e["scope"] == "place") & e["counted"] & ~e["prior_parking_dose"] & e["bps_key"].notna()]
    place_years = pl.groupby("bps_key")["event_year"].apply(lambda s: sorted(set(int(x) for x in s))).to_dict()
    st = e[e["scope"] == "state"]
    state_years = st.groupby(st["bps_key"].str.split("|").str[0])["event_year"].apply(lambda s: sorted(set(int(x) for x in s))).to_dict()
    return place_years, state_years


def window(variant: str, E: int) -> tuple[int, int]:
    return (E, E + 3) if variant.endswith("_after") else (E - 3, E - 1)


class Excluder:
    def __init__(self, variant: str):
        self.v = variant
        self.place_years, self.state_years = load_events()
        self.cache: dict = {}

    def has(self, years, lo, hi) -> bool:
        return any(lo <= y <= hi for y in years)

    def pool_drop(self, target: str, E: int, cands) -> set:
        """Pool places to leave out for this target and event year."""
        if self.v not in ("pool", "pool_after", "state"):
            return set()
        lo, hi = window(self.v, int(E))
        if self.v == "state":
            st = str(target).split("|")[0]
            bad = {s for s, ys in self.state_years.items() if s != st and self.has(ys, lo, hi)}
            return {k for k in cands if k.split("|")[0] in bad}
        ck = (lo, hi)
        if ck not in self.cache:
            self.cache[ck] = {k for k, ys in self.place_years.items() if self.has(ys, lo, hi)}
        return self.cache[ck] & set(cands)

    def repeal_drop(self, keys_years) -> set:
        if self.v not in ("repeal", "repeal_after"):
            return set()
        out = set()
        for k, E in keys_years:
            lo, hi = window(self.v, int(E))
            if self.has(self.place_years.get(k, []), lo, hi):
                out.add(k)
        return out


# ---------------------------------------------------------------- main pipeline steps ---------------------------------
LOG: list[dict] = []


def patch_controls(X: Excluder, log: bool) -> None:
    from missing_middleware.parking import comparison as cmp
    orig = cmp.controls

    def controls(p, key, event_year, excluded, homes, population=None):
        drop = X.pool_drop(key, event_year, homes.index)
        c, lab = orig(p, key, event_year, set(excluded) | drop, homes, population)
        if log and X.v != "base":
            c0, lab0 = orig(p, key, event_year, excluded, homes, population)
            gone = sorted(set(c0) - set(c))
            LOG.append(dict(key=key, event_year=int(event_year), pool_base=len(c0), pool_variant=len(c), removed=len(gone),
                            added=len(set(c) - set(c0)), window_base=lab0, window_variant=lab,
                            removed_states=";".join(sorted({g.split("|")[0] for g in gone}))))
        return c, lab
    cmp.controls = controls


def step(variant: str, name: str) -> None:
    from missing_middleware.paths import REFERENCE
    assert Path(REFERENCE).resolve() == work(variant).resolve(), (REFERENCE, work(variant))
    X = Excluder(variant)
    patch_controls(X, log=name != "placebo")
    if name != "placebo":
        atexit.register(lambda: pd.DataFrame(LOG).to_csv(REFERENCE / f"parking_t52_b_pool_log_{name}.csv", index=False))
    script = {"salvage": "run_parking_salvage.py", "partial": "run_parking_partial.py", "expanded": "run_parking_expanded.py",
              "placebo": "run_parking_placebo.py"}[name]
    sys.argv = [script] + (["--full", "--save-draws"] if name == "placebo" else [])
    runpy.run_path(str(ROOT / "scripts" / script), run_name="__main__")
    if name == "expanded":  # 52b.2: drop repeal places with a separate reform in the window
        f = REFERENCE / "parking_expanded_effects.csv"
        eff = pd.read_csv(f)
        inc = eff[eff["status"] == "included"]
        drop = X.repeal_drop(set(zip(inc["key"], inc["event_year"])))
        if drop:
            eff.loc[eff["key"].isin(drop) & (eff["status"] == "included"), "status"] = "excluded: t52b separate reform in window"
            eff.to_csv(f, index=False)
        pd.DataFrame({"key": sorted(drop)}).to_csv(REFERENCE / "parking_t52_b_repeal_dropped.csv", index=False)
        print("t52b repeal places dropped:", sorted(drop))


# ---------------------------------------------------------------- method D --------------------------------------------
def method_d(variant: str) -> None:
    import run_parking_method2 as rm2
    from missing_middleware.paths import REFERENCE
    assert Path(REFERENCE).resolve() == work(variant).resolve()
    rm2.SUF, rm2.CORRECTED = "_corrected", True
    X = Excluder(variant)
    orig_sp = rm2.select_pool
    log = []

    def select_pool(D, target, ey, pre, post, cand, opt):
        if "_E" in opt or X.v == "base":
            return orig_sp(D, target, ey, pre, post, cand, opt)
        h = D.homes_pre(ey, opt["homes_fixed"])
        E0 = rm2.eligible(D, target, list(pre) + list(post), opt["exc"], opt["shock"], h)
        drop = X.pool_drop(target, ey, E0)
        s = orig_sp(D, target, ey, pre, post, cand, {**opt, "_E": [k for k in E0 if k not in drop]})
        s0 = orig_sp(D, target, ey, pre, post, cand, {**opt, "_E": E0})
        log.append(dict(key=target, event_year=int(ey), pool_base=len(s0["pool"]), pool_variant=len(s["pool"]),
                        removed=len(set(s0["pool"]) - set(s["pool"])), step_base=s0["step"], step_variant=s["step"],
                        eligible_removed=len(drop)))
        return s
    rm2.select_pool = select_pool
    D = rm2.Data()
    real, cases = rm2.real_cases()
    v = rm2.placebo_v(len(real))
    wi = rm2.target_cells(D, "55")
    rows = []
    for c in cases:
        r = rm2.case_effect(D, c, "D", rm2.OPT_MAIN)
        gap = np.nan
        if r.get("pool") and len(r["pool"]) >= rm2.MIN_POOL:
            pl = rm2.long_pre(c["event_year"], list(c["pre"]), c.get("trimmed", False))
            h = D.homes_pre(c["event_year"], False)
            t = rm2.rates(D, [c["key"]], pl, h).iloc[0]
            cc = rm2.pool_rate(D, r["pool"], pl, h, True)
            gap = float((t[pl].mean() - cc[pl].mean()) / c.get("scale", 1.0))
        rows.append(dict(key=c["key"], place=c["place"], state=c["state"], event_year=c["event_year"], effect=r["effect"],
                         n_pool=r["n_pool"], step=r["step"], pre_gap=gap, homes=c["homes"], n_post=c["n_post"],
                         band=int(rm2.band_of([real.loc[c["i"], "population"] if pd.notna(real.loc[c["i"], "population"]) else 0])[0]),
                         metro=D.metro.get(c["key"], 0.0), v=v[c["i"]]))
    P = pd.DataFrame(rows)
    P.to_csv(REFERENCE / "parking_t52_b_d_places.csv", index=False)
    pd.DataFrame(log).to_csv(REFERENCE / "parking_t52_b_pool_log_d.csv", index=False)
    y = P["effect"].values
    ok = np.isfinite(y)
    ev = P[["v", "homes", "n_post", "band", "metro"]].copy()
    ev["base"] = ev["homes"] * ev["n_post"]
    a = rm2.weighted_avg("target-state mix", y[ok], ev[ok].reset_index(drop=True), wi)
    lo, hi = rm2.boot_range("target-state mix", y[ok], ev[ok].reset_index(drop=True), wi, rm2.BOOT, rm2.SEED)
    pd.DataFrame([dict(variant="method 2, D", weights="target-state mix", places=int(ok.sum()), average=a, p05=lo, p95=hi,
                       wi_homes=a * rm2.WI_K, wi_p05=lo * rm2.WI_K, wi_p95=hi * rm2.WI_K)]).to_csv(REFERENCE / "parking_t52_b_d_result.csv", index=False)
    print("D", variant, ok.sum(), a, lo, hi)


# ---------------------------------------------------------------- orchestration ----------------------------------------
def env_for(variant: str) -> dict:
    return {**os.environ, **THREADS, "MM_REFERENCE_DIR": str(work(variant)), "MM_GATE_TIME": "15:50",
            "MM_BATCH_COMMITTED_DIR": "reference/batch_2026-11-05",
            "MM_BPS_LAST_YEAR": "2025"}  # = the default last year; also skips the expanded script's prediction-tool scoring


def run_all(variant: str) -> None:
    import datetime as dt
    w = work(variant)
    logs = T52 / f"b_{variant}_logs"
    subprocess.run(["rm", "-rf", str(w), str(logs)], check=True)
    w.mkdir(parents=True)
    logs.mkdir(parents=True)
    subprocess.run(["rsync", "-a", "--exclude", "batch_2026-11-05/", "reference/", str(w) + "/"], cwd=ROOT, check=True)
    subprocess.run(["rsync", "-a", "reference/batch_2026-11-05/", str(w) + "/"], cwd=ROOT, check=True)
    env = env_for(variant)
    for name in ("salvage", "partial", "expanded", "placebo", "d"):
        print(f"== {variant} {dt.datetime.now(dt.UTC):%H:%M:%S} {name}", flush=True)
        args = ["uv", "run", "--all-extras", "python", __file__] + (["d", variant] if name == "d" else ["step", variant, name])
        with open(logs / f"{name}.log", "w") as fh:
            r = subprocess.run(args, cwd=ROOT, env=env, stdout=fh, stderr=subprocess.STDOUT)
        if r.returncode:
            print((logs / f"{name}.log").read_text()[-3000:])
            raise SystemExit(f"FAILED {variant} {name}")
    print(f"== {variant} done {dt.datetime.now(dt.UTC):%H:%M:%S}", flush=True)


# ---------------------------------------------------------------- summary ---------------------------------------------
def main_effects(variant):
    e = pd.read_csv(work(variant) / "parking_expanded_effects.csv")
    e = e[(e["status"] == "included") & (e["outcome"] == "all")].dropna(subset=["effect"])
    e = e.assign(w=e["homes"] * e["n_post"], gap=e["rate_before"] - e["ctrl_before"])
    e.index = e["key"].astype(str) + "|" + e["event_year"].astype(int).astype(str)
    return e


def d_places(variant):
    P = pd.read_csv(work(variant) / "parking_t52_b_d_places.csv", dtype={"key": str})
    P.index = P["key"] + "|" + P["event_year"].astype(int).astype(str)
    return P[np.isfinite(P["effect"])]


def est_main(df):
    def f(k):
        x = df.loc[k]
        return float(np.sum(x["effect"] * x["w"]) / np.sum(x["w"]))
    return f


def est_d(df, wi):
    import run_parking_method2 as rm2

    def f(k):
        x = df.loc[k].reset_index(drop=True)
        ev = x[["v", "homes", "n_post", "band", "metro"]].copy()
        ev["base"] = ev["homes"] * ev["n_post"]
        return rm2.weighted_avg("target-state mix", x["effect"].values, ev, wi)
    return f


def paired(keys_b, keys_v, f_b, f_v):
    """Shift (variant - base), paired place bootstrap over the base places (2,000 draws, seed 20261105): each draw takes
    the same places in both runs; a place the variant dropped is left out of the variant's side of that draw."""
    rng = np.random.default_rng(SEED)
    keys_b = np.asarray(keys_b)
    inv = set(keys_v)
    n = len(keys_b)
    out = []
    for _ in range(DRAWS):
        kb = keys_b[rng.integers(0, n, n)]
        kv = np.array([k for k in kb if k in inv])
        if len(kv):
            out.append(f_v(kv) - f_b(kb))
    return float(np.percentile(out, 5)), float(np.percentile(out, 95))


def indicator(df, flag, kind, wi=None):
    """52b.4: keep every place; effect for places without a separate reform = intercept of a weighted regression on
    [1, flag] (the estimator's own weights over all places). Returns (intercept, flag coefficient, intercept range,
    shift vs all-place estimate and its paired range)."""
    import run_parking_method2 as rm2

    def fit(x):
        if kind == "main":
            y, w = x["effect"].values, x["w"].values
        else:
            y = rm2.winsor(x["effect"].values)
            ev = x[["v", "homes", "n_post", "band", "metro"]].reset_index(drop=True)
            ev["base"] = ev["homes"] * ev["n_post"]
            w, _ = rm2.mix_weights(ev, wi)
        fl = x.index.isin(flag)
        a = np.sum((w * y)[~fl]) / np.sum(w[~fl])
        b = (np.sum((w * y)[fl]) / np.sum(w[fl]) - a) if fl.any() and np.sum(w[fl]) > 0 else np.nan
        return a, b, np.sum(w * y) / np.sum(w)
    a, b, allp = fit(df)
    rng = np.random.default_rng(SEED)
    keys = df.index.values
    ia, sh = [], []
    for _ in range(DRAWS):
        x = df.loc[keys[rng.integers(0, len(keys), len(keys))]]
        aa, _, al = fit(x)
        ia.append(aa)
        sh.append(aa - al)
    return a, b, np.percentile(ia, 5), np.percentile(ia, 95), a - allp, np.percentile(sh, 5), np.percentile(sh, 95)


def summary() -> None:
    os.environ.setdefault("MM_REFERENCE_DIR", str(work("base")))
    import run_parking_method2 as rm2
    rm2.SUF, rm2.CORRECTED = "_corrected", True
    wi = rm2.tool_cells_wi()
    batch = pd.read_csv(ROOT / "reference" / "batch_2026-11-05" / "parking_placebo_full_summary.csv").iloc[0]
    bm2 = pd.read_csv(ROOT / "reference" / "batch_2026-11-05" / "parking_method2_corrected_results.csv")
    bm2 = bm2[(bm2["variant"] == "method 2, D") & (bm2["weights"] == "target-state mix")].iloc[0]
    eb, Pb = main_effects("base"), d_places("base")
    plb = pd.read_csv(work("base") / "parking_placebo_full_summary.csv").iloc[0]
    db = pd.read_csv(work("base") / "parking_t52_b_d_result.csv").iloc[0]
    rows, by_state = [], []
    for v in VARIANTS:
        if not (work(v) / "parking_t52_b_d_result.csv").exists():
            continue
        pl = pd.read_csv(work(v) / "parking_placebo_full_summary.csv").iloc[0]
        d = pd.read_csv(work(v) / "parking_t52_b_d_result.csv").iloc[0]
        ev_, Pv = main_effects(v), d_places(v)
        r = dict(variant=v, main_places=len(ev_), main_rate=pl["real_average"], main_p05=pl["range_from_placebo_low"],
                 main_p95=pl["range_from_placebo_high"], main_wi=pl["real_average"] * WI_K,
                 main_wi_p05=pl["range_from_placebo_low"] * WI_K, main_wi_p95=pl["range_from_placebo_high"] * WI_K,
                 d_places=int(d["places"]), d_rate=d["average"], d_p05=d["p05"], d_p95=d["p95"], d_wi=d["wi_homes"],
                 d_wi_p05=d["wi_p05"], d_wi_p95=d["wi_p95"])
        if v == "base":
            r.update(main_shift=pl["real_average"] - batch["real_average"], d_shift=d["average"] - bm2["average"],
                     note="base minus committed batch (should be 0)")
        else:
            lo, hi = paired(eb.index, ev_.index, est_main(eb), est_main(ev_))
            sh = pl["real_average"] - plb["real_average"]
            dlo, dhi = paired(Pb.index, Pv.index, est_d(Pb, wi), est_d(Pv, wi))
            dsh = d["average"] - db["average"]
            r.update(main_shift=sh, main_shift_p05=lo, main_shift_p95=hi, main_counts=bool(not lo <= 0 <= hi),
                     d_shift=dsh, d_shift_p05=dlo, d_shift_p95=dhi, d_counts=bool(not dlo <= 0 <= dhi))
        r.update(main_pre_gap=float(np.average(ev_["gap"], weights=ev_["w"])),
                 main_pre_gap_abs=float(np.average(ev_["gap"].abs(), weights=ev_["w"])),
                 d_pre_gap=float(Pv["pre_gap"].mean()), d_pre_gap_abs=float(Pv["pre_gap"].abs().mean()))
        rows.append(r)
        # by state of the repeal place
        logs = {}
        for nm in ("expanded", "salvage", "partial", "d"):
            f = work(v) / f"parking_t52_b_pool_log_{nm}.csv"
            if f.exists() and f.stat().st_size > 1:
                logs[nm] = pd.read_csv(f, dtype={"key": str})
        dropped = set()
        f = work(v) / "parking_t52_b_repeal_dropped.csv"
        if f.exists() and f.stat().st_size > 4:
            dropped = set(pd.read_csv(f, dtype={"key": str})["key"])
        for st, g in eb.groupby("state"):
            ks = set(g["key"])
            m = logs.get("expanded", pd.DataFrame(columns=["key", "removed"]))
            m = pd.concat([m] + [logs[x] for x in ("salvage", "partial") if x in logs])
            m = m[m["key"].isin(ks)].drop_duplicates(["key", "event_year"], keep="last") if len(m) else m
            md = logs.get("d", pd.DataFrame(columns=["key", "removed"]))
            md = md[md["key"].isin(ks)].drop_duplicates(["key", "event_year"], keep="last") if len(md) else md
            gv = ev_[ev_["state"] == st]
            pbs, pvs = Pb[Pb["state"] == st], Pv[Pv["state"] == st]
            by_state.append(dict(variant=v, state=st, repeal_places=len(g), repeal_dropped=len(ks & dropped),
                                 main_places_pool_changed=int((m["removed"] > 0).sum()) if len(m) else 0,
                                 main_pool_members_removed=int(m["removed"].sum()) if len(m) else 0,
                                 d_places_pool_changed=int((md["removed"] > 0).sum()) if len(md) else 0,
                                 d_pool_members_removed=int(md["removed"].sum()) if len(md) else 0,
                                 main_pre_gap_base=float(np.average(g["gap"], weights=g["w"])),
                                 main_pre_gap_variant=float(np.average(gv["gap"], weights=gv["w"])) if len(gv) else np.nan,
                                 d_pre_gap_base=float(pbs["pre_gap"].mean()), d_pre_gap_variant=float(pvs["pre_gap"].mean()) if len(pvs) else np.nan))
    # 52b.4 indicator version (from base: every place kept), flags = places the repeal / repeal_after variants drop
    for v, lab in (("repeal", "indicator"), ("repeal_after", "indicator_after")):
        X = Excluder(v)
        flag_m = {k for k in eb.index if k.rsplit("|", 1)[0] in X.repeal_drop(set(zip(eb["key"], eb["event_year"])))}
        flag_d = {k for k in Pb.index if k.rsplit("|", 1)[0] in X.repeal_drop(set(zip(Pb["key"], Pb["event_year"])))}
        a, b, lo, hi, sh, slo, shi = indicator(eb, flag_m, "main")
        da, dbb, dlo, dhi, dsh, dslo, dshi = indicator(Pb, flag_d, "d", wi)
        rows.append(dict(variant=lab, main_places=len(eb), main_rate=a, main_p05=lo, main_p95=hi, main_wi=a * WI_K, main_wi_p05=lo * WI_K,
                         main_wi_p95=hi * WI_K, main_shift=sh, main_shift_p05=slo, main_shift_p95=shi, main_counts=bool(not slo <= 0 <= shi),
                         d_places=len(Pb), d_rate=da, d_p05=dlo, d_p95=dhi, d_wi=da * WI_K, d_wi_p05=dlo * WI_K, d_wi_p95=dhi * WI_K,
                         d_shift=dsh, d_shift_p05=dslo, d_shift_p95=dshi, d_counts=bool(not dslo <= 0 <= dshi),
                         note=f"flagged places {len(flag_m)} (main) / {len(flag_d)} (D); flag coefficient main {b:.3f}, D {dbb:.3f}; "
                              "range = place bootstrap of the intercept (no placebo spread)"))
    out = pd.DataFrame(rows)
    out.round(4).to_csv(OUT, index=False)
    pd.DataFrame(by_state).round(4).to_csv(OUT_STATE, index=False)
    pd.set_option("display.width", 250)
    print(out.round(3).T.to_string())
    bs = pd.DataFrame(by_state)
    print(bs[(bs["repeal_dropped"] > 0) | (bs["main_pool_members_removed"] > 0) | (bs["d_pool_members_removed"] > 0)].round(2).to_string(index=False))


def main() -> None:
    cmd = sys.argv[1]
    if cmd == "all":
        run_all(sys.argv[2])
    elif cmd == "step":
        step(sys.argv[2], sys.argv[3])
    elif cmd == "d":
        method_d(sys.argv[2])
    elif cmd == "summary":
        summary()
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
