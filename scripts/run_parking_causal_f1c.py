"""Parking causal framework, test F1c: Seattle car spaces per home, inside vs outside urban centers and villages,
around the 2012 and 2018 parking reforms. docs/parking/CAUSAL_FRAMEWORK_PLAN.md (F1c, locked before counting).

    uv run python scripts/run_parking_causal_f1c.py --check   # writes 50 random parsed rows for hand-checking
    uv run python scripts/run_parking_causal_f1c.py           # counts
Inputs: data/raw/parking_first_stage/seattle_land_use_permits.csv (SDCI, public domain),
        data/raw/parking_first_stage/seattle_zones/urban_centers_villages.geojson (Seattle Planning GIS).
Outputs: reference/parking_causal_f1c_summary.csv, reference/parking_causal_f1c_by_year.csv
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from missing_middleware import geom  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

SEED, DRAWS = 20261103, 2000
D = RAW / "parking_first_stage"
CUT_2012, CUT_2018 = pd.Timestamp("2012-06-01"), pd.Timestamp("2018-05-01")
LEFT_OUT_ZONES = {"Center_City"}  # Downtown, Uptown, South Lake Union: no minimum before either reform
WORDS = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen "
                                    "fifteen sixteen seventeen eighteen nineteen twenty".split())}
NUM = r"(\d{1,4}|" + "|".join(WORDS) + r")"


def num(s: str) -> int:
    s = s.lower()
    return WORDS[s] if s in WORDS else int(s)


def parse_car(t: str):
    t = t.replace(",", "")
    if re.search(r"\bno (?:on-?site |off-street |vehicular |vehicle |auto(?:mobile)? )?parking\b", t, re.I):
        return 0
    m = re.search(r"parking for (?:approximately |approx\. |up to |about )?" + NUM + r"\s+(?:vehicles?|cars?)", t, re.I) \
        or re.search(NUM + r"\s+(?:vehicular |vehicle |car |auto |surface |below[- ]grade |structured |underground )?parking (?:spaces?|stalls?)", t, re.I) \
        or re.search(r"parking for " + NUM + r"\b", t, re.I)
    return num(m.group(1)) if m else None


def parse_homes(t: str):
    t = t.replace(",", "")
    m = re.findall(NUM + r"(?:-| )(?:residential |apartment |dwelling |live-work |townhouse |rowhouse |condominium )?units?\b", t, re.I)
    sedu = re.findall(NUM + r" small efficiency dwelling units?", t, re.I)
    vals = [num(x) for x in m] + [num(x) for x in sedu]
    return max(vals) if vals else None


def load() -> pd.DataFrame:
    d = pd.read_csv(D / "seattle_land_use_permits.csv", low_memory=False)
    d = d[~d["StatusCurrent"].isin(["Canceled", "Withdrawn"])]
    d = d[d["PermitNum"].astype(str).str.endswith("-LU")]
    desc = d["Description"].fillna("").astype(str)
    d = d[~desc.str.contains(r"\bcancel", case=False)]
    desc = d["Description"].fillna("").astype(str)
    d = d.assign(car=desc.map(parse_car), homes_text=desc.map(parse_homes),
                 applied=pd.to_datetime(d["AppliedDate"], errors="coerce"))
    d["homes"] = pd.to_numeric(d["HousingUnitsAdded"], errors="coerce").where(lambda s: s > 0, d["homes_text"])
    return d


def zones(d: pd.DataFrame) -> pd.Series:
    lay = geom.read_geojson(D / "seattle_zones" / "urban_centers_villages.geojson")
    keep = [i for i, a in enumerate(lay.attrs["UVDA"]) if a not in LEFT_OUT_ZONES and not str(lay.attrs["UV_TYPE"].iloc[i]).startswith("MIC")]
    cc = [i for i, a in enumerate(lay.attrs["UVDA"]) if a in LEFT_OUT_ZONES]
    x, y = d["Longitude"].astype(float).values, d["Latitude"].astype(float).values
    inside = geom.points_in_any(x, y, [lay.polys[i] for i in keep])
    center = geom.points_in_any(x, y, [lay.polys[i] for i in cc])
    return pd.Series(np.where(center, "center_city", np.where(inside, "inside", "outside")), index=d.index)


def ratio(d):
    return d["car"].sum() / d["homes"].sum()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--check-out", default="f1c_check.csv")
    a = ap.parse_args()
    d = load()
    if a.check:
        s = d[d["car"].notna() & d["homes"].notna()].sample(50, random_state=SEED)
        out = Path(a.check_out)
        s[["PermitNum", "Description", "HousingUnitsAdded", "homes", "car"]].to_csv(out, index=False)
        print(out)
        return
    n0 = len(d)
    d = d[d["homes"].notna() & d["car"].notna() & d["applied"].notna() & d["Latitude"].notna()]
    d = d[d["homes"] >= 5]
    d = d.sort_values("applied").drop_duplicates("OriginalAddress1", keep="last")
    d["zone"] = zones(d)
    rng = np.random.default_rng(SEED)

    def cells(lo, cut, hi):
        f = lambda z, a, b: d[(d["zone"] == z) & (d["applied"] >= a) & (d["applied"] < b)]  # noqa: E731
        return f("inside", lo, cut), f("inside", cut, hi), f("outside", lo, cut), f("outside", cut, hi)

    rows = []
    for lab, (lo, cut, hi) in (("2012 reform", (pd.Timestamp("2006-01-01"), CUT_2012, CUT_2018)),
                               ("2018 reform", (CUT_2012, CUT_2018, pd.Timestamp("2030-01-01")))):
        ib, ia, ob, oa = cells(lo, cut, hi)
        est = (ratio(ia) - ratio(ib)) - (ratio(oa) - ratio(ob))
        bs = []
        for _ in range(DRAWS):
            s_ = [x.iloc[rng.integers(0, len(x), len(x))] for x in (ib, ia, ob, oa)]
            bs.append((ratio(s_[1]) - ratio(s_[0])) - (ratio(s_[3]) - ratio(s_[2])))
        p05, p95 = np.percentile(bs, [5, 95])
        rows.append(dict(contrast=f"{lab}: inside minus outside (DiD)", inside_before=ratio(ib), inside_after=ratio(ia),
                         outside_before=ratio(ob), outside_after=ratio(oa), n_inside_before=len(ib), n_inside_after=len(ia),
                         n_outside_before=len(ob), n_outside_after=len(oa), difference=est, p05=p05, p95=p95,
                         mde=1.645 * np.std(bs, ddof=1),
                         reading="binding (fewer spaces per home)" if p95 < 0 else ("more spaces per home" if p05 > 0 else "interval includes 0")))
    S = pd.DataFrame(rows)
    S["note"] = f"{n0} land-use rows after dropping canceled/withdrawn; {len(d)} projects of 5+ homes with homes, car spaces, date and location (one per address)"
    S.to_csv(REFERENCE / "parking_causal_f1c_summary.csv", index=False)
    Y = d.assign(year=d["applied"].dt.year).groupby(["zone", "year"]).apply(
        lambda g: pd.Series(dict(projects=len(g), spaces_per_home=ratio(g), share_zero=(g["car"] == 0).mean())), include_groups=False).reset_index()
    Y.to_csv(REFERENCE / "parking_causal_f1c_by_year.csv", index=False)
    pd.set_option("display.width", 250)
    print(S.round(3).to_string(index=False))
    print(Y.pivot(index="year", columns="zone", values="spaces_per_home").round(2).to_string())


if __name__ == "__main__":
    main()
