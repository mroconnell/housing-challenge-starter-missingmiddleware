"""Option D line for the tool (docs/tod/OPTION_D_PLAN.md, section 5 rule fixed before results): no model beat the
other places' average on hidden places within 1/4 mile (rounds 1-3 and the all-models sweep, logged in the plan), so the
central line is the average rule: the 11 district places' mean measured effect within 1/4 mile (extra new homes per
100 lot acres a year) x Wisconsin's lot acres within 1/4 mile of rail and rapid stops (Milwaukee and Madison) x 5 years
x the statewide scale (owner 2026-11-02 14:54: lot acres within 1/4 mile of rail and rapid stops, state / cities of
Milwaukee and Madison, from reference/tod_station_areas.csv; was homes within 1/2 mile, 1.1062). Range: each
place left out in turn. Beyond 1/4 mile: zero (no rule beat zero there in the 1/4-1/2 band; locked rule).

Also written: the same scaled to a 15% district by the places' pooled ratio of effect to coverage (sum of effects /
sum of coverage differences x 0.15), since the 11 places' districts averaged about 12% of the 1/4-mile lots.

Little line (owner 2026-11-02 14:24, "I love that"; AQ-071): the best lot model (lot + place traits, 5 averaged fits,
the "fix_equal_fill" round) Wisconsin answer within 1/4 mile, already statewide and over 5 years; range = the fits that
each leave one training place out, rescaled from the 1/2-mile homes scale to the 1/4-mile land scale. To change the
little line, change LITTLE_FILE (one row, optiond_little).

What-ifs and checks (auditor review 2026-11-02): districts of 10% and 25% (pooled ratio x share); a straight line of
effect on district share at 15%; and the broad-places check (reference/tod_optiond_broad_check.csv): the district rules
applied to the 5 broad upzonings left out of training.

    uv run --all-extras python scripts/build_tod_optiond_line.py  -> reference/tod_optiond_line.csv, tod_optiond_broad_check.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
from missing_middleware.paths import REFERENCE  # noqa: E402
import run_tod_optiond as O  # noqa: E402


# The tool's little line (AQ-071): one file, band 0-1/4 (statewide, extra homes over 2027-2031). That file was scaled to
# the state by the old 1/2-mile homes ratio (OLD_SCALE); it is rescaled to the 1/4-mile land ratio below.
LITTLE_FILE = "tod_optiond_wisconsin_lot_place_fix_equal_fill_k5_s1.csv"
OLD_SCALE = O.HOMES_HALF_MILE_STATE / O.HOMES_HALF_MILE_MKE_MAD          # 89,528 / 80,930 = 1.1062
BROAD = ["bellevue_belred_2009", "honolulu_2017", "la_toc_2017", "san_diego_2021", "chicago_2022"]
TWO_CITIES = ["Milwaukee city", "Madison city"]


def statewide_scale() -> tuple[float, float, float]:
    """Owner 2026-11-02 14:54 ("You can switch."): the statewide scale is the 1/4-mile land ratio, all Wisconsin lot
    acres within 1/4 mile of rail and rapid stops / those in the cities of Milwaukee and Madison (the same land the
    placement step uses; reference/tod_station_areas.csv, band rapid_quarter). Returns (scale, state acres, two cities)."""
    sa = pd.read_csv(REFERENCE / "tod_station_areas.csv")
    q = sa[sa.band == "rapid_quarter"]
    state, two = float(q.acres.sum()), float(q[q.city.isin(TWO_CITIES)].acres.sum())
    return state / two, state, two


def main() -> None:
    C = pd.read_csv(REFERENCE / "tod_station_area_effects_by_city.csv")
    q = C[(C.band == "0-1/4") & C.city.isin(O.TRAIN)].set_index("city")
    V = pd.read_csv(REFERENCE / "tod_station_area_wisconsin_versions.csv").set_index("band").loc["0-1/4"]
    scale, state_acres, two_acres = statewide_scale()
    k = V.wi_acres / 100 * 5 * scale
    avg = lambda d: d.effect_per_100_acres.mean() * k                                            # noqa: E731
    pooled = lambda d: d.effect_per_100_acres.sum() / d.coverage_diff.sum()                      # noqa: E731
    at = lambda share: (lambda d: pooled(d) * share * k)                                         # noqa: E731

    def linear(d, share=O.SHARE):
        b, a = np.polyfit(d.coverage_diff, d.effect_per_100_acres, 1)
        return (a + b * share) * k

    rows = []
    for name, f, note in (("optiond_average", avg, "average rule (central by the pre-set rule)"),
                          ("optiond_average_scaled_15", at(O.SHARE), "average scaled to a 15% district by the pooled ratio"),
                          ("optiond_scaled_10", at(0.10), "what-if: district 10% (pooled ratio x 0.10)"),
                          ("optiond_scaled_25", at(0.25), "what-if: district 25% (pooled ratio x 0.25)"),
                          ("optiond_linear_fit_15", linear, "check: straight line of effect on district share through the 11 places, at 15%")):
        loo = [f(q.drop(index=c)) for c in q.index]
        rows.append({"line": name, "extra_homes_2027_2031": round(f(q), 1), "range_low": round(min(loo), 1),
                     "range_high": round(max(loo), 1), "places": len(q),
                     "mean_effect_per_100_acres": round(q.effect_per_100_acres.mean(), 2),
                     "mean_district_share": round(q.coverage_diff.mean(), 3), "wi_acres_quarter": round(V.wi_acres, 1),
                     "statewide_scale": round(scale, 4), "note": note})
    w = pd.read_csv(REFERENCE / LITTLE_FILE).drop_duplicates("band").set_index("band").loc["0-1/4"]
    r = scale / OLD_SCALE
    rows.append({"line": "optiond_little", "extra_homes_2027_2031": round(float(w.central) * r, 1),
                 "range_low": round(float(w.low) * r, 1), "range_high": round(float(w.high) * r, 1), "places": len(q),
                 "mean_effect_per_100_acres": float("nan"), "mean_district_share": float("nan"),
                 "wi_acres_quarter": round(V.wi_acres, 1), "statewide_scale": round(scale, 4),
                 "note": f"best lot model (lot + place traits, 5 averaged fits), {LITTLE_FILE} x {scale:.4f} / {OLD_SCALE:.4f} "
                         f"(file used the 1/2-mile homes scale); range = each place left out"})
    out = pd.DataFrame(rows)
    out.to_csv(REFERENCE / "tod_optiond_line.csv", index=False)
    print(out.to_string(index=False))
    print(f"scale {scale:.4f} = {state_acres:,.1f} / {two_acres:,.1f}; Spearman effect vs share "
          f"{spearmanr(q.coverage_diff, q.effect_per_100_acres).statistic:.3f}")
    # Broad-places check (auditor 2026-11-02): do the district rules predict the 5 broad upzonings left out of training?
    b = C[(C.band == "0-1/4") & C.city.isin(BROAD)].set_index("city")
    chk = pd.DataFrame({"measured": b.effect_per_100_acres, "coverage_diff": b.coverage_diff,
                        "average_rule": q.effect_per_100_acres.mean(), "scaled_rule": pooled(q) * b.coverage_diff, "zero": 0.0})
    for c in ("average_rule", "scaled_rule", "zero"):
        chk[f"miss_{c}"] = (chk[c] - chk.measured).abs()
    chk.loc["median"] = chk.median(numeric_only=True)
    chk.round(2).to_csv(REFERENCE / "tod_optiond_broad_check.csv")
    print(chk.round(1).to_string())


if __name__ == "__main__":
    main()
