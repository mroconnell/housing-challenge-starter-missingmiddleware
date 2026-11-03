"""Test P (docs/tod/CAUSAL_FRAMEWORK_PLAN.md, "Test P: do the causal factors predict places they never saw?" and
"Test P: logged change to the pass rule"; locked 2026-11-03 before any count).

Hide one D-11 place at a time; rebuild every Stage 1 number without it; predict its measured 1/4-mile effect (extra new
homes per 100 lot acres a year, as the central line: run_tod_station_model.case_effects("permit_est"), New York and
Philadelphia averaged over their rezonings) with
  A   plug-in: T2b 2x2 cells (old and new line, rezoned minus not), scaled by the upzoned share, one distance gradient;
  A0  the same without the upzoned-share scaling;
  B   two-part lot model (logit for "any new homes in the window", log-linear for how many; difference-in-differences
      terms), held-out intercept set from the place's own before-window lots only;
and compare with the plain average of the other 10 places (the current Stage 2 method), zero, and the stored
hide-one-place results of the lot and stop models (not rerun). Placebo for A, A0 and B: the after window is replaced
by the second half of the before window.

All B covariates are discrete, so the lots are collapsed to cells (exactly the same fit as one row per lot).

    OMP_NUM_THREADS=1 .venv/bin/python scripts/run_tod_causal_predict.py [--rebuild]

Writes reference/tod_causal_predict.csv (summaries only: no lot rows, no parcel ids).
"""
from __future__ import annotations

import os
import sys
import tempfile
from math import comb
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from missing_middleware.paths import REFERENCE  # noqa: E402

OUT = ROOT / "data" / "processed" / "tod_station_area"
CACHE = Path(os.environ.get("TOD_PREDICT_CACHE", Path(tempfile.gettempdir()) / "tod_causal_predict_cache"))  # local aggregates
EIGHTH = 1609.344 / 8                         # 0-1/8 mile in metres
WI_FACTOR = 4874.1 / 100 * 5 * 1.2269         # central: 33.54 x this = 10,028
SEED = 20261103
TIER3 = 1.15                                  # owner 2026-11-03 11:14 ("then let's make it 15%")
MKE = "Milwaukee Hop placebo"
BROAD = {"la_toc_2017": "Los Angeles TOC", "san_diego_2021": "San Diego 2021", "chicago_2022": "Chicago 2022",
         "bellevue_belred_2009": "Bellevue BelRed"}
PLACES = ["New York", "Philadelphia", "Austin", "Charlotte", "Chicago 2015", "Denver", "Portland 2020",
          "Seattle Mount Baker", "Seattle Othello", "Salt Lake City", "Saint Paul"]
CASE_OF = {"Austin": "austin_2009", "Charlotte": "charlotte_2019", "Chicago 2015": "chicago_2015", "Denver": "denver_2018",
           "Portland 2020": "portland_2020", "Seattle Mount Baker": "seattle_mount_baker_2014",
           "Seattle Othello": "seattle_othello_2012", "Salt Lake City": "slc_2010", "Saint Paul": "stpaul_2011"}


# ----------------------------------------------------------------------------------------------------------------------
# data: one lot frame per case -> stop aggregates (A) and cell aggregates (B)
# ----------------------------------------------------------------------------------------------------------------------
def cfg(case: str) -> dict:
    import build_tod_station_lot_table as BL
    return {**BL.CASES, **{k: v for k, (_, v) in BL.adapter_cases().items()}}[case]


def event_years(case: str, src: Path = OUT) -> pd.DataFrame:
    """Per-building events with the permit-year estimate, filtered exactly as run_tod_station_model.event_windows."""
    import run_tod_station_model as SM
    E = pd.read_parquet(src / f"events_{case}.parquet")
    if "match" in E:
        E = E[E["match"] != "completed_only_near_permit"]
    elif E.completed_year.notna().any() and E.permit_year.notna().any():
        E = E[E.completed_year.notna()]
    if SM.county_of(case) == "king" and E.permit_year.isna().all():
        E = E.copy()
        E["permit_year"] = SM.king_permit_years(case, E, src)
    return E.assign(yr=SM.permit_year_est(E, SM.county_of(case)))


def placebo_windows(case: str, D: pd.DataFrame, src: Path = OUT) -> tuple[pd.DataFrame, int]:
    """Fake reform: before = first half of the real before window, after = its second half (h = n // 2 years each;
    an odd middle year is left out). Hand-check corrections of the real before window are split between the halves in
    proportion to the raw homes in each half (duplicates 0)."""
    b0, b1 = cfg(case)["before"]
    h = (b1 - b0 + 1) // 2
    E = event_years(case, src)
    out = D.copy()
    halves = {"homes_before_win": (b0, b0 + h - 1), "homes_after_win": (b1 - h + 1, b1)}
    for col, (a, b) in halves.items():
        out[col] = E[E.yr.between(a, b)].groupby("lot_index").homes.sum().reindex(out.index).fillna(0)
    raw_full = E[E.yr.between(b0, b1)].groupby("lot_index").homes.sum()
    hc = OUT / "hand_check_big_lots.csv"
    if hc.exists():
        H = pd.read_csv(hc)
        H = H[(H["case"] == case) & H.lot_index.isin(out.index) & H["class"].isin(["wrong count", "duplicate"])
              & (H["window"] != "after")]
        for _, r in H.iterrows():
            ix = r["lot_index"]
            tot = 0.0 if r["class"] == "duplicate" else r["homes_corrected"]
            if pd.isna(tot):
                continue
            raw = raw_full.get(ix, 0.0)
            f1 = out.loc[ix, "homes_before_win"] / raw if raw > 0 else 0.5
            f2 = out.loc[ix, "homes_after_win"] / raw if raw > 0 else 0.5
            out.loc[ix, "homes_before_win"], out.loc[ix, "homes_after_win"] = float(tot) * f1, float(tot) * f2
    return out, h


