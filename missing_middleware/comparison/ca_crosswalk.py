"""Crosswalk HCD jurisdiction names to Census place codes, county FIPS and BPS place ids.

HCD reports by jurisdiction: an incorporated city (JURIS_NAME = city name) or a
county's unincorporated area (JURIS_NAME = "<NAME> COUNTY"). San Francisco is a
consolidated city and county and reports once, as "SAN FRANCISCO".

Matching is deterministic: normalized exact name within the reported county,
then a short, documented alias table. Nothing is fuzzy-matched.
"""
from __future__ import annotations

import pandas as pd

from missing_middleware.comparison.ca_inputs import norm_name

# HCD spelling -> TIGER 2024 place NAME (normalized). Each checked by hand against
# the TIGER/BPS name and county on 2026-10-24.
ALIASES = {
    "VENTURA": "SAN BUENAVENTURA (VENTURA)",
    "PASO ROBLES": "EL PASO DE ROBLES (PASO ROBLES)",
    "CATHEDRAL": "CATHEDRAL CITY",
    "ANGELS CAMP": "ANGELS",
    "AMADOR": "AMADOR CITY",
    "CARMEL": "CARMEL BY THE SEA",
    "SAINT HELENA": "SAINT HELENA",
    # Typo in the Building an ADU compilation (row label repeats a word).
    "RANCHO SANTA MARGARITA MARGARITA": "RANCHO SANTA MARGARITA",
}

# Cities incorporated after the TIGER/ACS 2024 vintage (geography as of 2024-01-01).
LATE_INCORPORATIONS = {"MOUNTAIN HOUSE": {"placefp": "49582", "county_fips": "077",
                                          "note": "Incorporated 2024-07-01; a CDP in TIGER/ACS 2024"}}


def county_lookup(pep_v2020: pd.DataFrame) -> pd.DataFrame:
    """County FIPS and name from the PEP Vintage 2020 file (SUMLEV 050 rows)."""
    c = pep_v2020[pep_v2020["SUMLEV"] == "050"][["COUNTY", "CTYNAME"]].copy()
    c.columns = ["county_fips", "county_name"]
    c["county_key"] = c["county_name"].map(norm_name).str.replace(r" COUNTY$", "", regex=True)
    return c


def build_crosswalk(hcd_names: pd.DataFrame, places: pd.DataFrame, place_county: pd.DataFrame,
                    counties: pd.DataFrame, bps_place: pd.DataFrame) -> pd.DataFrame:
    """hcd_names: juris_name, cnty_name (one row per jurisdiction, any source).
    places: TIGER places (placefp, name, incorporated). place_county: placefp -> county_fips
    (ACS sumlevel 155). counties: county_lookup(). bps_place: BPS place annual rows.
    """
    pl = places[places["incorporated"]].copy()
    pl["key"] = pl["name"].map(norm_name)
    pl = pl.merge(place_county, on="placefp", how="left")
    for nm, v in LATE_INCORPORATIONS.items():
        if nm not in set(pl["key"]):
            pl = pd.concat([pl, pd.DataFrame([{"placefp": v["placefp"], "name": nm.title(), "key": nm,
                                               "county_fips": v["county_fips"], "incorporated": True}])])
    by_key = pl.drop_duplicates("key").set_index("key")
    ck = counties.set_index("county_key")

    bps = bps_place.copy()
    bps_ids_place = bps[~bps["fips_place"].isin(["00000", "99990"])].groupby("fips_place")["bps_id"].agg(
        lambda s: ";".join(sorted(set(s))))
    bps_uninc = bps[bps["fips_place"].isin(["00000", "99990"])].groupby("county_fips")["bps_id"].agg(
        lambda s: ";".join(sorted(set(s))))

    rows = []
    for _, r in hcd_names.drop_duplicates("juris_name").iterrows():
        jn = r["juris_name"]
        key = norm_name(jn)
        cnty = norm_name(r.get("cnty_name") or "").replace(" COUNTY", "") or None
        rec = {"juris_name": jn, "cnty_name": r.get("cnty_name"), "juris_type": None, "placefp": None,
               "census_geoid": None, "county_fips": None, "bps_ids": None, "match_method": None, "note": None}
        if key == "SAN FRANCISCO":
            rec.update(juris_type="city_county", placefp="67000", census_geoid="0667000", county_fips="075",
                       match_method="consolidated city-county")
        elif key.endswith(" COUNTY") and key[:-7] in ck.index:
            fips = ck.loc[key[:-7], "county_fips"]
            rec.update(juris_type="county_unincorporated", county_fips=fips,
                       census_geoid=f"06{fips}_UNINC", match_method="county name")
        else:
            target = ALIASES.get(key, key)
            if target in by_key.index:
                p = by_key.loc[target]
                rec.update(juris_type="city", placefp=p["placefp"], census_geoid="06" + p["placefp"],
                           county_fips=p["county_fips"],
                           match_method="alias" if target != key else "exact name")
                if key in LATE_INCORPORATIONS:
                    rec["note"] = LATE_INCORPORATIONS[key]["note"]
                if cnty and cnty in ck.index and ck.loc[cnty, "county_fips"] != p["county_fips"]:
                    rec["note"] = f"county mismatch: HCD {r.get('cnty_name')} vs Census {p['county_fips']}"
        if rec["juris_type"] in ("city", "city_county"):
            rec["bps_ids"] = bps_ids_place.get(rec["placefp"])
        elif rec["juris_type"] == "county_unincorporated":
            rec["bps_ids"] = bps_uninc.get(rec["county_fips"])
        rows.append(rec)
    out = pd.DataFrame(rows).sort_values("juris_name").reset_index(drop=True)
    out["matched_census"] = out["census_geoid"].notna()
    out["matched_bps"] = out["bps_ids"].notna()
    return out


