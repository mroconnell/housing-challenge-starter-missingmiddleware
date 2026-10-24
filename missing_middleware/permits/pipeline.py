"""City-agnostic permit pipeline: standard frame -> permits_observed -> permits_by_area_year."""
from __future__ import annotations

import hashlib

import pandas as pd

from .classify import SF_TO_TWO_RE, apply_parcel_rule, apply_text_rules
from .match import AddressIndex, match_addresses

DISCLOSURE_THRESHOLD = 3  # observed sub-city counts 1..threshold-1 are flagged suppressed
RAZE_TYPES_DEFAULT = ("BLDRRZ", "BLDCRZ")


def record_key(source_id: str, permit_id: str) -> str:
    return hashlib.sha256(f"{source_id}:{permit_id}".encode()).hexdigest()[:16]


def dedupe(raw: pd.DataFrame) -> pd.DataFrame:
    """One row per permit number.

    Rule: rows sharing a permit number are one permit. Keep the earliest issue
    date as the issued stage_date (later dates are reissues/reprints); keep the
    row with the largest absolute unit count from among the duplicates (they
    agree in all observed cases; disagreements are flagged). Record how many
    source rows and distinct issue dates were collapsed.
    """
    df = raw.sort_values(["permit_id", "issue_date", "source_file", "source_row"]).copy()
    g = df.groupby("permit_id", sort=False)
    agg = g.agg(
        n_source_rows=("permit_id", "size"),
        n_issue_dates=("issue_date", "nunique"),
        first_issue=("issue_date", "min"),
        last_issue=("issue_date", "max"),
        units_min=("units_raw", "min"),
        units_max=("units_raw", "max"),
    )
    first = g.head(1).set_index("permit_id")
    out = first.join(agg)
    out["issue_date"] = out["first_issue"]
    out["units_conflict"] = out["units_min"] != out["units_max"]
    out = out.drop(columns=["first_issue", "units_min", "units_max"]).reset_index()
    return out


def find_renewal_duplicates(df: pd.DataFrame, days: int = 1095) -> pd.Series:
    """A unit-adding permit whose text says renewal/reissue and whose parcel has an
    earlier unit-adding permit within `days` is a duplicate authorization."""
    from .classify import EXCLUDE_RES

    ren = df["description"].fillna("").str.contains(EXCLUDE_RES["renewal"])
    dup = pd.Series(False, index=df.index)
    cand = df[ren & (df["units_added"] > 0) & df["parcel_id"].notna()]
    for idx, r in cand.iterrows():
        prior = df[(df["parcel_id"] == r.parcel_id) & (df["units_added"] > 0)
                   & (df["issue_date"] < r.issue_date) & ((r.issue_date - df["issue_date"]).dt.days <= days)]
        if len(prior):
            dup.at[idx] = True
    return dup


