"""Test 56 (docs/parking/CAUSAL_FRAMEWORK_PLAN.md, "Test 56: one reading at lock"): shared pieces, imported by the
Test 56 scripts. No existing estimator is edited; these helpers patch at run time only.

- OUTCOMES: the Census BPS outcome runs (MM_BPS_OUTCOME values; see run_parking_comparison.outcome_swap).
- patch_method2(m): method 2's pre-event homes (the denominator, and the population scaling that picks D's pools) are
  rebuilt from ALL permits, so only the outcome changes, never the pools or the existing-homes count. Same rule as
  Test 52d's 1-unit run (run_parking_t52_placebos.use_one_unit_in_D). With MM_BPS_OUTCOME unset it changes nothing.
- patch_rebuild(t46): South Bend's combined-area scale (run_parking_t45_t46.rebuild divides by the place's effect)
  falls back to the salvage file's South Bend share of homes when that effect is exactly 0 (possible for a sparse
  outcome); identical otherwise.
- pop2010(...): 2010 census population exactly as Test 53 (scripts/run_parking_t53_area.py).
"""
from __future__ import annotations

import io
import os
import sys
import zipfile
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import run_parking_comparison as rpc  # noqa: E402
from missing_middleware.parking import comparison as cmp  # noqa: E402
from missing_middleware.paths import RAW  # noqa: E402

OUTCOMES = ("units_2_4", "1unit_units", "5plus_units", "units_2_4_rep")  # runs the lock needs (other _rep values work too)
SEED, DRAWS = 20261105, 2000
SPLIT = 25_000  # 2010 census population; convention fixed in the lock
SJ_KEY = "18|687500"


def all_homes_bps() -> pd.DataFrame:
    """rpc.read_bps_us() with the Test 56 outcome switch off (all permits)."""
    saved = os.environ.pop("MM_BPS_OUTCOME", None)
    try:
        return rpc.read_bps_us()
    finally:
        if saved is not None:
            os.environ["MM_BPS_OUTCOME"] = saved


def geo_table(bps: pd.DataFrame) -> pd.DataFrame:
    """Place table as in run_parking_method2.Data (panel plus South Bend's St. Joseph County row), last year kept."""
    p = cmp.panel(bps)
    sj = bps[(bps["state_fips"].astype(str).str.strip() == "18") & (bps["bps_id"].astype(str).str.strip() == "687500")].copy()
    sj["fips_place"] = "00001"
    p = pd.concat([p, cmp.panel(sj)], ignore_index=True)
    return p


def patch_method2(m) -> None:
    if getattr(m.Data, "_t56", False):
        return
    orig_init = m.Data.__init__

    def __init__(self):
        orig_init(self)
        if os.environ.get("MM_BPS_OUTCOME"):
            p = geo_table(all_homes_bps())
            P = p[p["year"].between(m.FIRST, m.LAST)].pivot_table(index="key", columns="year", values="units_total", aggfunc="sum")
            self.P_all = P.reindex(index=self.P.index, columns=self.P.columns)
            assert (self.P_all.notna() == self.P.notna()).all().all(), "outcome and all-permit panels differ in coverage"
        else:
            self.P_all = self.P

    @lru_cache(maxsize=None)
    def homes_pre(self, ey: int, fixed: bool = False) -> pd.Series:
        # as Data.homes_pre, but the permits subtracted are all permits whatever the outcome
        if fixed:
            return self.homes
        since = self.P_all[[y for y in self.P_all.columns if ey <= y <= 2024]].sum(axis=1).reindex(self.homes.index).fillna(0)
        return (self.homes - since).clip(lower=self.homes * 0.5)

    m.Data.__init__ = __init__
    m.Data.homes_pre = homes_pre
    m.Data._t56 = True


def patch_rebuild(t46) -> None:
    if getattr(t46, "_t56", False):
        return
    rps = t46.rps

    def rebuild(real: pd.DataFrame, calls: list[dict]) -> pd.DataFrame:
        by = {}
        for c in calls:
            by[(c["key"], c["event_year"])] = c
        out = []
        for r in real.itertuples():
            k = rps.SJ_KEY if r.source == "rescued" and str(r.place).startswith("South Bend") else r.key
            c = by.get((k, int(r.event_year)))
            if c is None:
                out.append(dict(i=r.Index, found=False))
                continue
            scale = 1.0
            if k == rps.SJ_KEY:
                if float(r.effect) != 0:
                    scale = float((r.rate_after - r.rate_before) - (r.ctrl_after - r.ctrl_before)) / float(r.effect)
                else:  # Test 56 fallback: the combined area's effect is 0, so the ratio is undefined
                    s = pd.read_csv(t46.REFERENCE / "parking_salvage_effects.csv")
                    scale = float(s.loc[s["key"] == rps.SJ_KEY, "south_bend_share_of_homes"].dropna().iloc[0])
            own = float(r.rate_after - r.rate_before)
            cc = t46.ctrl_change(c["p"], c["pool"], c["pre"], c["post"], c["homes"]) if c["pool"] else np.nan
            out.append(dict(i=r.Index, found=True, call=c, scale=scale, own=own, ctrl=cc, effect=(own - cc) / scale,
                            n_pool=len(c["pool"]), window=c["window"]))
        return pd.DataFrame(out)

    t46.rebuild = rebuild
    t46._t56 = True


def _gz(path):
    with zipfile.ZipFile(path) as z:
        g = pd.read_csv(io.BytesIO(z.read(z.namelist()[0])), sep="\t", dtype={"GEOID": str}, encoding="latin-1")
    g.columns = [c.strip() for c in g.columns]
    return g


def pop2010(keys, geo_acs: pd.Series, fallback) -> tuple[np.ndarray, list[str]]:
    """2010 census population per key, as Test 53: place Gazetteer for 160| places, county-subdivision Gazetteer for
    060| (Connecticut on state + MCD), else the ACS population given in `fallback` (South Bend's combined row)."""
    gp = _gz(RAW / "parking_older_reforms" / "Gaz_places_national.zip").set_index("GEOID")["POP10"]
    gc = _gz(RAW / "census_gazetteer_2010" / "Gaz_cousubs_national.zip")
    gc_ct = gc[gc["GEOID"].str.startswith("09")].assign(k=lambda d: d["GEOID"].str[:2] + d["GEOID"].str[5:]).set_index("k")["POP10"]
    gc = gc.set_index("GEOID")["POP10"]
    out, src = [], []
    for k, fb in zip(keys, fallback):
        g = str(geo_acs.get(k, "")) if k in geo_acs.index else ""
        v = np.nan
        if g.startswith("160|"):
            v = gp.get(g[4:], np.nan)
        elif g.startswith("060|"):
            v = gc.get(g[4:], np.nan)
            if not np.isfinite(v) and g[4:6] == "09":
                v = gc_ct.get(g[4:6] + g[9:], np.nan)
        if np.isfinite(v):
            out.append(float(v))
            src.append("2010 census (Gazetteer)")
        else:
            out.append(float(fb))
            src.append("ACS 2020-2024 (fallback, as Test 53)")
    return np.array(out, float), src