# ---------------------------------------------------------------------------
# Pre-registered 20% holdout (docs/gate3/CA_COMPARISON_PLAN.md, "Held-out data")
# ---------------------------------------------------------------------------

HOLDOUT_SEED = 20261024
HOLDOUT_SHARE = 0.20
HOLDOUT_METHOD = ("Universe: every California jurisdiction that reports to HCD as of 2026 "
                  "(incorporated places in TIGER 2024 incl. San Francisco city-county, plus Mountain House "
                  "incorporated 2024-07-01, plus 57 county unincorporated areas), keyed by census_geoid and "
                  "sorted ascending. Simple random sample without replacement of round(0.20 * N) "
                  "jurisdictions with numpy.random.default_rng(20261024).choice. Drawn from identifiers only, "
                  "before any ADU rate by group was computed.")


# Correction note carried beside `method` (the method text is kept as drawn). The universe is
# the Census geography of HCD reporting jurisdictions, not the set that actually has HCD data.
HOLDOUT_METHOD_NOTE = ("The universe is Census geography (TIGER 2024 incorporated places, Mountain House and county "
                       "remainders), not the jurisdictions with data: Loyalton has no HCD or compilation rows, and "
                       "Vernon, Industry, Laguna Woods and Tehama appear only in the 2012-2019 compilation. "
                       "The draw used identifiers only and a fixed seed, and a rebuild reproduces it. No claim is made "
                       "about its timing relative to earlier development runs of step 0; see has_hcd_a2_data.")


def holdout_flag(geoids: pd.Series, hold: pd.DataFrame) -> pd.Series:
    """True where a census_geoid is in the pre-registered holdout; False otherwise (including
    geoids outside the universe, which cannot be held out)."""
    ids = set(hold.loc[hold["holdout"].astype(str).str.lower() == "true", "census_geoid"])
    return geoids.isin(ids)


def holdout_universe(places: pd.DataFrame, place_county: pd.DataFrame, counties: pd.DataFrame) -> pd.DataFrame:
    inc = places[places["incorporated"]][["placefp", "name"]].merge(place_county, on="placefp", how="left")
    inc = inc.assign(census_geoid="06" + inc["placefp"],
                     juris_type=inc["placefp"].map(lambda p: "city_county" if p == "67000" else "city"))
    for nm, v in LATE_INCORPORATIONS.items():
        if v["placefp"] not in set(inc["placefp"]):
            inc = pd.concat([inc, pd.DataFrame([{"placefp": v["placefp"], "name": nm.title(),
                                                 "county_fips": v["county_fips"], "census_geoid": "06" + v["placefp"],
                                                 "juris_type": "city"}])])
    co = counties[counties["county_fips"] != "075"]
    un = pd.DataFrame({"placefp": None, "name": co["county_name"] + " unincorporated", "county_fips": co["county_fips"],
                       "census_geoid": "06" + co["county_fips"] + "_UNINC", "juris_type": "county_unincorporated"})
    return pd.concat([inc, un], ignore_index=True).sort_values("census_geoid").reset_index(drop=True)


def draw_holdout(universe: pd.DataFrame, seed: int = HOLDOUT_SEED, share: float = HOLDOUT_SHARE) -> pd.DataFrame:
    import numpy as np

    u = universe.sort_values("census_geoid").reset_index(drop=True)
    n = int(round(share * len(u)))
    idx = np.random.default_rng(seed).choice(len(u), size=n, replace=False)
    out = u.assign(holdout=False)
    out.loc[idx, "holdout"] = True
    out["seed"] = seed
    out["universe_size"] = len(u)
    out["method"] = HOLDOUT_METHOD
    return out
