"""Eligible-property basis: permits (1 per parcel per year) per 1,000 properties eligible under each
place's ADU law, rerun through the pooled model, the G3F-2 test and the Wisconsin engine.
Owner reframing 2026-10-25; documented in docs/gate3/ELIGIBLE_BASIS.md. Writes new files only.

Inputs: everything scripts/run_pooled_revision.py reads, plus data/raw/hcd_apr_a2/tablea2.csv
(APN and site address, in memory only), data/raw/la_county_assessor_rolls/roll_*.csv, the city
permit caches read by scripts/build_other_cities.py, the Wisconsin permit records in
data/processed/permits*/permits_records_full.parquet, data/raw/milwaukee_* and the full ACS
2020-2024 B25024 table (data/raw/census_acs5_2024_tbsf/acsdt5y2024-b25024.dat).

Outputs:
  reference/eligible_basis_denominators.csv    eligible properties by series/state, scenario and size set
  reference/eligible_basis_numerators.csv      units vs flattened permits by source and year
  reference/eligible_basis_propensity_la.csv   LA County permits per 1,000 properties, SF vs MF lots, by year
  reference/eligible_basis_parcel_check.csv    LA County ADU parcels: existing units, buildings, ADUs per parcel, band rates
  reference/eligible_basis_a2_adu_per_parcel.csv  statewide A2 parcel-years by ADU units on the parcel (1, 2, 3, 4+)
  reference/eligible_basis_ca_rates.csv        California 2023-2025 rate under each basis
  reference/eligible_basis_g3f2.csv            G3F-2: RMS log error by configuration, noise checks
  reference/eligible_basis_loso.csv            held-out log errors by state
  reference/eligible_basis_wi.csv              Wisconsin engine outputs, every run
  reference/eligible_basis_stage2_levels.csv   each state's level on the eligible basis
  data/processed/eligible_basis/summary.json
Run: uv run python scripts/run_eligible_basis.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import run_pooled_revision as RV  # noqa: E402
from missing_middleware.comparison import ca_inputs as I  # noqa: E402
from missing_middleware.comparison import ca_mf_lot as M  # noqa: E402
from missing_middleware.comparison import ca_regression as cr  # noqa: E402
from missing_middleware.comparison import ca_study as S  # noqa: E402
from missing_middleware.comparison import eligible_basis as E  # noqa: E402
from missing_middleware.comparison import other_cities as oc  # noqa: E402
from missing_middleware.comparison import pooled_regression as pr  # noqa: E402
from missing_middleware.comparison import pooled_revision as R  # noqa: E402
from missing_middleware.foundation.parsers import read_acs_sf  # noqa: E402
from missing_middleware.model import baseline as bl  # noqa: E402
from missing_middleware.paths import PROCESSED, RAW, REFERENCE, processed_dir  # noqa: E402

rp = RV.rp
A2 = RAW / "hcd_apr_a2" / "tablea2.csv"
B25024 = RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25024.dat"
LA_ROLLS = RAW / "la_county_assessor_rolls"
FLOOR = RV.FLOOR_NEW
CONFIGS = RV.CONFIGS
STATES = RV.STATES
CITY_KEY = {"5363000": "seattle", "4159000": "portland", "4805000": "austin", "0820000": "denver",
            "2743000": "minneapolis"}
POOLED_REVISION = {"cap_a2": dict(lower=4424, central=8912, upper=17374, madison_path=8721),
                   "cap_la_calibrated": dict(lower=4586, central=8579, upper=15621, madison_path=8402)}


# ---------------------------------------------------------------------------
# ACS B25024 components
# ---------------------------------------------------------------------------

def read_b25024(states: set[str], sumlevels=("040", "050", "060", "160")) -> pd.DataFrame:
    keep = []
    with open(B25024, encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("|")
        for line in f:
            gid = line.split("|", 1)[0]
            if gid[:3] in sumlevels and gid[3:9] == "0000US" and gid[9:11] in states:
                keep.append(line.rstrip("\n").split("|"))
    d = pd.DataFrame(keep, columns=header)
    d["sumlevel"], d["geoid"] = d["GEO_ID"].str[:3], d["GEO_ID"].str[9:]
    return E.components_from_acs(d)


def ca_juris_components() -> pd.DataFrame:
    """B25024 components per HCD-style jurisdiction (as ca_mf_lot.acs_mf_share)."""
    acs = read_acs_sf(B25024, state_fips="06", sumlevels=("050", "155", "160"))
    places = I.read_tiger_places(RAW / "census_tiger_2024_ca_place/tl_2024_06_place.zip")
    a = E.components_from_acs(acs)
    comps = list(E.COMPONENTS)
    a["placefp"] = np.where(a["sumlevel"].isin(["155", "160"]), a["geoid"].str[2:7], None)
    a["county_fips"] = np.select([a["sumlevel"] == "050", a["sumlevel"] == "155"],
                                 [a["geoid"].str[2:5], a["geoid"].str[7:10]], default=None)
    inc = set(places.loc[places["incorporated"], "placefp"])
    pl = a[(a["sumlevel"] == "160") & a["placefp"].isin(inc)].assign(census_geoid=lambda x: "06" + x["placefp"])
    parts = a[(a["sumlevel"] == "155") & a["placefp"].isin(inc)].groupby("county_fips")[comps].sum()
    co = a[a["sumlevel"] == "050"].set_index("county_fips")[comps]
    rem = (co - parts.reindex(co.index).fillna(0)).reset_index()
    rem = rem[rem["county_fips"] != "075"]
    rem["census_geoid"] = "06" + rem["county_fips"] + "_UNINC"
    return pd.concat([pl[["census_geoid"] + comps], rem[["census_geoid"] + comps]], ignore_index=True)


def group_key(gid: str) -> str:
    if gid.startswith("ca:"):
        return "CA"
    if gid.startswith("place:"):
        return CITY_KEY.get(gid.split(":")[1], "other")
    return E.STATE_OF_SERIES[gid]


def eligible_members(members: pd.DataFrame, acs: pd.DataFrame, caj: pd.DataFrame, scenario: str = "central",
                     size: str | None = None, mf_weight: dict | None = None, drop: tuple = ()) -> pd.DataFrame:
    """Members with `homes` replaced by eligible properties (the exposure, size term and context
    weights all follow). mf_weight: optional {group key: multiplier on multifamily properties}
    (the propensity-adjusted sensitivity)."""
    m = members.copy()
    st = m[~m["group_id"].str.startswith("ca:")].merge(acs, on=["geoid", "sumlevel"], how="left")
    ca = m[m["group_id"].str.startswith("ca:")].merge(caj.rename(columns={"census_geoid": "geoid"}), on="geoid", how="left")
    out = []
    for part in (st, ca):
        part = part.copy()
        keys = part["group_id"].map(group_key)
        el = np.full(len(part), np.nan)
        for k in keys.unique():
            sel = (keys == k).to_numpy()
            if k == "other":
                el[sel] = part.loc[sel, "homes"]
                continue
            i, sz = E.SCENARIOS[scenario]
            scope = {c: w for c, w in E.LAW_SCOPE[k][i].items() if c not in drop}
            if mf_weight and k in mf_weight:
                scope = {c: (w * mf_weight[k] if c in E.MF else w) for c, w in scope.items()}
            # eligible / one-unit detached from the components, applied to the member's own homes count
            # (California's study denominators differ slightly from the B25024 place/remainder sums)
            ratio = E.eligible(part.loc[sel], scope, E.SIZES[size or sz]) / part.loc[sel, "sf_det"].where(part.loc[sel, "sf_det"] > 0)
            el[sel] = (part.loc[sel, "homes"] * ratio.fillna(1.0)).to_numpy()
        part["sf_homes"] = part["homes"]
        part["homes"] = np.where(np.isnan(el), part["homes"], el)
        out.append(part[list(members.columns) + ["sf_homes"]])
    return pd.concat(out, ignore_index=True)


# ---------------------------------------------------------------------------
# Numerators
# ---------------------------------------------------------------------------

def a2_rows_with_site() -> pd.DataFrame:
    """As ca_mf_lot.read_a2_adu_rows (study main measure), plus a site key: APN, else the
    standardised (or reported) street address, else the permit row. In memory only."""
    rows = I.classify_permit_rows(I.read_apr_a2(A2))
    raw = pd.read_csv(A2, usecols=["APN", "NOTES", "PROJECT_NAME", "BP_ISSUE_DT1", "STREET_ADDRESS", "STD_ADDRESS"],
                      dtype=str, low_memory=False)
    raw.index = rows.index
    flag = S.classify_adu_text(raw["NOTES"].fillna("") + " | " + raw["PROJECT_NAME"].fillna(""))
    rows["apn"] = M.normalize_apn(raw["APN"])
    rows["site"], rows["site_basis"] = E.site_key(rows["apn"], raw["STD_ADDRESS"].fillna(raw["STREET_ADDRESS"]),
                                                  rows["permit_key"])
    r = rows[rows["unit_cat"].eq("ADU") & rows["bp_units"].fillna(0).gt(0)].copy()
    r["text_flag"] = flag.reindex(r.index).fillna("kept")
    flagged = set(r.loc[r["text_flag"].ne("kept"), "permit_key"])
    r = r[~r["permit_key"].isin(flagged) & r["date_status"].isin(["date_in_year", "date_missing"])]
    out = r[["juris_name", "cnty_name", "year", "bp_units", "permit_key", "apn", "site", "site_basis"]].rename(
        columns={"bp_units": "units"})
    out["year"] = out["year"].astype(int)
    return out.reset_index(drop=True)


def a2_owner_check() -> list[dict]:
    """The owner's figure: every A2 ADU row with permitted units and an APN, by year."""
    rows = I.classify_permit_rows(I.read_apr_a2(A2))
    raw = pd.read_csv(A2, usecols=["APN"], dtype=str, low_memory=False)
    raw.index = rows.index
    rows["apn"] = M.normalize_apn(raw["APN"])
    a = rows[rows["unit_cat"].eq("ADU") & rows["bp_units"].fillna(0).gt(0) & rows["apn"].notna()]
    out = []
    for y in range(2018, 2026):
        z = a[a["year"].astype(int).eq(y)]
        out.append(dict(source="CA HCD A2, all ADU rows with permitted units and an APN", year=y,
                        units=float(z["bp_units"].sum()), permits=float(z.groupby("juris_name")["apn"].nunique().sum())))
    return out


