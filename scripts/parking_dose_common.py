"""Parking dose-response (docs/parking/DOSE_PLAN.md, with "Ryan's choices", "C11 amended" and "Audit fixes", which
override the text above them): shared pieces for scripts/run_parking_dose_effects.py and scripts/run_parking_dose.py.
Pure functions and file checks; nothing here reads a permit file. See docs/parking/DOSE_CODE_NOTES.md.

- The dose freeze (audit fix 6): reference/parking_doses.csv must hash to the FIRST sha256 recorded for it in
  docs/parking/DOSES_BUILT.md, and both files must be committed and unchanged; otherwise nothing runs.
- Which reforms are pooled, which are reported alone, which wait for a fact (C7, C8, C9 and plan section 5).
- The estimator: beta = sum(w d e) / sum(w d^2) through the origin (main: homes x after-years; D: target-state mix,
  effects winsorised 5/95 over the fit's places, exactly as run_parking_method2.weighted_avg), the intercept fit, the
  placebo-set version (each stand-in takes its real place's dose) and the place bootstrap.
"""
from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DOSES = ROOT / "reference" / "parking_doses.csv"
DOSES_DOC = ROOT / "docs" / "parking" / "DOSES_BUILT.md"
UNIVERSE = ROOT / "reference" / "parking_dose_universe.csv"
WORK = ROOT / "data" / "processed" / "dose"

OUTCOMES = ("all_homes", "units_2_4")  # all_homes: MM_BPS_OUTCOME unset (the batch's outcome)
METHODS = ("main", "D")
SEED, DRAWS = 20261105, 2000          # D place bootstrap (plan); also the lead bootstrap (Test 56 event study)
SEED_M2 = 20261104                    # run_parking_method2 SEED: used only to reproduce its D range in the identity check
PL_SEED, PL_SETS = 20261027 + 1, 20_000  # run_parking_placebo.py --full set draws (SEED + 1), 20,000 sets
Z_MDE = 1.6449 + 0.8416               # 2.486: 90% two-sided test, 80% power
MIX = "target-state mix"
LEADS = (-5, -4, -3, -2)
SHIFTS = (2, 4)

# Identity targets (audit fix 7): today's averages with all 74 places at dose 100. Main all homes: batch 2026-11-05
# parking_placebo_full_summary real_average; D all homes: batch parking_method2_corrected_results "method 2, D",
# target-state mix; 2-4 units: reference/parking_t56_cells.csv H1 (main) and H7 (D). All are rounded to 4 places.
IDENTITY = {("all_homes", "main"): -1.1526, ("all_homes", "D"): -0.9647,
            ("units_2_4", "main"): -0.0674, ("units_2_4", "D"): -0.0068}
TOL_HARD = 1.0e-4      # vs the 4-place figures above (rounding 5e-5, plus D's 4-place place effects)
TOL_RANGE = 2.0e-3     # range rebuilt from stand-in effects saved to 4 places (Test 56 draw_rebuild_max_diff)

# Pool membership of the reforms that are not in the 74 (plan section 5 and Ryan's choices). Keyed by reform_id.
ALONE = {"oth_seabrook_2019": "dose-0 check (non-residential only)",
         "oth_brainerd_2023": "C7: added minimums; reported alone, not pooled"}
