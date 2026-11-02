"""T4: Los Angeles TOC tier cutoffs, difference in discontinuities (docs/tod/CAUSAL_FRAMEWORK_PLAN.md, "Test 4 (T4)",
locked before any count).

Design A (main): signed distance to the edge of the City's October 2017 TOC tier map (tier k inside vs tier k-1 outside).
Design B (brief): distance to the nearest Metro Rail (subway / light rail) or Metrolink station point, at the Guidelines'
cutoffs; reduced form, first stage in density-bonus points, fuzzy ratio.
Outcome per lot: y = 100 x (after homes / 5 - before homes / 6) / land acres (permit_est dates, hand checks).
Local linear each side (land acres x triangular kernel); bandwidth by the Imbens-Kalyanaraman rule, clipped [25, 300] m;
46 / 76 / 122 m beside it; cluster bootstrap (400 m boundary cells for A, nearest station for B).

    OMP_NUM_THREADS=1 .venv/bin/python scripts/run_tod_causal_la_toc_rd.py

Writes reference/tod_causal_la_toc_rd.csv (summaries only; no lot rows or ids).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from missing_middleware import geom as G  # noqa: E402
from missing_middleware import geom_extra_station as X  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
import run_tod_station_model as M  # noqa: E402
from run_tod_causal_edge import boundary_points  # noqa: E402

CASE, CRS = "la_toc_2017", 5070
SEED, DRAWS, DONUT, SEG, PUBLIC_MAX = 20261104, 1000, 25.0, 400.0, 0.5
H_FIXED = {"46 m (150 ft)": 45.72, "76 m (250 ft, brief main)": 76.2, "122 m (400 ft)": 121.92}
BONUS = {0: 0.0, 1: 50.0, 2: 60.0, 3: 70.0, 4: 80.0}
FT = 0.3048


def lots() -> pd.DataFrame:
    cols = ["city_name", "acres_land", "land_value", "homes_existing", "homes_before_win", "homes_after_win", "implausible",
            "public", "x", "y"]
    D = pd.read_parquet(M.OUT / f"lots_{CASE}.parquet", columns=cols)
    D = M.event_windows(CASE, D, "permit_est").rename(columns={"x": "px", "y": "py"})   # "y" is the outcome below
    D = D[(D.city_name == "Los Angeles") & ~D.implausible.fillna(False) & (D.acres_land > 0)].copy()
    yb, ya = M.windows(CASE)
    D["y"] = 100 * (D.homes_after_win / ya - D.homes_before_win / yb) / D.acres_land
    D["y_before"] = 100 * (D.homes_before_win / yb) / D.acres_land
    D["log_land_value_per_acre"] = np.log(D.land_value / D.acres_land).where(D.land_value > 0)
    D["log_acres"] = np.log(D.acres_land)
    D["existing_per_acre"] = D.homes_existing / D.acres_land
    D["num"] = D.homes_after_win / ya - D.homes_before_win / yb
    T = X.read_vector(RAW / "tod_radius_programs" / "la" / "toc_tiers_oct2017.geojson", dst=CRS)
    tiers = {int(t): [g for g, tt in zip(T.geometry, T.FINALTIER) if int(tt) == int(t) and g] for t in T.FINALTIER}
    D["tier"] = 0
    for t in sorted(tiers):
        inside = G.points_in_any(D.px.values, D.py.values, tiers[t], union=True)
        D.loc[inside, "tier"] = np.maximum(D.loc[inside, "tier"], t)
    D["bonus"] = D.tier.map(BONUS)
    D.attrs["tiers"] = tiers
    return D.reset_index(drop=True)


# ------------------------------------------------------------------ estimators (weighted sufficient statistics)

def _side_stats(x, y, w, cl, ncl):
    """Per cluster: sums of w, wx, wx2, wy, wxy -> array (ncl, 5)."""
    S = np.zeros((ncl, 5))
    for j, v in enumerate((w, w * x, w * x * x, w * y, w * x * y)):
        S[:, j] = np.bincount(cl, weights=v, minlength=ncl)
    return S


def _intercept(S):
    """S (..., 5) summed sufficient stats -> weighted least-squares intercept."""
    sw, sx, sxx, sy, sxy = (S[..., j] for j in range(5))
    det = sw * sxx - sx * sx
    with np.errstate(divide="ignore", invalid="ignore"):
        return (sxx * sy - sx * sxy) / det


def rd(D: pd.DataFrame, s: str, ycol: str, h: float, cl: np.ndarray, ncl: int, W: np.ndarray, donut: float = 0.0):
    """Local linear jump (inside - outside) at s = 0 with triangular kernel x land acres; point and bootstrap draws."""
    x = D[s].to_numpy()
    yv = D[ycol].to_numpy()
    m = (np.abs(x) <= h) & (np.abs(x) >= donut) & np.isfinite(yv)
    out = []
    for side in (x >= 0, x < 0):
        k = m & side
        w = D.acres_land.to_numpy()[k] * (1 - np.abs(x[k]) / h)
        S = _side_stats(x[k], yv[k], w, cl[k], ncl)
        out.append((_intercept(S.sum(0)), _intercept(np.einsum("dc,cj->dj", W, S)), int(k.sum())))
    return out[0][0] - out[1][0], out[0][1] - out[1][1], out[0][2], out[1][2]


def ratio(D, s, h, cl, ncl, W, donut=0.0):
    x = D[s].to_numpy()
    m = (np.abs(x) <= h) & (np.abs(x) >= donut)
    r = []
    for side in (x >= 0, x < 0):
        k = m & side
        n = np.bincount(cl[k], weights=D.num.to_numpy()[k], minlength=ncl)
        a = np.bincount(cl[k], weights=D.acres_land.to_numpy()[k], minlength=ncl)
        with np.errstate(divide="ignore", invalid="ignore"):
            r.append((100 * n.sum() / a.sum(), 100 * (W @ n) / (W @ a)))
    return r[0][0] - r[1][0], r[0][1] - r[1][1]


def _wls(x, y, w, deg):
    Xm = np.vander(x, deg + 1, increasing=True)
    sw = np.sqrt(w)
    return np.linalg.lstsq(Xm * sw[:, None], y * sw, rcond=None)[0]


def ik_bandwidth(x: np.ndarray, y: np.ndarray, w: np.ndarray) -> tuple[float, float]:
    """Imbens-Kalyanaraman (2012) MSE-optimal bandwidth, triangular kernel, weights w. Returns (clipped, raw)."""
    k = (np.abs(x) <= 1000) & np.isfinite(y)
    x, y, w = x[k], y[k], w[k]
    N = len(x)
    h1 = 1.84 * np.std(x) * N ** -0.2
    p, q = x >= 0, x < 0
    n1 = np.abs(x) <= h1
    f = n1.sum() / (2 * N * h1)

    def wvar(m):
        mu = np.average(y[m], weights=w[m])
        return np.average((y[m] - mu) ** 2, weights=w[m])
    vp, vm = wvar(n1 & p), wvar(n1 & q)
    g = (x >= np.median(x[q])) & (x <= np.median(x[p]))
    Xm = np.c_[np.ones(g.sum()), (x[g] >= 0), x[g], x[g] ** 2, x[g] ** 3]
    sw = np.sqrt(w[g])
    m3 = 6 * np.linalg.lstsq(Xm * sw[:, None], y[g] * sw, rcond=None)[0][4]
    Np, Nm = p.sum(), q.sum()
    h2p = 3.56 * (vp / (f * m3 ** 2)) ** (1 / 7) * Np ** (-1 / 7)
    h2m = 3.56 * (vm / (f * m3 ** 2)) ** (1 / 7) * Nm ** (-1 / 7)
    kp, km = p & (x <= h2p), q & (x >= -h2m)
    m2p = 2 * _wls(x[kp], y[kp], w[kp], 2)[2]
    m2m = 2 * _wls(x[km], y[km], w[km], 2)[2]
    rp = 2160 * vp / (kp.sum() * h2p ** 4)
    rm = 2160 * vm / (km.sum() * h2m ** 4)
    h = 3.4375 * ((vp + vm) / (f * ((m2p - m2m) ** 2 + rp + rm))) ** 0.2 * N ** -0.2
    return float(np.clip(h, 25.0, 300.0)), float(h)


# ------------------------------------------------------------------ designs

def design_a(D: pd.DataFrame) -> list[dict]:
    tiers = D.attrs["tiers"]
    rows = []
    for k in (4, 3, 2, 1):
        polys = [g for t, gs in tiers.items() if t >= k for g in gs]
        B = boundary_points(polys)[:, :2]
        tree = cKDTree(B)
        S = D[D.tier.isin([k, k - 1])].copy()
        d, j = tree.query(np.c_[S.px, S.py])
        S["s"] = np.where(S.tier == k, d, -d)
        S["bx"], S["by"] = B[j, 0], B[j, 1]
        S = S[np.abs(S.s) <= 1000]
        cell = pd.Series(list(zip(np.floor(S.bx / SEG).astype(int), np.floor(S.by / SEG).astype(int))), index=S.index)
        S["cell"] = pd.factorize(cell)[0]
        # usable cells (T3's rule): lots on both sides within 300 m, public land under half of either side's acres
        near = S[np.abs(S.s) <= 300]
        g = near.assign(side=near.s >= 0, pa=near.acres_land * near.public.fillna(False)).groupby(["cell", "side"]).agg(
            n=("s", "size"), ac=("acres_land", "sum"), pa=("pa", "sum")).unstack("side")
        ok = (g[("n", True)].fillna(0) > 0) & (g[("n", False)].fillna(0) > 0) & \
             (g[("pa", True)].fillna(0) / g[("ac", True)] < PUBLIC_MAX) & (g[("pa", False)].fillna(0) / g[("ac", False)] < PUBLIC_MAX)
        S = S[S.cell.isin(ok[ok].index)].copy()
        S["cell"] = pd.factorize(S.cell)[0]
        rows += estimate(S, "s", S.cell.to_numpy(), f"A map edge tier {k}|{k - 1 if k > 1 else 'none'}", first_stage=False)
    return rows


def design_b(D: pd.DataFrame) -> list[dict]:
    T = pd.read_csv(REFERENCE / "tod_stop_table.csv", low_memory=False)
    T = T[T.case == CASE]
    rows = []
    for lab, kinds, cuts in (("Metro Rail", ['"Subway, Metro"', '"Tram, Streetcar, Light rail"'], {"750 ft (tier 4|3)": 750}),
                             ("Metro Rail", ['"Subway, Metro"', '"Tram, Streetcar, Light rail"'], {"2,640 ft (tier 3|below)": 2640}),
                             ("Metrolink", ['"Rail"'], {"750 ft (tier 3|2)": 750, "1,500 ft (tier 2|1)": 1500, "2,640 ft (tier 1|none)": 2640})):
        st = T[T.stop_type_text.isin(kinds)].drop_duplicates("stop_key")
        if not len(st):
            st = T[T.stop_type_text.str.strip('"').isin([k.strip('"') for k in kinds])].drop_duplicates("stop_key")
        sx, sy = X.transform(st.lon.values, st.lat.values, 4326, CRS)
        d, j = cKDTree(np.c_[sx, sy]).query(np.c_[D.px, D.py])
        for name, ft in cuts.items():
            S = D.assign(s=ft * FT - d, cl=j)          # + = inside the cutoff (closer to the station)
            S = S[np.abs(S.s) <= 1000].copy()
            if min((S.s.between(0, 300)).sum(), (S.s.between(-300, 0)).sum()) < 200:
                rows.append({"design": f"B {lab} {name}", "note": "fewer than 200 lots a side within 300 m: not run"})
                continue
            S["cl"] = pd.factorize(S.cl)[0]
            rows += estimate(S, "s", S.cl.to_numpy(), f"B {lab} {name}", first_stage=True)
    return rows


def estimate(S: pd.DataFrame, s: str, cl: np.ndarray, design: str, first_stage: bool) -> list[dict]:
    rng = np.random.default_rng(SEED)
    ncl = cl.max() + 1
    W = rng.multinomial(ncl, np.full(ncl, 1 / ncl), size=DRAWS).astype(float)
    h_ik, h_raw = ik_bandwidth(S[s].to_numpy(), S.y.to_numpy(), S.acres_land.to_numpy())
    rows = []
    for hl, h in [(f"IK {h_ik:.0f} m (main)", h_ik)] + list(H_FIXED.items()):
        rec = {"design": design, "bandwidth": hl, "h_m": h, "ik_unclipped_m": h_raw, "clusters": int(ncl)}
        for ycol, lab in (("y", "jump"), ("y_before", "balance_before_rate"), ("log_land_value_per_acre", "balance_log_land_value"),
                          ("log_acres", "balance_log_lot_size"), ("existing_per_acre", "balance_existing_homes_per_acre")) + \
                         ((("bonus", "first_stage_bonus_points"),) if first_stage else ()):
            e, d, ni, no = rd(S, s, ycol, h, cl, ncl, W)
            rec[lab], rec[f"{lab}_lo90"], rec[f"{lab}_hi90"] = e, np.nanpercentile(d, 5), np.nanpercentile(d, 95)
            if lab == "jump":
                rec["lots_inside"], rec["lots_outside"] = ni, no
                ed, dd, *_ = rd(S, s, "y", h, cl, ncl, W, DONUT)
                rec["jump_donut25"], rec["jump_donut25_lo90"], rec["jump_donut25_hi90"] = ed, np.nanpercentile(dd, 5), np.nanpercentile(dd, 95)
                er, dr = ratio(S, s, h, cl, ncl, W)
                rec["jump_ratio_of_sums"], rec["jump_ratio_lo90"], rec["jump_ratio_hi90"] = er, np.nanpercentile(dr, 5), np.nanpercentile(dr, 95)
                jd = d
            if lab == "first_stage_bonus_points":
                with np.errstate(divide="ignore", invalid="ignore"):
                    fr = 10 * jd / d
                rec["fuzzy_per_10_bonus_points"] = 10 * rec["jump"] / e if e else np.nan
                rec["fuzzy_lo90"], rec["fuzzy_hi90"] = np.nanpercentile(fr, 5), np.nanpercentile(fr, 95)
        rec["balance_pass"] = bool(rec["balance_before_rate_lo90"] <= 0 <= rec["balance_before_rate_hi90"])
        rec["descriptive_flags"] = "; ".join(b for b in ("balance_log_land_value", "balance_log_lot_size", "balance_existing_homes_per_acre")
                                             if not (rec[f"{b}_lo90"] <= 0 <= rec[f"{b}_hi90"]))
        rows.append(rec)
        print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in rec.items()
               if k in ("design", "bandwidth", "lots_inside", "lots_outside", "jump", "jump_lo90", "jump_hi90", "balance_pass",
                        "balance_before_rate", "jump_donut25", "first_stage_bonus_points", "fuzzy_per_10_bonus_points")}, flush=True)
    return rows


def main() -> None:
    D = lots()
    print("LA city lots:", len(D), "by tier:", D.tier.value_counts().sort_index().to_dict(), flush=True)
    R = pd.DataFrame(design_a(D) + design_b(D))
    main_a = R[R.design.str.startswith("A") & R.bandwidth.str.startswith("IK", na=False)]
    passing = main_a[main_a.balance_pass & (np.sign(main_a.jump) == np.sign(main_a.jump_donut25))]
    R = pd.concat([R, pd.DataFrame([{"design": "USE rule", "note": (
        f"{len(passing)} of {len(main_a)} map-edge cutoffs pass balance with a same-sign donut: "
        + ("dose evidence usable" if len(passing) else "not usable as dose evidence")
        + (" (" + "; ".join(f"{d} {j:+.1f}" for d, j in zip(passing.design, passing.jump)) + ")" if len(passing) else ""))}])],
        ignore_index=True)
    R.round(4).to_csv(REFERENCE / "tod_causal_la_toc_rd.csv", index=False)
    print(R.iloc[-1].note)


if __name__ == "__main__":
    main()
