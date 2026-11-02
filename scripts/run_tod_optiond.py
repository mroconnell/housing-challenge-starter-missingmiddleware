"""Option D, the transit district mandate (docs/tod/OPTION_D_PLAN.md; owner decisions 2026-11-02 10:45).

The law: every Wisconsin city with qualifying rail or rapid-bus stops zones a by-right multifamily district covering
15% of the lot acres within 1/4 mile of those stops. No site is picked: the district is treated as spread at random
over the 1/4-mile land, so each lot there is in the district with probability 0.15 and the answer is the expected
extra homes (a density in the radius, owner 2026-11-02).

Training: the 11 places whose reform covered under 30% of the lots within 1/4 mile (reform minus comparison
coverage): New York, Philadelphia, Austin, Charlotte, Chicago 2015, Denver, Portland 2020, Seattle Mount Baker,
Seattle Othello, Salt Lake City, Saint Paul. Lot rows as in scripts/run_tod_station_lotmodel.py (near-all lots:
every lot outside New York and Philadelphia, their reform lots, one fixed comparison set per seed).

Test (place is the unit): hide one place, fit on the other 10, predict its measured effect per 100 lot acres a year
by band; compare the median absolute error with two benchmark rules: zero, and the other places' average measured
effect. Steadiness: each fit is the average of K gradient-boosting fits with different seeds and no random early
stopping.

    uv run --all-extras python scripts/run_tod_optiond.py --trait-groups lot [--k 5] [--share 0.15] [--tag name]
Writes reference/tod_optiond_loco_<tag>.csv (hidden-place test) and reference/tod_optiond_wisconsin_<tag>.csv.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from missing_middleware.paths import REFERENCE  # noqa: E402
import run_tod_station_lotmodel as L  # noqa: E402
import run_tod_station_model as M  # noqa: E402

TRAIN = ["New York", "Philadelphia", "austin_2009", "charlotte_2019", "chicago_2015", "denver_2018", "portland_2020",
         "seattle_mount_baker_2014", "seattle_othello_2012", "slc_2010", "stpaul_2011"]
SHARE = 0.15
HOMES_HALF_MILE_STATE, HOMES_HALF_MILE_MKE_MAD = 89_528, 80_930   # as scripts/build_tod_station_area_line.py
SWITCHES = ("reform_stop", "in_reform_area", "coverage", "strings_attached", "mandate")


def mandate_of() -> dict:
    c = pd.read_csv(REFERENCE / "tod_inclusionary_coding.csv")
    return dict(zip(c.case_id, c.mandate_in_window.eq("yes").astype(float)))


def load(seed: int, tract: bool) -> pd.DataFrame:
    mand = mandate_of()
    rng = np.random.default_rng(seed)
    parts = []
    for f in sorted(L.OUT.glob("lots_*.parquet")):
        case = f.stem.removeprefix("lots_")
        if M.city_of(case) not in TRAIN:
            continue
        d = L.load_case(case, "permit_est", rng, "full", seed, tract=tract)
        if d is None:
            continue
        key = M.city_of(case) if M.city_of(case) in ("New York", "Philadelphia") else case
        d["mandate"] = np.float32(mand.get(key, 0.0)) * d.reform_stop
        parts.append(d)
    return pd.concat(parts, ignore_index=True)


def features(D: pd.DataFrame, groups: list[str]) -> list[str]:
    cols = L.features(D, [g for g in groups if g != "mandate"])
    if "mandate" in groups:
        cols.append("mandate")
    return cols


FILL_COLS = ["log_land_value_per_acre", "land_value_rank_in_case", "bldg_to_land", "building_age"]


def prepare(D: pd.DataFrame, fixes: set[str]) -> tuple[pd.DataFrame, dict]:
    """Round-2 fixes (plan log 2026-11-02):
    fill   - lot traits missing for a whole place (Austin: no land values; Philadelphia: no year built) are filled with
             the median over all training lots, so a hidden place with a gap is not sent down a branch learned from
             some other place's gap;
    equal  - each place gets the same total weight (the place is the unit of the test; New York and Philadelphia had
             about 95% of the weight); within a place, lot weights keep their ratios."""
    D = D.copy()
    med = {}
    if "fill" in fixes:
        for c in FILL_COLS:
            med[c] = float(np.nanmedian(D[c].astype(float)))
            D[c] = D[c].fillna(med[c])
    if "equal" in fixes:
        D["w"] = D.w / D.groupby("city").w.transform("sum") * 1e5
    return D, med


class Bag:
    """Average of K gradient-boosting fits (seeds 1..K), all 300 rounds (no random early stopping)."""

    def __init__(self, k: int, offset: int = 0, min_samples_leaf: int = 200, **kw):
        self.k, self.offset, self.leaf, self.kw = k, offset, min_samples_leaf, kw

    def fit(self, X, y, w):
        from sklearn.ensemble import HistGradientBoostingRegressor
        self.m = [HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, min_samples_leaf=self.leaf,
                                                early_stopping=False, random_state=s, **self.kw).fit(X, y, sample_weight=w)
                  for s in range(1 + self.offset, self.k + 1 + self.offset)]
        return self

    def predict(self, X):
        return np.mean([m.predict(X) for m in self.m], axis=0)


def wisconsin_rows(cols: list[str], med: dict | None = None) -> pd.DataFrame:
    W = L.wisconsin_rows()
    W["mandate"] = 0.0   # option D: by right, no affordability requirement
    for c, v in (med or {}).items():
        W[c] = W[c].fillna(v)
    return W


def wisconsin_extra(model, W: pd.DataFrame, cols: list[str], share: float) -> pd.Series:
    """Expected extra homes a year by band when a random `share` of the 1/4-mile lot land is in the district."""
    X = W[cols].astype(float)
    off = X.copy()
    off[[c for c in SWITCHES if c in cols]] = 0.0
    q = (W.band == "0-1/4").values
    base = model.predict(off)
    on = X.copy()
    on["reform_stop"] = 1.0
    if "coverage" in cols:
        on["coverage"] = np.where(q, share, 0.0)
    if "in_reform_area" in cols:
        in1 = on.copy(); in1["in_reform_area"] = np.where(q, 1.0, 0.0)
        in0 = on.copy(); in0["in_reform_area"] = 0.0
        exp = np.where(q, share * model.predict(in1) + (1 - share) * model.predict(in0), model.predict(in0))
    else:
        exp = model.predict(on)
    return pd.Series(exp - base, index=W.index).groupby(W.band).sum()


STOP_FEATS = ["reform_stop", "coverage", "band_q", "band_h", "log_stop_acres"]


def to_stops(D: pd.DataFrame, lot_cols: list[str], fixes: set[str]) -> pd.DataFrame:
    """Round 3 (plan log): one row per stop and band. Target: change in new homes per 100 lot acres a year (after
    window minus before window), as the measured effect is built; row weight: lot acres (each place equal if `equal`).
    Features: reform stop, coverage, band, log of the band's lot acres, and acre-weighted means of the lot traits."""
    D = D.copy()
    D["wa"] = D.w * D.acres.fillna(0).clip(lower=0)
    D["d_homes"] = D.w * (D.y - D.rate_before)
    g = D.groupby(["city", "case", "stop_id", "band"], sort=False)
    S = g.agg(wa=("wa", "sum"), d_homes=("d_homes", "sum"), reform_stop=("reform_stop", "max"),
              coverage=("coverage", "max")).reset_index()
    for c in lot_cols:
        D["_x"] = D[c].astype(float) * D.wa
        D["_n"] = D.wa.where(D[c].notna(), 0.0)
        t = D.groupby(["city", "case", "stop_id", "band"], sort=False)[["_x", "_n"]].sum().reset_index(drop=True)
        S[c] = (t._x / t._n.where(t._n > 0)).values
    S = S[S.wa > 0].copy()
    S["y"] = 100 * S.d_homes / S.wa
    S["band_q"], S["band_h"] = (S.band == "0-1/4").astype(float), (S.band == "1/4-1/2").astype(float)
    S["log_stop_acres"] = np.log(S.wa / S.groupby("case").wa.transform("count").clip(lower=1) + 0.01)
    S["w"] = S.wa / S.groupby("city").wa.transform("sum") * 1e5 if "equal" in fixes else S.wa
    return S


