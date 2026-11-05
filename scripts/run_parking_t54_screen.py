"""Test 54 (CAUSAL_FRAMEWORK_PLAN.md, "Test 54"): nested single/pair trait screen, then an honest causal forest.

For each outer fold (10 folds x 20 repeats), every single trait and every pair is scored on the training places only
(weighted linear regression, 5-fold inner CV, weighted MAE); the top-ranked singles/pairs are walked until 5 distinct
traits are chosen; the honest causal forest (primary) and a weighted regression are fit on those 5 and scored on the
held-out fold against "one average". Outcomes: main (homes x after-years), D (target-state mix), D (equal).

    MM_REFERENCE_DIR=<batch working copy> MM_GATE_TIME=15:50 uv run --all-extras python scripts/run_parking_t54_screen.py
Outputs: reference/parking_t54_results.csv, parking_t54_selection.csv, parking_t54_top_pairs.csv
"""
from __future__ import annotations

import concurrent.futures as cf
import io
import itertools
import multiprocessing as mp
import sys
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import run_parking_method2 as m  # noqa: E402
import run_parking_expanded as rpe  # noqa: E402
from missing_middleware.paths import RAW  # noqa: E402

OUT = ROOT / "reference"
BATCH = OUT / "batch_2026-11-05"
SEED, REPEATS, FOLDS, INNER, K = 20261105, 20, 10, 5, 5
G: dict = {}


def gz(path):
    with zipfile.ZipFile(path) as z:
        g = pd.read_csv(io.BytesIO(z.read(z.namelist()[0])), sep="\t", dtype={"GEOID": str}, encoding="latin-1")
    g.columns = [c.strip() for c in g.columns]
    return g


def build():
    m.SUF, m.CORRECTED = "_corrected", True
    D = m.Data()
    real, cases = m.real_cases()
    keys = [c["key"] for c in cases]
    ev = pd.DataFrame({"v": m.placebo_v(len(real)), "homes": real["homes"].values, "n_post": real["n_post"].values,
                       "band": m.band_of(real["population"].fillna(0)), "metro": [D.metro.get(k, 0.0) for k in keys]})
    ev["base"] = ev["homes"] * ev["n_post"]
    wi = m.target_cells(D, "55")
    wmix, _ = m.mix_weights(ev, wi)
    bp = pd.read_csv(BATCH / "parking_method2_corrected_places.csv")
    yD = bp[bp["variant"] == "method 2, D"]["effect"].values.astype(float)
    me = pd.read_csv(BATCH / "parking_expanded_effects.csv", dtype={"key": str})
    me = me[(me["outcome"] == "all") & me["effect"].notna()].set_index("key")
    yM, wM = me["effect"].reindex(keys).values.astype(float), me["weight"].reindex(keys).values.astype(float)
    # traits
    X = pd.DataFrame(index=range(len(keys)))
    av = pd.read_csv(OUT / "parking_allvars_values.csv")
    # non-ACS items measured before repeal only (audit 22:35 UTC). Dropped as post-repeal or current: the A_ items and
    # V4-V7, V20-V22, T1-T6, log_pop, rel_rent (ACS 2020-2024 / 2024 land area), metro (current CBSA), V16/V19 (current
    # stops and blocks); V15_region is text and dropped (the class and state traits cover geography).
    KEEP = ["V1_old_min_apartment", "V2_old_min_single_family", "V8_share_permits_5plus_before", "V9_value_per_unit_rel",
            "V10_permit_volatility", "V11_repeal_year", "V12_prior_partial_reform", "V13_rewrite_same_time",
            "V14_state_large_city_share_repealed", "rate_before"]
    av = av.set_index("prn_key")[[c for c in KEEP if c in av.columns]]
    X = X.join(av.reindex(real["prn_key"].values).reset_index(drop=True))
    tr = pd.read_csv(RAW / "parking_acs_tod_traits" / "traits_by_release.csv.gz")
    tr = tr.set_index(["acs_geoid", "release_end"])
    geo = [str(D.geo.loc[k, "acs_geoid"]) if k in D.geo.index else "" for k in keys]
    rows = []
    for g, c in zip(geo, cases):
        yr = int(min(max(c["event_year"] - 1, 2013), 2023))
        rows.append(tr.loc[(g, yr)] if (g, yr) in tr.index else pd.Series(dtype=float))
    acs = pd.DataFrame(rows).reset_index(drop=True).add_prefix("acs_")
    X = X.join(acs)
    mk = pd.read_csv(OUT / "parking_t52_a_places.csv", dtype={"key": str}).drop_duplicates("key").set_index("key")
    X["rent_growth"] = mk["rent_growth"].reindex(keys).values
    X["job_growth"] = mk["job_growth"].reindex(keys).values
    T = pd.read_csv(OUT / "parking_place_ruca_traits.csv", dtype={"key": str}).set_index("key")
    cls = pd.Series([T["area_class6"].get(k, "unknown") for k in keys])
    for c in ("secondary principal city", "suburb", "exurb", "outside metro", "rural"):
        X[f"class_{c.replace(' ', '_')}"] = (cls == c).astype(float).values
    gp = gz(RAW / "parking_older_reforms" / "Gaz_places_national.zip").set_index("GEOID")["POP10"]
    gc = gz(RAW / "census_gazetteer_2010" / "Gaz_cousubs_national.zip")
    gct = gc[gc["GEOID"].str.startswith("09")].assign(k=lambda d: d["GEOID"].str[:2] + d["GEOID"].str[5:]).set_index("k")["POP10"]
    gc = gc.set_index("GEOID")["POP10"]
    p10 = []
    for g in geo:
        v = gp.get(g[4:], np.nan) if g.startswith("160|") else gc.get(g[4:], np.nan) if g.startswith("060|") else np.nan
        if not np.isfinite(v) and g.startswith("060|09"):
            v = gct.get(g[4:6] + g[9:], np.nan)
        p10.append(v)
    p10 = np.where(np.isfinite(p10), p10, real["population"].astype(float).values)
    X["log10_pop2010"] = np.log10(p10)
    X = X.apply(pd.to_numeric, errors="coerce")
    # traits constant within a training fold are left in: standardised on that fold's rows they become 0 and carry no
    # information (audit 22:35 UTC: zero variance judged per fold, not on all 74)
    outcomes = {"main (homes x after-years)": (yM, wM), "D (target-state mix)": (m.winsor(yD), wmix),
                "D (equal)": (m.winsor(yD), np.ones(len(yD)))}
    return X, outcomes, real["place"].values


