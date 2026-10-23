"""Unit-category classification for deduplicated permit records (city-agnostic).

Order of rules (first that applies wins):

1. Text rule (classification_method = text_rule). A description matches the
   ADU pattern and none of the exclusion patterns. Sub-type:
   - adu_legalization: legalize / existing (unpermitted) ADU / as-built
   - adu_conversion: convert / conversion / basement / lower level / interior /
     "in existing" / attic - i.e. a unit created inside an existing structure
     (including converting an existing garage)
   - adu_attached: attached / addition
   - adu_detached: otherwise (new detached ADU, ADU above a garage, coach house)
   Records that match the ADU pattern AND an exclusion (e.g. "convert coach
   house to single family", raze, renewal/reinstatement, or "two-family/duplex
   with ADU" bundles) are flagged `near_miss` and fall through to rule 2/3.
2. Parcel rule (classification_method = parcel_rule): adu_equivalent per AQ-021,
   see `apply_parcel_rule`.
3. other_residential (classification_method = structured_field): any other
   record that adds dwelling units according to the structured unit field.
"""
from __future__ import annotations

import re

import pandas as pd

ADU_RE = re.compile(
    r"accessory\s+dwell|\bADU'?S?\b|\bA\.D\.U|accessory\s+(?:unit|apartment|living\s+unit|residential\s+unit)"
    r"|carriage\s+house|coach\s+house|granny|in[- ]law|backyard\s+cottage|garden\s+(?:cottage|suite)"
    r"|secondary\s+dwelling|second(?:ary)?\s+(?:living|dwelling)\s+unit|laneway",
    re.I,
)
EXCLUDE_RES = {
    "coach_house_to_sfr": re.compile(r"convert\w*\s+(?:the\s+|an?\s+)?(?:existing\s+)?coach\s+house\s+(?:in)?to\s+(?:a\s+)?single", re.I),
    "raze": re.compile(r"\braz(?:e|ing)\b|\bdemoli", re.I),
    "renewal": re.compile(r"\brenew|\breinstat|\bre-?issue|\bextension\s+of\s+permit|\bexpired\s+permit", re.I),
    "revision": re.compile(r"\brevision\s+to\b|\brevise\s+permit|\bchange\s+to\s+permit", re.I),
    "repair_or_finish": re.compile(r"\brepair\b|\bfinish\s+(?:the\s+)?ADU\b", re.I),
}
# Terms near the ADU concept that are NOT classified as ADUs by text; surfaced for audit.
RELATED_RE = re.compile(r"dependency\s+living|rear\s+(?:yard\s+)?(?:house|home|dwelling|cottage)|second\s+(?:house|home)"
                        r"|guest\s+(?:house|suite|cottage)|tiny\s+house|studio\s+apartment\s+above", re.I)
LEGAL_RE = re.compile(r"legaliz|as[- ]built|unpermitted|existing\s+illegal|without\s+(?:a\s+)?permit", re.I)
CONVERSION_RE = re.compile(
    r"\bconver(?:t|sion)|basement|lower\s+level|\binterior\b|\bwithin\s+(?:the\s+)?existing|\bin\s+(?:the\s+)?existing"
    r"|\battic\b|\bfinish\w*\s+(?:the\s+)?(?:existing|basement|lower)", re.I)
# location words (basement, lower level) indicate a conversion only when the work is not new construction
CONVERT_VERB_RE = re.compile(r"\bconver(?:t|sion)", re.I)
NEW_RE = re.compile(r"\bnew\b", re.I)
ATTACHED_RE = re.compile(r"\battached\b|\baddition\b", re.I)
DETACHED_RE = re.compile(r"\bdetached\b|garage|coach\s+house|carriage|cottage", re.I)


# Evidence in the description that the work creates or is a dwelling.
DWELLING_RE = re.compile(
    r"single[- ]?family|multi[- ]?family|\bSFR?\b|\bS\.\s?F\b|\bdwelling|\bresidence|\bhomes?\b|\bhouse\b|duplex|two[- ](?:family|unit|flat)"
    r"|\b\d+[- ]unit|\b(?:one|two|three|four)[- ]unit|apartment|\bapts?\b|kitchen|living\s+unit|efficiency"
    r"|condo|town\s?(?:home|house)|row\s?house|twin|\bflat\b|\bADU\b|cottage", re.I)