def ca_removed(rows: pd.DataFrame, cap: bool) -> pd.DataFrame:
    """Per jurisdiction-year: ADU units minus flattened permits (optionally capped at 2 parcel-year
    events per parcel, cumulated 2018-2025)."""
    f = E.flatten(rows, ["juris_name", "year"])
    if cap:
        ev = E.capped_events(rows)
        k = ev[ev["keep"]].groupby(["juris_name", "year"]).size().rename("kept")
        f = f.merge(k.reset_index(), on=["juris_name", "year"], how="left")
        f["permits"] = f["kept"].fillna(0)
    return f.rename(columns={"units": "adu_units"}).assign(removed=lambda x: x["adu_units"] - x["permits"])


def city_flat(log) -> tuple[pd.DataFrame, pd.DataFrame]:
    """City permits (main classifiers) with a site key; flattened per city-year over the permits
    in `units_incl_new_house` (all but legalizations)."""
    sea = pd.read_csv(RAW / "seattle_permits_socrata" / "building_permits_adu_subset.csv", dtype=str)
    sea_h = pd.read_csv(RAW / "seattle_permits_socrata" / "new_single_family_permits.csv", dtype=str)
    sea_h = sea_h[~sea_h["dwellingunittype"].fillna("").str.contains("Accessory Dwelling")]
    pdx = pd.read_csv(RAW / "portland_res_permits" / "residential_building_permits.csv", dtype=str, encoding="utf-8-sig")
    aus = pd.read_csv(RAW / "austin_permits_socrata" / "bp_adu_candidates.csv", dtype=str)
    aus_h = pd.read_csv(RAW / "austin_permits_socrata" / "bp_new_houses_2005plus.csv", dtype=str)
    den = pd.read_csv(RAW / "denver_rescon_permits" / "residential_construction_permits.csv", dtype=str)
    den["DATE_ISSUED"] = pd.to_numeric(den["DATE_ISSUED"], errors="coerce")
    msp = pd.read_csv(RAW / "minneapolis_ccs_permits" / "ccs_permits_res_adu_text.csv", dtype=str)
    msp["issueDate"] = pd.to_numeric(msp["issueDate"], errors="coerce")
    spec = [  # city, classified, raw, raw id column, parcel column, address column
        ("seattle", oc.classify_seattle(sea, sea_h), sea, "permitnum", None, "originaladdress1"),
        ("portland", oc.classify_portland(pdx), pdx, "FOLDERNUMB", "PROPGISID1", "PROP_ADDRE"),
        ("austin", oc.classify_austin(aus, aus_h), aus, "permit_number", "tcad_id", "permit_location"),
        ("denver", oc.classify_denver(den), den, "PERMIT_NUM", "SCHEDNUM", "ADDRESS"),
        ("minneapolis", oc.classify_minneapolis(msp), msp, "permitNumber", "APN", None),
    ]
    parts = []
    for city, c, raw, idc, parc, addr in spec:
        rr = raw.drop_duplicates(idc).set_index(idc)
        c = c[~c["legalization"]].copy()
        par = c["permit_id"].map(rr[parc]) if parc else pd.Series(pd.NA, index=c.index)
        ad = c["permit_id"].map(rr[addr]) if addr else None
        c["site"], c["site_basis"] = E.site_key(par, ad, c["permit_id"])
        parts.append(c)
    allp = pd.concat(parts, ignore_index=True)
    f = E.flatten(allp.rename(columns={"adu_units": "units"}), ["city", "year"])
    basis = allp.groupby("city")["site_basis"].value_counts(normalize=True).unstack(fill_value=0)
    log("city site basis shares\n" + basis.round(3).to_string())
    return f, basis


