"""Option D line for the tool (docs/tod/OPTION_D_PLAN.md, section 5 rule fixed before results): no model beat the
other places' average on hidden places within 1/4 mile (rounds 1-3 and the all-models sweep, logged in the plan), so the
central line is the average rule: the 11 district places' mean measured effect within 1/4 mile (extra new homes per
100 lot acres a year) x Wisconsin's lot acres within 1/4 mile of rail and rapid stops (Milwaukee and Madison) x 5 years
x the statewide scale (homes within 1/2 mile of rail and rapid stops: state / Milwaukee and Madison). Range: each
place left out in turn. Beyond 1/4 mile: zero (no rule beat zero there in the 1/4-1/2 band; locked rule).

Also written: the same scaled to a 15% district by the places' pooled ratio of effect to coverage (sum of effects /
sum of coverage differences x 0.15), since the 11 places' districts averaged about 12% of the 1/4-mile lots.

    uv run --all-extras python scripts/build_tod_optiond_line.py  -> reference/tod_optiond_line.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
from missing_middleware.paths import REFERENCE  # noqa: E402
import run_tod_optiond as O  # noqa: E402


def main() -> None:
    C = pd.read_csv(REFERENCE / "tod_station_area_effects_by_city.csv")
    q = C[(C.band == "0-1/4") & C.city.isin(O.TRAIN)].set_index("city")
    V = pd.read_csv(REFERENCE / "tod_station_area_wisconsin_versions.csv").set_index("band").loc["0-1/4"]
    k = V.wi_acres / 100 * 5 * O.HOMES_HALF_MILE_STATE / O.HOMES_HALF_MILE_MKE_MAD
    avg = lambda d: d.effect_per_100_acres.mean() * k                                            # noqa: E731
    sc = lambda d: d.effect_per_100_acres.sum() / d.coverage_diff.sum() * O.SHARE * k            # noqa: E731
    rows = []
    for name, f, note in (("optiond_average", avg, "average rule (central by the pre-set rule)"),
                          ("optiond_average_scaled_15", sc, "average scaled to a 15% district by the pooled ratio")):
        loo = [f(q.drop(index=c)) for c in q.index]
        rows.append({"line": name, "extra_homes_2027_2031": round(f(q), 1), "range_low": round(min(loo), 1),
                     "range_high": round(max(loo), 1), "places": len(q),
                     "mean_effect_per_100_acres": round(q.effect_per_100_acres.mean(), 2),
                     "mean_district_share": round(q.coverage_diff.mean(), 3), "wi_acres_quarter": round(V.wi_acres, 1),
                     "note": note})
    out = pd.DataFrame(rows)
    out.to_csv(REFERENCE / "tod_optiond_line.csv", index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
