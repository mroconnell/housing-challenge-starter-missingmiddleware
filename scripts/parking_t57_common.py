"""Test 57 (docs/parking/CAUSAL_FRAMEWORK_PLAN.md, Test 57 and every later block up to the LOCK of 2026-11-12
06:08 UTC): run definitions, the estimator, ranges, MDE and the reading rules. Pure functions on a panel table, so
every piece is checked on made-up data (tests/test_parking_t57.py) before any real panel exists.

Panel (one table per run, built by build_parking_t57_ny_panel.py / build_parking_t57_sf_panel.py):
    cluster  int   500 m grid cell (NY) or SF resampling unit; a cell split by the line is ONE cluster
    arm      str   "T" (treated: inside the 2016 Transit Zone / SF wave A) or "C" (not-yet-treated comparison)
    year     int   calendar year (filing year NY DOB; project start year HPD; issue year SF)
    units    float homes in the outcome (new-building units; HPD income-restricted units; SF new-construction units)
    jobs     int   records with units > 0 (DOB jobs, HPD buildings, SF permits) - used only for "too few to read"
    acres    float eligible lot acres of that cluster's part in that arm in that year (MIH lots leave from adoption)
A (cluster, arm) pair is a "cell part" (the plan's "cell"); parts with no eligible acres are not cells.

Estimator (plan "Measures"; TOD's measure, missing_middleware/tod/cases.py):
- Rate of an arm in a year = 100 x (sum of units) / (sum of eligible acres) over the arm's cell parts: homes per 100
  eligible lot acres a year (acre-weighted, so the arm is one pooled area, as in TOD's cases).
- Main effect (difference in differences) = (mean yearly T rate after - mean yearly T rate before)
  - (same for C). Year 0 (the wave year) is shown in the event study but not used in the before/after means (TOD's
  rule, and the plan's SF "after-years from 2009").
- Event study: year k effect = (T rate in k - T rate in -1) - (C rate in k - C rate in -1); reference year -1.
- Placebo date (fake wave k years earlier, k in PLACEBO_K): the same contrast with the fake year as year 0; its before
  window is the 5 years before the fake year (cut at the panel's first year) and its after-window ends the year
  before the real wave (the not-yet-treated rule: no arm is treated inside it).
- 90% range: 5th and 95th percentiles of DRAWS cluster-bootstrap draws (whole clusters drawn with replacement, so
  both parts of a split cell move together), seed SEED. Every cell of a run uses the same draws.
- Counts (plan "Reading"): a range excludes 0 when p05 > 0 or p95 < 0.
- MDE (90% two-sided test, 80% power, as Test 56): (1.6449 + 0.8416) x the standard deviation of the run's
  bootstrap draws of the main effect. Only the spread is written; no centre or percentile of the main effect.
- "Too few to read" (audit fix 8): fewer than 20 cell parts in either arm, or fewer than 30 jobs in either arm in the
  before-window.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

SEED, DRAWS, LEVEL = 20261105, 2000, 0.90
Z_MDE = 1.6449 + 0.8416
SCALE = 100.0                      # per 100 eligible lot acres
MIN_CELLS, MIN_JOBS = 20, 30       # "too few to read" (audit fix 8)
PLACEBO_K = (3, 4)                 # see RUN NOTES in docs/parking/T57_CODE_NOTES.md (plan: "3 years earlier"; addendum 2: "the -4 placebo"; lock: "both placebo dates")
UNIT = "homes per 100 eligible lot acres a year"

DILUTED = ("possibly diluted toward 0: the 2016 rule removed parking only for income-restricted units and affordable "
           "senior residences (ZR 25-251, 25-252); market-rate minimums did not change")
DOB_SWITCH = ("no seam: legacy filings at any date plus DOB NOW (from 2021-03-03), ALT-CO left out; the whole-city level "
              "drop at the March 2021 DOB NOW switch falls on both arms")
RUSH = "421-a rushes: before mid-2015 (2015 = year -1, the reference year) and before June 2022 (year +6)"
ZQA_ENV = "ZQA building-envelope changes (2016-03-22) are citywide, so on both arms"
MIH_DROP = "MIH-mapped lots dropped from both arms from each area's adoption date (primary MIH rule)"
MIH_KEEP = "bundled with MIH (MIH-mapped lots kept)"
HPD_NOTE = ("HPD affordable units (hg8x-zxpr), new construction, by project start year: before-years 2014-2015 only, so "
            "only lead -2 against -1 runs; no -5 to -3 leads and no placebo; 2015 is a 421-a rush year; only "
            "HPD-financed projects; no senior flag")
SF_NOTE = ("San Francisco is a case, not a headline cell; parking plus upzoning, not separable; Ord. 112-08 "
           "(2008-07-31; affordable and senior minimums to 0 citywide) is bundled with wave A's start year; the 2008-09 "
           "recession falls in the early after-years; measure: permits ISSUED")


@dataclass(frozen=True)
class Run:
    key: str
    city: str
    outcome: str
    wave_year: int
    before: tuple
    after: tuple
    leads: tuple                    # leads shown and read (pre-trend)
    placebo_k: tuple
    headline: bool = False
    measure: str = ""
    labels: tuple = field(default_factory=tuple)

    @property
    def lags(self) -> tuple:        # event years shown after the wave: 0 to the end of the after-window
        return tuple(range(0, self.after[-1] - self.wave_year + 1))

    @property
    def es_years(self) -> tuple:
        return tuple(self.leads) + self.lags

    def placebo(self, k: int, first_year: int) -> tuple[int, tuple, tuple]:
        f = self.wave_year - k
        return f, tuple(y for y in range(f - 5, f) if y >= first_year), tuple(range(f + 1, self.wave_year))

    @property
    def n_cells(self) -> int:
        return 1 + len(self.es_years) + len(self.placebo_k)


NY_B, NY_A = tuple(range(2011, 2016)), tuple(range(2017, 2024))
NY_DOB_LAB = (DILUTED, DOB_SWITCH, RUSH, ZQA_ENV)
RUNS: dict[str, Run] = {r.key: r for r in [
    Run("ny_dob", "New York", "all DOB new-building units (legacy + DOB NOW)", 2016, NY_B, NY_A, (-5, -4, -3, -2), PLACEBO_K,
        headline=True, measure="jobs FILED", labels=NY_DOB_LAB + (MIH_DROP,)),
    Run("ny_dob_keepmih", "New York", "all DOB new-building units (legacy + DOB NOW)", 2016, NY_B, NY_A, (-5, -4, -3, -2),
        PLACEBO_K, measure="jobs FILED", labels=NY_DOB_LAB + (MIH_KEEP,)),
    Run("ny_dob_samezone", "New York", "all DOB new-building units (legacy + DOB NOW)", 2016, NY_B, NY_A, (-5, -4, -3, -2),
        PLACEBO_K, measure="jobs FILED",
        labels=NY_DOB_LAB + (MIH_DROP, "pre-set sensitivity 1: same-zoning edge (lots whose nearest land-line point has the "
                                       "same modal zoning district on both sides)")),
    Run("ny_dob_legacy2020", "New York", "DOB new-building units, legacy file only", 2016, NY_B, tuple(range(2017, 2021)),
        (-5, -4, -3, -2), PLACEBO_K, measure="jobs FILED",
        labels=(DILUTED, RUSH, ZQA_ENV, MIH_DROP, "pre-set sensitivity 2: legacy-only window, after-window ends 2020 "
                                                  "(the March 2021 system switch is outside the window)")),
    Run("ny_hpd", "New York", "HPD affordable units (alongside, not headline)", 2016, (2014, 2015), NY_A, (-2,), (),
        measure="projects STARTED", labels=(HPD_NOTE, RUSH, ZQA_ENV, MIH_DROP)),
    Run("ny_hpd_keepmih", "New York", "HPD affordable units (alongside, not headline)", 2016, (2014, 2015), NY_A, (-2,), (),
        measure="projects STARTED", labels=(HPD_NOTE, RUSH, ZQA_ENV, MIH_KEEP)),
    Run("sf_a", "San Francisco", "new-construction units, permits issued (case)", 2008, tuple(range(2003, 2008)),
        tuple(range(2009, 2019)), (-5, -4, -3, -2), PLACEBO_K, measure="permits ISSUED", labels=(SF_NOTE,)),
]}
FIRST_YEAR = {"New York": 2007, "San Francisco": 2003}     # first panel year (NY: the -4 placebo's before-window)
N_CELLS = sum(r.n_cells for r in RUNS.values())


# ------------------------------------------------------------------------------------------------ panel arrays
@dataclass
class Arrays:
    clusters: np.ndarray            # cluster ids, length n
    years: np.ndarray               # panel years
    U: dict                         # arm -> (n, years) units by cluster
    A: dict                         # arm -> (n, years) eligible acres by cluster
    J: dict                         # arm -> (n, years) jobs by cluster
    parts: dict                     # arm -> number of cell parts (clusters with acres > 0 in that arm)


def arrays(panel: pd.DataFrame, years) -> Arrays:
    years = np.asarray(sorted(years))
    p = panel[panel["year"].isin(years)]
    cl = np.sort(panel["cluster"].unique())
    U, A, J, parts = {}, {}, {}, {}
    for arm in ("T", "C"):
        q = p[p["arm"] == arm]
        piv = lambda c: (q.pivot_table(index="cluster", columns="year", values=c, aggfunc="sum")  # noqa: E731
                         .reindex(index=cl, columns=years).fillna(0.0).to_numpy(float))
        U[arm], A[arm], J[arm] = piv("units"), piv("acres"), piv("jobs")
        parts[arm] = int((A[arm].sum(1) > 0).sum())
    return Arrays(cl, years, U, A, J, parts)


def boot_weights(n: int, draws: int = DRAWS, seed: int = SEED) -> np.ndarray:
    """(draws, n) counts: how often each cluster is drawn in each resample of n clusters with replacement."""
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(draws, n))
    W = np.zeros((draws, n))
    np.add.at(W, (np.repeat(np.arange(draws), n), idx.ravel()), 1.0)
    return W


def rates(W: np.ndarray, ar: Arrays, arm: str) -> np.ndarray:
    """(k, years) arm rates per 100 eligible acres for k weightings of the clusters (a row of ones = the estimate)."""
    with np.errstate(invalid="ignore", divide="ignore"):
        r = SCALE * (W @ ar.U[arm]) / (W @ ar.A[arm])
    r[~np.isfinite(r)] = np.nan
    return r


def _cols(ar: Arrays, yrs) -> np.ndarray:
    pos = {int(y): i for i, y in enumerate(ar.years)}
    return np.array([pos[int(y)] for y in yrs], int)


def did(rT: np.ndarray, rC: np.ndarray, ar: Arrays, before, after) -> np.ndarray:
    b, a = _cols(ar, before), _cols(ar, after)
    return (rT[:, a].mean(1) - rT[:, b].mean(1)) - (rC[:, a].mean(1) - rC[:, b].mean(1))


def es(rT: np.ndarray, rC: np.ndarray, ar: Arrays, year: int, ref: int) -> np.ndarray:
    t, r = _cols(ar, [year])[0], _cols(ar, [ref])[0]
    return (rT[:, t] - rT[:, r]) - (rC[:, t] - rC[:, r])


def summarise_draws(est: float, d: np.ndarray) -> dict:
    ok = np.isfinite(d)
    lo, hi = (np.quantile(d[ok], [(1 - LEVEL) / 2, 1 - (1 - LEVEL) / 2]) if ok.any() else (np.nan, np.nan))
    return dict(estimate=float(est), p05=float(lo), p95=float(hi), excludes_0=bool(lo > 0 or hi < 0),
                draws_used=int(ok.sum()))


# ------------------------------------------------------------------------------------------------ step 1 (no effect)
def counts(run: Run, panel: pd.DataFrame) -> dict:
    """Cell parts and clusters per arm, before-window jobs per arm, eligible acres per arm (first before year), and
    the too-few flag. Reads only the before-window jobs (the plan's rule needs them); no after-window number."""
    yrs = sorted(set(run.before) | set(run.after) | {run.wave_year})
    ar = arrays(panel, yrs)
    b = _cols(ar, run.before)
    jb = {arm: int(ar.J[arm][:, b].sum()) for arm in ("T", "C")}
    split = int(((ar.A["T"].sum(1) > 0) & (ar.A["C"].sum(1) > 0)).sum())
    few = min(ar.parts.values()) < MIN_CELLS or min(jb.values()) < MIN_JOBS
    return dict(run=run.key, city=run.city, outcome=run.outcome, measure=run.measure, headline=run.headline,
                cell_parts_T=ar.parts["T"], cell_parts_C=ar.parts["C"], clusters=len(ar.clusters), split_clusters=split,
                before_window=f"{run.before[0]}-{run.before[-1]}", before_jobs_T=jb["T"], before_jobs_C=jb["C"],
                eligible_acres_T_first_before_year=round(float(ar.A["T"][:, b[0]].sum()), 1),
                eligible_acres_C_first_before_year=round(float(ar.A["C"][:, b[0]].sum()), 1),
                too_few_to_read=bool(few),
                rule=f"fewer than {MIN_CELLS} cell parts per arm, or fewer than {MIN_JOBS} jobs per arm in the before-window")


def mde(run: Run, panel: pd.DataFrame) -> dict:
    """MDE of the main effect from the spread of its bootstrap draws. The estimate and percentiles are not computed."""
    yrs = sorted(set(run.before) | set(run.after))
    ar = arrays(panel, yrs)
    W = boot_weights(len(ar.clusters))
    d = did(rates(W, ar, "T"), rates(W, ar, "C"), ar, run.before, run.after)
    sd = float(np.nanstd(d, ddof=1))
    return dict(run=run.key, statistic="main effect (difference in differences)", bootstrap_sd=sd, mde=Z_MDE * sd,
                draws_used=int(np.isfinite(d).sum()), unit=UNIT,
                note="MDE = 2.486 x SD of the cluster-bootstrap draws (90% two-sided, 80% power); no centre read")


# ------------------------------------------------------------------------------------------------ step 2 (all cells)
def cells(run: Run, panel: pd.DataFrame, first_year: int) -> list[dict]:
    plac = [run.placebo(k, first_year) for k in run.placebo_k]
    yrs = sorted(set(run.before) | set(run.after) | set(run.wave_year + k for k in run.es_years) | {run.wave_year - 1}
                 | {y for f, b, a in plac for y in (*b, *a, f)})
    ar = arrays(panel, yrs)
    ones = np.ones((1, len(ar.clusters)))
    W = boot_weights(len(ar.clusters))
    eT, eC, bT, bC = rates(ones, ar, "T"), rates(ones, ar, "C"), rates(W, ar, "T"), rates(W, ar, "C")
    base = dict(run=run.key, city=run.city, outcome=run.outcome, measure=run.measure, headline_run=run.headline,
                unit=UNIT, labels=" | ".join(run.labels))
    out = []
    est = did(eT, eC, ar, run.before, run.after)[0]
    m = lambda r, ys: float(np.nanmean(r[0, _cols(ar, ys)]))  # noqa: E731
    out.append(dict(base, cell=f"{run.key}:main", kind="main effect", event_year=np.nan,
                    window=f"before {run.before[0]}-{run.before[-1]}; after {run.after[0]}-{run.after[-1]}; year 0 ({run.wave_year}) not used",
                    headline=run.headline, treat_before=m(eT, run.before), treat_after=m(eT, run.after),
                    comp_before=m(eC, run.before), comp_after=m(eC, run.after),
                    **summarise_draws(est, did(bT, bC, ar, run.before, run.after))))
    ref = run.wave_year - 1
    for k in run.es_years:
        y = run.wave_year + k
        kind = "event study lead" if k < 0 else "event study lag"
        out.append(dict(base, cell=f"{run.key}:es{k:+d}", kind=kind, event_year=k, window=f"year {y} vs {ref} (reference -1)",
                        headline=False, in_plan_window=bool(-5 <= k <= 3),
                        **summarise_draws(es(eT, eC, ar, y, ref)[0], es(bT, bC, ar, y, ref))))
    for k, (f, b, a) in zip(run.placebo_k, plac):
        out.append(dict(base, cell=f"{run.key}:placebo-{k}", kind="placebo date", event_year=-k,
                        window=f"fake wave {f}: before {b[0]}-{b[-1]} ({len(b)} years); after {a[0]}-{a[-1]}; year {f} not used",
                        headline=False, **summarise_draws(did(eT, eC, ar, b, a)[0], did(bT, bC, ar, b, a))))
    assert len(out) == run.n_cells, (run.key, len(out), run.n_cells)
    return out


def reading(cells_df: pd.DataFrame, counts_df: pd.DataFrame, mde_df: pd.DataFrame) -> pd.DataFrame:
    """The lock's reading rules, applied mechanically to each run (same bar for either sign)."""
    rows = []
    for key, run in RUNS.items():
        c = cells_df[cells_df["run"] == key]
        main = c[c["kind"] == "main effect"].iloc[0]
        leads = c[(c["kind"] == "event study lead") & c["event_year"].isin(run.leads)]
        pls = c[c["kind"] == "placebo date"]
        few = bool(counts_df.set_index("run").loc[key, "too_few_to_read"])
        lead_x = [int(k) for k in leads.loc[leads["excludes_0"], "event_year"]]
        pl_x = [int(-k) for k in pls.loc[pls["excludes_0"], "event_year"]]
        pre = bool(lead_x or pl_x)
        sign = "" if not main["excludes_0"] else ("above 0" if main["p05"] > 0 else "below 0")
        if few:
            verdict = "too few to read"
        elif pre:
            verdict = "pre-trend, not read as an effect"
        elif main["excludes_0"]:
            verdict = f"counts: 90% range excludes 0 ({sign})"
        else:
            verdict = "does not count: 90% range includes 0"
        rows.append(dict(run=key, city=run.city, outcome=run.outcome, headline=run.headline,
                         role="HEADLINE (the only headline cell)" if run.headline else
                         ("case (not headline)" if run.city == "San Francisco" else "alongside / sensitivity (not headline)"),
                         too_few_to_read=few, leads_read=",".join(f"{k:+d}" for k in run.leads),
                         leads_excluding_0=",".join(f"{k:+d}" for k in lead_x),
                         placebo_dates_read=",".join(f"-{k}" for k in run.placebo_k) or "none (cannot run)",
                         placebo_dates_excluding_0=",".join(f"-{k}" for k in pl_x), pre_trend=pre,
                         main_excludes_0=bool(main["excludes_0"]), main_sign=sign,
                         mde=float(mde_df.set_index("run").loc[key, "mde"]), reading=verdict,
                         labels=" | ".join(run.labels)))
    r = pd.DataFrame(rows)
    hl = r[r["headline"]]
    assert len(hl) == 1
    r.attrs["chance"] = ("1 headline cell (NY 2016, all DOB new-building units). With 1 cell at the 90% level, a range "
                         "excluding 0 by chance happens about 1 time in 10.")
    return r