def wi_flat() -> pd.DataFrame:
    """Wisconsin second-home permits 2022-2025 by city: permits vs distinct parcel-years (parcel id,
    else normalised address). Madison, Sun Prairie, Pleasant Prairie records; Milwaukee central
    candidates by address."""
    out = []
    for slug, d in (("Madison", "permits"), ("Sun Prairie", "permits_sun_prairie"), ("Pleasant Prairie", "permits_pleasant_prairie")):
        p = pd.read_parquet(PROCESSED / d / "permits_records_full.parquet")
        p["yr"] = pd.to_datetime(p["issue_date"], errors="coerce").dt.year
        s = p[(p["second_home_units"].fillna(0) > 0) & p["yr"].between(2022, 2025)].copy()
        addr = s["addr_house_nbr"].astype(str) + " " + s["addr_street_key"].astype(str)
        s["site"], _ = E.site_key(s["parcel_id"], addr.where(s["addr_street_key"].notna()), s["permit_id"])
        for y, g in s.groupby("yr"):
            out.append(dict(source=f"WI {slug} second homes on SF lots", year=int(y), units=float(g["second_home_units"].sum()),
                            rows=len(g), permits=float(g.drop_duplicates(["site"]).shape[0])))
    raw = pd.read_csv(RAW / "milwaukee_permits" / "buildingpermits.csv", low_memory=False)
    permits = pd.DataFrame({"record_id": raw["Record ID"], "issued": pd.to_datetime(raw["Date Issued"], errors="coerce"),
                            "permit_type": raw["Permit Type"].astype(str), "use": raw["Use of Building"],
                            "units_impact": raw["Dwelling units impact"], "address": raw["Address"]})
    cols = ["HOUSE_NR_LO", "HOUSE_NR_HI", "SDIR", "STREET", "NR_UNITS", "YR_BUILT"]
    mp = pd.read_csv(RAW / "milwaukee_mprop" / "mprop.csv", usecols=cols, dtype=str)
    mp.columns = ["house_lo", "house_hi", "sdir", "street", "nr_units", "yr_built"]
    cand = bl.milwaukee_candidates(permits, mp)
    cand = cand[cand["central"] & cand["issued"].dt.year.between(2022, 2025)].copy()
    cand["site"] = E.norm_site(cand["record_id"].map(permits.drop_duplicates("record_id").set_index("record_id")["address"]))
    for y, g in cand.groupby(cand["issued"].dt.year):
        out.append(dict(source="WI Milwaukee central candidates", year=int(y), units=float(len(g)), rows=len(g),
                        permits=float(g["site"].fillna(g["record_id"].astype(str)).nunique())))
    return pd.DataFrame(out)


# ---------------------------------------------------------------------------
# Equal-propensity test (LA County)
# ---------------------------------------------------------------------------

