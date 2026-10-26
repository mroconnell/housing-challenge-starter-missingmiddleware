"""Benchmark classification of parking reforms from the Parking Reform Network (PRN)
reform map database (github.com/ParkingReformNetwork/reform-map, MIT licence).

Benchmark: "Reduce or eliminate minimum parking requirements" for housing, statewide.
Each US city or state reform record is rated against it:

  at       - minimums removed citywide (or statewide) for all uses or all residential
             uses, by right, with no condition other than by right (PRN "requirements"
             is exactly ["by right"]);
  near     - minimums removed citywide for housing, but with a condition: a project-size
             limit, an ADU part, historic-preservation or "other" carve-outs, or for
             multifamily housing only;
  weaker   - removal limited to transit areas, centers, main streets or regions within the
             place; removal only for affordable/inclusionary housing; or minimums reduced,
             not removed; or removal for low-density housing only (houses and ADUs).
  not_housing - the reform does not touch residential uses.
  plan_only - PRN marks a plan or report recommendation as "adopted"; no code change is
             described in the summary (checked from the summary text, see plan_only).

The PRN date is the adoption (passed) date where recorded; effective dates are not in
the database and are recorded separately when verified from ordinance text.
Reporter names in the PRN data are never copied.
"""
from __future__ import annotations

import re

import pandas as pd

RESIDENTIAL = {"all uses", "residential, all uses", "residential, low-density", "residential, multi-family"}
FULL_RESIDENTIAL = {"all uses", "residential, all uses"}
AFFORDABLE = {"affordable housing", "inclusionary housing", "supportive housing"}


PLAN_WORDS = re.compile(r"\brecommend", re.I)
ENACTED_WORDS = re.compile(r"\b(removed|repealed|eliminated|exempt|abolished|no longer|has had no|adopted an ordinance|"
                           r"passed|approved|voted)\b", re.I)


def plan_only(summary: str) -> bool:
    """True when the PRN summary describes a plan or report recommendation, not a code change.
    PRN's status field marks such records 'adopted' (the plan was adopted), so the text is
    checked: a recommendation with no word of enactment is plan-only."""
    s = summary or ""
    return bool(PLAN_WORDS.search(s)) and not ENACTED_WORDS.search(s)


def rate(policy: str, scope: list[str], land: list[str], requirements: list[str],
         summary: str = "") -> tuple[str, str]:
    """Return (rating, reason) for one PRN reform record."""
    land_s, req_s, scope_s = set(land), set(requirements or []), set(scope)
    if plan_only(summary):
        return "plan_only", "a plan or report recommends it; no code change described"
    if not land_s & RESIDENTIAL:
        return "not_housing", "does not apply to residential uses"
    if policy != "rm_min":
        return "weaker", "minimums reduced, not removed"
    wide = bool(scope_s & {"citywide"}) or (scope_s == {"regional"})
    if not wide:
        return "weaker", "removal limited to " + ", ".join(sorted(scope_s))
    if req_s & AFFORDABLE and "by right" not in req_s:
        return "weaker", "removal only for affordable or supportive housing"
    if req_s & {"frequent transit"}:
        return "weaker", "removal conditioned on transit service"
    all_res = bool(land_s & FULL_RESIDENTIAL) or {"residential, low-density", "residential, multi-family"} <= land_s
    if all_res and req_s == {"by right"}:
        return "at", "removed for all housing, by right"
    if not all_res and (land_s & RESIDENTIAL) == {"residential, low-density"}:
        return "weaker", "removed only for low-density housing (houses, ADUs), where minimums rarely bind"
    if not all_res:
        return "near", "removed for one residential class only (" + ", ".join(sorted(land_s & RESIDENTIAL)) + ")"
    extra = sorted(req_s - {"by right"})
    return "near", "removed for housing with conditions: " + ", ".join(extra)


def classify(core: dict, extended: dict) -> pd.DataFrame:
    """One row per US city, county or state reform record in the PRN data."""
    rows = []
    for key, v in core.items():
        p = v["place"]
        if p.get("country") != "United States":
            continue
        for policy in ("rm_min", "reduce_min"):
            for i, r in enumerate(v.get(policy, [])):
                x = extended.get(key, {}).get(policy, [{}] * (i + 1))[i]
                req = x.get("requirements", []) or []
                rating, reason = rate(policy, r.get("scope", []), r.get("land", []), req, x.get("summary") or "")
                rows.append(dict(
                    prn_key=key, place=p.get("name"), state=p.get("state"), place_type=p.get("type"),
                    population=p.get("pop"), policy=policy, status=r.get("status"),
                    adopted_date=r.get("date"), scope=";".join(r.get("scope", [])),
                    land_use=";".join(r.get("land", [])), requirements=";".join(req),
                    benchmark_rating=rating, rating_reason=reason,
                    summary=(x.get("summary") or "").replace("\n", " ").strip(),
                    citation_urls=";".join(c.get("url") or "" for c in x.get("citations", []) if c.get("url")),
                ))
    df = pd.DataFrame(rows)
    df["adopted_year"] = pd.to_numeric(df["adopted_date"].str[:4], errors="coerce").astype("Int64")
    return df.sort_values(["place_type", "state", "place", "policy"]).reset_index(drop=True)