def stop_age(OY: pd.DataFrame, case: str) -> tuple[pd.DataFrame, float]:
    """T2b line-age rule per stop: new = opened from 3 years before the reform through the end of the after window;
    old = opened 10+ years before (or line code 'old'); else excluded (4-9 years, after the window, unknown)."""
    S = OY[OY.case == case].drop_duplicates("stop_id")
    if S.reform_year.dropna().empty:
        return pd.DataFrame({"stop_id": [], "age": []}), np.nan
    ry = float(S.reform_year.dropna().iloc[0])
    ae = cfg(case)["after"][1]
    age = np.where((S.oy >= ry - 3) & (S.oy <= ae), "new", np.where((ry - S.oy >= 10) | S.old, "old", "excl"))
    return pd.DataFrame({"stop_id": S.stop_id.values, "age": age}), ry


def lot_frame(case: str, place: str, OY: pd.DataFrame, src: Path = OUT) -> dict[str, pd.DataFrame]:
    """{'main': lots, 'placebo': lots} in the 1/4-mile band with the columns the methods need."""
    import run_tod_station_model as SM
    cols = ["group", "stop_id", "dist_m", "band", "in_reform_area", "implausible", "acres_land", "homes_before_win",
            "homes_after_win"]
    D0 = pd.read_parquet(src / f"lots_{case}.parquet", columns=cols)
    ages, _ = stop_age(OY, case)
    yb, ya = SM.windows(case)
    res = {}
    for kind in ("main", "placebo"):
        if kind == "main":
            D = SM.event_windows(case, D0, "permit_est", src) if (src / f"events_{case}.parquet").exists() else D0
            wb, wa = yb, ya
        else:
            if not (src / f"events_{case}.parquet").exists():
                continue
            D, h = placebo_windows(case, D0, src)
            if h == 0:            # a 1-year before window cannot be split (Saint Paul): no placebo for the case
                continue
            wb = wa = h
        D = D[~D.implausible.fillna(False) & (D.band == "0-1/4")]
        L = pd.DataFrame({"place": place, "case": case, "group": D.group.values, "stop_id": D.stop_id.values,
                          "sub": (D.dist_m.values < EIGHTH).astype(int), "up": D.in_reform_area.fillna(False).astype(int).values,
                          "A": D.acres_land.fillna(0).values, "hb": D.homes_before_win.values.astype(float),
                          "ha": D.homes_after_win.values.astype(float), "yb": wb, "ya": wa})
        res[kind] = L.merge(ages, on="stop_id", how="left").fillna({"age": "excl"})
    return res


def milwaukee_frame() -> pd.DataFrame:
    """The Milwaukee Hop placebo as one place in the new / not-rezoned cell (T2b main): all its 1/4-mile lots, pretend
    reform 2019, before b (5 years), after 2020-2024; recorded acres (flagged in T2b)."""
    M = pd.read_parquet(OUT / "checks_milwaukee_placebo_lots.parquet")
    M = M[(M.band == "0-1/4") & ~M.implausible.fillna(False)]
    return pd.DataFrame({"place": MKE, "case": "milwaukee_placebo", "group": "comparison", "stop_id": 0,
                         "sub": (M.dist_m.values < EIGHTH).astype(int), "up": 0, "A": M.acres.values,
                         "hb": M.b.values.astype(float), "ha": M.a2024.values.astype(float), "yb": 5, "ya": 5, "age": "new"})