# Work types that do not create a dwelling (decks, porches, sheds, ...).
NON_DWELLING_RE = re.compile(
    r"\bdecks?\b|porch|\bstoops?\b|sun\s?room|screen\s+room|\bsheds?\b|\bramps?\b|\bstairs?\b|pergola"
    r"|\bfoyer|mud\s?room|\bdormers?\b|\bpatio|gazebo|\bfence|\blanding\b|\bgarage\b|carport|reroof"
    r"|\bsiding\b|\bwindows?\b|\bbath(?:room)?\b|bedroom|family\s+room|addition", re.I)
UNIT_REDUCTION_RE = re.compile(
    r"conver\w*\s+(?:\w+\s+){0,4}?(?:two|2|three|3|four|4)[- ](?:family|unit|flat)\w*\s+(?:\w+\s+){0,3}?"
    r"(?:in)?to\s+(?:a\s+)?(?:single|one|1)[- ]?(?:family|unit)", re.I)
EXISTING_CONTEXT_RE = re.compile(
    r"\b(?:of|on|to|for|in|at|from)\s+(?:an?\s+|the\s+)?existing\s+(?:[\w-]+\s+){0,2}[\w-]+", re.I)
MOVED_RE = re.compile(r"moved\s+house|relocated\s+house|house\s+move|moving\s+house", re.I)


def unit_flags(description: str) -> dict:
    """Flags used to judge whether the structured unit count is plausible."""
    d = description or ""
    dw, nd = bool(DWELLING_RE.search(d)), bool(NON_DWELLING_RE.search(d))
    # "kitchen" alone is weak, and words describing the existing building
    # ("deck on second floor of existing duplex") are not evidence of new units
    core = EXISTING_CONTEXT_RE.sub(" ", re.sub(r"(?i)kitchen", " ", d))
    strong = bool(DWELLING_RE.search(core))
    return {
        "dwelling_text": dw,
        "non_dwelling_only": nd and not strong,
        "unit_reduction": bool(UNIT_REDUCTION_RE.search(d)),
        "moved_house": bool(MOVED_RE.search(d)),
    }


def text_class(description: str) -> tuple[str | None, str]:
    """Return (unit_category or None, note). Note explains exclusions for audit."""
    d = description or ""
    if not ADU_RE.search(d):
        return None, ("related_term" if RELATED_RE.search(d) else "")
    hits = [name for name, rx in EXCLUDE_RES.items() if rx.search(d)]
    if hits:
        return None, "near_miss:" + "+".join(hits)
    if LEGAL_RE.search(d):
        return "adu_legalization", "text"
    # "detached" wins over "convert" only when the ADU is new construction;
    # converting an existing detached garage is still a conversion.
    if CONVERT_VERB_RE.search(d) or (CONVERSION_RE.search(d) and not NEW_RE.search(d)):
        return "adu_conversion", "text"
    if re.search(r"\bdetached\b", d, re.I):
        return "adu_detached", "text"
    if ATTACHED_RE.search(d):
        return "adu_attached", "text"
    return "adu_detached", "text_default_detached"


def apply_text_rules(df: pd.DataFrame) -> pd.DataFrame:
    res = df["description"].fillna("").map(text_class)
    out = pd.DataFrame({"text_category": [r[0] for r in res], "text_note": [r[1] for r in res]},
                       index=df.index)
    out["adu_keyword"] = df["description"].fillna("").str.contains(ADU_RE)
    flags = pd.DataFrame([unit_flags(d) for d in df["description"].fillna("")], index=df.index)
    return out.join(flags)


