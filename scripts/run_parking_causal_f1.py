"""Parking causal framework, test F1 (first stage): did projects build less parking per home after repeal?
docs/parking/CAUSAL_FRAMEWORK_PLAN.md (locked 2026-11-03; F1 counting rules logged before counting).

Data: Minneapolis Planning Commission approvals 2011-2025, compiled by A. Schieferdecker
(data/raw/parking_first_stage/mpls_planning_commission_schieferdecker.xlsx, fetched by scripts/fetch_parking_first_stage.py).
Read with the standard library (no spreadsheet dependency).

Rules (fixed before counting):
- projects with 5+ homes; a row with an entry in "Later Action" (later resubmitted) is dropped so only the latest
  submission counts;
- downtown rows (no minimum before either repeal) are reported apart and left out of the main contrasts;
- splits: 2015 transit-area cut 2015-05-01; 2021 citywide repeal 2021-05-14 (adoption dates, approximate);
- spaces per home = total car spaces / total homes (homes-weighted), with the project median beside it;
- 90% interval of after minus before from 2,000 resamples of projects within each side (seed 20261103);
- "binding" if the interval of the difference is below 0;
- ramp vs floor: spaces per home by year since the 2021 repeal.

    uv run python scripts/run_parking_causal_f1.py
Outputs: reference/parking_causal_f1_summary.csv, reference/parking_causal_f1_by_year.csv
"""
from __future__ import annotations

import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

SEED, DRAWS = 20261103, 2000
XLSX = RAW / "parking_first_stage" / "mpls_planning_commission_schieferdecker.xlsx"
M = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
CUT_2015, CUT_2021 = pd.Timestamp("2015-05-01"), pd.Timestamp("2021-05-14")
COLS = {"A": "date", "B": "name", "D": "neighborhood", "F": "downtown", "G": "homes", "H": "car", "J": "later_action"}