def wls_mae_cv(Xs, y, w, folds):
    """Inner CV weighted MAE of a weighted linear regression on columns Xs."""
    err, wt = 0.0, 0.0
    for te in folds:
        trm = np.ones(len(y), bool)
        trm[te] = False
        A = np.column_stack([np.ones(trm.sum()), Xs[trm]])
        sw = np.sqrt(w[trm])
        b, *_ = np.linalg.lstsq(A * sw[:, None], y[trm] * sw, rcond=None)
        p = np.column_stack([np.ones(len(te)), Xs[te]]) @ b
        err += np.sum(w[te] * np.abs(p - y[te]))
        wt += np.sum(w[te])
    return err / wt


def outer_job(args):
    r, oname = args
    X, outcomes = G["X"], G["outcomes"]
    y, w = outcomes[oname]
    ok = np.isfinite(y) & (w > 0)
    Xa, ya, wa = X.values[ok], y[ok], w[ok]
    cols = list(X.columns)
    rng = np.random.default_rng(SEED + r)
    perm = rng.permutation(len(ya))
    res = []
    for f in range(FOLDS):
        te = perm[f::FOLDS]
        trn = np.setdiff1d(np.arange(len(ya)), te)
        med = np.nanmedian(Xa[trn], axis=0)
        Xtr = np.where(np.isfinite(Xa[trn]), Xa[trn], med)
        Xte = np.where(np.isfinite(Xa[te]), Xa[te], med)
        # standardise on training rows (constant columns become 0)
        mu, sd = Xtr.mean(0), Xtr.std(0)
        sd[sd == 0] = 1.0
        Ztr, Zte = (Xtr - mu) / sd, (Xte - mu) / sd
        ytr, wtr = ya[trn], wa[trn]
        ip = rng.permutation(len(ytr))
        inner = [ip[k::INNER] for k in range(INNER)]
        scores = []
        for j in range(len(cols)):
            scores.append((wls_mae_cv(Ztr[:, [j]], ytr, wtr, inner), (j,)))
        for a, b in itertools.combinations(range(len(cols)), 2):
            scores.append((wls_mae_cv(Ztr[:, [a, b]], ytr, wtr, inner), (a, b)))
        scores.sort(key=lambda t: t[0])
        chosen = []
        for _, comb in scores:
            for j in comb:
                if j not in chosen and len(chosen) < K:
                    chosen.append(j)
            if len(chosen) >= K:
                break
        top_pair = next(c for _, c in scores if len(c) == 2)
        wte = wa[te]
        base = np.full(len(te), np.average(ytr, weights=wtr))
        e0 = np.sum(wte * np.abs(base - ya[te])) / wte.sum()
        frng = np.random.default_rng(SEED + 1000 * r + f)
        pf = rpe.predict("causal forest (honest)", Xtr[:, chosen], ytr, wtr, Xte[:, chosen], frng)
        pr = rpe.predict("weighted regression, all traits", Xtr[:, chosen], ytr, wtr, Xte[:, chosen], frng)
        res.append(dict(outcome=oname, repeat=r, fold=f, n_test=len(te), mae_one=e0,
                        mae_forest=np.sum(wte * np.abs(pf - ya[te])) / wte.sum(),
                        mae_regression=np.sum(wte * np.abs(pr - ya[te])) / wte.sum(),
                        chosen=";".join(cols[j] for j in chosen), top_pair="+".join(cols[j] for j in top_pair),
                        w_test=float(wte.sum())))
    return res