def stop_effect(model, S: pd.DataFrame, cols: list[str]) -> pd.Series:
    R = S[S.reform_stop == 1]
    off = R[cols].astype(float).copy(); off[["reform_stop", "coverage"]] = 0.0
    d = (model.predict(R[cols].astype(float)) - model.predict(off)) * R.wa
    return d.groupby(R.band).sum() / R.wa.groupby(R.band).sum()


def wisconsin_stops(W: pd.DataFrame, lot_cols: list[str]) -> pd.DataFrame:
    W = W.copy()
    W["w"], W["y"], W["city"] = 1.0, 0.0, "Wisconsin"
    W["rate_before"] = 0.0
    S = to_stops(W, lot_cols, set())
    return S


def wisconsin_stop_extra(model, S: pd.DataFrame, cols: list[str], share: float) -> pd.Series:
    off = S[cols].astype(float).copy(); off[["reform_stop", "coverage"]] = 0.0
    on = S[cols].astype(float).copy(); on["reform_stop"] = 1.0
    on["coverage"] = np.where(S.band == "0-1/4", share, 0.0)
    return ((model.predict(on) - model.predict(off)) * S.wa / 100).groupby(S.band).sum()


def main_stops(a, groups, fixes) -> None:
    D, med = prepare(load(a.seed, "tract" in groups), fixes - {"equal"})
    lot_cols = [c for c in features(D, groups) if c not in SWITCHES]
    S = to_stops(D, lot_cols, fixes)
    cols = STOP_FEATS + lot_cols
    print(f"stop-band rows {len(S):,}; places {S.city.nunique()}; features {cols}")
    measured = M.city_level(M.case_effects("permit_est")).set_index(["city", "band"])["effect_per_100_acres"]
    measured = measured[measured.index.get_level_values(0).isin(TRAIN)]
    WS = wisconsin_stops(wisconsin_rows(cols, med), lot_cols)
    rows, wi = [], []
    for city in TRAIN:
        tr, te = S[S.city != city], S[S.city == city]
        m = Bag(a.k, a.bag_offset, min_samples_leaf=20).fit(tr[cols].astype(float), tr.y, tr.w)
        wi.append(wisconsin_stop_extra(m, WS, cols, a.share).rename(f"without {city}"))
        for band, v in stop_effect(m, te, cols).items():
            others = measured.drop(index=city, level=0, errors="ignore").xs(band, level=1).mean()
            rows.append({"city": city, "band": band, "measured": measured.get((city, band), np.nan), "model": v,
                         "others_average": others})
    finish(a, rows, wi, Bag(a.k, a.bag_offset, min_samples_leaf=20).fit(S[cols].astype(float), S.y, S.w),
           lambda m: wisconsin_stop_extra(m, WS, cols, a.share), groups, fixes | {"stops"})