def read_xlsx_year_sheets(path: Path) -> pd.DataFrame:
    z = zipfile.ZipFile(path)
    ss = ["".join(t.text or "" for t in si.iter(M + "t")) for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall(M + "si")]
    sheets = re.findall(r'<sheet [^>]*name="([^"]+)"[^>]*r:id="rId(\d+)"', z.read("xl/workbook.xml").decode())
    rows = []
    for name, rid in sheets:
        if not name.isdigit():
            continue
        for r in ET.fromstring(z.read(f"xl/worksheets/sheet{rid}.xml")).iter(M + "row"):
            if int(r.get("r")) == 1:
                continue
            d = {"sheet": int(name)}
            for c in r.findall(M + "c"):
                col = re.match(r"[A-Z]+", c.get("r")).group()
                if col not in COLS:
                    continue
                v = c.find(M + "v")
                d[COLS[col]] = None if v is None else (ss[int(v.text)] if c.get("t") == "s" else v.text)
            rows.append(d)
    df = pd.DataFrame(rows)
    num = pd.to_numeric(df["date"], errors="coerce")
    df = df[num.notna()].copy()
    df["date"] = [pd.Timestamp(date(1899, 12, 30) + timedelta(days=int(x))) for x in num[num.notna()]]
    for c in ("homes", "car"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["later_action"] = df["later_action"].fillna("").astype(str).str.strip()
    df["downtown"] = df["downtown"].fillna("").astype(str).str.strip().str.upper().str[:1]
    return df


def ratio(d):
    return d["car"].sum() / d["homes"].sum()


def contrast(before, after, label, rng):
    est = ratio(after) - ratio(before)
    bs = []
    for _ in range(DRAWS):
        b = before.iloc[rng.integers(0, len(before), len(before))]
        a = after.iloc[rng.integers(0, len(after), len(after))]
        bs.append(ratio(a) - ratio(b))
    bs = np.array(bs)
    lo, hi = np.percentile(bs, [5, 95])
    return dict(contrast=label, projects_before=len(before), projects_after=len(after),
                homes_before=int(before["homes"].sum()), homes_after=int(after["homes"].sum()),
                spaces_per_home_before=ratio(before), spaces_per_home_after=ratio(after),
                median_before=(before["car"] / before["homes"]).median(), median_after=(after["car"] / after["homes"]).median(),
                share_zero_before=(before["car"] == 0).mean(), share_zero_after=(after["car"] == 0).mean(),
                difference=est, p05=lo, p95=hi, mde=1.645 * bs.std(ddof=1),
                reading="binding (fewer spaces per home)" if hi < 0 else ("more spaces per home" if lo > 0 else "interval includes 0"))


def main() -> None:
    raw = read_xlsx_year_sheets(XLSX)
    checks = dict(rows=len(raw), missing_homes_or_car=int(raw[["homes", "car"]].isna().any(axis=1).sum()),
                  later_resubmitted=int((raw["later_action"] != "").sum()))
    df = raw.dropna(subset=["homes", "car"])
    df = df[(df["homes"] >= 5) & (df["later_action"] == "")]
    nd, dt = df[df["downtown"] != "Y"], df[df["downtown"] == "Y"]
    rng = np.random.default_rng(SEED)
    out = [
        contrast(nd[nd["date"] < CUT_2015], nd[(nd["date"] >= CUT_2015) & (nd["date"] < CUT_2021)],
                 "2015 transit-area cut (outside downtown; citywide, not only transit areas)", rng),
        contrast(nd[(nd["date"] >= CUT_2015) & (nd["date"] < CUT_2021)], nd[nd["date"] >= CUT_2021],
                 "2021 citywide repeal (outside downtown), against 2015-2021", rng),
        contrast(nd[nd["date"] < CUT_2015], nd[nd["date"] >= CUT_2021],
                 "Both reforms: 2021 on against before 2015 (outside downtown)", rng),
        contrast(dt[dt["date"] < CUT_2021], dt[dt["date"] >= CUT_2021],
                 "Downtown (no minimum either side), 2021 on against before: a check on market drift", rng),
    ]
    # Audit fix (2026-11-03): downtown, which had no minimum either side, as the comparison group.
    # Difference = (rest-of-city after minus before) minus (downtown after minus before); resampled within each of 4 cells.
    def dd(nb, na, db, da, label):
        f = lambda: (ratio(na) - ratio(nb)) - (ratio(da) - ratio(db))  # noqa: E731
        est = f()
        bs = []
        for _ in range(DRAWS):
            s_ = [x.iloc[rng.integers(0, len(x), len(x))] for x in (nb, na, db, da)]
            bs.append((ratio(s_[1]) - ratio(s_[0])) - (ratio(s_[3]) - ratio(s_[2])))
        lo, hi = np.percentile(bs, [5, 95])
        return dict(contrast=label, projects_before=len(nb), projects_after=len(na), homes_before=int(nb["homes"].sum()),
                    homes_after=int(na["homes"].sum()), spaces_per_home_before=ratio(nb), spaces_per_home_after=ratio(na),
                    downtown_projects_before=len(db), downtown_projects_after=len(da),
                    downtown_before=ratio(db), downtown_after=ratio(da), difference=est, p05=lo, p95=hi,
                    mde=1.645 * np.std(bs, ddof=1),
                    reading="binding (fewer spaces per home)" if hi < 0 else ("more spaces per home" if lo > 0 else "interval includes 0"))
    w15 = lambda d: (d[d["date"] < CUT_2015], d[(d["date"] >= CUT_2015) & (d["date"] < CUT_2021)])  # noqa: E731
    w21 = lambda d: (d[(d["date"] >= CUT_2015) & (d["date"] < CUT_2021)], d[d["date"] >= CUT_2021])  # noqa: E731
    wall = lambda d: (d[d["date"] < CUT_2015], d[d["date"] >= CUT_2021])  # noqa: E731
    for wf, lab in ((w15, "2015 cut"), (w21, "2021 repeal"), (wall, "both reforms")):
        out.append(dd(*wf(nd), *wf(dt), f"Against downtown (DiD): {lab}, rest of city minus downtown"))
    S = pd.DataFrame(out)
    S["note"] = (f"{checks['rows']} rows read; {checks['missing_homes_or_car']} lacking homes or car spaces; "
                 f"{checks['later_resubmitted']} later resubmitted and dropped; homes 5+ only")
    S.to_csv(REFERENCE / "parking_causal_f1_summary.csv", index=False)
    nd = nd.assign(year=nd["date"].dt.year)
    Y = nd.groupby("year").apply(lambda d: pd.Series(dict(projects=len(d), homes=int(d["homes"].sum()),
                                 spaces=int(d["car"].sum()), spaces_per_home=ratio(d),
                                 median=(d["car"] / d["homes"]).median(), share_zero=(d["car"] == 0).mean())),
                                 include_groups=False).reset_index()
    Y.to_csv(REFERENCE / "parking_causal_f1_by_year.csv", index=False)
    pd.set_option("display.width", 250)
    print(S.drop(columns="note").round(3).to_string(index=False))
    print(S["note"].iloc[0])
    print(Y.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