WAIT = {  # conditional or unsure in plan section 5; not pooled until the fact is confirmed (no choice made by Ryan)
    "oth_albany_2017": "conditional: exemption date", "oth_bangor_2024": "conditional: effective date",
    "oth_binghamton_2024": "conditional: effective 2024 or 2025", "oth_north_canton_2023": "conditional: Main Street exemption new in 2023?",
    "oth_charlottesville_2024": "unsure: only after-year under litigation", "oth_eureka_2019": "unsure: staged steps",
    "oth_shoreline_2022": "unsure: may fail the optional-reduction screen", "oth_portland_2018": "unsure: parking detail unknown",
    "oth_honolulu_2017": "unsure: parking change not verified",
}
KEPT_FLAGGED = {"oth_central_falls_2022": "C8: reversed in 2025, kept and flagged; after-years 2023-2024 only"}
POST_END = {"oth_central_falls_2022": 2024}  # last after-year (plan 11.2: "after-years 2023-2024 only")
STAGED = {("Spokane", "Washington"), ("Pomona", "California")}  # C9: event_used picks one row of each
# the 24 "clearly eligible" new places of plan section 5 (C9 decides Spokane 2023 vs 2024 and Pomona 2019 vs 2024)
PLAN_24 = {"oth_chicago_2015", "oth_san_diego_2019", "oth_albuquerque_2018", "oth_penndel_2020", "oth_somerville_2019",
           "oth_madison_2023", "oth_denver_2018", "oth_bakersfield_2024", "oth_covington_2020", "oth_columbia_2021",
           "oth_fremont_2015", "oth_camden_2021", "oth_waukegan_2024", "oth_watertown_2023", "oth_bloomsburg_2024",
           "oth_lewisburg_2023", "oth_boise_2023", "oth_tulsa_2024", "oth_maumee_2020", "oth_dover_2015",
           "oth_jackson_2021", "oth_norman_2021"}  # + one Spokane row + one Pomona row = 24
N_NEW_POOLED = 25  # 24 + Central Falls (C8)
C6_PLACES = {("Canandaigua", "New York"), ("Plainfield", "Indiana"), ("Cambridge", "Maryland"), ("Branson", "Missouri"),
             ("Trenton", "New Jersey"), ("Duluth", "Minnesota")}
MAPPED_TYPES = ("TOD/transit area", "district", "commercial-only")  # audit fix 5 (2010 blocks): mapped reforms


# ------------------------------------------------------------------ freeze -------------------------------------------
def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def frozen_hash(doc: Path = DOSES_DOC) -> str:
    """The first sha256 recorded for parking_doses.csv in DOSES_BUILT.md (later ones would be sensitivities)."""
    if not Path(doc).exists():
        raise SystemExit(f"dose freeze: {doc} does not exist (commit the dose table and its sha256 first, audit fix 6)")
    for line in Path(doc).read_text().splitlines():
        if "parking_doses.csv" in line or "sha256" in line.lower():
            h = re.findall(r"\b[0-9a-f]{64}\b", line)
            if h:
                return h[0]
    raise SystemExit(f"dose freeze: no sha256 for parking_doses.csv found in {doc}")


def committed(path: Path, root: Path = ROOT) -> bool:
    r = subprocess.run(["git", "ls-files", "--error-unmatch", str(path)], cwd=root, capture_output=True)
    d = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", str(path)], cwd=root, capture_output=True)
    return r.returncode == 0 and d.returncode == 0


def require_frozen_doses(doses: Path = DOSES, doc: Path = DOSES_DOC, check_git: bool = True) -> str:
    """Refuse to run unless the dose table matches the frozen hash (and, for real runs, both files are committed)."""
    if not Path(doses).exists():
        raise SystemExit(f"dose freeze: {doses} does not exist")
    want, got = frozen_hash(doc), sha256(doses)
    if got != want:
        raise SystemExit(f"dose freeze: sha256({doses}) = {got} differs from the frozen {want} in {doc}")
    if check_git and not (committed(doses) and committed(doc)):
        raise SystemExit("dose freeze: commit reference/parking_doses.csv and docs/parking/DOSES_BUILT.md unchanged first")
    return got


# ------------------------------------------------------------------ dose table ---------------------------------------
def _yes(v) -> bool:
    return str(v).strip().lower() in ("yes", "true", "1", "y")