def finish(a, rows, wi, m, wfun, groups, fixes) -> None:
    R = pd.DataFrame(rows)
    R["err_model"], R["err_avg"], R["err_zero"] = ((R.model - R.measured).abs(), (R.others_average - R.measured).abs(),
                                                   R.measured.abs())
    pd.set_option("display.width", 200)
    print(R.round(2).to_string(index=False))
    med = R.groupby("band")[["err_model", "err_avg", "err_zero"]].median()
    print("\nmedian absolute error by band (extra homes per 100 lot acres a year):\n" + med.round(2).to_string())
    scale = HOMES_HALF_MILE_STATE / HOMES_HALF_MILE_MKE_MAD
    X = pd.concat(wi, axis=1)
    out = pd.DataFrame({"central": wfun(m), "low": X.min(axis=1), "high": X.max(axis=1)})
    out.loc["total"] = out.sum()
    out = (5 * scale * out).round(1)
    print(f"\nWisconsin statewide, extra homes over 5 years, district = {a.share:.0%} of 1/4-mile lot acres:\n"
          + out.to_string())
    tag = a.tag or (a.trait_groups.replace(",", "_") + (f"_fix_{'_'.join(sorted(fixes))}" if fixes else "")
                    + f"_k{a.k}_s{a.seed}" + (f"_o{a.bag_offset}" if a.bag_offset else ""))
    R.round(4).to_csv(REFERENCE / f"tod_optiond_loco_{tag}.csv", index=False)
    out.to_csv(REFERENCE / f"tod_optiond_wisconsin_{tag}.csv")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trait-groups", default="lot")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--seed", type=int, default=1, help="New York / Philadelphia comparison set")
    ap.add_argument("--share", type=float, default=SHARE)
    ap.add_argument("--tag", default=None)
    ap.add_argument("--fixes", default="", help="comma list of round-2 fixes: fill,equal")
    ap.add_argument("--level", default="lot", choices=["lot", "stop"], help="round 3: stop-and-band rows")
    ap.add_argument("--bag-offset", type=int, default=0, help="steadiness check: use fit seeds offset+1..offset+k")
    a = ap.parse_args(argv)
    groups = a.trait_groups.split(",") if a.trait_groups else []
    fixes = set(x for x in a.fixes.split(",") if x)
    if a.level == "stop":
        return main_stops(a, groups, fixes)
    D, med = prepare(load(a.seed, "tract" in groups), fixes)
    cols = features(D, groups)
    print(f"rows {len(D):,}; places {D.city.nunique()}; features {len(cols)}: {cols}")
    measured = M.city_level(M.case_effects("permit_est")).set_index(["city", "band"])["effect_per_100_acres"]
    measured = measured[measured.index.get_level_values(0).isin(TRAIN)]
    W = wisconsin_rows(cols, med)
    rows, wi = [], []
    for city in TRAIN:
        tr, te = D[D.city != city], D[D.city == city]
        m = Bag(a.k, a.bag_offset).fit(tr[cols].astype(float), tr.y, tr.w)
        wi.append(wisconsin_extra(m, W, cols, a.share).rename(f"without {city}"))
        for band, v in L.effect_by_band(m, te, cols).items():
            others = measured.drop(index=city, level=0, errors="ignore").xs(band, level=1).mean()
            rows.append({"city": city, "band": band, "measured": measured.get((city, band), np.nan), "model": v,
                         "others_average": others})
    R = pd.DataFrame(rows)
    R["err_model"], R["err_avg"], R["err_zero"] = ((R.model - R.measured).abs(), (R.others_average - R.measured).abs(),
                                                   R.measured.abs())
    pd.set_option("display.width", 200)
    print(R.round(2).to_string(index=False))
    med = R.groupby("band")[["err_model", "err_avg", "err_zero"]].median()
    print("\nmedian absolute error by band (extra homes per 100 lot acres a year):\n" + med.round(2).to_string())
    m = Bag(a.k, a.bag_offset).fit(D[cols].astype(float), D.y, D.w)
    scale = HOMES_HALF_MILE_STATE / HOMES_HALF_MILE_MKE_MAD
    full = wisconsin_extra(m, W, cols, a.share)
    X = pd.concat(wi, axis=1)
    out = pd.DataFrame({"central": full, "low": X.min(axis=1), "high": X.max(axis=1)})
    out.loc["total"] = out.sum()
    out = (5 * scale * out).round(1)     # statewide, 2027-2031
    print(f"\nWisconsin statewide, extra homes over 5 years, district = {a.share:.0%} of 1/4-mile lot acres:\n"
          + out.to_string())
    tag = a.tag or (a.trait_groups.replace(",", "_") + (f"_fix_{'_'.join(sorted(fixes))}" if fixes else "")
                      + f"_k{a.k}_s{a.seed}" + (f"_o{a.bag_offset}" if a.bag_offset else ""))
    R.round(4).to_csv(REFERENCE / f"tod_optiond_loco_{tag}.csv", index=False)
    out.to_csv(REFERENCE / f"tod_optiond_wisconsin_{tag}.csv")


if __name__ == "__main__":
    main()
