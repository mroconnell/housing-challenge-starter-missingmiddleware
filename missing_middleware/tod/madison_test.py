"""Madison TOD overlay test (docs/tod/MADISON_TEST_PREREG.md; judging rules in GATE3_MODEL_SPEC.md sections 4 and 9).

The plan and method A's blind prediction were committed before any permit was counted by overlay. This module holds
the pieces that can be tested without geography; scripts/run_tod_madison_test.py runs the count.

- Periods (prereg section 4): before 2017-2022, after 2023-2025, 2026 shown only.
- Outcome (section 3): Dwell (dwelling units added) on BLDNRC and BLDNCC permits by issue date, one row per permit
  number (missing_middleware.permits.pipeline.dedupe: earliest issue date).
- Areas: the uniform area rule of CASE_ANALYSIS_PLAN.md section 7 (missing_middleware.tod.cases.uniform_areas).
  Lots rezoned outside the reform during 2017-2025 are read from the City's zoning map amendment ordinances
  (MGO 28.022, Legistar); lots outside the City on 1 January 2016 had zoning assigned during the window.
- Estimate, interval and sensitivities: missing_middleware.tod.cases (DiD of mean yearly rates, project bootstrap,
  2,000 draws, fixed seed).
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from . import cases as K

BEFORE = list(range(2017, 2023))
AFTER = [2023, 2024, 2025]
AFTER_ROUTE_A = [2024, 2025]
SHOWN = [2026]
WINDOW = (2017, 2025)
PERMIT_TYPES = ("BLDNRC", "BLDNCC")
LARGE_UNITS = 10
OVERLAY_EFFECTIVE = "2023-01-26"  # ORD-23-00013, passed 2023-01-17, enactment (publication) 2023-01-26 (Legistar 74703)

# Method A's committed prediction (reference/tod_madison_test_predictions.csv, commit bf6d347)
PRED = 0.251
PRED_LOW = 0.1364
PRED_HIGH = 0.3815
R_TYPICAL, R_LOW, R_HIGH = 0.6713, 0.3649, 1.0204
DOSE_OVERLAY = 0.3738


# --------------------------------------------------------------------------- rezonings (Legistar)

_ADDR_STARTS = [re.compile(p, re.I) for p in (
    r"(?:generally\s+)?located\s+at\s+", r"propert(?:y|ies)\s+at\s+", r"addressed\s+as\s+",
    r"zoning\s+of(?:\s+the)?(?:\s+[a-z0-9 ]*?\s+of)?\s+(?=\d)")]
_ADDR_END = re.compile(
    r"\s+(?:from\b|to\s+(?:approve|amend|assign|the\b|PD\b|SR-|TR-)|\(District|\(Ald|\(part\s+of)"
    r"|,?\s*\d+(?:st|nd|rd|th)?\s+Ald|\.\s*\(District|\.\s*$", re.I)


def is_map_amendment(title: str) -> bool:
    """A zoning map amendment: creates a section 28.022-xxxxx. Text amendments of 28.022(3)/(5) are not."""
    return bool(re.search(r"creat\w*\s+(?:Section\s+)?28\.022\s*-+\s*\d", title or "", re.I))


def window_rezonings(matters: list[dict], first: int = WINDOW[0], last: int = WINDOW[1]) -> pd.DataFrame:
    """Passed zoning map amendments with an enactment (else passed) date in [first, last]."""
    rows = []
    for m in matters:
        d = m.get("MatterEnactmentDate") or m.get("MatterPassedDate")
        if m.get("MatterStatusName") != "Passed" or not d or not is_map_amendment(m.get("MatterTitle", "")):
            continue
        y = int(d[:4])
        if first <= y <= last:
            rows.append({"matter_id": m["MatterId"], "file": m.get("MatterFile"), "date": d[:10], "year": y,
                         "name": m.get("MatterName") or "", "title": m.get("MatterTitle") or ""})
    return pd.DataFrame(rows, columns=["matter_id", "file", "date", "year", "name", "title"])


def address_text(title: str, name: str = "") -> str:
    """The address phrase of a rezoning title ("1233-1241 Moorland Road"), else the matter name's."""
    for pat in _ADDR_STARTS:
        m = pat.search(title or "")
        if not m:
            continue
        rest = title[m.end():]
        e = _ADDR_END.search(rest)
        txt = rest[: e.start()] if e else rest[:200]
        if re.match(r"^\d", txt.strip()):
            return txt.strip(" ,.;")
    n = re.sub(r"^(?:Rezon\w*|Rezone)\s+(?:property\s+(?:located\s+)?at\s+|properties\s+located\s+at\s+)?", "", name or "", flags=re.I)
    return n.strip(" ,.;") if re.match(r"^\d", n.strip()) else ""


