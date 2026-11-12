"""Test 61 (CAUSAL_FRAMEWORK_PLAN.md, "Test 61" and "Test 61 audit fixes", which override the text above them):
the honest forest on a small fixed trait set, dose included, against one weighted average. No trait screening.

    uv run --all-extras python scripts/run_parking_t61_forest.py            # the locked run (refuses unless doses frozen)
    uv run --all-extras python scripts/run_parking_t61_forest.py --jobs 6   # worker processes (default 6)

Design (see docs/parking/T61_CODE_NOTES.md for every choice):
- Places: the dose test's fit set per outcome (run_parking_dose.pooled_mask: the 74 and the pooled new places with a
  dose above 0 for that outcome); main also needs an included main effect (as the dose fit), D a finite D effect.
  Dose-0, "alone" and "wait" places are out. The same list goes to the forest and both benchmarks.
- Effects and weights: the dose working copies data/processed/dose/<outcome>_ref (run_parking_dose.Work).
  main: main_effect, weight main_weight (homes x after-years). D: d_effect winsorised 5/95 over the cell's places,
  target-state mix weights over the cell's places (as parking_dose_common.d_point with all doses 1, and Test 54).
- Traits. 3-trait set (judged): dose (d_all; d_24 for 2-4 units), log10 2010 population (Gazetteer, ACS fallback as
  Test 53), area class (Test 53's six classes, one-hot, main city as base). 4-trait set (extra): + rate_before.
  Missing values: training-fold median.
- Tool: run_parking_expanded.predict("causal forest (honest)") unchanged (500 trees, leaf 5, honest halves).
- Benchmarks: one weighted average of the training fold; dose-scaled average beta x dose, beta = sum(w d e)/sum(w d^2)
  through the origin refitted on each training fold (parking_dose_common.beta).
- Scoring: held-out weighted MAE, 10 folds x 20 repeats, Test 54's fold and forest seeds. Per repeat, MAE pools the
  10 folds' test rows (= Test 54's test-weight-weighted fold average). Gain per repeat = 1 - MAE_forest/MAE_benchmark.
- Pass (judged only for 2-4 units, 3 traits, vs one average; chances main and D): mean gain >= 5% and gain > 0 in
  >= 80% of repeats, under main or D.
- Shuffle check: the trait rows are shuffled across places 20 times (seed below); shuffle s is scored on repeat s's
  folds (3 traits vs one average), giving 20 chance-alone gains per outcome x method.
- If the judged rule passes: permutation importance for the passing cells (second pass, same fits; see notes).
Outputs: reference/parking_t61_results.csv (16 cells + 4 shuffle rows, asserted), parking_t61_reading.csv,
parking_t61_places.csv, parking_t61_repeats.csv, and parking_t61_importance.csv only when the rule passes.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import io
import multiprocessing as mp
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import parking_dose_common as dc  # noqa: E402
import run_parking_expanded as rpe  # noqa: E402

OUT = ROOT / "reference"
SEED, REPEATS, FOLDS = 20261105, 20, 10       # Test 54 (run_parking_t54_screen.py), unchanged
SHUFFLES, SHUFFLE_SEED = 20, 20261105 + 6100  # audit fix: shuffle check
PERM_SEED = 20261105 + 6161                    # permutation importance draws
FROZEN_PREFIX = "39a33135"                     # plan: frozen dose table sha256 39a33135...
TOOL = "causal forest (honest)"
CLASSES = ("main city", "secondary principal city", "suburb", "exurb", "outside metro", "rural")  # Test 53 GROUPS
TRAITS3 = ("dose", "log10 population 2010", "area class")
TRAITS4 = TRAITS3 + ("rate before repeal",)
TRAIT_SETS = {"3 traits (judged)": TRAITS3, "4 traits (extra, + rate before)": TRAITS4}
BENCHMARKS = ("one weighted average", "dose-scaled average (beta x dose)")
JUDGED = ("units_2_4", "3 traits (judged)", "one weighted average")  # audit fixes 1 and 2
PASS_MEAN, PASS_SHARE = 0.05, 0.80
UNIT = "homes permitted per 1,000 existing homes a year (held-out weighted mean absolute error)"
N_CELLS = len(dc.OUTCOMES) * len(dc.METHODS) * len(TRAIT_SETS) * len(BENCHMARKS)
N_SHUFFLE_ROWS = len(dc.OUTCOMES) * len(dc.METHODS)
assert N_CELLS == 16 and N_SHUFFLE_ROWS == 4
G: dict = {}


# ------------------------------------------------------------------ traits ----------------------------------------------
def columns_for(traits) -> tuple[list[str], dict[str, list[int]]]:
    """Matrix columns and the trait -> column-index groups (area class is 5 one-hot columns, main city the base)."""
    cols, groups = [], {}
    for t in traits:
        if t == "area class":
            cs = [f"class_{c.replace(' ', '_')}" for c in CLASSES[1:]]
        else:
            cs = [{"dose": "dose", "log10 population 2010": "log10_pop2010", "rate before repeal": "rate_before"}[t]]
        groups[t] = list(range(len(cols), len(cols) + len(cs)))
        cols += cs
    return cols, groups


def one_hot(cls: pd.Series) -> pd.DataFrame:
    """Five indicators; a place with no known class gets NaN in all five (then the training-fold median)."""
    known = cls.isin(CLASSES).values
    out = {}
    for c in CLASSES[1:]:
        out[f"class_{c.replace(' ', '_')}"] = np.where(known, (cls == c).astype(float).values, np.nan)
    return pd.DataFrame(out, index=cls.index)


def _gz(path):
    with zipfile.ZipFile(path) as z:
        g = pd.read_csv(io.BytesIO(z.read(z.namelist()[0])), sep="\t", dtype={"GEOID": str}, encoding="latin-1")
    g.columns = [c.strip() for c in g.columns]
    return g


def pop2010(keys, acs_pop) -> tuple[np.ndarray, np.ndarray]:
    """2010 census population as Test 53 / Test 54: place Gazetteer, county-subdivision Gazetteer (Connecticut on
    state + MCD), else the working copy's ACS population (fallback). Returns (population, source label)."""
    from missing_middleware.paths import RAW
    import run_parking_method2 as m
    D = m.Data()
    gp = _gz(RAW / "parking_older_reforms" / "Gaz_places_national.zip").set_index("GEOID")["POP10"]
    gc = _gz(RAW / "census_gazetteer_2010" / "Gaz_cousubs_national.zip")
    gct = gc[gc["GEOID"].str.startswith("09")].assign(k=lambda d: d["GEOID"].str[:2] + d["GEOID"].str[5:]).set_index("k")["POP10"]
    gc = gc.set_index("GEOID")["POP10"]
    vals = []
    for k in keys:
        g = str(D.geo.loc[k, "acs_geoid"]) if k in D.geo.index else ""
        v = np.nan
        if g.startswith("160|"):
            v = gp.get(g[4:], np.nan)
        elif g.startswith("060|"):
            v = gc.get(g[4:], np.nan)
            if not np.isfinite(v) and g[4:6] == "09":
                v = gct.get(g[4:6] + g[9:], np.nan)
        vals.append(float(v))
    v = np.array(vals, float)
    src = np.where(np.isfinite(v), "2010 Gazetteer", np.where(np.isfinite(np.asarray(acs_pop, float)), "ACS fallback", "missing"))
    v = np.where(np.isfinite(v), v, np.asarray(acs_pop, float))
    return v, src


