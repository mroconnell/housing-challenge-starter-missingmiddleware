"""Shared pieces for comparison cities whose permits carry county parcel numbers.

Used by the Pleasant Prairie and Sun Prairie adapters (and any later city of
the same shape): Wisconsin V12 statewide parcels as the parcel reference,
parcel-number matching, and an ADU-equivalent rule that works without an
assessor "year built" field.

Why a different parcel rule than Madison's: neither V12 nor the public county
layers reachable without a login give year built or dwelling counts for these
places (Kenosha County's assessor GIS is behind bot protection; Dane County's
public layers carry values only). "The parcel already had a dwelling" is
therefore read from the permit history of the same parcel number:

* prior-dwelling evidence = an earlier permit on the parcel, issued at least
  `evidence_min_days` before, for work on an existing dwelling (re-roof,
  HVAC, plumbing, addition/alteration, deck, pool, solar ...), or an earlier
  new-dwelling permit issued at least `reissue_years` before (a second
  dwelling, not a re-issued permit for the same house);
* teardown-rebuild = a teardown signal on the parcel (dwelling raze permit,
  raze-related work such as sewer capping, or a temporary "two principal
  structures" permit) from the first prior-dwelling evidence (or 730 days
  before) to 1,095 days after the permit (owners often raze the old house
  after moving into the new one), or replacement wording in the text.
  Reported as its own series, never as an ADU-equivalent;
* duplex conversion = text says an existing home becomes two units. Reported as
  its own ADU-equivalent series;
* sites with 3+ dwelling permits or any multi-family permit (mobile-home
  parks, condo plats on one parcel) are excluded, as are manufactured homes
  replacing a manufactured home.
"""
from __future__ import annotations

import json
import re
import urllib.parse
from pathlib import Path

import pandas as pd

from . import fetch_util as fu

V12_URL = ("https://services3.arcgis.com/n6uYoouQZW75n5WI/arcgis/rest/services/"
           "Wisconsin_Statewide_Parcels_DB/FeatureServer/0")
# owner names and mailing addresses (OWNERNME1/2, PSTLADRESS) are never requested
V12_FIELDS = ("OBJECTID,STATEID,PARCELID,TAXPARCELID,PARCELDATE,TAXROLLYEAR,SITEADRESS,ADDNUMPREFIX,ADDNUM,"
              "ADDNUMSUFFIX,PREFIX,STREETNAME,STREETTYPE,SUFFIX,UNITTYPE,UNITID,PLACENAME,ZIPCODE,CNTASSDVALUE,"
              "LNDVALUE,IMPVALUE,ESTFMKVALUE,PROPCLASS,AUXCLASS,ASSDACRES,GISACRES,CONAME,LOADDATE,PARCELSRC,"
              "LONGITUDE,LATITUDE")
# units_basis values that come from the permit type (structured), not from free text
TYPE_BASES = {"type", "type+text", "type+text_units", "munis_code", "munis_code+text", "munis_code+text_units"}
HOST_CLASSES = {"1", "4", "5", "5M", "6", "7"}  # residential, ag, undeveloped, ag forest, forest, other (farm homes)


# ---------------------------------------------------------------- V12 parcels
def _v12_query(where: str, log=print, page: int = 2000) -> list[dict]:
    ids = json.loads(fu.get(V12_URL + "/query", data=urllib.parse.urlencode(
        {"where": where, "returnIdsOnly": "true", "f": "json"}).encode()))
    oids = sorted(ids.get("objectIds") or [])
    feats: list[dict] = []
    for i in range(0, len(oids), page):
        chunk = oids[i:i + page]
        body = urllib.parse.urlencode({
            "where": f"({where}) AND OBJECTID>={chunk[0]} AND OBJECTID<={chunk[-1]}",
            "outFields": V12_FIELDS, "returnGeometry": "true", "outSR": "4326",
            "geometryPrecision": "7", "f": "geojson"}).encode()
        feats.extend(json.loads(fu.get(V12_URL + "/query", data=body, timeout=300))["features"])
    log(f"  V12 {where[:70]}: {len(feats)} features")
    return feats