_NUMS = r"\d+[A-Z]?(?:\s*-\s*\d+[A-Z]?)?"


def split_addresses(text: str) -> list[str]:
    """Split '405-407 & 311 West Gorham Street, 408-430 West Johnson Street' into single address strings.
    Bare numbers take the street of the next piece that names one."""
    t = re.sub(r"\s*(?:,|;|&|/|\band\b|\band(?=\d))\s*", "|", text or "", flags=re.I)
    pieces = [p.strip() for p in t.split("|") if p.strip()]
    out, pending = [], []
    for p in pieces:
        p = re.sub(r"^(?:the\s+\w+\s+approximately\s+\d+\s+feet\s+of|all\s+of|a\s+portion\s+of|portions?\s+of)\s+", "", p, flags=re.I)
        m = re.match(rf"^({_NUMS})(?:\s+(.*))?$", p)
        if not m:
            continue
        num, street = m.group(1).replace(" ", ""), (m.group(2) or "").strip()
        if not street or not re.search(r"[A-Za-z]{2,}", street):
            pending.append(num)
            continue
        for n in pending + [num]:
            out.append(f"{n} {street}")
        pending = []
    return out


NEAR_NUMBER_GAP = 50


def nearest_on_street(numbers: pd.DataFrame, street_key: str, house_nbr: int, max_gap: int = NEAR_NUMBER_GAP):
    """Index of the reference address on the same street with the nearest house number (any parity) within
    max_gap; for rezoning addresses retired by redevelopment. None when there is none."""
    s = numbers[numbers.street_key == street_key]
    if s.empty:
        return None
    gap = (s.house_nbr - house_nbr).abs()
    return gap.idxmin() if gap.min() <= max_gap else None


def range_bounds(addr: str) -> tuple[int, int] | None:
    m = re.match(r"^(\d+)[A-Z]?-(\d+)[A-Z]?\s", addr)
    if not m:
        return None
    a, b = int(m.group(1)), int(m.group(2))
    return (min(a, b), max(a, b)) if a != b else None


# --------------------------------------------------------------------------- permits

def test_permits(raw: pd.DataFrame) -> pd.DataFrame:
    """New-construction permits (BLDNRC, BLDNCC) with Dwell > 0, one row per permit number, issue years 2017-2026."""
    from missing_middleware.permits.pipeline import dedupe

    d = dedupe(raw[raw["permit_type"].isin(PERMIT_TYPES)])
    d["year"] = d["issue_date"].dt.year
    d = d[(d["units_raw"].fillna(0) > 0) & d["year"].between(BEFORE[0], SHOWN[-1])].copy()
    d["units"] = d["units_raw"].astype(float)
    return d.reset_index(drop=True)


def project_ids(address_key: pd.Series, year: pd.Series) -> pd.Series:
    """Permits at the same address in the same year are one project (prereg section 5)."""
    return address_key.astype(str) + "|" + year.astype(int).astype(str)


def street_only(addr: str) -> str:
    """Street name without the house number (for the unmatched-permit list)."""
    s = re.sub(r"^\s*\d+[A-Z]?(?:\s*-\s*\d+[A-Z]?)?\s+", "", str(addr or "").upper())
    return re.sub(r"\s+(?:UNIT|APT|STE|#)\s*\S+$", "", s).strip()


# --------------------------------------------------------------------------- estimates and judging

def estimate(permits: pd.DataFrame, denom: dict, before=BEFORE, after=AFTER, treat=K.TREAT, comp=K.COMP,
             scale: float = 1.0, interval: bool = True) -> dict:
    """DiD of mean yearly rates and (optionally) the 90% project-bootstrap interval."""
    e = K.did(permits, denom, list(before), list(after), treat=treat, comp=comp, scale=scale)
    lo = hi = float("nan")
    if interval:
        lo, hi, _ = K.bootstrap_did(permits, denom, list(before), list(after), treat=treat, comp=comp, scale=scale)
    return {**e, "low": lo, "high": hi}


def per_far(value: float, dose: float) -> float:
    return value / dose if dose else float("nan")


def judge(pred: float, low: float, high: float) -> str:
    """Spec section 9: method A is confirmed in Wisconsin if the measured 90% interval contains its prediction."""
    if np.isnan(low) or np.isnan(high):
        return "no interval"
    return "confirmed (prediction inside the measured 90% interval)" if low <= pred <= high else \
        ("not confirmed: prediction above the measured 90% interval" if pred > high
         else "not confirmed: prediction below the measured 90% interval")