# ------------------------------------------------------------------ core (synthetic-testable) ----------------------------
def median_fill(Xtr: np.ndarray, Xte: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Training-fold median fill (a column with no training value is filled with 0)."""
    with np.errstate(all="ignore"):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            med = np.nanmedian(Xtr, axis=0)
    med = np.where(np.isfinite(med), med, 0.0)
    return np.where(np.isfinite(Xtr), Xtr, med), np.where(np.isfinite(Xte), Xte, med)


def wmae(p, y, w) -> tuple[float, float]:
    """(sum w |p - y|, sum w): pooled over folds within a repeat."""
    return float(np.sum(w * np.abs(p - y))), float(np.sum(w))


def score_repeat(X, y, w, d, r: int, folds: int = FOLDS, seed: int = SEED, shuffle_seed: int | None = None,
                 importance_groups: dict | None = None, perm_seed: int = PERM_SEED) -> dict:
    """One repeat of the outer CV (Test 54's scheme: fold perm from seed + r, forest rng seed + 1000 r + f).
    X: traits (NaN allowed), y effects, w weights, d dose. With shuffle_seed the rows of X are shuffled across places
    first (rng shuffle_seed + r). With importance_groups, each group's test columns are also permuted (rng
    perm_seed + 1000 r + f) and scored with the same fitted forest (stacked test rows: predictions are row-wise).
    Returns pooled numerators/denominators for the repeat."""
    X = np.asarray(X, float)
    y, w, d = (np.asarray(v, float) for v in (y, w, d))
    n = len(y)
    if shuffle_seed is not None:
        X = X[np.random.default_rng(shuffle_seed + r).permutation(n)]
    rng = np.random.default_rng(seed + r)
    perm = rng.permutation(n)
    acc = {"forest": 0.0, "one": 0.0, "dose": 0.0, "w": 0.0}
    imp = {g: 0.0 for g in (importance_groups or {})}
    for f in range(folds):
        te = perm[f::folds]
        trn = np.setdiff1d(np.arange(n), te)
        Xtr, Xte = median_fill(X[trn], X[te])
        ytr, wtr, yte, wte = y[trn], w[trn], y[te], w[te]
        frng = np.random.default_rng(seed + 1000 * r + f)
        stack = [Xte]
        if importance_groups:
            prng = np.random.default_rng(perm_seed + 1000 * r + f)
            for g, idx in importance_groups.items():
                Xp = Xte.copy()
                Xp[:, idx] = Xte[prng.permutation(len(te))][:, idx]
                stack.append(Xp)
        pall = rpe.predict(TOOL, Xtr, ytr, wtr, np.vstack(stack), frng)
        pf = pall[: len(te)]
        e, ww = wmae(pf, yte, wte)
        acc["forest"] += e
        acc["w"] += ww
        acc["one"] += wmae(np.full(len(te), np.average(ytr, weights=wtr)), yte, wte)[0]
        b = dc.beta(ytr, d[trn], wtr)
        acc["dose"] += wmae(b * d[te], yte, wte)[0]
        for j, g in enumerate(importance_groups or {}):
            imp[g] += wmae(pall[(j + 1) * len(te): (j + 2) * len(te)], yte, wte)[0]
    out = dict(repeat=r, mae_forest=acc["forest"] / acc["w"], mae_one=acc["one"] / acc["w"],
               mae_dose=acc["dose"] / acc["w"], w_test=acc["w"])
    for g, v in imp.items():
        out[f"mae_permuted|{g}"] = v / acc["w"]
    return out


def score_cell(X, y, w, d, repeats: int = REPEATS, folds: int = FOLDS, seed: int = SEED) -> pd.DataFrame:
    """All repeats, serially (the main run parallelises over repeats with the same function)."""
    return pd.DataFrame([score_repeat(X, y, w, d, r, folds, seed) for r in range(repeats)])


def gains(per: pd.DataFrame, bench_col: str) -> pd.Series:
    return 1 - per["mae_forest"] / per[bench_col]


def passes(g: pd.Series) -> bool:
    """Plan rule: mean gain >= 5% and gain > 0 in at least 80% of repeats."""
    g = pd.Series(g, dtype=float)
    return bool(len(g) and g.mean() >= PASS_MEAN and (g > 0).mean() >= PASS_SHARE)


def summarise(per: pd.DataFrame, bench: str) -> dict:
    col = "mae_one" if bench == BENCHMARKS[0] else "mae_dose"
    g = gains(per, col)
    return dict(mae_forest_mean=per["mae_forest"].mean(), mae_benchmark_mean=per[col].mean(), mean_gain=g.mean(),
                gain_of_mean_maes=1 - per["mae_forest"].mean() / per[col].mean(), gain_min=g.min(), gain_max=g.max(),
                share_repeats_gain_above_0=(g > 0).mean(), repeats=len(g), meets_rule=passes(g))


# ------------------------------------------------------------------ real data ------------------------------------------
def build(doses: pd.DataFrame):
    """Cells {(outcome, method): dict(X4, y, w, d, places frame)} from the dose working copies."""
    import run_parking_dose as rd
    import run_parking_method2 as m
    T = pd.read_csv(OUT / "parking_place_ruca_traits.csv", dtype={"key": str}).drop_duplicates("key").set_index("key")
    cells, rows = {}, []
    for o in dc.OUTCOMES:
        Wk = rd.Work(o, doses)
        P = Wk.P
        mem = rd.pooled_mask(P)
        p10, src = pop2010(P["key"].values, P["population"].values)
        cls = P["key"].map(T["area_class6"]).fillna("unknown")
        cols4, _ = columns_for(TRAITS4)
        X = pd.concat([pd.DataFrame({"dose": P["d"].values.astype(float), "log10_pop2010": np.log10(p10)}),
                       one_hot(cls.reset_index(drop=True)),
                       pd.DataFrame({"rate_before": P["rate_before"].values.astype(float)})], axis=1)[cols4]
        ev = Wk.ev()
        for meth in dc.METHODS:
            if meth == "main":
                sel = mem & P["main_ok"].values
                y, w = P["main_effect"].values.astype(float)[sel], P["main_weight"].values.astype(float)[sel]
            else:
                sel = mem & np.isfinite(P["d_effect"].values.astype(float))
                y = m.winsor(P["d_effect"].values.astype(float)[sel])
                w, _ = m.mix_weights(ev[sel].reset_index(drop=True), Wk.wi)
            keep = np.isfinite(y) & (np.asarray(w) > 0)  # zero-weight rows carry nothing in any weighted score
            idx = np.where(sel)[0][keep]
            cells[(o, meth)] = dict(X=X.values[idx], y=np.asarray(y)[keep], w=np.asarray(w, float)[keep],
                                    d=P["d"].values.astype(float)[idx])
            used = set(idx.tolist())
            for i in range(len(P)):
                why = ("used" if i in used else
                       "not in the dose fit set (dose 0, alone, wait or not used)" if not mem[i] else
                       "no main effect (not included)" if meth == "main" and not P["main_ok"].values[i] else
                       "no D effect" if meth == "D" and not np.isfinite(P["d_effect"].values[i]) else "weight 0")
                rows.append(dict(outcome=o, method=meth, reform_id=P["reform_id"].iloc[i], place=P["place"].iloc[i],
                                 state=P["state"].iloc[i], group=P["group"].iloc[i], role=P["role"].iloc[i],
                                 status=why, dose=P["d"].iloc[i], pop2010=p10[i], pop_source=src[i],
                                 area_class6=cls.iloc[i], rate_before_missing=not np.isfinite(P["rate_before"].iloc[i])))
    return cells, pd.DataFrame(rows)


def job(args):
    kind, o, meth, tset, r = args
    c = G["cells"][(o, meth)]
    cols, groups = columns_for(TRAIT_SETS[tset])
    _, g4 = columns_for(TRAITS4)
    use = [j for t in TRAIT_SETS[tset] for j in g4[t]]
    X = c["X"][:, use]
    if kind == "cv":
        res = score_repeat(X, c["y"], c["w"], c["d"], r)
    elif kind == "shuffle":
        res = score_repeat(X, c["y"], c["w"], c["d"], r, shuffle_seed=SHUFFLE_SEED)
    else:  # importance
        res = score_repeat(X, c["y"], c["w"], c["d"], r, importance_groups=groups)
    return dict(kind=kind, outcome=o, method=meth, traits=tset, **res)


def run_jobs(jobs, n):
    rows = []
    with cf.ProcessPoolExecutor(n, mp_context=mp.get_context("fork")) as ex:
        for res in ex.map(job, jobs):
            rows.append(res)
            print(res["kind"], res["outcome"], res["method"], res["traits"], res["repeat"], flush=True)
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--first", action="store_true", help="places and per-cell counts only (no fit, no effect read); commit before the full run")
    a = ap.parse_args()
    h = dc.require_frozen_doses()
    assert h.startswith(FROZEN_PREFIX), f"dose table sha256 {h} is not the frozen 39a33135... named in the plan"
    doses = dc.load_doses()
    cells, places = build(doses)
    places.to_csv(OUT / "parking_t61_places.csv", index=False)
    for k, c in cells.items():
        print(k, "places used", len(c["y"]), flush=True)
    if a.first:
        pd.DataFrame([dict(cell=str(k), places_used=len(c["y"])) for k, c in cells.items()]).to_csv(OUT / "parking_t61_counts.csv", index=False)
        print("--first: wrote parking_t61_places.csv and parking_t61_counts.csv; no fit run", flush=True)
        return
    G["cells"] = cells
    jobs = [("cv", o, meth, t, r) for o in dc.OUTCOMES for meth in dc.METHODS for t in TRAIT_SETS for r in range(REPEATS)]
    jobs += [("shuffle", o, meth, "3 traits (judged)", s) for o in dc.OUTCOMES for meth in dc.METHODS for s in range(SHUFFLES)]
    F = run_jobs(jobs, a.jobs)
    F.round(6).to_csv(OUT / "parking_t61_repeats.csv", index=False)

    out = []
    for o in dc.OUTCOMES:
        for meth in dc.METHODS:
            n = len(cells[(o, meth)]["y"])
            for t in TRAIT_SETS:
                per = F[(F["kind"] == "cv") & (F["outcome"] == o) & (F["method"] == meth) & (F["traits"] == t)]
                assert len(per) == REPEATS
                for b in BENCHMARKS:
                    judged = (o, t, b) == JUDGED
                    out.append(dict(row="cell", outcome=o, method=meth, traits=t, benchmark=b, places=n, judged=judged,
                                    **summarise(per, b), unit=UNIT))
            sh = F[(F["kind"] == "shuffle") & (F["outcome"] == o) & (F["method"] == meth)]
            assert len(sh) == SHUFFLES
            obs = gains(F[(F["kind"] == "cv") & (F["outcome"] == o) & (F["method"] == meth) &
                          (F["traits"] == "3 traits (judged)")], "mae_one").mean()
            s = summarise(sh, BENCHMARKS[0])
            s["meets_rule"] = np.nan  # not a test: chance-alone gains
            out.append(dict(row="shuffle check (20 trait shuffles; chance alone)", outcome=o, method=meth,
                            traits="3 traits, rows shuffled", benchmark=BENCHMARKS[0], places=n, judged=False, **s,
                            share_shuffles_at_or_above_observed_mean=float((gains(sh, "mae_one") >= obs).mean()),
                            unit=UNIT))
    R = pd.DataFrame(out)
    assert (R["row"] == "cell").sum() == N_CELLS and len(R) == N_CELLS + N_SHUFFLE_ROWS, len(R)
    R.round(4).to_csv(OUT / "parking_t61_results.csv", index=False)

    # reading: judged (2-4 units, 3 traits, one average; main or D) and the reported-only rows
    read = []
    for o in dc.OUTCOMES:
        for t in TRAIT_SETS:
            for b in BENCHMARKS:
                c = R[(R["row"] == "cell") & (R["outcome"] == o) & (R["traits"] == t) & (R["benchmark"] == b)]
                mm = {r.method: bool(r.meets_rule) for r in c.itertuples()}
                any_ = any(mm.values())
                judged = (o, t, b) == JUDGED
                read.append(dict(outcome=o, traits=t, benchmark=b, judged=judged, main_meets_rule=mm["main"],
                                 D_meets_rule=mm["D"], forest_beats_benchmark=any_,
                                 reading=(("PASS: " if any_ else "FAIL: ") if judged else "reported only: ") +
                                 ("the forest beats the benchmark (mean gain >= 5% and > 0 in >= 80% of repeats, "
                                  "under main or D); importance follows; a pass is optimistic (dose results already seen)"
                                  if any_ else "these traits, dose included, don't predict a city's effect better than "
                                  "the benchmark")))
    Rd = pd.DataFrame(read)
    Rd.to_csv(OUT / "parking_t61_reading.csv", index=False)
    pd.set_option("display.width", 250)
    print(R.round(3).to_string(index=False))
    print(Rd.to_string(index=False))

    jr = R[(R["row"] == "cell") & R["judged"].astype(bool) & R["meets_rule"].astype(bool)]
    if len(jr):
        ij = [("importance", o, meth, JUDGED[1], r) for o, meth in zip(jr["outcome"], jr["method"]) for r in range(REPEATS)]
        I = run_jobs(ij, a.jobs)
        rows = []
        for (o, meth), d in I.groupby(["outcome", "method"]):
            base = F[(F["kind"] == "cv") & (F["outcome"] == o) & (F["method"] == meth) & (F["traits"] == JUDGED[1])]
            assert np.allclose(d.sort_values("repeat")["mae_forest"].values, base.sort_values("repeat")["mae_forest"].values), \
                "importance pass did not reproduce the forest's MAE"
            for t in TRAITS3:
                inc = d[f"mae_permuted|{t}"] / d["mae_forest"] - 1
                rows.append(dict(outcome=o, method=meth, trait=t, mean_mae_increase_share=inc.mean(),
                                 min_over_repeats=inc.min(), max_over_repeats=inc.max(), repeats=len(inc),
                                 unit="share increase in held-out weighted MAE when the trait is permuted in test folds"))
        pd.DataFrame(rows).round(4).to_csv(OUT / "parking_t61_importance.csv", index=False)
        print(pd.DataFrame(rows).round(3).to_string(index=False))
    else:
        print("judged rule not met: no permutation importance (plan)")


if __name__ == "__main__":
    main()
