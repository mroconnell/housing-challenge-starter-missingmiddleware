"""Test 50 (CAUSAL_FRAMEWORK_PLAN.md): San Francisco sampling frame and draw, before any project record is read.

Frame: DataSF "Planning Department Records - Projects" (qvu5-m3a2): PRJ records with 5+ net new homes, open_date in the
window, approved planning decision. Zoning from DataSF "Parcels - Active and Retired" (acdm-wktn) by block/lot (current
zoning, a proxy). Section: Sec. 151.1 (no minimums before 2019) vs Sec. 151 (minimums), by zoning-code prefix using the
151.1 district list as of 2018 (Planning Code Sec. 151.1(a)); every drawn project's section is re-checked against its
case report. Draw: up to 10 from Sec. 151 and the rest from Sec. 151.1 to 15 per window (seed 20261105, sorted by id).

    uv run python scripts/draw_parking_t50_sf_sample.py
Outputs: reference/parking_t50_sf_frame_counts.csv, reference/parking_t50_sf_sample.csv (record id, window, section,
zoning code, units net; no addresses). Raw downloads: data/raw/parking_t50/ (with download date).
"""
from __future__ import annotations

import datetime as dt
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

UA = {"User-Agent": "missing-middleware-research/1.0 (public data)"}
SEED = 20261105
WINDOWS = {"before": ("2016-01-01", "2019-01-20"), "after": ("2019-01-21", "2022-12-31")}
# Sec. 151.1 districts (no residential minimums before 2019), as of 2018, matched by zoning-code prefix
S1511_PREFIX = ("C-3", "DTR", "RC-", "RCD", "NCT", "RTO", "UMU", "MUG", "MUO", "MUR", "SPD", "WMUG", "WMUO", "WMUR",
                "RED", "SALI", "SLI", "SLR", "CCB", "CRNC", "CVR", "RSD", "MB-", "TB ", "C-3-")
OUT = RAW / "parking_t50"


def get(url):
    return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read())


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    where = "number_of_units_net >= 5 AND open_date between '2016-01-01' and '2022-12-31'"
    q = urllib.parse.urlencode({"$select": "record_id,record_type,record_status,open_date,project_decision,number_of_units_net,block,lot",
                                "$where": where, "$limit": 50000})
    rows = get("https://data.sf.gov/resource/qvu5-m3a2.json?" + q)
    (OUT / "qvu5-m3a2_frame.json").write_text(json.dumps({"downloaded": dt.date.today().isoformat(), "query": q, "rows": rows}))
    F = pd.DataFrame(rows)
    F["open_date"] = pd.to_datetime(F["open_date"])
    for c in ("block", "lot"):
        if c not in F:
            F[c] = None
    F["blklot"] = F["block"].fillna("").astype(str).str.strip() + F["lot"].fillna("").astype(str).str.strip()
    bl = sorted(b for b in set(F["blklot"]) if len(b) >= 5)
    zz = []
    for i in range(0, len(bl), 200):
        ids = ",".join(f"'{b}'" for b in bl[i:i + 200])
        zz += get("https://data.sf.gov/resource/acdm-wktn.json?" + urllib.parse.urlencode(
            {"$select": "blklot,zoning_code", "$where": f"blklot in ({ids})", "$limit": 5000}))
    Z = pd.DataFrame(zz).drop_duplicates("blklot").set_index("blklot")["zoning_code"] if zz else pd.Series(dtype=str)
    (OUT / "acdm-wktn_zoning.json").write_text(json.dumps({"downloaded": dt.date.today().isoformat(), "rows": zz}))
    F["zoning_code"] = F["blklot"].map(Z)
    F["section"] = np.where(F["zoning_code"].fillna("").str.upper().str.startswith(S1511_PREFIX), "151.1",
                            np.where(F["zoning_code"].isna(), "unknown", "151"))
    F["window"] = np.select([F["open_date"].between(*WINDOWS["before"]), F["open_date"].between(*WINDOWS["after"])],
                            ["before", "after"], "")
    F["approved"] = F["project_decision"].fillna("").str.lower().str.startswith("approv")
    counts = F[F["window"] != ""].groupby(["window", "section", "approved", "record_status"]).size().rename("records").reset_index()
    counts.to_csv(REFERENCE / "parking_t50_sf_frame_counts.csv", index=False)
    rng = np.random.default_rng(SEED)
    picks = []
    for w in ("before", "after"):
        fr = F[(F["window"] == w) & F["approved"]].sort_values("record_id")
        s151 = fr[fr["section"] == "151"]
        s1511 = fr[fr["section"] != "151"]
        a = s151.iloc[rng.permutation(len(s151))[: min(10, len(s151))]]
        b = s1511.iloc[rng.permutation(len(s1511))[: 15 - len(a)]]
        for draw_order, (_, r) in enumerate(pd.concat([a, b]).iterrows(), 1):
            picks.append(dict(window=w, draw_order=draw_order, record_id=r["record_id"], section=r["section"],
                              zoning_code=r["zoning_code"], units_net=r["number_of_units_net"], open_date=r["open_date"].date()))
        # replacements in draw order: the remaining records, same strata order
        rest = pd.concat([s151.drop(a.index), s1511.drop(b.index)])
        for k, (_, r) in enumerate(rest.iloc[rng.permutation(len(rest))].iterrows(), 1):
            picks.append(dict(window=w, draw_order=100 + k, record_id=r["record_id"], section=r["section"],
                              zoning_code=r["zoning_code"], units_net=r["number_of_units_net"], open_date=r["open_date"].date(),
                              replacement=True))
    P = pd.DataFrame(picks)
    P.to_csv(REFERENCE / "parking_t50_sf_sample.csv", index=False)
    print(counts.to_string(index=False))
    print(P[P["draw_order"] < 100].groupby(["window", "section"]).size())


if __name__ == "__main__":
    main()