def la_propensity(rows: pd.DataFrame, acs_la: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame]:
    la = rows[rows["cnty_name"].eq("Los Angeles")].copy()
    la["ain"] = M.la_ain(la["apn"])
    rolls = pd.concat([pd.read_csv(f, dtype=str) for f in sorted(LA_ROLLS.glob("roll_*.csv"))], ignore_index=True)
    rolls["year"] = rolls["RollYear"].astype(int)
    rolls = rolls.drop_duplicates(["AIN", "year"])
    rolls["lot_class"] = M.classify_la_use(rolls["UseCode"], rolls["UseCodeDescChar2"])
    la = la.merge(rolls[["AIN", "year", "lot_class", "Units", "totBuildingDataLines"]].rename(columns={"AIN": "ain"}),
                  on=["ain", "year"], how="left")
    la["lot_class"] = la["lot_class"].fillna("unmatched")
    ev = la.drop_duplicates(["juris_name", "site", "year"])          # flattened permits
    sizes = {k: E.SIZES[k] for k in E.SIZES}
    one = pd.Series(acs_la)
    props = {"sf": one["sf_det"]}
    for k, sz in sizes.items():
        b = E.buildings(one.to_frame().T, sz).iloc[0]
        props[f"mf_{k}"] = float(b[list(E.MF)].sum())
        props[f"mf2_{k}"] = float(b["mf2"])
        props[f"mf3_4_{k}"] = float(b["mf3_4"])
        props[f"mf5p_{k}"] = float(b[["mf5_9", "mf10_19", "mf20_49", "mf50p"]].sum())
    out = []
    for y, g in ev.groupby("year"):
        cnt = g["lot_class"].value_counts()
        matched = len(g) - cnt.get("unmatched", 0)
        scale = len(g) / matched                     # spread unmatched permits pro rata
        sf = cnt.get("single_family", 0) * scale
        c2, c34, c5 = (cnt.get(k, 0) * scale for k in ("two_units", "three_four_units", "five_plus_units"))
        mf = c2 + c34 + c5
        row = dict(year=int(y), permits=len(g), matched_permits=int(matched), sf_lot_permits=sf, mf_lot_permits=mf,
                   two_unit_permits=c2, three_four_permits=c34, five_plus_permits=c5,
                   other_permits=len(g) - sf - mf, sf_detached_homes=props["sf"])
        for k in sizes:
            p = E.propensity(sf, mf, props["sf"], props[f"mf_{k}"])
            row[f"mf_properties_{k}"] = props[f"mf_{k}"]
            row[f"rate_mf_{k}"] = p["rate_mf"]
            row[f"ratio_mf_to_sf_{k}"] = p["ratio_mf_to_sf"]
            row[f"rate_two_unit_{k}"] = c2 / props[f"mf2_{k}"] * 1000
            row[f"rate_three_four_{k}"] = c34 / props[f"mf3_4_{k}"] * 1000
            row[f"rate_five_plus_{k}"] = c5 / props[f"mf5p_{k}"] * 1000
        row["rate_sf"] = sf / props["sf"] * 1000
        out.append(row)
    prop = pd.DataFrame(out)
    # building-vs-parcel check on multifamily ADU parcels (one row per parcel, first year it appears)
    mfp = la[la["lot_class"].isin(M.LA_MF_CLASSES)].drop_duplicates("ain").copy()
    mfp["units_on_parcel"] = pd.to_numeric(mfp["Units"], errors="coerce")
    mfp["building_lines"] = pd.to_numeric(mfp["totBuildingDataLines"], errors="coerce")
    chk = mfp.groupby("lot_class").agg(parcels=("ain", "size"), mean_units=("units_on_parcel", "mean"),
                                       median_units=("units_on_parcel", "median"),
                                       mean_building_lines=("building_lines", "mean"),
                                       share_multi_building=("building_lines", lambda s: float((s > 1).mean())),
                                       units_per_building_line=("units_on_parcel", "sum")).reset_index()
    bl_sum = mfp.groupby("lot_class")["building_lines"].sum()
    chk["units_per_building_line"] = chk["units_per_building_line"] / chk["lot_class"].map(bl_sum)
    f5 = mfp[mfp["lot_class"].eq("five_plus_units")]["units_on_parcel"]
    bands = pd.cut(f5, [4, 9, 19, 49, 1e9], labels=["5-9", "10-19", "20-49", "50+"]).value_counts().sort_index()
    chk = pd.concat([chk, pd.DataFrame({"lot_class": [f"five_plus_units, {b} units" for b in bands.index],
                                        "parcels": bands.to_numpy()})], ignore_index=True)
    # ADU units per parcel-year (1, 2, 3, 4+) against the parcel's existing units (assessor), 2023-2025,
    # and multifamily-lot permits per 1,000 buildings by building size band
    z = la[la["year"].between(2023, 2025) & la["ain"].notna()].copy()
    py = z.groupby(["ain", "year"]).agg(adu_units=("units", "sum"), lot_class=("lot_class", "first"),
                                        existing=("Units", "first")).reset_index()
    py["existing"] = pd.to_numeric(py["existing"], errors="coerce")
    py["adu_bucket"] = pd.cut(py["adu_units"], [0, 1, 2, 3, 1e9], labels=["1", "2", "3", "4+"]).astype(str)
    py["existing_band"] = pd.cut(py["existing"], [-1, 1, 2, 4, 9, 19, 49, 1e9],
                                 labels=["0-1", "2", "3-4", "5-9", "10-19", "20-49", "50+"]).astype(str)
    dist = (py.groupby(["lot_class", "adu_bucket", "existing_band"]).agg(parcel_years=("ain", "size"), adu_units=("adu_units", "sum"))
            .reset_index().assign(table="LA County ADU parcel-years 2023-2025: ADU units on the parcel-year x existing units"))
    mfpy = py[py["lot_class"].isin(M.LA_MF_CLASSES)]
    b = E.buildings(one.to_frame().T, E.SIZES[E.CENTRAL_SIZE]).iloc[0]
    band_map = {"2": "mf2", "3-4": "mf3_4", "5-9": "mf5_9", "10-19": "mf10_19", "20-49": "mf20_49", "50+": "mf50p"}
    sf3 = py[py["lot_class"].eq("single_family")].shape[0]
    bands_rows = [dict(table="LA County 2023-2025 permits (parcel-years) per 1,000 properties by existing-building band",
                       lot_class="single_family", existing_band="one-unit detached", parcel_years=sf3,
                       properties=float(one["sf_det"]), rate_per_1000_per_year=sf3 / 3 / float(one["sf_det"]) * 1000)]
    for bd, comp in band_map.items():
        n = int((mfpy["existing_band"] == bd).sum())
        bands_rows.append(dict(table=bands_rows[0]["table"], lot_class="multifamily", existing_band=bd, parcel_years=n,
                               properties=float(b[comp]), rate_per_1000_per_year=n / 3 / float(b[comp]) * 1000,
                               share_4plus_adu=float((mfpy.loc[mfpy["existing_band"] == bd, "adu_bucket"] == "4+").mean())
                               if n else np.nan))
    # parcel correction: small multifamily parcels with 2+ buildings (two detached houses, house + duplex)
    # are not ACS 2-unit / 3-4-unit structures; their units sit in one-unit detached. Scale those bands'
    # properties by 1 / (1 - share of ADU parcels with 2+ building lines) and move the implied units out
    # of the single-family count (an upper bound: assumes all are one-unit detached).
    sm = chk.set_index("lot_class")
    mf_n = sum(r_["parcel_years"] for r_ in bands_rows[1:])
    corr_mf, moved = 0.0, 0.0
    for bd, comp, cls in (("2", "mf2", "two_units"), ("3-4", "mf3_4", "three_four_units")):
        sh = float(sm.loc[cls, "share_multi_building"])
        extra = float(b[comp]) * sh / (1 - sh)
        corr_mf += float(b[comp]) + extra
        moved += extra * float(sm.loc[cls, "mean_units"])
    corr_mf += float(b[["mf5_9", "mf10_19", "mf20_49", "mf50p"]].sum())
    sf_corr = float(one["sf_det"]) - moved
    for lab, mfp_, sfp in (("ACS buildings (large sizes)", float(b[list(E.MF)].sum()), float(one["sf_det"])),
                           ("parcel-corrected, multifamily side only", corr_mf, float(one["sf_det"])),
                           ("parcel-corrected, both sides (upper bound)", corr_mf, sf_corr)):
        pp = E.propensity(sf3 / 3, mf_n / 3, sfp, mfp_)
        bands_rows.append(dict(table="LA County 2023-2025 multifamily vs single-family propensity, parcel correction",
                               lot_class=lab, existing_band="all", parcel_years=mf_n, properties=mfp_,
                               rate_per_1000_per_year=pp["rate_mf"], rate_sf=pp["rate_sf"], ratio_mf_to_sf=pp["ratio_mf_to_sf"],
                               sf_properties=sfp))
    mf4 = int((mfpy["adu_bucket"] == "4+").sum())
    pp = E.propensity(sf3 / 3, (mf_n - mf4) / 3, float(one["sf_det"]), float(b[list(E.MF)].sum()))
    bands_rows.append(dict(table="LA County 2023-2025 multifamily vs single-family propensity, parcel correction",
                           lot_class="ACS buildings (large sizes), excluding 4+-ADU parcel-years", existing_band="all",
                           parcel_years=mf_n - mf4, properties=float(b[list(E.MF)].sum()),
                           rate_per_1000_per_year=pp["rate_mf"], rate_sf=pp["rate_sf"], ratio_mf_to_sf=pp["ratio_mf_to_sf"],
                           sf_properties=float(one["sf_det"])))
    chk = pd.concat([chk.assign(table="LA County multifamily ADU parcels: existing units and building lines"), dist,
                     pd.DataFrame(bands_rows)], ignore_index=True)
    return prop, chk