def aggregate(L: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Stop aggregates (A) and cell aggregates (B) of a lot frame."""
    L = L.assign(N=L.ha / L.ya - L.hb / L.yb, Aup=L.A * L.up, pb=(L.hb > 0).astype(int), pa=(L.ha > 0).astype(int),
                 lb=np.log(L.hb.where(L.hb > 0, 1.0)), la=np.log(L.ha.where(L.ha > 0, 1.0)),
                 sb=L.hb.where(L.hb > 0, 0.0), sa=L.ha.where(L.ha > 0, 0.0))
    S = L.groupby(["place", "case", "group", "stop_id", "age", "sub"], as_index=False).agg(
        N=("N", "sum"), A=("A", "sum"), Aup=("Aup", "sum"))
    C = L.groupby(["place", "case", "group", "age", "up", "sub"], as_index=False).agg(
        n=("A", "size"), A=("A", "sum"), pb=("pb", "sum"), pa=("pa", "sum"), lb=("lb", "sum"), la=("la", "sum"),
        sb=("sb", "sum"), sa=("sa", "sum"), yb=("yb", "first"), ya=("ya", "first"))
    return S, C


def build(rebuild: bool = False) -> dict[str, pd.DataFrame]:
    import run_tod_causal_line_age as LA
    CACHE.mkdir(parents=True, exist_ok=True)
    names = ["S_main", "C_main", "S_placebo", "C_placebo"]
    if not rebuild and all((CACHE / f"{n}.parquet").exists() for n in names):
        return {n: pd.read_parquet(CACHE / f"{n}.parquet") for n in names}
    OY = LA.opening_years()
    cases = sorted(p.stem.removeprefix("lots_") for p in OUT.glob("lots_*.parquet"))
    parts = {"main": [], "placebo": []}
    for case in cases:
        place = LA.place_of(case)
        if not place and case not in BROAD:
            continue
        fr = lot_frame(case, place or BROAD[case], OY)
        for k, L in fr.items():
            parts[k].append(aggregate(L))
        print("built", case, flush=True)
    parts["main"].append(aggregate(milwaukee_frame()))
    out = {}
    for k in ("main", "placebo"):
        out[f"S_{k}"] = pd.concat([p[0] for p in parts[k]], ignore_index=True)
        out[f"C_{k}"] = pd.concat([p[1] for p in parts[k]], ignore_index=True)
    for n, v in out.items():
        v.to_parquet(CACHE / f"{n}.parquet")
    return out


# ----------------------------------------------------------------------------------------------------------------------
# measured effect (the central line's definition) from stop aggregates
# ----------------------------------------------------------------------------------------------------------------------
def measured(S: pd.DataFrame) -> pd.Series:
    g = S.groupby(["place", "case", "group"])[["N", "A"]].sum()
    rate = 100 * g.N / g.A
    e = (rate.xs("reform", level="group") - rate.xs("comparison", level="group")).dropna()
    return e.groupby(level="place").mean()


# ----------------------------------------------------------------------------------------------------------------------
# Test A / A0
# ----------------------------------------------------------------------------------------------------------------------
def _cells(S: pd.DataFrame, sub: int | None = None) -> pd.DataFrame:
    T = S[S.age != "excl"]
    if sub is not None:
        T = T[T["sub"] == sub]
    T = T.assign(cell=T.age + "/" + np.where(T.group == "reform", "up", "no"))
    g = T.groupby(["place", "case", "cell"])[["N", "A", "Aup"]].sum()
    g = g[g.A > 0]
    g = g.assign(d=100 * g.N / g.A, u=g.Aup / g.A)
    return g.groupby(["place", "cell"])[["d", "u"]].mean().reset_index()   # NY / PHL: mean over rezonings


def fit_A(S: pd.DataFrame) -> dict:
    """Stage 1 numbers from the training stops only."""
    P = _cells(S)
    cm = P.groupby("cell").d.mean()
    um = P.groupby("cell").u.mean()
    C_old, C_new = cm["old/up"] - cm["old/no"], cm["new/up"] - cm["new/no"]
    e = {}
    for s in (1, 0):
        q = _cells(S, s).groupby("cell").d.mean()
        e[s] = np.mean([q["old/up"] - q["old/no"], q["new/up"] - q["new/no"]])
    R = e[1] / e[0]                                           # 0-1/8 effect / 1/8-1/4 effect
    Rf = S[S.group == "reform"]
    pc = Rf.groupby(["place", "case"]).apply(lambda g: g.A[g["sub"] == 1].sum() / g.A.sum(), include_groups=False)
    s1_tr = pc.groupby(level="place").mean().mean()
    cl = Rf[Rf.age != "excl"].groupby(["place", "case"]).apply(
        lambda g: g.A[g.age == "new"].sum() / g.A.sum() if g.A.sum() > 0 else np.nan, include_groups=False)
    mix = cl.groupby(level="place").mean().mean()
    return {"C_old": C_old, "C_new": C_new, "u_old": um["old/up"], "u_new": um["new/up"], "R": R, "e_eighth": e[1],
            "e_quarter": e[0], "s1_tr": s1_tr, "mix_new": mix, "cells": cm.to_dict(), "places_in_cells": P.groupby("cell").place.nunique().to_dict()}


def predict_A(par: dict, S_p: pd.DataFrame, scale: bool = True, u_override: float | None = None) -> float:
    """Prediction for one place from its reform stops' acres only (no outcome)."""
    preds = []
    for _, g in S_p[S_p.group == "reform"].groupby("case"):
        A = g.A.sum()
        if A <= 0:
            continue
        a_new, a_ex = g.A[g.age == "new"].sum(), g.A[g.age == "excl"].sum()
        w_new = (a_new + a_ex * par["mix_new"]) / A
        u = g.Aup.sum() / A if u_override is None else u_override
        s1 = g.A[g["sub"] == 1].sum() / A
        R, s1t = par["R"], par["s1_tr"]
        f = (s1 * R + 1 - s1) / (s1t * R + 1 - s1t)
        k_old, k_new = (u / par["u_old"], u / par["u_new"]) if scale else (1.0, 1.0)
        preds.append(f * ((1 - w_new) * par["C_old"] * k_old + w_new * par["C_new"] * k_new))
    return float(np.mean(preds)) if preds else np.nan


# ----------------------------------------------------------------------------------------------------------------------
# Test B: two-part lot model on collapsed cells
# ----------------------------------------------------------------------------------------------------------------------
TERMS = ["after", "up", "new", "band8", "after_up", "after_new", "after_up_new", "after_band8"]


def _long(C: pd.DataFrame) -> pd.DataFrame:
    """Two rows per cell: before (after = 0) and after window."""
    b = C.assign(after=0, pos=C.pb, sumlog=C.lb, sumy=C.sb, yrs=C.yb)
    a = C.assign(after=1, pos=C.pa, sumlog=C.la, sumy=C.sa, yrs=C.ya)
    return pd.concat([b, a], ignore_index=True)


def _x(T: pd.DataFrame, new: np.ndarray | float | None = None, up: np.ndarray | float | None = None,
       after: np.ndarray | float | None = None) -> np.ndarray:
    af = T.after.values if after is None else np.broadcast_to(after, len(T))
    u = T.up.values if up is None else np.broadcast_to(up, len(T))
    nw = (T.age.to_numpy(dtype=object) == "new").astype(float) if new is None else np.broadcast_to(new, len(T))
    b8 = T["sub"].values.astype(float)
    return np.column_stack([af, u, nw, b8, af * u, af * nw, af * u * nw, af * b8]).astype(float)


def _weights(T: pd.DataFrame) -> np.ndarray:
    """Each place the same total weight in each window; lots equal within a place."""
    tot = T.groupby(["place", "after"]).n.transform("sum")
    return (T.n / tot).values * len(T) / T.place.nunique() / 2


def _sigmoid(z):
    return 1 / (1 + np.exp(-z))


def fit_B(C: pd.DataFrame) -> dict:
    from sklearn.linear_model import LogisticRegression
    T = _long(C[C.age != "excl"])
    places = sorted(T.place.unique())
    Pd = (T.place.to_numpy(dtype=object)[:, None] == np.array(places, dtype=object)[None, :]).astype(float)
    X = np.hstack([Pd, _x(T)])
    w = _weights(T)
    # part 1: logit on "any new homes in the window" (cells -> positive and negative weights)
    y = np.r_[np.ones(len(T)), np.zeros(len(T))]
    sw = np.r_[w * T.pos.values, w * (T.n.values - T.pos.values)]
    keep = sw > 0
    lg = LogisticRegression(C=np.inf, fit_intercept=False, max_iter=5000, tol=1e-10)
    lg.fit(np.vstack([X, X])[keep], y[keep], sample_weight=sw[keep])
    beta1 = lg.coef_.ravel()
    # part 2: log homes if any (weighted least squares on cell means = lot-level fit)
    m = T.pos.values > 0
    Xm, ym, wm = X[m], T.sumlog.values[m] / T.pos.values[m], w[m] * T.pos.values[m]
    sq = np.sqrt(wm)
    beta2 = np.linalg.lstsq(Xm * sq[:, None], ym * sq, rcond=None)[0]
    smear = (w[m] * np.exp(-(Xm @ beta2)) * T.sumy.values[m]).sum() / wm.sum()     # Duan smearing
    k = len(places)
    return {"places": places, "a1": dict(zip(places, beta1[:k])), "b1": beta1[k:], "a2": dict(zip(places, beta2[:k])),
            "b2": beta2[k:], "smear": smear}


def _mixed(par: dict, T: pd.DataFrame, a1: float, a2: float, part: str, mix: float, **kw) -> np.ndarray:
    """Per-cell prediction; cells on excluded-age stops take the training line-age mix."""
    def one(new):
        X = _x(T, new=new, **kw)
        p = _sigmoid(a1 + X @ par["b1"])
        if part == "p":
            return p
        if part == "xb2":
            return a2 + X @ par["b2"]
        return p * np.exp(a2 + X @ par["b2"]) * par["smear"]
    ex = T.age.to_numpy(dtype=object) == "excl"
    base = one(None)
    if ex.any():
        base = np.where(ex, mix * one(1.0) + (1 - mix) * one(0.0), base)
    return base


def place_intercepts(par: dict, C_p: pd.DataFrame, mix: float) -> tuple[float, float, str]:
    """Held-out intercepts from the place's own BEFORE-window lots only (the after window is never read)."""
    T = _long(C_p)
    T = T[T.after == 0].reset_index(drop=True)
    target = T.pos.sum()
    lo, hi = -40.0, 40.0
    for _ in range(200):
        mid = (lo + hi) / 2
        v = (T.n.values * _mixed(par, T, mid, 0.0, "p", mix)).sum()
        lo, hi = (mid, hi) if v < target else (lo, mid)
    a1 = (lo + hi) / 2
    m = T.pos.values > 0
    if m.any():
        xb = _mixed(par, T, a1, 0.0, "xb2", mix)
        a2 = (T.sumlog.values[m] - T.pos.values[m] * xb[m]).sum() / T.pos.values[m].sum()
        note = ""
    else:
        a2, note = float(np.mean(list(par["a2"].values()))), "no before-window homes: part-2 intercept = training mean"
    if target == 0:
        note += "; no before-window homes: part-1 intercept at the search bound"
    return a1, a2, note


def predict_B(par: dict, C_p: pd.DataFrame, mix: float) -> tuple[float, float, str]:
    """(B, B with the before-window toggle taken off = difference-in-differences reading, note)."""
    a1, a2, note = place_intercepts(par, C_p, mix)
    out, did = [], []
    for _, g in C_p[C_p.group == "reform"].groupby("case"):
        g = g.reset_index(drop=True).assign(after=1)
        A = g.A.sum()
        if A <= 0:
            continue
        ya, yb = g.ya.iloc[0], g.yb.iloc[0]
        on = _mixed(par, g, a1, a2, "e", mix, after=1.0)
        off = _mixed(par, g, a1, a2, "e", mix, after=1.0, up=0.0)
        on_b = _mixed(par, g, a1, a2, "e", mix, after=0.0)
        off_b = _mixed(par, g, a1, a2, "e", mix, after=0.0, up=0.0)
        n = g.n.values
        out.append(100 * (n * (on - off)).sum() / ya / A)
        did.append(100 * ((n * (on - off)).sum() / ya - (n * (on_b - off_b)).sum() / yb) / A)
    return (float(np.mean(out)) if out else np.nan, float(np.mean(did)) if did else np.nan, note)


# ----------------------------------------------------------------------------------------------------------------------
# hide-one-place loop
# ----------------------------------------------------------------------------------------------------------------------
def loo(S: pd.DataFrame, C: pd.DataFrame, places: list[str]) -> pd.DataFrame:
    rows = []
    for p in places:
        St, Ct = S[S.place != p], C[(C.place != p) & ~C.place.isin(BROAD.values())]
        St = St[~St.place.isin(BROAD.values())]
        pa = fit_A(St)
        pb = fit_B(Ct)
        Sp, Cp = S[S.place == p], C[C.place == p]
        b, bd, note = predict_B(pb, Cp, pa["mix_new"])
        rows.append({"place": p, "A": predict_A(pa, Sp, True), "A0": predict_A(pa, Sp, False), "B": b, "B_did": bd,
                     "note_B": note, "R": pa["R"], "C_old": pa["C_old"], "C_new": pa["C_new"], "u_old": pa["u_old"],
                     "u_new": pa["u_new"], "mix_new": pa["mix_new"]})
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------------------------------------------------
# stored hide-one-place results (not rerun)
# ----------------------------------------------------------------------------------------------------------------------
def _disp(c: str) -> str:
    inv = {v: k for k, v in CASE_OF.items()}
    return inv.get(c, c)


def stored() -> tuple[pd.DataFrame, dict]:
    R = REFERENCE
    out, notes = {}, {}

    def loco(f):
        d = pd.read_csv(R / f)
        d = d[d.band == "0-1/4"]
        return pd.Series(d.model.values, index=[_disp(c) for c in d.city])

    out["stored: boosted lot model (lot + place, 5 fits; the lower line)"] = loco("tod_optiond_loco_lot_place_fix_equal_fill_k5_s1.csv")
    notes["stored: boosted lot model (lot + place, 5 fits; the lower line)"] = "tod_optiond_loco_lot_place_fix_equal_fill_k5_s1.csv"
    out["stored: random forest lot model (lot + place, 1 fit)"] = loco("tod_optiond_loco_lot_place_fix_equal_fill_k1_s1_rf_ms0.05.csv")
    notes["stored: random forest lot model (lot + place, 1 fit)"] = ("tod_optiond_loco_lot_place_fix_equal_fill_k1_s1_rf_ms0.05.csv; "
                                                                    "older data state (before the land and hand-check fixes)")
    cf = [loco(f"tod_optiond_loco_lot_place_fix_equal_fill_stops_k1_s1_cf_honest{s}.csv") for s in ("", "_cs1", "_cs2", "_cs3")]
    out["stored: honest causal forest (stop level, 4-seed average)"] = pd.concat(cf, axis=1).mean(axis=1)
    notes["stored: honest causal forest (stop level, 4-seed average)"] = "tod_optiond_loco_..._cf_honest{,_cs1,_cs2,_cs3}.csv"
    sp = pd.read_csv(R / "tod_optiond_stopmodel_places.csv")
    sp = sp[(sp.set == "D-11") & (sp.band == "0-1/4")]
    for meth, lab in (("gradient_boosting", "stored: stop model, boosted"),
                      ("gradient_boosting_plus_stop_traits", "stored: stop model, boosted + stop traits"),
                      ("linear_4", "stored: stop model, 4-trait"), ("linear_4_plus_coverage", "stored: stop model, 4-trait + coverage")):
        d = sp[sp.method == meth]
        out[lab] = pd.Series(d.predicted.values, index=[_disp(c) for c in d.city])
        notes[lab] = "tod_optiond_stopmodel_places.csv"
    for f, tag in (("tod_optiond_dml_hidden_D-11.csv", ""), ("tod_optiond_dml_hidden_D-11_placebo.csv", ", with no-reform lots")):
        d = pd.read_csv(R / f)
        d = d[(d.band == "0-1/4") & (d.treatment == "in_area")]
        for v in ("A", "B-PLR"):
            q = d[d.version == v]
            lab = f"stored: double ML {v}{tag}"
            out[lab] = pd.Series(q.predicted.values, index=[_disp(c) for c in q.hidden])
            notes[lab] = f
    return pd.DataFrame(out), notes


# ----------------------------------------------------------------------------------------------------------------------
# scoring
# ----------------------------------------------------------------------------------------------------------------------
def p_at_least(k: int, n: int = 11) -> float:
    return sum(comb(n, i) for i in range(k, n + 1)) / 2 ** n


def tier(med: float, k: int, m0: float, placebo_ok: bool | None) -> str:
    if placebo_ok is False:
        return "none (placebo fails)"
    if med < m0 and k >= 8:
        t = "1 switch"
    elif med < m0 and k >= 6:
        t = "2 show beside"
    elif med <= TIER3 * m0:
        t = "3 close"
    else:
        t = "none"
    return t if placebo_ok is not None else f"{t} (by the rule only; no placebo run)"


DEVIATIONS = [
    "Placebo: Saint Paul left out (its before window is 1 year, 2010, so it cannot be split); placebo on 10 places.",
    "Placebo: Milwaukee Hop left out of the placebo 2x2 (its lot table has one before-window total, no years).",
    "Placebo windows: fake before = first h, fake after = last h years of the before window, h = years // 2 (Denver's "
    "5-year window drops its middle year). Hand-check corrections of the real before window are split between the "
    "halves in proportion to the raw homes in each half (duplicates 0).",
    "Placebo: stops keep their real line-age class (not re-dated to the fake reform year).",
    "Placebo interval: 2,000 draws resampling the held-out places' placebo predictions (the pooled = their mean).",
    "Upzoned share (A): the in-district (in_reform_area) share of the land acres of the place's reform stops' 1/4-mile "
    "lots; a cell's training share = place-equal mean of that share over the cell's stops (comparison stops have 0 in "
    "every D-11 place).",
    "Unknown line age (A and B): every stop T2b excludes (4-9 years old, opened after the after window, unknown year) "
    "takes the training mix = place-equal mean of the training places' acre-weighted new-line share of classified "
    "reform acres (about 0.46).",
    "Distance (A): band shares are the place's reform stops' 1/4-mile land acres within 1/8 mile (201 m) vs 1/8-1/4; "
    "the ratio is the 0-1/8 over 1/8-1/4 effect averaged over the two cell contrasts (old, new) of the training 2x2.",
    "B: not stated in the lock, chosen as the stored models: each place the same total weight in each window, lots "
    "equal within a place; the Milwaukee Hop lots are in B's training as new-line, not-rezoned lots (as in the 2x2 "
    "main); lots on excluded-age stops are left out of B's fit and take the training mix when predicted; the outcome is "
    "homes in the window and predictions are divided by the window's years.",
    "B: the locked toggle (upzoned as observed minus upzoned = 0, at the after-window level) also switches off the "
    "upzoned main term (the before-reform level gap); a difference-in-differences reading (after toggle minus before "
    "toggle, per year) is reported beside, not tiered.",
    "Stored models: errors scored against the current measured effects; the random forest file is from the older data "
    "state (before the land and hand-check fixes). Stop models: place totals from tod_optiond_stopmodel_places.csv. "
    "Double ML: in-area treatment, seed 1. No stored model has a placebo run, so their tier is by the rule only.",
    "Wisconsin translation of a method = mean of its 11 held-out predictions x 298.97 (4,874.1 / 100 x 5 x 1.2269; "
    "the plain average gives 33.54 -> 10,028).",
    "Milwaukee Hop beside: the 2x2 cell version only (B needs stop line ages and reform lots; not run for the Hop).",
    "Madison beside: its station-area lot table has no after-window homes and no comparison stops, so the measured "
    "station-area effect cannot be built; A's prediction is set beside the overlay test (different design, short window).",
]


def main() -> None:
    import run_tod_station_model as SM
    rebuild = "--rebuild" in sys.argv
    data = build(rebuild)
    S, C = data["S_main"], data["C_main"]
    meas = measured(S[S.place.isin(PLACES)]).reindex(PLACES)
    # check: equals the central line's measured effects
    E = SM.city_level(SM.case_effects("permit_est"))
    E = E[E.band == "0-1/4"].set_index("city").effect_per_100_acres
    ref = pd.Series({p: E[CASE_OF.get(p, p)] for p in PLACES})
    assert np.allclose(meas.values, ref.values, atol=1e-6), pd.concat([meas, ref], axis=1)
    assert abs(meas.mean() - 33.54) < 0.005, meas.mean()
    print(f"measured effects reproduce the central line: mean {meas.mean():.4f}")

    L = loo(S, C, PLACES)
    L = L.set_index("place")
    preds = pd.DataFrame({"A": L.A, "A0": L.A0, "B": L.B,
                          "plain average": pd.Series({p: meas.drop(p).mean() for p in PLACES}),
                          "zero": 0.0}, index=PLACES)
    ST, notes = stored()
    preds = preds.join(ST)
    preds["B, DiD reading (beside, not tiered)"] = L.B_did
    err = (preds.sub(meas, axis=0)).abs()

    # placebo
    Sp, Cp = data["S_placebo"], data["C_placebo"]
    no_split = sorted(Cp.loc[Cp.ya == 0, "place"].unique())          # before window of 1 year: cannot be split
    Sp, Cp = Sp[~Sp.place.isin(no_split)], Cp[~Cp.place.isin(no_split)]
    PL_PLACES = [p for p in PLACES if p not in no_split]
    LP = loo(Sp, Cp, PL_PLACES).set_index("place")
    rng = np.random.default_rng(SEED)
    plac = {}
    for m in ("A", "A0", "B"):
        v = LP[m].values
        bs = np.array([np.nanmean(v[rng.integers(0, len(v), len(v))]) for _ in range(2000)])
        lo, hi = np.nanpercentile(bs, [5, 95])
        plac[m] = {"pooled": np.nanmean(v), "lo90": lo, "hi90": hi, "pass": bool(lo <= 0 <= hi)}

    # summaries
    m0 = err["plain average"].median()
    rng = np.random.default_rng(SEED)
    draws = [rng.integers(0, len(PLACES), len(PLACES)) for _ in range(1000)]
    rows = []
    for m in preds.columns:
        e = err[m]
        k = int((e < err["plain average"]).sum()) if m != "plain average" else np.nan
        loo_med = [e.drop(p).median() for p in PLACES]
        diff = [np.median(e.values[d]) - np.median(err["plain average"].values[d]) for d in draws]
        pl = plac.get(m)
        if m in ("A", "A0", "B"):
            t = tier(e.median(), k, m0, pl["pass"])
        elif m.startswith("stored"):
            t = tier(e.median(), k, m0, None)
        else:
            t = "benchmark" if m in ("plain average", "zero") else "beside, not tiered"
        rows.append({"row": "method", "method": m, "mean_miss": e.mean(), "median_miss": e.median(),
                     "median_miss_loo_low": min(loo_med), "median_miss_loo_high": max(loo_med),
                     "places_beaten_vs_average": k, "p_binom_at_least_k": p_at_least(k) if k == k else np.nan,
                     "median_minus_average_lo90": np.percentile(diff, 5), "median_minus_average_hi90": np.percentile(diff, 95),
                     "placebo_pooled": pl["pooled"] if pl else np.nan, "placebo_lo90": pl["lo90"] if pl else np.nan,
                     "placebo_hi90": pl["hi90"] if pl else np.nan,
                     "placebo_places": len(PL_PLACES) if pl else np.nan,
                     "placebo": ("pass" if pl["pass"] else "fail") if pl else ("not run (stored)" if m.startswith("stored") else ""),
                     "tier": t, "mean_prediction": preds[m].mean(), "wisconsin": preds[m].mean() * WI_FACTOR,
                     "note": notes.get(m, "")})
    M = pd.DataFrame(rows)
    order = {"1 switch": 1, "2 show beside": 2, "3 close": 3}
    q = M[M.method.isin(["A0", "A", "B"])].assign(o=lambda d: d.tier.map(order).fillna(9),
                                                   s=lambda d: d.method.map({"A0": 0, "A": 1, "B": 2}))
    best = q.sort_values(["o", "s"]).iloc[0]
    winner = best.method if best.o < 9 else "none"

    per = []
    for p in PLACES:
        for m in preds.columns:
            per.append({"row": "place", "place": p, "method": m, "prediction": preds.loc[p, m], "measured": meas[p],
                        "abs_error": err.loc[p, m]})
    for p in PL_PLACES:
        for m in ("A", "A0", "B"):
            per.append({"row": "placebo_place", "place": p, "method": m, "prediction": LP.loc[p, m],
                        "measured": measured(Sp[Sp.place == p]).get(p, np.nan)})
    diag = [{"row": "fold_inputs", "place": p, "method": "A", **{k: L.loc[p, k] for k in
                                                                 ("R", "C_old", "C_new", "u_old", "u_new", "mix_new")},
             "note": L.loc[p, "note_B"]} for p in PLACES]

    # beside rows (not pooled, not scored): broad maps, Milwaukee Hop transit-alone, Madison
    trainS = S[S.place.isin(PLACES + [MKE])]
    trainC = C[C.place.isin(PLACES + [MKE])]
    paF, pbF = fit_A(trainS), fit_B(trainC)
    full = {"row": "full_fit", "method": "A", "R": paF["R"], "C_old": paF["C_old"], "C_new": paF["C_new"],
            "u_old": paF["u_old"], "u_new": paF["u_new"], "mix_new": paF["mix_new"],
            "note": f"cells {paF['cells']}; places {paF['places_in_cells']}; 0-1/8 effect {paF['e_eighth']:.2f}, "
                    f"1/8-1/4 effect {paF['e_quarter']:.2f}; training 0-1/8 acre share {paF['s1_tr']:.3f}"}
    beside = []
    for case, nm in BROAD.items():
        Sb, Cb = S[S.place == nm], C[C.place == nm]
        if not len(Sb):
            continue
        mb = measured(Sb).get(nm, np.nan)
        b, bd, note = predict_B(pbF, Cb, paF["mix_new"])
        for m, v in (("A", predict_A(paF, Sb, True)), ("A0", predict_A(paF, Sb, False)), ("B", b),
                     ("plain average", meas.mean()), ("zero", 0.0)):
            beside.append({"row": "beside_broad", "place": nm, "method": m, "prediction": v, "measured": mb,
                           "abs_error": abs(v - mb), "note": note if m == "B" else ""})
    # Milwaukee Hop: the new / not-rezoned cell and the transit-alone contrast, predicted without the Hop
    noM = _cells(S[S.place.isin(PLACES)]).groupby("cell").d.mean()
    hop_d = _cells(S[S.place == MKE]).set_index("cell").d.get("new/no", np.nan)
    hop_ref = pd.read_csv(REFERENCE / "tod_station_checks_milwaukee_placebo.csv")
    hop_ref = hop_ref[hop_ref.band == "0-1/4"]
    beside.append({"row": "beside_milwaukee", "place": MKE, "method": "new/no cell without the Hop (D-11 places)",
                   "prediction": noM["new/no"], "measured": hop_d, "abs_error": abs(noM["new/no"] - hop_d),
                   "note": "Hop's own before-after change in new homes per 100 lot acres a year, all its 1/4-mile lots"})
    for v, e in zip(hop_ref.version, hop_ref.effect_per_100_acres):
        tr = noM["new/no"] - noM["old/no"]
        beside.append({"row": "beside_milwaukee", "place": MKE, "method": "transit alone (new/no - old/no) without the Hop",
                       "prediction": tr, "measured": e, "abs_error": abs(tr - e), "note": f"Hop placebo effect vs comparison ({v})"})
    # Madison: the station-area lot table has no after-window homes and no comparison stops (not supported); A's
    # prediction for its 1/4-mile reform lots (overlay share, Rapid Route A = new line) is set beside the overlay test.
    W = pd.read_parquet(OUT / "wi_lots_station.parquet", columns=["case", "band", "dist_m", "in_reform_area", "acres_land", "implausible"])
    W = W[(W.case == "wi_madison") & (W.band == "0-1/4") & ~W.implausible.fillna(False)]
    Sm = pd.DataFrame({"place": "Madison", "case": "wi_madison", "group": "reform", "stop_id": 0, "age": "new",
                       "sub": (W.dist_m.values < EIGHTH).astype(int), "A": W.acres_land.fillna(0).values,
                       "Aup": (W.acres_land.fillna(0) * W.in_reform_area.fillna(False)).values, "N": 0.0})
    um = Sm.Aup.sum() / Sm.A.sum()
    mres = pd.read_csv(REFERENCE / "tod_madison_test_results.csv")
    for m, sc in (("A", True), ("A0", False)):
        v = predict_A(paF, Sm, sc)
        beside.append({"row": "beside_madison", "place": "Madison", "method": m, "prediction": v,
                       "prediction_per_100_overlay_acres": v / um, "measured": 8.0,
                       "note": ("NOT the station-area design: its lot table has no after-window homes and no comparison "
                                "stops. Prediction per 100 1/4-mile acres; divided by the overlay share "
                                f"({um:.3f}) to compare with the overlay test (0.080 per overlay acre a year = 8.0 per 100, "
                                "90% -16.7 to 30.9; after 2023-2025, short window)")})
    beside.append({"row": "beside_madison", "place": "Madison", "method": "B", "note": "not run: no after-window or comparison lots in the Madison station-area table"})

    dev = pd.DataFrame({"row": "deviation", "note": DEVIATIONS})
    out = pd.concat([dev, M, pd.DataFrame([{"row": "winner", "method": winner, "tier": best.tier if winner != "none" else "none",
                                       "note": f"plain average median miss {m0:.2f}; tier 3 bar {TIER3:.2f} x = {TIER3 * m0:.2f}"}]),
                     pd.DataFrame(per), pd.DataFrame(diag), pd.DataFrame([full]), pd.DataFrame(beside)], ignore_index=True)
    out.round(4).to_csv(REFERENCE / "tod_causal_predict.csv", index=False)
    pd.set_option("display.width", 250, "display.max_columns", 30, "display.max_colwidth", 60)
    print(M.drop(columns=["note"]).round(2).to_string(index=False))
    print("winner:", winner)
    print(pd.concat([preds[["A", "A0", "B", "plain average", "B, DiD reading (beside, not tiered)"]], meas.rename("measured")], axis=1).round(1))
    print(LP[["A", "A0", "B"]].round(1), plac)
    print(L[["R", "C_old", "C_new", "u_old", "u_new", "mix_new", "note_B"]].round(3))
    print(pd.DataFrame([full]).T)
    print(pd.DataFrame(beside).round(1).to_string(index=False))


if __name__ == "__main__":
    main()
