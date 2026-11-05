"""Test 52d placebo lists (docs/parking/CAUSAL_FRAMEWORK_PLAN.md, "Test 52", audit fix 4). Committed before any join
to outcomes: this script reads no permit or effect values.

    uv run --all-extras python scripts/build_parking_t52_placebo_lists.py

52d.2 (houses): the 74 repeal places (batch 2026-11-05 sample) whose old minimum for a house was 2 spaces or fewer.
  Sources: reference/parking_reform_type_15.csv (`req_before_house`, ordinance-read coding of 15 places) where it gives a
  number, else reference/parking_old_minimums.csv (`old_min_single_family`). Places with no coded house minimum are left out.
52d.3 (ADU-only reform places): Mercatus ADU taxonomy places with an ADU ordinance effective 2015-2022, minus PRN-map
  places, the 74 and their pools. The local copy (data/raw/mercatus_adu_taxonomy_2025/page.html) is checked for
  ordinance years; if it has none, the list is written empty with the reason, and the item stops (caller's instruction).
Outputs: reference/parking_t52_d_houses_list.csv, reference/parking_t52_d_adu_list.csv, reference/parking_t52_d_lists_summary.csv
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
REF = ROOT / "reference"
BATCH = REF / "batch_2026-11-05"
MERCATUS = ROOT / "data" / "raw" / "mercatus_adu_taxonomy_2025" / "page.html"
MAX_HOUSE_MIN = 2.0


def read_old_minimums() -> tuple[pd.DataFrame, list[str]]:
    """Read parking_old_minimums.csv. One committed row (Emeryville) has an unquoted comma inside source_urls, which
    gives 11 fields against a 10-field header; the extra fields are joined back into source_urls (reported)."""
    rows = list(csv.reader((REF / "parking_old_minimums.csv").open(encoding="utf-8")))
    head, fixed, notes = rows[0], [], []
    i_src = head.index("source_urls")
    for r in rows[1:]:
        if len(r) > len(head):
            extra = len(r) - len(head)
            notes.append(f"{r[1]}: {len(r)} fields, source_urls rejoined")
            r = r[:i_src] + [",".join(r[i_src:i_src + extra + 1])] + r[i_src + extra + 1:]
        fixed.append(r)
    return pd.DataFrame(fixed, columns=head), notes


def first_number(s) -> float | None:
    m = re.match(r"\s*(\d+(?:\.\d+)?)", str(s))
    return float(m.group(1)) if m else None


def houses_list() -> tuple[pd.DataFrame, list[str]]:
    # the 74: identity columns only (no effect values are read)
    real = pd.read_csv(BATCH / "parking_expanded_effects.csv", usecols=["prn_key", "place", "state", "key", "event_year",
                                                                          "status", "outcome", "source"])
    real = real[(real["status"] == "included") & (real["outcome"] == "all")].drop(columns=["status", "outcome"])
    real = real.drop_duplicates("prn_key").reset_index(drop=True)
    assert len(real) == 74, len(real)
    om, notes = read_old_minimums()
    om = om.drop_duplicates("prn_key").set_index("prn_key")
    rt = pd.read_csv(REF / "parking_reform_type_15.csv")
    rt = rt.set_index(rt["place"].str.strip() + "|" + rt["state"].str.strip())
    rows = []
    for r in real.itertuples(index=False):
        base_place = "South Bend" if str(r.place).startswith("South Bend") else r.place
        rt_val = rt["req_before_house"].get(f"{base_place}|{r.state}")
        om_val = om["old_min_single_family"].get(r.prn_key) if r.prn_key in om.index else None
        n_rt, n_om = first_number(rt_val), first_number(om_val)
        if n_rt is not None:
            v, src = n_rt, "parking_reform_type_15.csv req_before_house"
        elif n_om is not None:
            v, src = n_om, "parking_old_minimums.csv old_min_single_family"
        else:
            v, src = None, ""
        if v is None:
            why = "no coded house minimum" + ("" if r.prn_key in om.index or rt_val is not None else " (place not in either file)")
            use = False
        else:
            use = v <= MAX_HOUSE_MIN
            why = f"house minimum {v:g} {'<=' if use else '>'} {MAX_HOUSE_MIN:g}"
        conflict = n_rt is not None and n_om is not None and n_rt != n_om
        rows.append(dict(prn_key=r.prn_key, place=r.place, state=r.state, key=r.key, event_year=int(r.event_year),
                         source=r.source, house_min=v, house_min_source=src,
                         reform_type_value=None if rt_val is None else str(rt_val),
                         old_minimums_value=None if om_val in (None, "") else str(om_val),
                         sources_differ=conflict, in_list=use, reason=why))
    return pd.DataFrame(rows), notes


def adu_list() -> tuple[pd.DataFrame, str]:
    cols = ["place", "state", "adu_ordinance_year", "key", "event_year"]
    html = MERCATUS.read_text(encoding="utf-8", errors="replace") if MERCATUS.exists() else ""
    blocked = "Attention Required! | Cloudflare" in html or "Sorry, you have been blocked" in html
    years = re.findall(r"\b20(?:1[5-9]|2[0-2])\b", re.sub(r"<script.*?</script>", "", html, flags=re.S))
    if not html:
        return pd.DataFrame(columns=cols), "stopped: local Mercatus copy missing"
    if blocked or not years:
        return pd.DataFrame(columns=cols), ("stopped: the local Mercatus copy (data/raw/mercatus_adu_taxonomy_2025/page.html, "
                                            f"{len(html):,} bytes) is a Cloudflare 'you have been blocked' page with no "
                                            "places and no ordinance years")
    raise SystemExit("Mercatus page has content; a parser for it is not written yet")


def main() -> None:
    h, notes = houses_list()
    h.to_csv(REF / "parking_t52_d_houses_list.csv", index=False)
    a, a_status = adu_list()
    a.to_csv(REF / "parking_t52_d_adu_list.csv", index=False)
    summ = [dict(list="52d.2 houses", places=int(h["in_list"].sum()), of=len(h),
                 note=f"left out, no coded house minimum: {int(h['house_min'].isna().sum())}; above {MAX_HOUSE_MIN:g}: "
                      f"{int((h['house_min'] > MAX_HOUSE_MIN).sum())}; sources differ: {int(h['sources_differ'].sum())}; "
                      + ("; ".join(notes) if notes else "no read fixes")),
            dict(list="52d.3 ADU-only", places=len(a), of=None, note=a_status)]
    pd.DataFrame(summ).to_csv(REF / "parking_t52_d_lists_summary.csv", index=False)
    print(h[["place", "state", "event_year", "house_min", "house_min_source", "sources_differ", "in_list", "reason"]].to_string())
    print(pd.DataFrame(summ).to_string())


if __name__ == "__main__":
    main()