def a2_bucket_table(rows: pd.DataFrame) -> pd.DataFrame:
    """Statewide A2 (study measure) parcel-years by ADU units on the parcel-year: 1, 2, 3, 4+."""
    k = rows[rows["site_basis"].eq("parcel")]
    py = k.groupby(["juris_name", "site", "year"])["units"].sum().reset_index()
    py["adu_bucket"] = pd.cut(py["units"], [0, 1, 2, 3, 1e9], labels=["1", "2", "3", "4+"]).astype(str)
    t = py.groupby(["year", "adu_bucket"]).agg(parcel_years=("site", "size"), adu_units=("units", "sum")).reset_index()
    t["share_of_parcel_years"] = t["parcel_years"] / t.groupby("year")["parcel_years"].transform("sum")
    t["share_of_adu_units"] = t["adu_units"] / t.groupby("year")["adu_units"].transform("sum")
    return t


# ---------------------------------------------------------------------------
# Pooled runs
# ---------------------------------------------------------------------------

def make_data(d, cities_flat, state_factor):
    d2 = dict(d)
    c = d["cities"].copy()
    fl = cities_flat.set_index(["city", "year"])["permits"]
    k = pd.MultiIndex.from_arrays([c["city"], c["year"]])
    c["permits_flat"] = pd.Series(fl.reindex(k).to_numpy(), index=c.index).where(c["units_incl_new_house"].notna())
    d2["cities"] = c
    a = d["annual"].copy()
    a["adu_count"] = a["adu_count"] * a["series"].map(state_factor).fillna(1.0)
    d2["annual"] = a
    return d2


def build_eb(d2, panel, acs, caj, scenario="central", size=None, mf_weight=None, city_measure="permits_flat",
             eligible_den=True, drop=()):
    p = rp.pooled({**d2, "panel": panel}, city_measure=city_measure)
    rows = R.adjust_other_rows(p.rows, vacant_lot=True, minneapolis=False)
    mem = eligible_members(p.members, acs, caj, scenario, size, mf_weight, drop) if eligible_den else p.members
    return pr.Pooled(rows, mem[p.members.columns])


def madison_path_totals(wi, G, Y, fac, ramp, ml, x):
    """Madison: the pooled-level engine addition and the observed Madison-like path addition."""
    H = wi["homes"].to_numpy(float)
    path = np.asarray(RV.MADISON_LIKE_PATH)
    add_ml = (H[ml, None] * np.maximum(path[None, :] - x[ml, None] * G[ml], 0) / 1000).sum()
    add_c = RV.engine_totals(wi.loc[ml], G[ml], Y[ml, 4] * fac, ramp, FLOOR_EFF)[0].sum()
    return float(add_c), float(add_ml)


FLOOR_EFF = FLOOR


def wi_run(p, name, d2, G, ml_ids, sens=True, ca_only=None):
    r, by, f, Y = RV.wi_results(p, name, d2, G, FLOOR_EFF, None, ml_ids, sens=sens)
    wi = d2["wi"]
    ml = wi["area_id"].isin(ml_ids).to_numpy()
    x = wi["x_rate"].to_numpy(float)
    fac80 = r["factor80"]
    for pth, fac in (("lower", 1 / fac80), ("central", 1.0), ("upper_tau90", fac80)):
        ramp = np.array([float(v) for v in r[f"ramp_{pth}"].split("|")])
        a_c, a_ml = madison_path_totals(wi, G, Y, fac, ramp, ml, x)
        r[f"engine_{pth}_madison_path"] = r[f"engine_{pth}"] - a_c + a_ml
        r[f"madison_pooled_{pth}"] = a_c
    r["madison_observed_path"] = a_ml
    if ca_only is not None:
        r["sens_ca_only_regression"] = ca_only
    return r, by, f, Y


def ca_only_regression(panel_adj, ca_ds, caj, wiy, wi, G, scenario="central"):
    """California-only market regression refitted with flattened permits per eligible property."""
    s = cr.panel_series(panel_adj)
    po = cr.plateau_outcome(s)
    d = ca_ds.set_index("census_geoid").copy()
    d["adu"] = po["adu"].reindex(d.index).to_numpy()
    c = caj.set_index("census_geoid")
    ratio = E.scenario_eligible(c, "CA", scenario) / c["sf_det"].where(c["sf_det"] > 0)
    d["homes"] = d["homes"] * ratio.reindex(d.index).fillna(1.0).to_numpy()
    d["exposure"] = d["n_years"] * d["homes"] / 1000
    d = d.dropna(subset=["adu"]).reset_index()
    f = cr.fit(d, cr.SPEC_BY_NAME["group_value_hinge_size"])
    w = wi[["area_id"]].merge(wiy.rename(columns={"ca_group": "group", "median_value": "value"})[
        ["area_id", "group", "value", "homes", "y_central"]], on="area_id", how="left")
    y = f.predict_rate(w)
    add, _ = RV.engine_totals(wi, G, y, RV.CA_ONLY_RAMP, FLOOR_EFF)
    return float(add.sum())


