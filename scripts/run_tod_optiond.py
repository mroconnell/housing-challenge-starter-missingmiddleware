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


class Bag:
    """Average of K gradient-boosting fits (seeds 1..K), all 300 rounds (no random early stopping)."""

    def __init__(self, k: int, **kw):
        self.k, self.kw = k, kw

    def fit(self, X, y, w):
        from sklearn.ensemble import HistGradientBoostingRegressor
        self.m = [HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, min_samples_leaf=200,
                                                early_stopping=False, random_state=s, **self.kw).fit(X, y, sample_weight=w)
                  for s in range(1, self.k + 1)]
        return self

    def predict(self, X):
        return np.mean([m.predict(X) for m in self.m], axis=0)


def wisconsin_rows(cols: list[str]) -> pd.DataFrame:
    W = L.wisconsin_rows()
    W["mandate"] = 0.0   # option D: by right, no affordability requirement
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


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trait-groups", default="lot")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--seed", type=int, default=1, help="New York / Philadelphia comparison set")
    ap.add_argument("--share", type=float, default=SHARE)
    ap.add_argument("--tag", default=None)
    a = ap.parse_args(argv)
    groups = a.trait_groups.split(",") if a.trait_groups else []
    D = load(a.seed, "tract" in groups)
    cols = features(D, groups)
    print(f"rows {len(D):,}; places {D.city.nunique()}; features {len(cols)}: {cols}")
    measured = M.city_level(M.case_effects("permit_est")).set_index(["city", "band"])["effect_per_100_acres"]
    measured = measured[measured.index.get_level_values(0).isin(TRAIN)]
    W = wisconsin_rows(cols)
    rows, wi = [], []
    for city in TRAIN:
        tr, te = D[D.city != city], D[D.city == city]
        m = Bag(a.k).fit(tr[cols].astype(float), tr.y, tr.w)
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
    m = Bag(a.k).fit(D[cols].astype(float), D.y, D.w)
    scale = HOMES_HALF_MILE_STATE / HOMES_HALF_MILE_MKE_MAD
    full = wisconsin_extra(m, W, cols, a.share)
    X = pd.concat(wi, axis=1)
    out = pd.DataFrame({"central": full, "low": X.min(axis=1), "high": X.max(axis=1)})
    out.loc["total"] = out.sum()
    out = (5 * scale * out).round(1)     # statewide, 2027-2031
    print(f"\nWisconsin statewide, extra homes over 5 years, district = {a.share:.0%} of 1/4-mile lot acres:\n"
          + out.to_string())
    tag = a.tag or (a.trait_groups.replace(",", "_") + f"_k{a.k}_s{a.seed}")
    R.round(4).to_csv(REFERENCE / f"tod_optiond_loco_{tag}.csv", index=False)
    out.to_csv(REFERENCE / f"tod_optiond_wisconsin_{tag}.csv")


if __name__ == "__main__":
    main()