def build_permits_observed(raw: pd.DataFrame, index: AddressIndex, parcels: pd.DataFrame,
                           parcel_xy: pd.DataFrame, areas_fn, raze_types=RAZE_TYPES_DEFAULT,
                           new_residential_types: tuple[str, ...] = (),
                           host_uses: tuple[str, ...] | None = None,
                           match_fn=None, parcel_rule_fn=None,
                           dwell0_conversions: bool = False,
                           exclude_parcel_rule: dict[str, str] | None = None) -> pd.DataFrame:
    """Full record-level table (all deduplicated permits, with diagnostics).

    `parcel_xy`: parcel_id, x, y (lon/lat representative point).
    `areas_fn(points_df with x,y)` -> DataFrame with tract_geoid, bg_geoid.
    Contract rows are the subset `in_scope` (see `to_contract`).

    Optional hooks for cities whose permits carry parcel numbers (defaults keep
    the Madison behaviour): `match_fn(df) -> match frame` replaces the address
    match (same columns as `match_addresses`), and `parcel_rule_fn(df, parcels)`
    replaces `apply_parcel_rule` (must return at least host_units_now,
    earlier_units, parcel_rule_pass, parcel_rule_reason).

    `dwell0_conversions`: a record whose unit field is 0 but whose description
    says a single-family home becomes two units (`SF_TO_TWO_RE`) is given
    units_added = 1 (`units_from_text = True`) so the ADU-equivalent rule can
    judge it; every other check still applies.
    `exclude_parcel_rule`: permit_id -> note for audit-judged false positives;
    they never pass the parcel rule and their unit count is marked suspect.

    ADU text bundles (ADU wording on a record adding 2+ units) are held out of
    every ADU series whichever rule they reach: they never pass the parcel rule
    either (reason `adu_bundle_held_for_review`) and are counted as
    other_residential until the unit split is known.
    """
    df = dedupe(raw)
    df["units_added"] = df["units_raw"].round().astype("Int64")
    df["is_raze"] = df["permit_type"].isin(raze_types)
    df["units_from_text"] = False
    if dwell0_conversions:
        z = (df["units_added"].fillna(0) == 0) & ~df["is_raze"] \
            & df["description"].fillna("").str.contains(SF_TO_TWO_RE)
        df.loc[z, "units_added"] = 1
        df.loc[z, "units_from_text"] = True
    txt = apply_text_rules(df)
    df = df.join(txt)
    # ADU text on a record that adds 2+ units ("new duplex w/ ADU", "detached duplex ADU",
    # "twin home ADU") cannot be split into ADU vs principal units from this source:
    # not classified as ADU by text; kept as near-miss for review (falls to rules below).
    multi = df["text_category"].notna() & (df["units_added"].fillna(0) >= 2)
    df.loc[multi, "text_note"] = "near_miss:multi_unit_adu_bundle"
    df.loc[multi, "text_category"] = None
    # structured unit count contradicted by the description (deck with Dwell 1, 2->1 conversions)
    # (only small counts are judged this way; multi-unit projects keep their count)
    df["units_suspect"] = df["units_added"].fillna(0).between(1, 2) \
        & (df["non_dwelling_only"] | df["unit_reduction"]) & df["text_category"].isna()
    m = match_fn(df) if match_fn is not None else match_addresses(df, index)
    df = df.join(m)
    df = apply_parcel_attrs(df, parcels)
    exclude_parcel_rule = exclude_parcel_rule or {}
    judged_fp = df["permit_id"].isin(list(exclude_parcel_rule))
    pr = (parcel_rule_fn(df, parcels) if parcel_rule_fn is not None
          else apply_parcel_rule(df, parcels, host_uses=host_uses, exclude_ids=exclude_parcel_rule))
    df = df.join(pr)
    held = multi & df["parcel_rule_pass"].astype(bool)
    df.loc[held, "parcel_rule_pass"] = False
    df.loc[held, "parcel_rule_reason"] = "adu_bundle_held_for_review"
    if "adu_eq_series" in df.columns:
        df.loc[held, "adu_eq_series"] = None
    df.loc[judged_fp, "parcel_rule_pass"] = False
    df.loc[judged_fp, "parcel_rule_reason"] = "judged_false_positive"
    df.loc[judged_fp, "units_suspect"] = True
    # a Dwell-0 conversion whose parcel has another unit-adding permit within 2 years is the
    # same conversion permitted twice (the other record carries the unit)
    for idx in df.index[df["units_from_text"] & df["parcel_rule_pass"].astype(bool)]:
        r = df.loc[idx]
        o = df[(df["parcel_id"] == r["parcel_id"]) & (df.index != idx) & ~df["units_from_text"]
               & (df["units_added"].fillna(0) > 0) & ~df["is_raze"]]
        if ((o["issue_date"] - r["issue_date"]).dt.days.abs() <= 730).any():
            df.at[idx, "parcel_rule_pass"] = False
            df.at[idx, "parcel_rule_reason"] = "conversion_already_permitted"
    # a Dwell-0 conversion enters scope only as an ADU-equivalent; otherwise it adds nothing
    dz = df["units_from_text"] & ~df["parcel_rule_pass"].astype(bool)
    df.loc[dz, "units_added"] = 0
    df.loc[dz, "units_from_text"] = False
    if parcel_rule_fn is None:  # Madison-style rule: label the ADU-equivalent sub-series
        ok = df["parcel_rule_pass"].astype(bool)
        conv = df["description"].fillna("").str.contains(SF_TO_TWO_RE) | df["description"].fillna("").str.contains(
            r"(?i)\b(?:convert\w*|change\w*|create|addition)\b.{0,60}\b(?:duplex|two[- ]?(?:unit|family)|2[- ]unit)")
        df["adu_eq_series"] = None
        df.loc[ok & conv, "adu_eq_series"] = "duplex_conversion"
        df.loc[ok & ~conv, "adu_eq_series"] = "second_dwelling"
    df["renewal_duplicate"] = find_renewal_duplicates(df)

    # unit_category + classification_method
    cat = pd.Series(None, index=df.index, dtype=object)
    method = pd.Series(None, index=df.index, dtype=object)
    t = df["text_category"].notna()
    cat[t], method[t] = df.loc[t, "text_category"], "text_rule"
    pr_ok = ~t & df["parcel_rule_pass"].astype(bool)
    cat[pr_ok], method[pr_ok] = "adu_equivalent", "parcel_rule"
    other = cat.isna() & (df["units_added"].fillna(0) > 0)
    cat[other], method[other] = "other_residential", "structured_field"
    df["unit_category"], df["classification_method"] = cat, method
    # in scope: unit-adding records, plus every ADU text hit (incl. Dwell-0 ones)
    df["in_scope"] = df["unit_category"].notna() & ~df["is_raze"]
    # counted toward the outcome: in scope, adds >=1 unit, not a renewal duplicate,
    # and the unit count is not contradicted by the description
    df["counted"] = (df["in_scope"] & (df["units_added"].fillna(0) > 0) & ~df["renewal_duplicate"]
                     & ~df["units_suspect"])

    # location for area attach: parcel representative point, else geocode point
    xy = parcel_xy.set_index("parcel_id")
    df["x"] = df["parcel_id"].map(xy["x"]).astype(float)
    df["y"] = df["parcel_id"].map(xy["y"]).astype(float)
    df["x"] = df["x"].fillna(pd.to_numeric(df["geo_x"], errors="coerce"))
    df["y"] = df["y"].fillna(pd.to_numeric(df["geo_y"], errors="coerce"))
    df["area_from_ambiguous"] = False
    amb = df["x"].isna() & df["candidate_parcels"].notna()
    if amb.any():  # ambiguous: area only if all candidates share a block group
        cands = df.loc[amb, "candidate_parcels"].str.split(";")
        flat = sorted({c for cs in cands for c in cs if c in xy.index})
        cxy = xy.loc[flat].reset_index()
        cbg = areas_fn(cxy).set_index(cxy["parcel_id"])["bg_geoid"]
        for idx, cs in cands.items():
            bgs = {cbg.get(c) for c in cs}
            if len(bgs) == 1 and None not in bgs and not pd.isna(next(iter(bgs))):
                c0 = cs[0]
                df.at[idx, "x"], df.at[idx, "y"] = xy.at[c0, "x"], xy.at[c0, "y"]
                df.at[idx, "area_from_ambiguous"] = True
    has = df["x"].notna()
    areas = areas_fn(df.loc[has, ["x", "y"]])
    df["tract_geoid"] = areas["tract_geoid"].reindex(df.index)
    df["bg_geoid"] = areas["bg_geoid"].reindex(df.index)
    df["year"] = df["issue_date"].dt.year
    return df