def main() -> None:
    X, outcomes, places = build()
    print("places", len(X), "traits", X.shape[1], flush=True)
    G.update(X=X, outcomes=outcomes)
    jobs = [(r, o) for o in outcomes for r in range(REPEATS)]
    rows = []
    with cf.ProcessPoolExecutor(6, mp_context=mp.get_context("fork")) as ex:
        for part in ex.map(outer_job, jobs):
            rows += part
            print(part[0]["outcome"], part[0]["repeat"], flush=True)
    F = pd.DataFrame(rows)
    F.to_csv(ROOT / "data" / "processed" / "t54_folds.csv", index=False)
    out = []
    for o, d in F.groupby("outcome"):
        per = d.groupby("repeat").apply(lambda g: pd.Series({k: np.sum(g[k] * g["w_test"]) / g["w_test"].sum()
                                                              for k in ("mae_one", "mae_forest", "mae_regression")}))
        for tool in ("forest", "regression"):
            gain_r = 1 - per[f"mae_{tool}"] / per["mae_one"]
            gain = 1 - per[f"mae_{tool}"].mean() / per["mae_one"].mean()
            out.append(dict(outcome=o, tool="honest causal forest (primary)" if tool == "forest" else "weighted regression",
                            mae_one_average=per["mae_one"].mean(), mae_tool=per[f"mae_{tool}"].mean(), gain=gain,
                            gain_min_over_repeats=gain_r.min(), gain_max_over_repeats=gain_r.max(),
                            passes=bool(tool == "forest" and o != "D (equal)" and gain >= 0.05)))
    R = pd.DataFrame(out)
    R.round(4).to_csv(OUT / "parking_t54_results.csv", index=False)
    sel = []
    for o, d in F.groupby("outcome"):
        c = Counter(t for s in d["chosen"] for t in s.split(";"))
        for t, n in c.most_common():
            sel.append(dict(outcome=o, trait=t, chosen_in_folds=n, share=n / len(d)))
    pd.DataFrame(sel).round(4).to_csv(OUT / "parking_t54_selection.csv", index=False)
    tp = F.groupby(["outcome", "top_pair"]).size().rename("folds_ranked_first").reset_index().sort_values(
        ["outcome", "folds_ranked_first"], ascending=[True, False])
    tp.to_csv(OUT / "parking_t54_top_pairs.csv", index=False)
    pd.set_option("display.width", 250)
    print(R.round(3).to_string(index=False))
    print(pd.DataFrame(sel).groupby("outcome").head(8).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