def g3f2(p, label):
    err, loso_rows = {}, []
    for name in CONFIGS:
        lo = pr.loso_ts(p, RV.tspec(name), clusters=STATES)
        lo = lo[lo["series"].isin(pr.STATE_CODING)].assign(run=label, config=name)
        loso_rows.append(lo)
        err[name] = lo.set_index("held_out")["log_error"].reindex(list(STATES))
    Em = pd.DataFrame(err)
    rmsd = {n: R.rms(Em[n]) for n in CONFIGS}
    best_c = min((n for n in CONFIGS if n.startswith("C_")), key=rmsd.get)
    abc = ["A_ca_in_common_level", "B_ca_out_of_common_level", best_c]
    winner = min(abc, key=rmsd.get)
    boot = R.paired_bootstrap_wins(Em[abc])
    dr = {}
    for s0 in STATES:
        ps = pr.subset(p, p.rows["cluster"].ne(s0).to_numpy())
        others = tuple(s for s in STATES if s != s0)
        for name in abc:
            lo = pr.loso_ts(ps, RV.tspec(name), clusters=others)
            dr[(s0, name)] = R.rms(lo[lo["series"].isin(pr.STATE_CODING)]["log_error"])
    win_drop = pd.Series({s0: min(abc, key=lambda n: dr[(s0, n)]) for s0 in STATES})
    rows = []
    for n in CONFIGS:
        rows.append(dict(run=label, config=n, label=RV.CONFIG_LABELS[n], rms_log_error=rmsd[n],
                         mean_log_error=float(Em[n].mean()), **{f"log_error_{s}": float(Em.loc[s, n]) for s in STATES},
                         in_abc=n in abc, winner=n == winner,
                         bootstrap_win_share_abc=float(boot[n]) if n in abc else np.nan,
                         drop_one_wins_of_7=int((win_drop == n).sum()) if n in abc else np.nan,
                         drop_one_rms_min=min(dr[(s, n)] for s in STATES) if n in abc else np.nan,
                         drop_one_rms_max=max(dr[(s, n)] for s in STATES) if n in abc else np.nan,
                         drop_one_winner_by_state="|".join(f"{s}:{win_drop[s][0]}" for s in STATES) if n == winner else ""))
    return rows, pd.concat(loso_rows, ignore_index=True), winner


