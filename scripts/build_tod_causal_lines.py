"""The TOD tool's lower and upper lines from the causal framework (owner 2026-11-03 00:17, "sure", to "lock in 3,958 /
10,028 / 13,451"; docs/tod/CAUSAL_FRAMEWORK_PLAN.md, "Owner decision"; AQ-072). The central stays the D-11 plain average
in reference/tod_optiond_line.csv (row optiond_average).

- Lower = the edge test (T3) direct-effect floor: pooled edge effect of the 5 balance-passing places (extra new homes per
  100 lot acres a year of district land, reference/tod_causal_edge_test.csv, main 91 m) x 15% x Wisconsin lot acres within
  1/4 mile (Milwaukee and Madison) / 100 x 5 years x the statewide land scale. Range = the 90% interval (segment resampling);
  leave-one-place-out also written.
- Upper = the 2x2 near-new-lines reading (T2b): rezoning alone + interaction = new/rezoned cell - new/no-rezoning cell
  (reference/tod_causal_line_age_2x2.csv, main version) x the same acres, years and scale (no 15% factor: like the central,
  it is a 1/4-mile station-area effect). The CSV has no place-bootstrap interval for this difference, so the range is
  leave one place out, recomputed from each cell's per-place means (the cells are equal-place means); it is labelled so.
- Beside the central (what-ifs and notes): line-age matched (T2 M3) and transit alone (T2b; belongs in the baseline).

Owner decision 2026-11-03 11:52 ("good catch - yes to all three"; AQ-075): the tool's upper line becomes the D-11 average
scaled to a 15% district (row upper_average_scaled_15, copied from reference/tod_optiond_line.csv row
optiond_average_scaled_15, range = each place left out, the option D upper before AQ-072). The 2x2 reading
(causal_upper_2x2) is kept as a what-if, and so is the trend-adjusted 2x2 (whatif_2x2_trend_adjusted: real law effect near
new lines minus the fake-years effect on the same places, read from reference/tod_causal_line_age_pretrend.csv; range = the
paired place bootstrap 90% interval, leave one place out also written).

    uv run --all-extras python scripts/build_tod_causal_lines.py  -> reference/tod_causal_lines.csv
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
from missing_middleware.paths import REFERENCE  # noqa: E402

SHARE = 0.15
MAIN_2X2 = "main: D-11 + Milwaukee"


def factor() -> tuple[float, float, float]:
    """(acres x 5 / 100 x scale, scale, acres): the same Wisconsin factor as the central line."""
    od = pd.read_csv(REFERENCE / "tod_optiond_line.csv").set_index("line").loc["optiond_average"]
    acres, scale = float(od.wi_acres_quarter), float(od.statewide_scale)
    return acres / 100 * 5 * scale, scale, acres


def place_means(text: str) -> dict[str, float]:
    return {m.group(1).strip(): float(m.group(2)) for m in re.finditer(r"([^;]+?) (-?\d+(?:\.\d+)?)(?:;|$)", text)}


def main() -> None:
    k, scale, acres = factor()
    rows = []
    # Lower: edge test
    e = pd.read_csv(REFERENCE / "tod_causal_edge_test.csv")
    p = e[e.place.str.startswith("POOLED (5 places") & (e.variant == "main (91 m)")].iloc[0]
    loo = [float(p.loo_low), float(p.loo_high)]
    f = SHARE * k
    rows.append({"line": "causal_lower_edge", "effect_per_100_acres": round(p.edge_effect_per_100_acres_per_year, 3),
                 "extra_homes_2027_2031": round(p.edge_effect_per_100_acres_per_year * f, 1),
                 "range_low": round(p.low * f, 1), "range_high": round(p.high * f, 1), "range_kind": "90% interval (boundary segments resampled)",
                 "loo_low": round(min(loo) * f, 1), "loo_high": round(max(loo) * f, 1),
                 "note": f"edge test (T3), pooled 5 balance-passing places, 91 m; x 15% x {acres:,.1f} acres / 100 x 5 x {scale:.4f}"})
    # Upper: 2x2, rezoning alone + interaction = new/up - new/no
    d = pd.read_csv(REFERENCE / "tod_causal_line_age_2x2.csv")
    d = d[d.version == MAIN_2X2].set_index("name")
    up, no = place_means(d.loc["new/up", "place_list"]), place_means(d.loc["new/no", "place_list"])
    val = float(d.loc["new/up", "value"] - d.loc["new/no", "value"])
    places = sorted(set(up) | set(no))
    loo2 = []
    for c in places:
        u = [v for kk, v in up.items() if kk != c]
        n = [v for kk, v in no.items() if kk != c]
        loo2.append(sum(u) / len(u) - sum(n) / len(n))
    rows.append({"line": "causal_upper_2x2", "effect_per_100_acres": round(val, 3), "extra_homes_2027_2031": round(val * k, 1),
                 "range_low": round(min(loo2) * k, 1), "range_high": round(max(loo2) * k, 1),
                 "range_kind": f"leave one place out ({len(places)} places; per-place cell means from the 2x2 file)",
                 "loo_low": round(min(loo2) * k, 1), "loo_high": round(max(loo2) * k, 1),
                 "note": "T2b: new line rezoned minus new line not rezoned (rezoning alone + interaction), main D-11 + Milwaukee Hop placebo"})
    # Upper since AQ-075: the D-11 average scaled to a 15% district (the option D upper before AQ-072)
    o = pd.read_csv(REFERENCE / "tod_optiond_line.csv").set_index("line").loc["optiond_average_scaled_15"]
    rows.append({"line": "upper_average_scaled_15", "effect_per_100_acres": round(float(o.extra_homes_2027_2031) / k, 3),
                 "extra_homes_2027_2031": float(o.extra_homes_2027_2031),
                 "range_low": float(o.range_low), "range_high": float(o.range_high), "range_kind": "leave one place out (11 places)",
                 "loo_low": float(o.range_low), "loo_high": float(o.range_high),
                 "note": "D-11 average scaled to a 15% district by the pooled ratio (reference/tod_optiond_line.csv optiond_average_scaled_15); upper line since AQ-075"})
    # What-if (AQ-075): the 2x2 minus the fake-years (pre-trend) effect, from the T2b-PT check
    pt = pd.read_csv(REFERENCE / "tod_causal_line_age_pretrend.csv")
    ta2 = pt[(pt.version == "trend-adjusted") & (pt["row"] == "upper")].iloc[0]
    fk = pt[(pt.version == "fake, same places") & (pt["row"] == "effect") & (pt["name"] == "law_near_new_lines")].iloc[0]
    rows.append({"line": "whatif_2x2_trend_adjusted", "effect_per_100_acres": round(float(ta2.value), 3),
                 "extra_homes_2027_2031": round(float(ta2.wisconsin), 1),
                 "range_low": round(float(ta2.wisconsin_lo90), 1), "range_high": round(float(ta2.wisconsin_hi90), 1),
                 "range_kind": "90% interval (paired place bootstrap)",
                 "loo_low": round(float(ta2.wisconsin_loo_low), 1), "loo_high": round(float(ta2.wisconsin_loo_high), 1),
                 "note": f"T2b-PT: 2x2 near new lines minus the fake-years effect on the same places ({float(fk.value):.1f} per 100 lot "
                         f"acres a year, 90% {float(fk.lo90):.1f} to {float(fk.hi90):.1f}; the before-reform check failed); reference/tod_causal_line_age_pretrend.csv"})
    # Beside the central
    t = pd.read_csv(REFERENCE / "tod_causal_line_age.csv")
    m3 = t[(t["row"] == "pooled") & (t["place"] == "M3 | all 11")].iloc[0]
    rows.append({"line": "beside_line_age_m3", "effect_per_100_acres": round(float(m3.M3), 3),
                 "extra_homes_2027_2031": round(float(m3.M3) * k, 1), "range_low": round(float(m3.M3_lo90) * k, 1),
                 "range_high": round(float(m3.M3_hi90) * k, 1), "range_kind": "90% interval",
                 "loo_low": round(float(m3.loo_low) * k, 1), "loo_high": round(float(m3.loo_high) * k, 1),
                 "note": "T2 line-age matched (M3, all 11): each reform stop compared with stops of a similar line age"})
    ta = d.loc["transit_alone"]
    rows.append({"line": "beside_transit_alone", "effect_per_100_acres": round(float(ta.value), 3),
                 "extra_homes_2027_2031": round(float(ta.value) * k, 1), "range_low": round(float(ta.lo90) * k, 1),
                 "range_high": round(float(ta.hi90) * k, 1), "range_kind": "90% interval", "loo_low": float("nan"), "loo_high": float("nan"),
                 "note": "T2b transit alone (new line, no rezoning, minus old line, no rezoning): belongs in the baseline, not the law"})
    out = pd.DataFrame(rows)
    out.to_csv(REFERENCE / "tod_causal_lines.csv", index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
