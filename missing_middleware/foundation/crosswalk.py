"""Crosswalk from Census BPS permit-issuing places to Wisconsin municipalities.

In Wisconsin every city, village and town is a county subdivision (MCD), and
BPS records the 5-digit FIPS MCD code of each permit-issuing jurisdiction.
FIPS MCD codes are unique within the state, so a BPS row links to every
county-subdivision piece that shares its COUSUBFP. Match methods, in order:

  county_unincorporated  the BPS NAME says it is a county row ("<County> Part
                         Unincorporated Area"): permits the county issued for
                         towns that do not report on their own. Only the name
                         decides this; a blank MCD code alone does not.
                         Linked to the county's towns that have no own BPS row
                         in a year the county row covers; per-year shares are
                         in county_unincorporated_allocation().
  exact                  MCD code -> one piece, in the BPS county
  mcd_other_county       MCD code -> one piece, in a different county
  multi_county           MCD code -> several pieces (a city or village crossing
                         county lines); BPS reports it once, under its main
                         county. Each piece gets an allocation share by ACS
                         one-unit detached homes; is_primary_piece marks the
                         BPS county.
  place_code             MCD code blank or 00000 (BPS leaves it blank for some
                         villages in some years) but the BPS FIPS place code is
                         a TIGER county-subdivision code in the BPS county with
                         the same name.
  name_county            no usable code, but the name matches one municipality
                         in the BPS county: first the full name with its type
                         ("harrison village"), then the base name if exactly one
                         municipality has it (a town that incorporated as a
                         village and got a new code, e.g. Rib Mountain town ->
                         Rib Mountain village).
  name_alias             a documented merger/rename in NAME_ALIASES.
  unmatched              none of the above (dissolved municipalities).
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

MATCHED_TYPES = {"exact", "mcd_other_county", "multi_county", "place_code", "name_county", "name_alias"}


def bps_jurisdictions(bps_place: pd.DataFrame) -> pd.DataFrame:
    """One row per (bps_id, county, MCD, place) identity seen across years."""
    keys = ["bps_id", "county_fips", "fips_mcd", "fips_place"]
    g = bps_place.sort_values("year").groupby(keys)
    j = g.agg(
        bps_name=("name", "last"),
        first_year=("year", "min"),
        last_year=("year", "max"),
        n_years=("year", "nunique"),
        units_total_all_years=("units_total", "sum"),
    ).reset_index()
    return j


def base_name(name: str) -> str:
    """'Greenville town' -> 'greenville'; 'Adams' -> 'adams'."""
    return re.sub(r"\s+(city|village|town)$", "", name.strip().lower())


def is_county_row(name: str) -> bool:
    """A BPS row is a county (unincorporated-area) row only if its name says so."""
    low = name.lower()
    return " county" in low or low.startswith("county") or "unincorporated" in low


def _blank(code) -> bool:
    return code is None or (isinstance(code, float) and np.isnan(code)) or str(code).strip() in ("", "00000")


# Documented mergers/renames: (BPS county FIPS, lower-case BPS name) -> TIGER 2024 name.
# Silver Lake village merged with Salem town into Salem Lakes village (2017).
NAME_ALIASES = {("059", "silver lake village"): "Salem Lakes village"}


def _name_match(m: pd.DataFrame, county_geoid: str, bps_name: str) -> tuple[str | None, str]:
    """Return (cousubfp, how) for a name match within the county, or (None, '')."""
    cty = m[m["county_geoid"] == county_geoid]
    full = bps_name.strip().lower()
    hit = cty[cty["name"].str.lower() == full]
    if hit["cousubfp"].nunique() == 1:
        return hit["cousubfp"].iloc[0], "full name"
    hit = cty[cty["name"].map(base_name) == base_name(bps_name)]
    if hit["cousubfp"].nunique() == 1:
        return hit["cousubfp"].iloc[0], "base name (type changed)"
    return None, ""


def resolve_identity(r, m: pd.DataFrame, by_fp: dict) -> tuple[str | None, str, str]:
    """Return (cousubfp, match_method, note) for a non-county BPS identity."""
    bps_county = "55" + r.county_fips
    if not _blank(r.fips_mcd):
        if r.fips_mcd in by_fp:
            return r.fips_mcd, "code", ""
        fp, how = _name_match(m, bps_county, r.bps_name)
        if fp:
            return fp, "name_county", f"BPS MCD code {r.fips_mcd} not in TIGER 2024; matched by {how} in county to code {fp}"
    else:
        fp = None if _blank(r.fips_place) else str(r.fips_place).strip()
        if fp in by_fp:
            p = by_fp[fp]
            if (p["county_geoid"] == bps_county).any() and (p["name"].map(base_name) == base_name(r.bps_name)).any():
                return fp, "place_code", f"BPS MCD code blank; BPS place code {fp} is the TIGER county-subdivision code with the same name"
        fp, how = _name_match(m, bps_county, r.bps_name)
        if fp:
            return fp, "name_county", f"BPS MCD code blank; matched by {how} in county to code {fp}"
    alias = NAME_ALIASES.get((r.county_fips, r.bps_name.strip().lower()))
    if alias:
        fp, _ = _name_match(m, bps_county, alias)
        if fp:
            return fp, "name_alias", f"merged/renamed: BPS '{r.bps_name}' is now {alias} (code {fp})"
    return None, "unmatched", ("FIPS MCD code not in TIGER 2024 county subdivisions" if not _blank(r.fips_mcd)
                               else "BPS MCD code blank and no name match in county")


def build_crosswalk(bps_place: pd.DataFrame, munis: pd.DataFrame) -> pd.DataFrame:
    """Link BPS jurisdictions to municipality pieces.

    munis columns: area_id, geoid, cousubfp, county_geoid, muni_type, name,
    homes_1unit_detached.
    """
    j = bps_jurisdictions(bps_place)
    m = munis[munis["muni_type"] != "not_defined"]
    by_fp = {fp: grp for fp, grp in m.groupby("cousubfp")}
    keys = ["bps_id", "county_fips", "fips_mcd", "fips_place"]
    j["is_county_row"] = j["bps_name"].map(is_county_row)

    # pass 1: municipal identities
    rows = []
    resolved = {}
    for r in j[~j["is_county_row"]].itertuples(index=False):
        base = _base(r)
        bps_county = "55" + r.county_fips
        fp, method, note = resolve_identity(r, m, by_fp)
        resolved[(r.bps_id, r.county_fips, r.fips_mcd, r.fips_place)] = fp
        if fp is None:
            rows.append({**base, "match_type": "unmatched", "area_id": None, "wi_muni_id": None, "muni_name": None,
                         "piece_county": None, "is_primary_piece": None, "alloc_share": None, "n_pieces": 0,
                         "match_note": note})
            continue
        pieces = by_fp[fp]
        n = len(pieces)
        if method != "code":
            mt = method
        elif n == 1:
            mt = "exact" if pieces.iloc[0]["county_geoid"] == bps_county else "mcd_other_county"
        else:
            mt = "multi_county"
        tot = pieces["homes_1unit_detached"].sum()
        in_cty = pieces["county_geoid"] == bps_county
        primary_geoid = (pieces.loc[in_cty, "geoid"].iloc[0] if in_cty.any()
                         else pieces.sort_values("homes_1unit_detached", ascending=False)["geoid"].iloc[0])
        if n > 1 and method != "code":
            note += " (multi-county; share by ACS one-unit detached homes)"
        for p in pieces.itertuples(index=False):
            share = 1.0 if n == 1 else ((p.homes_1unit_detached / tot) if tot else np.nan)
            rows.append({**base, "match_type": mt, "area_id": p.area_id, "wi_muni_id": p.geoid, "muni_name": p.name,
                         "piece_county": p.county_geoid, "is_primary_piece": p.geoid == primary_geoid,
                         "alloc_share": share, "n_pieces": n,
                         "match_note": note or {
                             "exact": "",
                             "mcd_other_county": "BPS county differs from TIGER county",
                             "multi_county": "BPS reports the whole municipality once; share = piece's ACS one-unit detached homes",
                         }[mt]})

    # municipality code -> years with its own BPS row (after resolving blank codes)
    bp = bps_place.assign(_fp=[resolved.get(k) for k in zip(*(bps_place[c] for c in keys))])
    own_years = bp.dropna(subset=["_fp"]).groupby("_fp")["year"].apply(lambda s: set(map(int, s))).to_dict()
    county_years = bps_place.groupby(keys)["year"].apply(lambda s: sorted(set(map(int, s)))).to_dict()

    # pass 2: county rows -> towns without their own row in at least one covered year
    for r in j[j["is_county_row"]].itertuples(index=False):
        base = _base(r)
        bps_county = "55" + r.county_fips
        yrs = county_years[(r.bps_id, r.county_fips, r.fips_mcd, r.fips_place)]
        towns = m[(m["county_geoid"] == bps_county) & (m["muni_type"] == "town")]
        cov = {t.cousubfp: [y for y in yrs if y not in own_years.get(t.cousubfp, set())] for t in towns.itertuples()}
        towns = towns[[bool(cov[fp]) for fp in towns["cousubfp"]]]
        if towns.empty:
            rows.append({**base, "match_type": "county_unincorporated", "area_id": None, "wi_muni_id": None,
                         "muni_name": None, "piece_county": bps_county, "is_primary_piece": None,
                         "alloc_share": None, "n_pieces": 0, "county_years_covered": "",
                         "town_has_own_row_some_years": None,
                         "match_note": "county-issued permits; every town in the county has its own BPS row in these years"})
            continue
        last = [fp for fp in towns["cousubfp"] if r.last_year in cov[fp]]
        tot = towns.loc[towns["cousubfp"].isin(last), "homes_1unit_detached"].sum()
        for t in towns.itertuples(index=False):
            share = (t.homes_1unit_detached / tot) if (t.cousubfp in last and tot) else (0.0 if t.cousubfp not in last else np.nan)
            partial = len(cov[t.cousubfp]) < len(yrs)
            rows.append({**base, "match_type": "county_unincorporated", "area_id": t.area_id, "wi_muni_id": t.geoid,
                         "muni_name": t.name, "piece_county": t.county_geoid, "is_primary_piece": False,
                         "alloc_share": share, "n_pieces": len(towns),
                         "county_years_covered": ";".join(map(str, cov[t.cousubfp])),
                         "town_has_own_row_some_years": partial,
                         "match_note": ("county-issued permits for towns without their own BPS row; alloc_share is for "
                                        f"{r.last_year} (per-year shares: county_unincorporated_allocation)")
                                       + ("; this town has its own BPS row in the other years" if partial else "")})
    out = pd.DataFrame(rows)
    return out


def _base(r) -> dict:
    return dict(bps_id=r.bps_id, bps_name=r.bps_name, bps_county_fips=r.county_fips, fips_mcd=r.fips_mcd,
                fips_place=r.fips_place, first_year=r.first_year, last_year=r.last_year, n_years=r.n_years,
                units_total_all_years=r.units_total_all_years)


def county_unincorporated_allocation(xw: pd.DataFrame, bps_place: pd.DataFrame, munis: pd.DataFrame) -> pd.DataFrame:
    """Per-year split of each county row to the towns it covers that year.

    Shares are ACS one-unit detached homes among the towns without their own
    BPS row in that year. The split is an assumption, not an observation.
    """
    c = xw[(xw["match_type"] == "county_unincorporated") & xw["area_id"].notna()]
    homes = munis.set_index("area_id")["homes_1unit_detached"]
    keys = ["bps_id", "county_fips", "fips_mcd", "fips_place"]
    units = bps_place.set_index(keys + ["year"])[["units_total", "1unit_units"]]
    rows = []
    for r in c.itertuples(index=False):
        for y in filter(None, str(r.county_years_covered).split(";")):
            rows.append(dict(year=int(y), bps_id=r.bps_id, bps_name=r.bps_name, bps_county_fips=r.bps_county_fips,
                             fips_mcd=r.fips_mcd, fips_place=r.fips_place, area_id=r.area_id, muni_name=r.muni_name,
                             homes_1unit_detached=float(homes.get(r.area_id, np.nan))))
    a = pd.DataFrame(rows)
    if a.empty:
        return a
    gk = ["year", "bps_id", "bps_county_fips", "fips_mcd", "fips_place"]
    a["alloc_share"] = a["homes_1unit_detached"] / a.groupby(gk)["homes_1unit_detached"].transform("sum")
    u = units.reset_index().rename(columns={"county_fips": "bps_county_fips"})
    a = a.merge(u, on=gk, how="left")
    a["allocated_units_total"] = a["units_total"] * a["alloc_share"]
    a["allocated_1unit"] = a["1unit_units"] * a["alloc_share"]
    a["status"] = "assumed"
    return a.rename(columns={"units_total": "county_row_units_total", "1unit_units": "county_row_1unit"})


def match_summary(xw: pd.DataFrame, bps_place: pd.DataFrame, year: int | None = None) -> dict:
    """Match rate by jurisdiction count and by permitted units."""
    j = xw.drop_duplicates(["bps_id", "bps_county_fips", "fips_mcd", "fips_place"])
    if year is not None:
        j = j[(j["first_year"] <= year) & (j["last_year"] >= year)]
        keys = ["bps_id", "county_fips", "fips_mcd", "fips_place"]
        units = bps_place[bps_place["year"] == year].groupby(keys)["units_total"].sum()
        j = j.assign(units=[units.get((a, b, c, d), 0.0) for a, b, c, d in
                            zip(j["bps_id"], j["bps_county_fips"], j["fips_mcd"], j["fips_place"])])
    else:
        j = j.assign(units=j["units_total_all_years"])
    counts = j["match_type"].value_counts().to_dict()
    matched = j["match_type"].isin(MATCHED_TYPES)
    county = j["match_type"] == "county_unincorporated"
    return {
        "year": year,
        "jurisdictions": int(len(j)),
        "by_type": {k: int(v) for k, v in counts.items()},
        "matched_to_municipality_pct": round(100 * matched.mean(), 2) if len(j) else None,
        "matched_or_county_pct": round(100 * (matched | county).mean(), 2) if len(j) else None,
        "units": float(j["units"].sum()),
        "units_matched_to_municipality_pct": round(100 * j.loc[matched, "units"].sum() / j["units"].sum(), 2) if j["units"].sum() else None,
        "units_county_unincorporated_pct": round(100 * j.loc[county, "units"].sum() / j["units"].sum(), 2) if j["units"].sum() else None,
        "units_unmatched": float(j.loc[j["match_type"] == "unmatched", "units"].sum()),
    }