def main():
    global FLOOR_EFF
    log = print
    od = processed_dir("eligible_basis")
    summary = {}
    mlp = pd.read_csv(REFERENCE / "madison_like_median_path.csv")
    RV.MADISON_LIKE_PATH = mlp[mlp["group"].eq("WA+OR Madison-like (main)")].sort_values("year_since_law")["median_rate"].to_numpy()
    d = rp.load()
    wi0, growth = d["wi"], d["growth"]
    G = RV.growth_matrix(wi0, growth)
    mlw = RV.wi_madison_like(d)
    ml_ids = set("|".join(mlw.loc[mlw["madison_like"], "area_ids"]).split("|"))

    # ---------------- denominators ----------------
    acs = read_b25024({"53", "41", "44", "25", "23", "49", "50", "48", "08", "27", "55", "06"})
    caj = ca_juris_components()
    p_base = rp.pooled(d)
    den_rows = []
    for scen in E.SCENARIOS:
        mem = eligible_members(p_base.members, acs, caj, scen)
        mem["key"] = mem["group_id"].map(group_key)
        for k, g in mem.groupby("key"):
            den_rows.append(dict(key=k, scenario=scen, size_set=E.SCENARIOS[scen][1], one_unit_detached=g["sf_homes"].sum(),
                                 eligible_properties=g["homes"].sum(), ratio_to_one_unit_detached=g["homes"].sum() / g["sf_homes"].sum()))
    for sz in E.SIZES:
        mem = eligible_members(p_base.members, acs, caj, "central", size=sz)
        mem["key"] = mem["group_id"].map(group_key)
        for k, g in mem.groupby("key"):
            den_rows.append(dict(key=k, scenario=f"central_scope_size_{sz}", size_set=sz, one_unit_detached=g["sf_homes"].sum(),
                                 eligible_properties=g["homes"].sum(), ratio_to_one_unit_detached=g["homes"].sum() / g["sf_homes"].sum()))
    den = pd.DataFrame(den_rows)
    den["law_basis"] = den["key"].map(lambda k: E.LAW_SCOPE.get(k, ("",) * 5)[3])
    den["legal_status"] = den["key"].map(lambda k: E.LAW_SCOPE.get(k, ("",) * 5)[4])
    den["central_scope"] = den["key"].map(lambda k: json.dumps(E.LAW_SCOPE[k][1]) if k in E.LAW_SCOPE else "")
    # California statewide components (all jurisdictions) and the multifamily-property range
    ca_tot = caj[list(E.COMPONENTS)].sum()
    mfr = {sz: float(E.mf_properties(ca_tot.to_frame().T, E.SIZES[sz]).iloc[0]) for sz in E.SIZES}
    summary["ca_statewide_components_units"] = ca_tot.to_dict()
    summary["ca_mf_properties_by_size"] = mfr
    for sz, v in mfr.items():
        den_rows.append(dict(key="CA statewide (all jurisdictions): multifamily properties only", scenario=f"size_{sz}",
                             size_set=sz, one_unit_detached=float(ca_tot["sf_det"]), eligible_properties=v,
                             ratio_to_one_unit_detached=v / float(ca_tot["sf_det"])))
    den = pd.DataFrame(den_rows).merge(den[["key", "scenario", "law_basis", "legal_status", "central_scope"]],
                                       on=["key", "scenario"], how="left")
    den.round(4).to_csv(REFERENCE / "eligible_basis_denominators.csv", index=False)
    log(den[["key", "scenario", "one_unit_detached", "eligible_properties", "ratio_to_one_unit_detached"]].round(3).to_string())

    # ---------------- numerators ----------------
    rows = a2_rows_with_site()
    num = []
    for y, g in rows.groupby("year"):
        num.append(dict(source="CA HCD A2, study main measure (all jurisdictions)", year=int(y), units=float(g["units"].sum()),
                        rows=len(g), permits=float(g.drop_duplicates(["juris_name", "site"]).shape[0]),
                        share_site_apn=float((g["site_basis"] == "parcel").mean()),
                        share_site_address=float((g["site_basis"] == "address").mean())))
    ev = E.capped_events(rows)
    for y, g in ev.groupby("year"):
        num.append(dict(source="CA HCD A2, study main measure, permits capped at 2 parcel-years per parcel", year=int(y),
                        units=np.nan, rows=np.nan, permits=float(g["keep"].sum())))
    num += a2_owner_check()
    cf, cbasis = city_flat(log)
    for r_ in cf.itertuples():
        num.append(dict(source=f"city {r_.city} (excl. legalizations; incl. with new house)", year=int(r_.year),
                        units=float(r_.units), rows=int(r_.rows), permits=float(r_.permits)))
    wf = wi_flat()
    num += wf.to_dict("records")
    num = pd.DataFrame(num)
    num["units_per_permit"] = num["units"] / num["permits"]
    num.round(4).to_csv(REFERENCE / "eligible_basis_numerators.csv", index=False)

    # state-series factors (permits per unit): WA from Seattle (2 per lot allowed), OR from Portland,
    # others 1 (one ADU per lot under the law)
    def ratio(city, years):
        z = cf[(cf["city"] == city) & cf["year"].isin(years)]
        return float(z["permits"].sum() / z["units"].sum())
    state_factor = {"WA_inc_exSeattle": ratio("seattle", range(2021, 2025)), "OR_panel32_exPortland": ratio("portland", range(2019, 2023))}
    wz = wf[wf["year"].between(2022, 2025)]
    f_wi = float(wz["permits"].sum() / wz["units"].sum())
    summary["state_factor_permits_per_unit"] = {**state_factor, "others": 1.0}
    summary["wi_factor_permits_per_unit"] = f_wi
    summary["wi_flat_counts_2022_2025"] = {"units": float(wz["units"].sum()), "permits": float(wz["permits"].sum())}
    log("state factors", state_factor, "WI", f_wi)

    # ---------------- Wisconsin flattened ----------------
    d2 = make_data(d, cf, state_factor)
    wi = wi0.copy()
    wi["x_rate"] = wi["x_rate"] * f_wi
    d2["wi"] = wi
    d2["baseline"] = d["baseline"] * f_wi
    FLOOR_EFF = FLOOR * f_wi

    # ---------------- California panels ----------------
    xw = pd.read_parquet(PROCESSED / "comparison_ca/ca_jurisdiction_crosswalk.parquet")
    panels = {}
    for lab, cap in (("permits", False), ("permits_cap2", True)):
        rem = ca_removed(rows, cap)
        panels[lab] = R.adjust_ca_panel(d["panel"], R.to_geoid(rem[["juris_name", "year", "adu_units", "removed"]], xw),
                                        R.statewide_factor(rem[["juris_name", "year", "adu_units", "removed"]]))

    # ---------------- California 2023-2025 rates under each basis ----------------
    groups = pd.read_csv(PROCESSED / "comparison_ca/study/groups_by_jurisdiction.csv")
    g3 = groups[(groups["spec"] == "main") & (groups["wave"] == 3) & groups["group"].isin(["restrictive", "middle", "permissive"])]
    nonhold = set(d["panel"].loc[~d["panel"]["in_holdout"], "census_geoid"]) & set(g3["census_geoid"])
    plateau = pd.read_csv(REFERENCE / "ca_mf_lot_adu_share_plateau.csv")
    pl = plateau[plateau["set"].str.startswith("all_grouped_non_holdout")].set_index("variant")
    caj_i = caj.set_index("census_geoid")

    def ca_ratio(scope, sizes):
        return E.eligible(caj_i, scope, sizes) / caj_i["sf_det"].where(caj_i["sf_det"] > 0)
    rates = []
    for v, lab in (("as_reported", "as used (study main measure)"), ("cap_mf_lower", "cap + A2 (POOLED_REVISION option ii)"),
                   ("cap_mf_central", "cap + LA-calibrated (option iii)")):
        rates.append(dict(basis=lab, numerator="ADU units", denominator="one-unit detached homes x years",
                          numerator_value=pl.loc[v, "adu_numerator"], denominator_value=pl.loc[v, "home_years_denominator"],
                          rate_per_1000=pl.loc[v, "rate_per_1000"]))
    for plab, pan in panels.items():
        q = pan[pan["census_geoid"].isin(nonhold) & pan["year"].between(2023, 2025)].dropna(subset=["adu_main"])
        numv = float(q["adu_main"].sum())
        rates.append(dict(basis=f"{plab} per one-unit detached home", numerator="flattened permits", denominator="one-unit detached homes x years",
                          numerator_value=numv, denominator_value=float(q["sf_detached"].sum()), rate_per_1000=numv / q["sf_detached"].sum() * 1000))
        for scen in ("low", "central", "high"):
            i_, sz_ = E.SCENARIOS[scen]
            den_v = float((q["sf_detached"] * q["census_geoid"].map(ca_ratio(E.LAW_SCOPE["CA"][i_], E.SIZES[sz_])).fillna(1)).sum())
            rates.append(dict(basis=f"{plab} per eligible property ({scen} denominator)", numerator="flattened permits",
                              denominator=f"eligible properties x years ({scen})", numerator_value=numv, denominator_value=den_v,
                              rate_per_1000=numv / den_v * 1000))
        for sz in E.SIZES:
            den_v = float((q["sf_detached"] * q["census_geoid"].map(ca_ratio(E.LAW_SCOPE["CA"][1], E.SIZES[sz])).fillna(1)).sum())
            rates.append(dict(basis=f"{plab} per eligible property (size set {sz})", numerator="flattened permits",
                              denominator=f"eligible properties x years (central scope, {sz} buildings)", numerator_value=numv,
                              denominator_value=den_v, rate_per_1000=numv / den_v * 1000))

    # ---------------- equal propensity (LA County) ----------------
    la_units = acs[(acs["sumlevel"] == "050") & (acs["geoid"] == "06037")].iloc[0][list(E.COMPONENTS)].astype(float)
    prop, pchk = la_propensity(rows, la_units)
    prop.round(4).to_csv(REFERENCE / "eligible_basis_propensity_la.csv", index=False)
    pchk.round(4).to_csv(REFERENCE / "eligible_basis_parcel_check.csv", index=False)
    a2_bucket_table(rows).round(4).to_csv(REFERENCE / "eligible_basis_a2_adu_per_parcel.csv", index=False)
    pz = prop[prop["year"].between(2023, 2025)]
    rho = {sz: float((pz["mf_lot_permits"].sum() / pz[f"mf_properties_{sz}"].iloc[0]) /
                     (pz["sf_lot_permits"].sum() / pz["sf_detached_homes"].iloc[0])) for sz in E.SIZES}
    summary["la_rho_2023_2025"] = rho
    log(prop[["year", "permits", "sf_lot_permits", "mf_lot_permits", "rate_sf", f"rate_mf_{E.CENTRAL_SIZE}",
              f"ratio_mf_to_sf_{E.CENTRAL_SIZE}"]].round(3).to_string())
    # statewide: what the blended (eligible-basis) rate implies for single-family lots
    s_ca = float(ca_tot["sf_det"] + ca_tot["sf_att"])
    m_ca = mfr[E.CENTRAL_SIZE]
    blended = [r_ for r_ in rates if r_["basis"] == "permits per eligible property (central denominator)"][0]["rate_per_1000"]
    r_c = rho[E.CENTRAL_SIZE]
    sf_impl = E.sf_rate_from_blended(blended, s_ca, m_ca, r_c)
    summary["ca_propensity"] = dict(blended=blended, sf_properties=s_ca, mf_properties=m_ca, rho=r_c, sf_lot_rate_implied=sf_impl,
                                    blended_over_sf=blended / sf_impl)
    corr = pchk[pchk["table"].fillna("").str.contains("parcel correction")]
    summary["ca_propensity"]["sf_lot_rate_implied_by_rho"] = {
        r_.lot_class: dict(rho=float(r_.ratio_mf_to_sf), sf_lot_rate=E.sf_rate_from_blended(blended, s_ca, m_ca, float(r_.ratio_mf_to_sf)))
        for r_ in corr.itertuples()}
    rates.append(dict(basis="permits per eligible property, single-family-lot rate implied by LA County propensity ratio",
                      numerator="flattened permits", denominator="eligible properties (SF lots only)", numerator_value=np.nan,
                      denominator_value=np.nan, rate_per_1000=sf_impl))
    pd.DataFrame(rates).round(4).to_csv(REFERENCE / "eligible_basis_ca_rates.csv", index=False)
    log(pd.DataFrame(rates)[["basis", "numerator_value", "denominator_value", "rate_per_1000"]].round(3).to_string())

    # ---------------- G3F-2 on the eligible basis ----------------
    p_main = build_eb(d2, panels["permits"], acs, caj)
    p_cap = build_eb(d2, panels["permits_cap2"], acs, caj)
    p_num = build_eb(d2, panels["permits"], acs, caj, eligible_den=False)
    p_noatt = build_eb(d2, panels["permits"], acs, caj, drop=("sf_att",))
    g_rows, lo_rows = [], []
    for lab, p in (("eligible_permits", p_main), ("eligible_permits_cap2", p_cap),
                   ("numerator_only_permits_per_sf_home", p_num), ("eligible_permits_no_one_unit_attached", p_noatt)):
        gr, lo, win = g3f2(p, lab)
        g_rows += gr
        lo_rows.append(lo)
        summary.setdefault("g3f2_winner", {})[lab] = win
        log(lab, win, {r_["config"]: round(r_["rms_log_error"], 3) for r_ in gr})
    pd.DataFrame(g_rows).round(4).to_csv(REFERENCE / "eligible_basis_g3f2.csv", index=False)
    pd.concat(lo_rows, ignore_index=True).round(4).to_csv(REFERENCE / "eligible_basis_loso.csv", index=False)

    # ---------------- Wisconsin runs ----------------
    ca_ds = pd.read_parquet(PROCESSED / "ca_regression/ca_dataset.parquet")
    wiy = pd.read_csv(REFERENCE / "wi_y_by_area.csv")
    caonly = ca_only_regression(panels["permits"], ca_ds, caj, wiy, wi, G)
    runs = {   # label -> (pooled data, config, full sensitivities)
        "main: eligible basis, permits, configuration A": (p_main, "A_ca_in_common_level", True),
        "with cap (2 parcel-years per parcel)": (p_cap, "A_ca_in_common_level", False),
        "configuration B (California out of the common level)": (p_main, "B_ca_out_of_common_level", False),
        "denominator low (narrow law reading, very large buildings)": (build_eb(d2, panels["permits"], acs, caj, "low"), "A_ca_in_common_level", False),
        "denominator high (broad law reading, small buildings, mobile homes)": (build_eb(d2, panels["permits"], acs, caj, "high"), "A_ca_in_common_level", False),
        "propensity-adjusted (CA multifamily properties x LA ratio)": (build_eb(d2, panels["permits"], acs, caj, mf_weight={"CA": r_c}), "A_ca_in_common_level", False),
        "numerator only: permits per one-unit detached home": (p_num, "A_ca_in_common_level", False),
        "denominator without one-unit attached homes": (p_noatt, "A_ca_in_common_level", False),
    }
    for sz in E.SIZES:
        if sz != E.CENTRAL_SIZE:
            runs[f"size set {sz} (central law scope)"] = (build_eb(d2, panels["permits"], acs, caj, size=sz), "A_ca_in_common_level", False)
    wi_rows, st2 = [], []
    for lab, (p, cfg, sens) in runs.items():
        r_, _, f, _ = wi_run(p, cfg, d2, G, ml_ids, sens=sens, ca_only=caonly if sens else None)
        r_["run"] = lab
        wi_rows.append(r_)
        if sens:
            lawc = f.beta[f.within_names.index("law")]
            for c, a in f.alpha.items():
                st2.append(dict(run=lab, cluster=c, in_stage2=c in set(f.stage2["cluster"]),
                                level_with_law_k4=float(np.exp(a + lawc)), alpha=float(a)))
            pts = pr.adoption_points(p.rows, p.row_homes())
            c = pr.adoption_curve(pts)
            app = pr.apply_curve(c["median_rate"].to_numpy(), d2["baseline"])
            r_["adoption_line_rates"] = "|".join(f"{v:.4f}" for v in c["median_rate"])
            r_["adoption_line_additional"] = float(app["additional"].sum())
        log(lab, {k: round(r_[k]) for k in ("engine_lower_madison_path", "engine_central_madison_path",
                                            "engine_upper_tau90_madison_path", "engine_central")})
    wdf = pd.DataFrame(wi_rows)
    first = ["run", "config"]
    wdf[first + [c for c in wdf.columns if c not in first]].round(4).to_csv(REFERENCE / "eligible_basis_wi.csv", index=False)
    pd.DataFrame(st2).round(4).to_csv(REFERENCE / "eligible_basis_stage2_levels.csv", index=False)
    summary["floor_effective"] = FLOOR_EFF
    summary["wi_main"] = {k: (float(v) if isinstance(v, (int, float, np.floating)) else v) for k, v in wi_rows[0].items()}
    summary["pooled_revision_reference"] = POOLED_REVISION
    (od / "summary.json").write_text(json.dumps(summary, indent=2, default=float))


if __name__ == "__main__":
    main()
