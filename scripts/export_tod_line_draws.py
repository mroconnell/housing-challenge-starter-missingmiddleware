"""Bootstrap draws for the three TOD lines in the tool (lower 3,958; central 10,028; upper 12,521), for combining TOD
with other scenarios draw by draw. The draws were never saved, so they are regenerated here with the original code and
seeds (nothing is re-implemented; the functions are imported).

    OMP_NUM_THREADS=1 .venv/bin/python scripts/export_tod_line_draws.py

Lower: the Test 2 edge-test pooled floor (run_tod_causal_edge_expand, pool "(a) original places", filter (a) level
    balance, 5 places, main 91 m bandwidth). Pool membership is the published one (read from the cached lot-part
    results). Each place's segment bootstrap is re-run with the original seed stream [SEED, place index] and 2,000 draws
    instead of 1,000: the main variant is the first use of each place's stream, so draws 1-1,000 equal the published
    draws exactly (checked here), and the published 2,279 to 5,791 is reproduced from them. Pooled draw = mean of the
    5 place draws; homes = pooled x the floor factor F_WI (88.25 -> 3,958).
Central: place bootstrap of the 11 D-11 places' 1/4-mile effects (run_tod_causal_central_pretrend.real_effect,
    draw_places, boot_means; seed 20261103, 2,000 draws); homes = mean x 298.97 (33.5373 -> 10,028).
Upper: central draws x 12,521 / 10,028.

Writes reference/tod_line_draws.csv and reference/tod_line_draws_meta.json (no lot rows, no parcel ids). Reads the
cached files under data/processed/ and never writes there.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from missing_middleware.paths import REFERENCE  # noqa: E402

import run_tod_causal_edge as E  # noqa: E402
import run_tod_causal_edge_expand as X  # noqa: E402
import run_tod_causal_central_pretrend as C  # noqa: E402

DRAWS = 2000
OUT_CSV = REFERENCE / "tod_line_draws.csv"
OUT_META = REFERENCE / "tod_line_draws_meta.json"
LOWER_POINT, CENTRAL_POINT, UPPER_POINT = 3958, 10028, 12521
LOWER_PUBLISHED_90 = (2279, 5791)
CENTRAL_PUBLISHED_90_PER100 = (16.3, 51.4)
TOOL_LOO = {"central": (7580, 12010), "upper": (9089, 16771)}
POOL_LABEL, FILT, VMAIN = "(a) original 11 places, place level", "a", "main (91 m)"


def ci(x):
    return float(np.percentile(x, 5)), float(np.percentile(x, 95))


# ---------------------------------------------------------------------------------------------------------- lower
def lower_draws() -> tuple[np.ndarray, dict]:
    units = X.load("lots")                                    # cached Test 2 expansion lot part (read only)
    orig = [u for u in units if u["section"].startswith("original")]
    _, pm, bflag = X.group_pool(orig, POOL_LABEL, FILT)
    f = X.floor_row("(a) original places", pm, bflag, FILT)
    assert f["variant"] == f"uses {VMAIN}", f["variant"]
    pooled_places = f["units_in_pool"].split(";")
    assert f["n_units"] == 5, f["n_units"]
    pub = (round(f["wisconsin_floor_low"]), round(f["wisconsin_floor_high"]))
    assert pub == LOWER_PUBLISHED_90 and round(f["wisconsin_direct_only_floor_2027_2031"]) == LOWER_POINT, (pub, f)

    # re-run each pooled place's main-variant segment bootstrap with its original stream and 2,000 draws
    PL = X.places()
    idx = {p: i for i, p in enumerate(PL)}
    E.DRAWS = DRAWS                                           # read by E.boot at call time
    per_place, points = [], []
    for place in pooled_places:
        cases, pi = PL[place], idx[place]
        water, art = E.water_polys(place), E.arterials(place)
        parts = {c: X.orig_sample(c, water, art) for c in cases}
        S = pd.concat([p for p in parts.values() if len(p)], ignore_index=True)          # as part_lots
        S = S[(S.s.abs() <= 200) | (S.s_lotmid.abs() <= 200)]
        S = X.k_weight(S, len(cases))
        rng = np.random.default_rng([X.SEED, pi])
        kw = X.VARIANTS[VMAIN]
        T = E.select(S, kw["h"], kw.get("dist", "s"), kw.get("donut", 0.0), kw.get("half", False), kw.get("no_art", False))
        pt, dr = E.boot(T, "chg", rng)                        # first rng use in run_unit, as published
        cached = next(u for u in orig if u["unit"] == place)
        assert np.isclose(pt, X.main_row(cached)["edge_effect_per_100_acres_per_year"]), (place, pt)
        assert np.allclose(dr[:1000], cached["draws"][VMAIN], equal_nan=True), f"{place}: draws 1-1000 differ"
        per_place.append(dr); points.append(pt)
        print(f"lower: {place} (stream [{X.SEED}, {pi}]) {pt:.2f}; draws 1-1,000 match the published run", flush=True)
    pooled = np.nanmean(np.stack(per_place), axis=0)
    assert np.allclose(pooled[:1000], f["_draws"], equal_nan=True)
    info = {"pooled_places": pooled_places, "place_streams": {p: [X.SEED, idx[p]] for p in pooled_places},
            "point_per100ac": float(np.mean(points)), "factor": float(X.F_WI),
            "published_90_first_1000_draws_homes": [float(v * X.F_WI) for v in ci(pooled[:1000])]}
    return pooled, info


# ---------------------------------------------------------------------------------------------------------- central
def central_draws() -> tuple[np.ndarray, dict]:
    rows = []
    for f in sorted(C.OUT.glob("lots_*.parquet")):
        case = f.stem.removeprefix("lots_")
        place = C.place_of(case)
        if place:
            rows.append({"place": place, "case": case, "real": C.real_effect(case)})
    real_all = pd.DataFrame(rows).dropna(subset=["real"]).groupby("place").real.mean()
    assert len(real_all) == 11 and round(real_all.mean(), 4) == C.SANITY_MEAN, real_all.mean()
    d = C.boot_means(real_all, C.draw_places(sorted(real_all.index), C.SEED, DRAWS))
    lo, hi = C.ci(d)
    assert (round(lo, 1), round(hi, 1)) == CENTRAL_PUBLISHED_90_PER100, (lo, hi)
    return d, {"places": {C.display(p): float(v) for p, v in real_all.items()}, "point_per100ac": float(real_all.mean()),
               "factor": float(C.WI_FACTOR), "per100ac_90": [lo, hi]}


def main() -> None:
    lo_d, lo_info = lower_draws()
    ce_d, ce_info = central_draws()
    up_ratio = UPPER_POINT / CENTRAL_POINT
    D = pd.DataFrame({"draw": np.arange(1, DRAWS + 1),
                      "lower_homes": lo_d * X.F_WI, "central_homes": ce_d * C.WI_FACTOR,
                      "upper_homes": ce_d * C.WI_FACTOR * up_ratio,
                      "lower_per100ac": lo_d, "central_per100ac": ce_d})
    D.to_csv(OUT_CSV, index=False, float_format="%.4f")

    def summ(col, point):
        x = D[col].to_numpy()
        lo, hi = ci(x)
        return {"point": point, "median": float(np.median(x)), "mean": float(x.mean()), "p05": lo, "p95": hi}

    meta = {
        "file": "reference/tod_line_draws.csv",
        "script": "scripts/export_tod_line_draws.py",
        "draws": {"lower": DRAWS, "central": DRAWS, "upper": DRAWS},
        "seeds": {"lower": f"segment bootstrap, numpy default_rng([{X.SEED}, place index]) per place (place index in "
                           f"run_tod_causal_citywide.places() order): {lo_info['place_streams']}",
                  "central": f"place bootstrap, numpy default_rng({C.SEED})", "upper": "same draws as central"},
        "units": {"*_homes": "Wisconsin extra homes permitted, 2027-2031 (five years)",
                  "*_per100ac": "extra homes per 100 lot acres a year (lower: edge effect at the district edge, 91 m "
                                "bandwidth; central: 1/4-mile station-area effect)"},
        "methods": {
            "lower": "Test 2 edge-test pooled floor (scripts/run_tod_causal_edge_expand.py, pool (a) original places, filter "
                     "(a) level balance, main 91 m variant): 5 places " + "; ".join(lo_info["pooled_places"]) + ". Each "
                     "place's segment bootstrap re-run with its original seed stream and 2,000 draws; draws 1-1,000 equal "
                     "the published 1,000 exactly. Pooled draw = mean of the 5 place draws. Homes = pooled x "
                     f"{lo_info['factor']:.4f} (15% x 4,874.1 / 100 x 5 x 1.2269). Pool membership fixed as published.",
            "central": "Place bootstrap of the 11 D-11 places' 1/4-mile effects (run_tod_causal_central_pretrend.real_effect; "
                       "New York and Philadelphia averaged over their rezonings), places resampled with replacement, mean "
                       f"per draw. Homes = mean x {ce_info['factor']:.4f}.",
            "upper": f"central draws x 12,521 / 10,028 = {up_ratio:.6f} (central scaled to a 15% district).",
        },
        "pairing": "Lower draws come from a different procedure (segment bootstrap of edge places) and are independent of "
                   "central and upper draws; pair them by row only as independent draws. Upper is perfectly tied to "
                   "central (same row = same place resample).",
        "point_values_homes": {"lower": LOWER_POINT, "central": CENTRAL_POINT, "upper": UPPER_POINT},
        "point_values_per100ac": {"lower": lo_info["point_per100ac"], "central": ce_info["point_per100ac"]},
        "summary_homes": {"lower": summ("lower_homes", LOWER_POINT), "central": summ("central_homes", CENTRAL_POINT),
                          "upper": summ("upper_homes", UPPER_POINT)},
        "checks": {
            "lower_published_90_homes": list(LOWER_PUBLISHED_90),
            "lower_first_1000_draws_90_homes": lo_info["published_90_first_1000_draws_homes"],
            "central_published_90_per100ac": list(CENTRAL_PUBLISHED_90_PER100),
            "central_reproduced_90_per100ac": ce_info["per100ac_90"],
        },
        "caveat": "The tool's displayed ranges for central (7,580 to 12,010) and upper (9,089 to 16,771) are "
                  "leave-one-place-out ranges, not bootstrap intervals. The bootstrap 90% intervals here are wider. The "
                  "lower's displayed range (2,279 to 5,791) is its bootstrap 90% interval.",
        "tool_displayed_ranges_homes": {"lower": list(LOWER_PUBLISHED_90) + ["bootstrap 90%"],
                                        "central": list(TOOL_LOO["central"]) + ["leave one place out"],
                                        "upper": list(TOOL_LOO["upper"]) + ["leave one place out"]},
        "central_place_effects_per100ac": ce_info["places"],
    }
    OUT_META.write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta["summary_homes"], indent=2))
    print(json.dumps(meta["checks"], indent=2))


if __name__ == "__main__":
    main()
