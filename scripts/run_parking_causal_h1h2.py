"""Parking causal framework, tests H1 and H2 (docs/parking/CAUSAL_FRAMEWORK_PLAN.md, locked 2026-11-03).

H1: homes per new 5+ unit building, difference-in-differences against matched comparison places.
H2: new 2-4 unit buildings and new 5+ unit buildings per 1,000 existing homes a year, same comparison.

    uv run python scripts/run_parking_causal_h1h2.py
Outputs: reference/parking_causal_h1h2_places.csv, reference/parking_causal_h1h2_summary.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_parking_comparison as rpc  # noqa: E402
from missing_middleware.parking import comparison as cmp  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

SEED, DRAWS = 20261103, 2000


def boot(values: np.ndarray, weights: np.ndarray, ratio_den: np.ndarray | None = None):
    """Weighted mean (or ratio of weighted sums) with a 90% interval from resampling places; SE for the MDE."""
    rng = np.random.default_rng(SEED)
    n = len(values)
    est = lambda i: (np.sum(values[i] * weights[i]) / np.sum(weights[i])) if ratio_den is None else \
        (np.sum(values[i] * weights[i]) / np.sum(ratio_den[i] * weights[i]))  # noqa: E731
    full = est(np.arange(n))
    bs = np.array([est(rng.integers(0, n, n)) for _ in range(DRAWS)])
    loo = [est(np.delete(np.arange(n), j)) for j in range(n)]
    return full, np.percentile(bs, 5), np.percentile(bs, 95), 1.645 * bs.std(ddof=1), min(loo), max(loo)


def main() -> None:
    bps = rpc.read_bps_us()
    p = cmp.panel(bps)
    b = bps.assign(key=bps["state_fips"].astype(str).str.strip() + "|" + bps["bps_id"].astype(str).str.strip()) \
        .drop_duplicates(["key", "year"])
    b["b24"] = b["2units_bldgs"] + b["3_4units_bldgs"]
    b5b, b5u, b24 = (b.pivot_table(index="key", columns="year", values=c, aggfunc="sum") for c in ("5plus_bldgs", "5plus_units", "b24"))
    geo = p.drop_duplicates("key", keep="last").set_index("key")
    homes = geo["acs_geoid"].map(rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25002.dat", "B25002_E001"))
    homes = homes[homes > 0]
    popn = geo["acs_geoid"].map(rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b01003.dat", "B01003_E001"))
    tax = pd.read_csv(REFERENCE / "parking_reform_taxonomy.csv")
    excluded = {k for r in tax[(tax["policy"] == "rm_min") & tax["benchmark_rating"].isin(["at", "near"]) & (tax["place_type"] == "city")]
                .drop_duplicates("prn_key").itertuples() if (k := cmp.match_place(p, rpc.STATE_FIPS.get(r.state, "??"), r.place, r.population))}
    real = pd.read_csv(REFERENCE / "parking_expanded_effects.csv")
    real = real[(real["status"] == "included") & (real["outcome"] == "all")]
    excluded |= set(real["key"])

    def sums(tab, keys, years):
        t = tab.reindex(index=list(keys), columns=years)
        return float(np.nansum(t.values))

    rows = []
    for r in real.itertuples():
        pre, post = cmp.windows(int(r.event_year))
        post = post[: int(r.n_post)]
        ctrl, label = cmp.controls(p, r.key, int(r.event_year), excluded - {r.key}, homes, popn)
        h, hc = float(homes.get(r.key, np.nan)), float(homes.reindex(ctrl).sum())
        d = dict(key=r.key, place=r.place, state=r.state, event_year=int(r.event_year), n_post=len(post), n_controls=len(ctrl),
                 pool=label, homes=h, simultaneous_rewrite=r.simultaneous_rewrite)
        for nm, keys in (("p", [r.key]), ("c", ctrl)):
            for w, yrs in (("b", pre), ("a", post)):
                bl, un, mid = sums(b5b, keys, yrs), sums(b5u, keys, yrs), sums(b24, keys, yrs)
                den = (h if nm == "p" else hc) * len(yrs) / 1000
                d[f"{nm}{w}_bldg5"], d[f"{nm}{w}_units5"] = bl, un
                d[f"{nm}{w}_size5"] = un / bl if bl > 0 else np.nan
                d[f"{nm}{w}_rate5"] = bl / den if den else np.nan
                d[f"{nm}{w}_rate24"] = mid / den if den else np.nan
        d["h1_did"] = (d["pa_size5"] - d["pb_size5"]) - (d["ca_size5"] - d["cb_size5"])
        d["h1_weight"] = d["pb_bldg5"] + d["pa_bldg5"]
        d["h2_did_5"] = (d["pa_rate5"] - d["pb_rate5"]) - (d["ca_rate5"] - d["cb_rate5"])
        d["h2_did_24"] = (d["pa_rate24"] - d["pb_rate24"]) - (d["ca_rate24"] - d["cb_rate24"])
        d["h2_weight"] = h * len(post)
        rows.append(d)
    P = pd.DataFrame(rows)
    P.to_csv(REFERENCE / "parking_causal_h1h2_places.csv", index=False)

    out = []
    h1 = P.dropna(subset=["h1_did"])
    h1 = h1[h1["h1_weight"] > 0]
    m, lo, hi, mde, l1, l2 = boot(h1["h1_did"].values, h1["h1_weight"].values)
    base = np.sum(h1["pb_size5"] * h1["h1_weight"]) / np.sum(h1["h1_weight"])
    out.append(dict(test="H1 homes per new 5+ unit building (DiD)", unit="homes per building", places=len(h1),
                    left_out=len(P) - len(h1), estimate=m, p05=lo, p95=hi, mde=mde, loo_min=l1, loo_max=l2,
                    before_level=base, pct=100 * m / base, pct_p05=100 * lo / base, pct_p95=100 * hi / base))
    for col, nm in (("h2_did_24", "H2 new 2-4 unit buildings per 1,000 existing homes a year (DiD)"),
                    ("h2_did_5", "H2 new 5+ unit buildings per 1,000 existing homes a year (DiD)")):
        d = P.dropna(subset=[col])
        m, lo, hi, mde, l1, l2 = boot(d[col].values, d["h2_weight"].values)
        lvl = "pb_rate24" if "24" in col else "pb_rate5"
        base = np.sum(d[lvl] * d["h2_weight"]) / np.sum(d["h2_weight"])
        out.append(dict(test=nm, unit="buildings per 1,000 existing homes a year", places=len(d), left_out=len(P) - len(d),
                        estimate=m, p05=lo, p95=hi, mde=mde, loo_min=l1, loo_max=l2, before_level=base, pct=100 * m / base,
                        pct_p05=100 * lo / base, pct_p95=100 * hi / base))
    S = pd.DataFrame(out)
    S["reading"] = np.where(S["p05"] > 0, "supported", np.where(S["p95"] < 0, "opposite sign", "not supported (interval includes 0)"))
    S.to_csv(REFERENCE / "parking_causal_h1h2_summary.csv", index=False)
    pd.set_option("display.width", 250)
    print(S.round(3).to_string(index=False))
    print(P.sort_values("h1_weight", ascending=False)[["place", "pb_size5", "pa_size5", "cb_size5", "ca_size5", "h1_did", "h1_weight"]].head(10).round(1).to_string(index=False))


if __name__ == "__main__":
    main()