def apply_parcel_attrs(df: pd.DataFrame, parcels: pd.DataFrame) -> pd.DataFrame:
    cols = ["parcel_id", "dwelling_units", "property_use", "property_class", "zoning", "year_built",
            "parcel_address", "more_than_one_building"]
    p = parcels[[c for c in cols if c in parcels.columns]].set_index("parcel_id")
    return df.join(p.add_prefix("parcel_"), on="parcel_id")


CONTRACT_EXTRA = [
    "year", "permit_type", "parcel_stateid", "parcel_id", "area_id", "tract_geoid", "bg_geoid",
    "counted", "match_rule", "text_note", "parcel_rule_reason", "n_source_rows", "units_from_text",
]


def to_contract(df: pd.DataFrame, source_id: str, jurisdiction_id: str) -> pd.DataFrame:
    s = df[df["in_scope"]].copy()
    out = pd.DataFrame({
        "record_key": [record_key(source_id, p) for p in s["permit_id"]],
        "jurisdiction_id": jurisdiction_id,
        "stage": "issued",
        "stage_date": s["issue_date"].dt.date,
        "unit_category": s["unit_category"],
        "classification_method": s["classification_method"],
        "units_added": s["units_added"],
        "match_method": s["match_method"],
        "match_quality": s["match_quality"],
        "source_id": source_id,
    }, index=s.index)
    out["year"] = s["year"]
    out["permit_type"] = s["permit_type"]
    out["parcel_stateid"] = None  # V12 STATEID crosswalk not built in this package
    out["parcel_id"] = s["parcel_id"]
    out["area_id"] = s["tract_geoid"]
    out["tract_geoid"] = s["tract_geoid"]
    out["bg_geoid"] = s["bg_geoid"]
    for c in ("counted", "match_rule", "text_note", "parcel_rule_reason", "n_source_rows", "units_from_text"):
        out[c] = s[c]
    return out.reset_index(drop=True)


def by_area_year(obs: pd.DataFrame, city_area_id: str, threshold: int = DISCLOSURE_THRESHOLD) -> pd.DataFrame:
    """Counted units by tract and by city, per year and unit_category.

    coverage = share of the city's counted units in that year and category that
    could be placed in a tract (tract rows and city row carry the same value).
    Tract rows are written only where units > 0; missing tract rows mean "none
    observed among placed records", not a confirmed zero.
    """
    c = obs[obs["counted"]].copy()
    c["units"] = c["units_added"].astype(int)
    city = c.groupby(["year", "unit_category"])["units"].sum().rename("units").reset_index()
    placed = c[c["tract_geoid"].notna()].groupby(["year", "unit_category"])["units"].sum()
    city["coverage"] = [
        round(float(placed.get((y, k), 0)) / u, 4) if u else None
        for y, k, u in city[["year", "unit_category", "units"]].itertuples(index=False)
    ]
    city["area_id"] = city_area_id
    city["level"] = "municipality"
    city["suppressed"] = False
    tr = c[c["tract_geoid"].notna()].groupby(["tract_geoid", "year", "unit_category"])["units"].sum().reset_index()
    tr = tr.rename(columns={"tract_geoid": "area_id"})
    tr = tr.merge(city[["year", "unit_category", "coverage"]], on=["year", "unit_category"], how="left")
    tr["level"] = "tract"
    tr["suppressed"] = (tr["units"] > 0) & (tr["units"] < threshold)
    out = pd.concat([city, tr], ignore_index=True)
    out["status"] = "observed"
    return out[["area_id", "level", "year", "unit_category", "units", "coverage", "suppressed", "status"]]
