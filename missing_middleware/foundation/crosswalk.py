"""Crosswalk from Census BPS permit-issuing places to Wisconsin municipalities.

In Wisconsin every city, village and town is a county subdivision (MCD), and
BPS records the 5-digit FIPS MCD code of each permit-issuing jurisdiction.
FIPS MCD codes are unique within the state, so a BPS row links to every
county-subdivision piece that shares its COUSUBFP:

  exact                  one piece, in the BPS county
  mcd_other_county       one piece, in a different county than BPS lists
  multi_county           several pieces (a city or village crossing county
                         lines); BPS reports it once, under its main county.
                         Each piece gets an allocation share by ACS one-unit
                         detached homes; is_primary_piece marks the BPS county.
  county_unincorporated  BPS "<County> Part Unincorporated Area" rows (MCD
                         00000): permits issued by the county for towns that
                         do not report on their own; linked to those towns.
  name_county            FIPS MCD code not in TIGER 2024, but the base name
                         (without city/village/town) matches exactly one
                         municipality in the BPS county: typically a town that
                         incorporated as a village and got a new code (BPS
                         kept the old code for some years).
  unmatched              neither the code nor the name matches (dissolved or
                         merged municipalities).
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

MATCHED_TYPES = {"exact", "mcd_other_county", "multi_county", "name_county"}


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


def build_crosswalk(bps_place: pd.DataFrame, munis: pd.DataFrame) -> pd.DataFrame:
    """Link BPS jurisdictions to municipality pieces.

    munis columns: area_id, geoid, cousubfp, county_geoid, muni_type, name,
    homes_1unit_detached.
    """
    j = bps_jurisdictions(bps_place)
    m = munis[munis["muni_type"] != "not_defined"]
    by_fp = {fp: grp for fp, grp in m.groupby("cousubfp")}
    # towns with their own BPS row, by year (to resolve county-unincorporated rows)
    own_years = bps_place[bps_place["fips_mcd"] != "00000"].groupby("fips_mcd")["year"].apply(set).to_dict()

    rows = []
    for r in j.itertuples(index=False):
        base = dict(bps_id=r.bps_id, bps_name=r.bps_name, bps_county_fips=r.county_fips, fips_mcd=r.fips_mcd,
                    fips_place=r.fips_place, first_year=r.first_year, last_year=r.last_year, n_years=r.n_years,
                    units_total_all_years=r.units_total_all_years)
        bps_county = "55" + r.county_fips
        if r.fips_mcd in ("00000", "") or "unincorporated" in r.bps_name.lower():
            towns = m[(m["county_geoid"] == bps_county) & (m["muni_type"] == "town")]
            towns = towns[[r.last_year not in own_years.get(fp, set()) for fp in towns["cousubfp"]]]
            if towns.empty:
                rows.append({**base, "match_type": "county_unincorporated", "area_id": None, "wi_muni_id": None,
                             "muni_name": None, "piece_county": bps_county, "is_primary_piece": None,
                             "alloc_share": None, "n_pieces": 0,
                             "match_note": "county-issued permits; no town without its own BPS row found"})
            tot = towns["homes_1unit_detached"].sum()
            for t in towns.itertuples(index=False):
                rows.append({**base, "match_type": "county_unincorporated", "area_id": t.area_id, "wi_muni_id": t.geoid,
                             "muni_name": t.name, "piece_county": t.county_geoid, "is_primary_piece": False,
                             "alloc_share": (t.homes_1unit_detached / tot) if tot else np.nan, "n_pieces": len(towns),
                             "match_note": f"county-issued permits covering towns without their own BPS row in {r.last_year}"})
            continue
        pieces = by_fp.get(r.fips_mcd)
        fallback = False
        if pieces is None:
            cand = m[(m["county_geoid"] == bps_county) & (m["name"].map(base_name) == base_name(r.bps_name))]
            if cand["cousubfp"].nunique() == 1:
                pieces = by_fp[cand["cousubfp"].iloc[0]]
                fallback = True
        if pieces is None:
            rows.append({**base, "match_type": "unmatched", "area_id": None, "wi_muni_id": None, "muni_name": None,
                         "piece_county": None, "is_primary_piece": None, "alloc_share": None, "n_pieces": 0,
                         "match_note": "FIPS MCD code not in TIGER 2024 county subdivisions"})
            continue
        n = len(pieces)
        if fallback:
            mt = "name_county"
        elif n == 1:
            mt = "exact" if pieces.iloc[0]["county_geoid"] == bps_county else "mcd_other_county"
        else:
            mt = "multi_county"
        tot = pieces["homes_1unit_detached"].sum()
        # primary piece = the one in the BPS county; if none is, the piece with most homes
        in_cty = pieces["county_geoid"] == bps_county
        primary_geoid = (pieces.loc[in_cty, "geoid"].iloc[0] if in_cty.any()
                         else pieces.sort_values("homes_1unit_detached", ascending=False)["geoid"].iloc[0])
        for p in pieces.itertuples(index=False):
            share = 1.0 if n == 1 else ((p.homes_1unit_detached / tot) if tot else np.nan)
            rows.append({**base, "match_type": mt, "area_id": p.area_id, "wi_muni_id": p.geoid, "muni_name": p.name,
                         "piece_county": p.county_geoid, "is_primary_piece": p.geoid == primary_geoid,
                         "alloc_share": share, "n_pieces": n,
                         "match_note": {
                             "exact": "",
                             "mcd_other_county": "BPS county differs from TIGER county",
                             "multi_county": "BPS reports the whole municipality once; share = piece's ACS one-unit detached homes",
                             "name_county": f"BPS MCD code {r.fips_mcd} not in TIGER 2024; matched by name in county to code {p.cousubfp}"
                                            + (" (multi-county; share by ACS one-unit detached homes)" if n > 1 else ""),
                         }[mt]})
    return pd.DataFrame(rows)


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