def _num(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return np.nan


def norm_place(s: str) -> str:
    s = re.sub(r"\s*\(.*\)$", "", str(s)).strip().lower()  # "South Bend (with unincorporated ...)" -> "south bend"
    return s


def main74(universe: Path = UNIVERSE) -> pd.DataFrame:
    """The 74 places' reform_ids (universe rows marked in_main_74) with a match key place|state|year."""
    u = pd.read_csv(universe, dtype=str)
    u = u[u["in_main_74"].str.strip().str.lower() == "yes"].copy()
    u["m"] = u["place"].map(norm_place) + "|" + u["state"].str.strip() + "|" + u["year"].map(lambda y: str(int(float(y))))
    assert len(u) == 74 and u["m"].is_unique, (len(u), u["m"].duplicated().sum())
    return u[["reform_id", "place", "state", "year", "m"]]


def match74(real: pd.DataFrame, universe: Path = UNIVERSE) -> list[str]:
    """reform_id for each of the 74 rows of parking_expanded_effects (batch order)."""
    u = main74(universe).set_index("m")["reform_id"]
    m = real["place"].map(norm_place) + "|" + real["state"].str.strip() + "|" + real["event_year"].map(lambda y: str(int(float(y))))
    miss = sorted(set(m) - set(u.index))
    if miss:
        raise SystemExit(f"the 74 places do not all match parking_dose_universe.csv: {miss}")
    return list(m.map(u))


def load_doses(path: Path = DOSES, universe: Path = UNIVERSE) -> pd.DataFrame:
    """Dose table with d_all / d_24 as shares (0-1), flags, and each reform's role:
    '74' (in the 74), 'pooled' (new, pooled), 'alone' (C7 / dose-0 check), 'wait' (conditional or unsure),
    'not used' (event_used = no, C9), 'dose 0' (a new place whose frozen dose is 0: reported with the alone group)."""
    t = pd.read_csv(path, dtype=str).fillna("")
    for c in ("reform_id", "place", "state", "event_year", "dose", "dose_source"):
        if c not in t.columns:
            raise SystemExit(f"{path}: column {c} missing")
    assert t["reform_id"].is_unique, "reform_id repeated in the dose table"
    ids74 = set(main74(universe)["reform_id"])
    miss = ids74 - set(t["reform_id"])
    if miss:
        raise SystemExit(f"dose table lacks {len(miss)} of the 74: {sorted(miss)[:5]}")
    t["dose_num"] = t["dose"].map(_num)
    if t["dose_num"].isna().any():
        raise SystemExit(f"dose table: no dose for {list(t.loc[t['dose_num'].isna(), 'reform_id'])}")
    if ((t["dose_num"] < 0) | (t["dose_num"] > 100)).any():
        raise SystemExit("dose table: a dose outside 0-100 (plan section 2 caps doses at 0-100)")
    t["d_all"] = t["dose_num"] / 100
    has24 = "dose_units_2_4" in t.columns
    d24 = t["dose_units_2_4"].map(_num) if has24 else pd.Series(np.nan, index=t.index)
    t["d_24"] = np.where(np.isfinite(d24), d24 / 100, t["d_all"])
    t["d_24_source"] = np.where(np.isfinite(d24), "dose_units_2_4 column", "all-homes dose (no 2-4 dose given)")
    t["fallback"] = t["dose_source"].str.strip().str.lower().eq("fallback")
    t["placeholder"] = t.get("fallback_class", pd.Series("", index=t.index)).str.contains("PLACEHOLDER") | \
        t.get("notes", pd.Series("", index=t.index)).str.contains("C3 PLACEHOLDER")
    t["event_used_yes"] = t["event_used"].map(_yes) if "event_used" in t.columns else True
    t["year_num"] = t["event_year"].map(lambda v: int(float(v)) if str(v).strip() else -1)
    role, why = [], []
    for r in t.itertuples():
        if r.reform_id in ids74:
            role.append("74"), why.append("")
        elif not r.event_used_yes:
            role.append("not used"), why.append("C9: the other step of a two-step reform is the event")
        elif r.reform_id in ALONE:
            role.append("alone"), why.append(ALONE[r.reform_id])
        elif r.reform_id in WAIT:
            role.append("wait"), why.append(WAIT[r.reform_id])
        elif r.dose_num == 0:
            role.append("dose 0"), why.append("frozen dose 0: reported with the dose-0 places, not pooled")
        else:
            role.append("pooled"), why.append(KEPT_FLAGGED.get(r.reform_id, ""))
    t["role"], t["role_note"] = role, why
    return t


def check_pooled(t: pd.DataFrame) -> None:
    """Exact pooled set: the plan's 24 (one Spokane row and one Pomona row, by event_used) + Central Falls (C8)."""
    new = t[t["role"] == "pooled"]
    for place, state in STAGED:
        n = int(((new["place"] == place) & (new["state"] == state)).sum())
        if n != 1:
            raise SystemExit(f"C9: {place}, {state} has {n} pooled events; set event_used = no on all but its first step")
    extra = set(new["reform_id"]) - PLAN_24 - set(KEPT_FLAGGED) - {r for r in new["reform_id"] if r.startswith(("oth_spokane_", "oth_pomona_"))}
    missing = (PLAN_24 | set(KEPT_FLAGGED)) - set(new["reform_id"])
    if extra or missing or len(new) != N_NEW_POOLED:
        raise SystemExit(f"pooled new places: {len(new)} (want {N_NEW_POOLED}); unexpected {sorted(extra)}; missing {sorted(missing)}")


# ------------------------------------------------------------------ estimator ----------------------------------------
def beta(e, d, w) -> float:
    """sum(w d e) / sum(w d^2) over finite rows with w > 0."""
    e, d, w = (np.asarray(x, float) for x in (e, d, w))
    ok = np.isfinite(e) & np.isfinite(d) & np.isfinite(w) & (w > 0)
    den = np.sum(w[ok] * d[ok] ** 2)
    return float(np.sum(w[ok] * d[ok] * e[ok]) / den) if den > 0 else np.nan


def wls_line(e, d, w) -> tuple[float, float]:
    """Weighted least squares e = a + b d. Returns (a, b): a = effect at dose 0, b = change per 100 dose points."""
    e, d, w = (np.asarray(x, float) for x in (e, d, w))
    ok = np.isfinite(e) & np.isfinite(d) & np.isfinite(w) & (w > 0)
    e, d, w = e[ok], d[ok], w[ok]
    if len(e) < 2 or w.sum() <= 0:
        return np.nan, np.nan
    dm, em = np.average(d, weights=w), np.average(e, weights=w)
    sxx = np.sum(w * (d - dm) ** 2)
    if sxx <= 0:
        return np.nan, np.nan
    b = float(np.sum(w * (d - dm) * (e - em)) / sxx)
    return float(em - b * dm), b


def set_betas(E: np.ndarray, W: np.ndarray, d: np.ndarray, mask=None) -> np.ndarray:
    """Through-origin beta for each placebo set (rows of E, W; columns = real places that have stand-ins, each with its
    real place's dose d). mask limits the columns (a dose group)."""
    sel = np.ones(E.shape[1], bool) if mask is None else np.asarray(mask, bool)
    Ws, Es, ds = W[:, sel], E[:, sel], d[sel]
    return (Ws * ds * Es).sum(axis=1) / (Ws * ds ** 2).sum(axis=1)


def set_lines(E: np.ndarray, W: np.ndarray, d: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Intercept and slope of the weighted line for each placebo set."""
    dm = (W * d).sum(axis=1) / W.sum(axis=1)
    em = (W * E).sum(axis=1) / W.sum(axis=1)
    dd = d[None, :] - dm[:, None]
    b = (W * dd * (E - em[:, None])).sum(axis=1) / (W * dd ** 2).sum(axis=1)
    return em - b * dm, b


def placebo_range(real: float, draws: np.ndarray) -> tuple[float, float]:
    """Test 56 / run_parking_placebo: real + (p05 - p50, p95 - p50) of the placebo-set draws."""
    v = np.asarray(draws, float)
    v = v[np.isfinite(v)]
    if not len(v) or not np.isfinite(real):
        return np.nan, np.nan
    p05, p50, p95 = np.percentile(v, [5, 50, 95])
    return float(real + p05 - p50), float(real + p95 - p50)


def draw_matrix(st: pd.DataFrame, n_sets: int | None = None, seed: int | None = None):
    """run_parking_placebo.py --full set draws, rebuilt from saved stand-ins: columns in sorted `col` order, one
    rng.integers call per column in that order (so the 74's columns are identical to the saved draws whatever is
    appended after them). st: col, effect, weight. Returns (cols, E, W)."""
    s = st.dropna(subset=["effect", "weight"])
    s = s[s["weight"] > 0]
    groups = {i: g for i, g in s.groupby("col")}
    n_sets = PL_SETS if n_sets is None else n_sets
    rng = np.random.default_rng(PL_SEED if seed is None else seed)
    draws = np.column_stack([rng.integers(0, len(g), n_sets) for g in groups.values()])
    E = np.column_stack([g["effect"].values[draws[:, j]] for j, g in enumerate(groups.values())])
    W = np.column_stack([g["weight"].values[draws[:, j]] for j, g in enumerate(groups.values())])
    return np.array(list(groups)), E, W


# ---- method 2, D: target-state mix weights (run_parking_method2.mix_weights), winsorised effects ----
def _m2():
    import run_parking_method2 as m  # imported lazily: heavy module, pure functions used here
    return m


def d_point(y, d, ev: pd.DataFrame, wi: pd.Series, intercept: bool = False, wins: bool = True):
    """D estimate on the finite rows: effects winsorised 5/95 over those rows, mix weights over those rows (base =
    ev['base']); through the origin, or (a, b) with intercept=True. With all d = 1 this is
    run_parking_method2.weighted_avg('target-state mix', ...) exactly."""
    m = _m2()
    y, d = np.asarray(y, float), np.asarray(d, float)
    ok = np.isfinite(y) & np.isfinite(d)
    if ok.sum() == 0:
        return (np.nan, np.nan) if intercept else np.nan
    yy = m.winsor(y[ok]) if wins else y[ok]
    w, _ = m.mix_weights(ev[ok].reset_index(drop=True), wi)
    if intercept:
        return wls_line(yy, d[ok], w)
    return beta(yy, d[ok], w)


def boot(fn, n: int, seed: int = SEED, draws: int | None = None) -> np.ndarray:
    """Place bootstrap: fn(index array) for `draws` resamples of n places; non-finite draws dropped (method 2 rule)."""
    rng = np.random.default_rng(seed)
    out = np.array([fn(rng.integers(0, n, n)) for _ in range(DRAWS if draws is None else draws)], float)
    return out[np.isfinite(out)]


def pct_range(v) -> tuple[float, float]:
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    return (float(np.percentile(v, 5)), float(np.percentile(v, 95))) if len(v) else (np.nan, np.nan)


def excludes0(lo, hi) -> bool:
    return bool(np.isfinite(lo) and np.isfinite(hi) and (lo > 0 or hi < 0))


def verdict(lo, hi) -> str:
    """Reading of a range: 'includes 0', 'excludes 0, positive' or 'excludes 0, negative' (audit fix 4)."""
    if not (np.isfinite(lo) and np.isfinite(hi)):
        return "no range"
    if lo > 0:
        return "excludes 0, positive"
    if hi < 0:
        return "excludes 0, negative"
    return "includes 0"


def dose_bin(d: float) -> str:
    x = 100 * d
    if x >= 100:
        return "100"
    if x >= 50:
        return "50 to under 100"
    if x >= 25:
        return "25 to under 50"
    if x >= 10:
        return "10 to under 25"
    if x > 0:
        return "above 0, under 10"
    return "0"


DOSE_BINS = ("100", "50 to under 100", "25 to under 50", "10 to under 25", "above 0, under 10", "0")