def fetch_v12_parcels(raw_dir: Path, source_id: str, placename: str, coname: str,
                      extra_parcel_ids: list[str] | None = None, log=print) -> dict:
    """Parcels whose PLACENAME is the municipality, plus any extra PARCELIDs (same county)
    that permits cite but that now lie outside the place (annexed or renamed)."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    feats = _v12_query(f"PLACENAME='{placename}' AND CONAME='{coname}'", log=log)
    have = {f["properties"]["PARCELID"] for f in feats}
    extra = sorted({p for p in (extra_parcel_ids or []) if p and p not in have})
    for i in range(0, len(extra), 150):
        ids = ",".join("'" + p.replace("'", "") + "'" for p in extra[i:i + 150])
        feats.extend(_v12_query(f"CONAME='{coname}' AND PARCELID IN ({ids})", log=log))
    path = raw_dir / "v12_parcels.geojson"
    path.write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
    fu.write_manifest(raw_dir / "manifest.json", [{
        "file": path.name, "url": V12_URL, "fields": V12_FIELDS, "features": len(feats),
        "where": f"PLACENAME='{placename}' AND CONAME='{coname}' (+{len(extra)} PARCELIDs cited by permits)",
        "accessed": fu.now_iso(), "sha256": fu.sha256_file(path)}], {
        "source_id": source_id, "publisher": "Wisconsin DOA / State Cartographer's Office, V12 Statewide Parcels",
        "vintage": "V12 (2026 release; tax roll 2025)",
        "license": "Public; statewide parcel initiative (Wis. Stat. 59.72). No owner fields requested.",
        "note": "Current snapshot only: no year built and no dwelling count."})
    return fu.read_manifest(raw_dir / "manifest.json")


def load_v12_parcel_table(raw_dir: Path) -> pd.DataFrame:
    """Standard parcel table (base.PARCEL_COLUMNS) plus lon/lat and V12 value/class fields."""
    import geopandas as gpd

    from .address import street_key_from_parts

    g = gpd.read_file(raw_dir / "v12_parcels.geojson").set_crs(4326, allow_override=True)
    rp = g.geometry.representative_point()
    out = pd.DataFrame({
        "parcel_id": g["PARCELID"].astype(str),
        "stateid": g["STATEID"],
        "parcel_address": g["SITEADRESS"],
        "house_nbr": pd.to_numeric(g["ADDNUM"], errors="coerce"),
        "street_key": [street_key_from_parts(d, n, t) for d, n, t in
                       zip(g["PREFIX"].fillna(""), g["STREETNAME"].fillna(""),
                           g["STREETTYPE"].map(_type_abbrev).fillna(""))],
        "unit": g["UNITID"].fillna(""),
        "dwelling_units": float("nan"),       # not in V12
        "property_class": g["PROPCLASS"],
        "property_use": None,
        "zoning": None,
        "year_built": float("nan"),           # not in V12
        "impvalue": pd.to_numeric(g["IMPVALUE"], errors="coerce"),
        "placename": g["PLACENAME"],
        "taxrollyear": g["TAXROLLYEAR"],
        "x": rp.x.values, "y": rp.y.values,
    })
    # V12 can hold several rows per PARCELID (condo units, multi-part); keep the first, count them
    n = out.groupby("parcel_id")["parcel_id"].transform("size")
    out["v12_rows"] = n
    return out.drop_duplicates("parcel_id").reset_index(drop=True)


_TYPE = {"AVENUE": "AVE", "STREET": "ST", "DRIVE": "DR", "ROAD": "RD", "LANE": "LN", "COURT": "CT",
         "PLACE": "PL", "BOULEVARD": "BLVD", "TRAIL": "TRL", "CIRCLE": "CIR", "PARKWAY": "PKWY",
         "TERRACE": "TER", "HIGHWAY": "HWY", "WAY": "WAY", "PASS": "PASS", "RUN": "RUN", "PATH": "PATH",
         "CROSSING": "XING", "POINT": "PT", "RIDGE": "RDG", "VIEW": "VW", "PLAZA": "PLZ", "SQUARE": "SQ",
         "LOOP": "LOOP", "GLEN": "GLN", "BEND": "BND", "COVE": "CV", "HEIGHTS": "HTS", "MEADOW": "MDW",
         "MEADOWS": "MDWS", "HILL": "HL", "HOLLOW": "HOLW", "GREEN": "GRN", "TRACE": "TRCE", "WALK": "WALK"}


def _type_abbrev(t):
    if t is None or (isinstance(t, float) and pd.isna(t)):
        return None
    return _TYPE.get(str(t).upper(), str(t).upper())


def address_reference(parcels: pd.DataFrame) -> pd.DataFrame:
    return parcels.rename(columns={"parcel_address": "address_full"})[
        ["house_nbr", "street_key", "unit", "parcel_id", "address_full", "x", "y"]].assign(ref_source="v12")


# ---------------------------------------------------------------- matching
def parcel_match_fn(known: set[str], index=None, normalize=None):
    """Return a `match_fn(df)` for the pipeline.

    Rules (fixed before evaluation):
    * parcel_id / confirmed: the permit's parcel number equals a V12 PARCELID.
    * parcel_id / probable: equal after removing spaces, dashes and dots (`normalize`).
    * address fallback (address_exact / address_normalized / geocode), via the
      city-agnostic address matcher on V12 site addresses, when the parcel
      number is missing or unknown to V12.
    * unmatched / none otherwise.
    """
    from .match import match_addresses

    norm = normalize or (lambda s: re.sub(r"[\s.\-]", "", s or ""))
    by_norm: dict[str, set[str]] = {}
    for p in known:
        by_norm.setdefault(norm(p), set()).add(p)

    def fn(df: pd.DataFrame) -> pd.DataFrame:
        base = {"addr_house_nbr": None, "addr_street_key": None, "addr_unit": None, "addr_flags": "",
                "parcel_id": None, "candidate_parcels": None, "match_method": "unmatched",
                "match_quality": "none", "match_rule": "no_match", "geo_x": None, "geo_y": None}
        rows, need_addr = [], []
        for idx, key in zip(df.index, df["parcel_key"]):
            key = None if key is None or (isinstance(key, float) and pd.isna(key)) else str(key)
            if key and key in known:
                rows.append({**base, "parcel_id": key, "match_method": "parcel_id", "match_quality": "confirmed",
                             "match_rule": "parcel_id_exact"})
            elif key and len(by_norm.get(norm(key), ())) == 1:
                rows.append({**base, "parcel_id": next(iter(by_norm[norm(key)])), "match_method": "parcel_id",
                             "match_quality": "probable", "match_rule": "parcel_id_normalized"})
            else:
                rows.append({**base, "match_rule": "parcel_id_unknown" if key else "no_parcel_id"})
                need_addr.append(idx)
        out = pd.DataFrame(rows, index=df.index)
        if index is not None and need_addr:
            sub = df.loc[need_addr]
            sub = sub[sub["address_raw"].fillna("").str.match(r"^\d")]
            if len(sub):
                am = match_addresses(sub, index)
                for c in am.columns:
                    out.loc[am.index, c] = am[c]
                out.loc[am.index, "match_rule"] = "address_fallback:" + am["match_rule"].astype(str)
        return out

    return fn


# ---------------------------------------------------------------- ADU-equivalent rule
TEARDOWN_TEXT_RE = re.compile(
    r"replac\w*\s+(?:the\s+|an?\s+)?(?:existing\s+|old\s+)?(?:\w+\s+){0,2}?(?:home|house|dwelling|residence|mobile)"
    r"|tear[- ]?down|(?:after|due\s+to)\s+(?:a\s+|the\s+)?fire|fire\s+damage|\bre-?bui?l?d\w*"
    r"|raz\w+\s+(?:and|&)\s+(?:re)?build", re.I)


def prior_dwelling_rule(adapter, evidence_min_days: int = 365, reissue_years: int = 3,
                        raze_after_days: int = 1095, raze_before_days: int = 730, max_units_added: int = 2):
    """Return a `parcel_rule_fn(df, parcels)` implementing the module docstring rule.

    Output columns: host_units_now, earlier_units, parcel_rule_pass, parcel_rule_reason,
    adu_eq_series, prior_evidence, prior_evidence_permit, prior_evidence_date.
    """

    def fn(df: pd.DataFrame, parcels: pd.DataFrame) -> pd.DataFrame:
        p = parcels.set_index("parcel_id")
        new_dw = adapter.is_new_dwelling(df)
        manuf = adapter.is_manufactured(df)
        exist_work = adapter.is_existing_dwelling_work(df)
        multi = df["units_added"].fillna(0) >= 3
        conv = df["units_basis"].eq("conversion_text")
        withdrawn = df["withdrawn"] if "withdrawn" in df.columns else pd.Series(False, index=df.index)
        # permit history is grouped by the permit's own parcel number (it also covers parcels
        # retired from today's V12 layer, e.g. a razed-and-replatted lot); V12 is used only
        # for the host class and the location
        hkey = df["parcel_key"].where(df["parcel_key"].notna(), df["parcel_id"])
        has = hkey.notna()
        w = df.loc[has, ["issue_date", "permit_id"]].copy()
        w["hkey"] = hkey[has]
        w["new_dw"] = new_dw[has] & ~withdrawn[has]
        w["manuf"], w["exist"] = manuf[has] & ~withdrawn[has], exist_work[has] & ~withdrawn[has]
        w["multi"] = multi[has]
        w["raze_dw"] = adapter.is_teardown_signal(df)[has]
        groups = {k: g.sort_values("issue_date") for k, g in w.groupby("hkey")}
        cols = ["host_units_now", "earlier_units", "parcel_rule_pass", "parcel_rule_reason", "adu_eq_series",
                "prior_evidence", "prior_evidence_permit", "prior_evidence_date"]
        out = pd.DataFrame(index=df.index, columns=cols, dtype=object)
        out["parcel_rule_pass"] = False
        # units read from the permit type are structured: the description cannot overrule them
        suspect = df["units_suspect"].astype(bool) & ~df["units_basis"].isin(TYPE_BASES)
        plausible = ~suspect & ~df.get("moved_house", pd.Series(False, index=df.index))
        for idx in df.index:
            r = df.loc[idx]
            ua = r["units_added"]
            if pd.isna(ua) or ua <= 0 or r["is_raze"]:
                out.at[idx, "parcel_rule_reason"] = "no_units_added"
                continue
            if not (new_dw.at[idx] or conv.at[idx]):
                out.at[idx, "parcel_rule_reason"] = "not_new_dwelling_or_conversion"
                continue
            if not plausible.at[idx]:
                out.at[idx, "parcel_rule_reason"] = "no_dwelling_evidence_in_text"
                continue
            if pd.isna(r["parcel_id"]) or r["match_quality"] not in ("confirmed", "probable"):
                out.at[idx, "parcel_rule_reason"] = "no_parcel"
                continue
            if ua > max_units_added:
                out.at[idx, "parcel_rule_reason"] = "too_many_units"
                continue
            pid = r["parcel_id"]
            cls = str(p.at[pid, "property_class"]) if pid in p.index else ""
            classes = {c.strip() for c in cls.split(",") if c.strip()}
            if not (classes & HOST_CLASSES):
                out.at[idx, "parcel_rule_reason"] = "host_not_residential"
                continue
            g = groups[hkey.at[idx]]
            others = g[g["permit_id"] != r["permit_id"]]
            earlier = others[others["issue_date"] < r["issue_date"]]
            out.at[idx, "earlier_units"] = int(earlier["new_dw"].sum())
            n_dw = int(g["new_dw"].sum())
            if TEARDOWN_TEXT_RE.search(r["description"] or ""):
                out.at[idx, "parcel_rule_reason"] = "teardown_rebuild_text"
                continue
            if g["multi"].any() or n_dw >= 3:
                out.at[idx, "parcel_rule_reason"] = "multi_dwelling_site"
                continue
            if conv.at[idx]:
                out.at[idx, "parcel_rule_pass"] = True
                out.at[idx, "parcel_rule_reason"] = "pass"
                out.at[idx, "adu_eq_series"] = "duplex_conversion"
                out.at[idx, "prior_evidence"] = "conversion_text"
                continue
            if manuf.at[idx] and (earlier["manuf"].any()):
                out.at[idx, "parcel_rule_reason"] = "manufactured_home_replacement"
                continue
            days_before = (r["issue_date"] - earlier["issue_date"]).dt.days
            ev_work = earlier[earlier["exist"] & (days_before >= evidence_min_days)]
            ev_dw = earlier[earlier["new_dw"] & (days_before >= 365 * reissue_years)]
            recent_dw = earlier[earlier["new_dw"] & (days_before < 365 * reissue_years)]
            ev = pd.concat([ev_work, ev_dw]).sort_values("issue_date")
            first_ev = ev["issue_date"].min() if len(ev) else None
            razes = g[g["raze_dw"]]
            lo = min(first_ev, r["issue_date"] - pd.Timedelta(days=raze_before_days)) if first_ev is not None \
                else r["issue_date"] - pd.Timedelta(days=raze_before_days)
            hi = r["issue_date"] + pd.Timedelta(days=raze_after_days)
            if ((razes["issue_date"] >= lo) & (razes["issue_date"] <= hi)).any():
                out.at[idx, "parcel_rule_reason"] = "teardown_rebuild_raze"
                continue
            if len(recent_dw) and not len(ev_work):
                out.at[idx, "parcel_rule_reason"] = "possible_reissue_of_earlier_dwelling_permit"
                continue
            if not len(ev):
                out.at[idx, "parcel_rule_reason"] = "no_prior_dwelling_evidence"
                continue
            e = ev.iloc[0]
            out.at[idx, "parcel_rule_pass"] = True
            out.at[idx, "parcel_rule_reason"] = "pass"
            out.at[idx, "adu_eq_series"] = "second_dwelling"
            out.at[idx, "prior_evidence"] = "earlier_new_dwelling_permit" if e["new_dw"] else "earlier_existing_dwelling_work"
            out.at[idx, "prior_evidence_permit"] = e["permit_id"]
            out.at[idx, "prior_evidence_date"] = e["issue_date"].date().isoformat()
        return out

    return fn


def recount(full: pd.DataFrame) -> pd.DataFrame:
    """Re-derive `units_suspect` and `counted` for type-based unit counts and withdrawn records.

    The pipeline judges small unit counts against the description (Madison's Dwell field is
    noisy). Here a new-dwelling permit type is the unit source, so "NSFR w/ garage and deck"
    must not be marked suspect. Withdrawn/void submissions authorize nothing.
    """
    full = full.copy()
    full["units_suspect"] = full["units_suspect"].astype(bool) & ~full["units_basis"].isin(TYPE_BASES)
    wd = (full["withdrawn"].astype(bool) if "withdrawn" in full.columns
          else pd.Series(False, index=full.index))
    full["counted"] = (full["in_scope"].astype(bool) & (full["units_added"].fillna(0) > 0)
                       & ~full["renewal_duplicate"].astype(bool) & ~full["units_suspect"] & ~wd)
    return full


def series_label(full: pd.DataFrame) -> pd.Series:
    """One reporting series per record (ADU text, ADU-equivalent by kind, teardown, other)."""
    s = pd.Series("other_residential", index=full.index, dtype=object)
    s[full["unit_category"].isin(["adu_detached", "adu_attached", "adu_conversion", "adu_legalization"])] = "adu_text"
    eq = full["unit_category"].eq("adu_equivalent")
    s[eq] = "adu_equivalent:" + full.loc[eq, "adu_eq_series"].fillna("unknown").astype(str)
    rr = full["parcel_rule_reason"].fillna("")
    oth = full["unit_category"].eq("other_residential")
    s[oth & rr.str.startswith("teardown_rebuild")] = "teardown_rebuild"
    s[oth & rr.eq("manufactured_home_replacement")] = "manufactured_home_replacement"
    s[full["unit_category"].isna()] = None
    return s


# --------------------------------------------------------------------------- restrictive period
def restrictive_flag(a, dates: pd.Series) -> pd.Series:
    """Record-level restrictive flag: before the reform date (adapter `restrictive_end`), else True."""
    end = getattr(a, "restrictive_end", None)
    if not end:
        return pd.Series(True, index=dates.index)
    return pd.to_datetime(dates).lt(pd.Timestamp(end))


def restrictive_periods(a, y: int) -> list[tuple[str, str, bool]]:
    """(period_start, period_end, restrictive) for year y; a reform year is split at the reform date."""
    start, stop = f"{y}-01-01", f"{y}-12-31"
    end = getattr(a, "restrictive_end", None)
    if not end:
        return [(start, stop, True)]
    e = pd.Timestamp(end)
    if e.year > y:
        return [(start, stop, True)]
    if e.year < y or e == pd.Timestamp(start):
        return [(start, stop, False)]
    return [(start, (e - pd.Timedelta(days=1)).date().isoformat(), True), (e.date().isoformat(), stop, False)]