def apply_parcel_rule(df: pd.DataFrame, parcels: pd.DataFrame, max_units_added: int = 2,
                      max_host_units: int = 3, raze_before_days: int = 730,
                      raze_after_days: int = 180, min_age_years: int = 2,
                      host_uses: tuple[str, ...] | None = None) -> pd.DataFrame:
    """ADU-equivalent (AQ-021): a permit adding a dwelling on a parcel that already had one.

    `df` holds deduplicated permits with parcel_id, units_added, issue_date,
    is_raze, match_quality. `parcels` has parcel_id, dwelling_units, year_built,
    property_class.

    Timing problem: the parcel layer is *current*. A new house built on a vacant
    lot in 2015 shows 1 dwelling today, so "the parcel has a dwelling" cannot be
    read from today's dwelling count alone. Also, Madison's assessor counts a
    single-family parcel with an ADU as 1 dwelling unit (checked on the 2014-2018
    text-rule ADUs: TotalDwellingUnits = 1, MoreThanOneBuild = YES), so
    "current units minus permitted units" undercounts prior dwellings and is
    not usable. The rule therefore uses the assessor's year built of the main
    building as the evidence that a dwelling existed before the permit:

      (0) the unit count is plausible: the description has dwelling evidence
          and is not a deck/porch/addition-only item, a conversion to fewer
          units, or a moved house (`units_suspect` / `moved_house` false);
      (1) parcel matched with quality confirmed or probable;
      (2) 1 <= units_added <= max_units_added (small-scale additions only);
      (3) the parcel is residential today with 1..max_host_units dwellings
          and (if `host_uses` is given) its property use is one of them
          (a one- to three-unit host, not an apartment or condo complex);
      (4) year_built of the main building is valid (>= 1800) and at least
          `min_age_years` before the permit's issue year. A new house on a
          vacant lot gets the new house's year built (or 0 while unbuilt), so
          it fails here; the 2-year margin absorbs assessor year-built values
          set one year early for houses under construction;
      (5) no earlier unit-adding permit on the parcel since the series start
          whose own construction would explain the main building
          (earlier permit issued in or after year_built - 1);
      (6) no raze permit removing dwelling units on the parcel from
          raze_before_days before to raze_after_days after the permit
          (a teardown-and-replace is not an added dwelling).
    Returns: host_units_now, earlier_units, parcel_rule_pass, parcel_rule_reason.
    """
    p = parcels.set_index("parcel_id")
    work = df[["parcel_id", "units_added", "issue_date", "is_raze", "match_quality"]].copy()
    plausible = df.get("dwelling_text", True) & ~df.get("units_suspect", False) & ~df.get("moved_house", False)
    plausible = pd.Series(plausible, index=df.index) if not isinstance(plausible, pd.Series) else plausible
    have = work["parcel_id"].notna()
    adds = work[have & (work["units_added"] > 0)]
    adds_by_parcel = {k: g for k, g in adds.groupby("parcel_id")}
    dwelling_razes = work[have & work["is_raze"] & (work["units_added"] < 0)]
    raze_dates = dwelling_razes.groupby("parcel_id")["issue_date"].apply(list).to_dict()
    out = pd.DataFrame(index=df.index, columns=["host_units_now", "earlier_units", "parcel_rule_pass",
                                                "parcel_rule_reason"], dtype=object)
    out["parcel_rule_pass"] = False
    for idx, r in work.iterrows():
        if pd.isna(r.units_added) or r.units_added <= 0:
            out.at[idx, "parcel_rule_reason"] = "no_units_added"
            continue
        if not plausible.at[idx]:
            out.at[idx, "parcel_rule_reason"] = "no_dwelling_evidence_in_text"
            continue
        if pd.isna(r.parcel_id) or r.match_quality not in ("confirmed", "probable"):
            out.at[idx, "parcel_rule_reason"] = "no_parcel"
            continue
        if r.parcel_id not in p.index:
            out.at[idx, "parcel_rule_reason"] = "parcel_not_in_layer"
            continue
        du, yb = p.at[r.parcel_id, "dwelling_units"], p.at[r.parcel_id, "year_built"]
        pclass = p.at[r.parcel_id, "property_class"] if "property_class" in p.columns else "Residential"
        du = 0 if pd.isna(du) else int(du)
        out.at[idx, "host_units_now"] = du
        g = adds_by_parcel.get(r.parcel_id)
        earlier = g[g["issue_date"] < r.issue_date] if g is not None else work.iloc[0:0]
        out.at[idx, "earlier_units"] = int(earlier["units_added"].sum())
        if r.units_added > max_units_added:
            out.at[idx, "parcel_rule_reason"] = "too_many_units"
            continue
        puse = p.at[r.parcel_id, "property_use"] if "property_use" in p.columns else None
        if (pclass != "Residential" or not (1 <= du <= max_host_units)
                or (host_uses is not None and puse not in host_uses)):
            out.at[idx, "parcel_rule_reason"] = "host_not_1_3_unit_residential"
            continue
        if pd.isna(yb) or int(yb) < 1800 or int(yb) > r.issue_date.year - min_age_years:
            out.at[idx, "parcel_rule_reason"] = "first_dwelling_on_parcel"  # main building not older
            continue
        if len(earlier) and (earlier["issue_date"].dt.year >= int(yb) - 1).any():
            out.at[idx, "parcel_rule_reason"] = "main_building_from_earlier_permit"
            continue
        rz = raze_dates.get(r.parcel_id, [])
        if any(0 <= (r.issue_date - d).days <= raze_before_days or 0 < (d - r.issue_date).days <= raze_after_days
               for d in rz):
            out.at[idx, "parcel_rule_reason"] = "raze_nearby"
            continue
        out.at[idx, "parcel_rule_pass"] = True
        out.at[idx, "parcel_rule_reason"] = "pass"
    return out
