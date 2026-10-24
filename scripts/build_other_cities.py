"""Build out-of-state ADU permit series and before/after rates (Gate 3, owner request 2026-10-24).

    uv run python scripts/build_other_cities.py --fetch   # download raw permit data first
    uv run python scripts/build_other_cities.py           # rebuild from data/raw caches

Raw inputs (git-ignored, each folder has _downloads.json with URL, query, date, bytes, SHA-256):
    data/raw/seattle_permits_socrata/   SDCI Building Permits (data.seattle.gov 76t5-zqzr), ADU subset
    data/raw/seattle_opcd_adu_report/   OPCD 2024 ADU Annual Report PDF (official)
    data/raw/portland_res_permits/      BDS Residential Building Permits (PortlandMaps layer 89)
    data/raw/austin_permits_socrata/    Issued Construction Permits (data.austintexas.gov 3syk-w9eu)
    data/raw/denver_rescon_permits/     Residential Construction Permits (Denver ArcGIS layer 316)
    data/raw/minneapolis_ccs_permits/   CCS Permits (Minneapolis ArcGIS), ADU-text subset
    data/raw/census_acs5_2024_tbsf/acsdt5y2024-b25024.dat        (read only)
    data/raw/census_acs5_2024_tbsf_market/acsdt5y2024-b25077/b25064/b19013.dat (read only)
Outputs (aggregates only): reference/other_cities_*.csv
No personal fields are requested from the APIs (no applicant/contractor names, phone or mailing
addresses). Permit site addresses stay in data/raw only.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from missing_middleware.comparison import other_cities as oc  # noqa: E402

RAW = ROOT / "data" / "raw"
REF = ROOT / "reference"
YEARS = range(2005, 2026)

SEA = "https://data.seattle.gov/resource/76t5-zqzr.csv"
AUS = "https://data.austintexas.gov/resource/3syk-w9eu.csv"
PDX = "https://gis-pdx.opendata.arcgis.com/api/download/v1/items/02d99db039e0428da88262bff513056a/csv?layers=89"
DEN = "https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services/ODC_DEV_RESIDENTIALCONSTPERMIT_P/FeatureServer/316"
MSP = "https://services.arcgis.com/afSMGVsC7QlRK1kZ/arcgis/rest/services/CCS_Permits/FeatureServer/0"

KW = ["%ADU%", "%ACCESSORY DWELLING%", "%BACKYARD COTTAGE%", "%MOTHER%IN%LAW%",
      "%SECONDARY APARTMENT%", "%GARAGE APARTMENT%", "%GUEST HOUSE%"]


def soql_kw(field: str) -> str:
    return "(" + " OR ".join(f"upper({field}) like '{k}'" for k in KW) + ")"


def fetch(log=print) -> None:
    oc.fetch_socrata_csv(
        RAW / "seattle_permits_socrata", "building_permits_adu_subset.csv", SEA,
        select=("permitnum,permitclass,permitclassmapped,permittypemapped,permittypedesc,description,"
                "housingunits,housingunitsremoved,housingunitsadded,applieddate,issueddate,statuscurrent,"
                "zoning,dwellingunittype,standardplan,housingcategory,originaladdress1"),
        where=f"permittypemapped='Building' AND (dwellingunittype like '%Accessory Dwelling%' OR {soql_kw('description')})",
        license_="Public Domain (data.seattle.gov)", log=log)
    oc.fetch_socrata_csv(
        RAW / "seattle_permits_socrata", "new_single_family_permits.csv", SEA,
        select="permitnum,originaladdress1,issueddate,dwellingunittype",
        where=("permittypemapped='Building' AND permittypedesc='New' AND issueddate >= '2005-01-01' AND "
               "(dwellingunittype like '%Detached Single-Family%' OR dwellingunittype like '%Townhouse%' "
               "OR dwellingunittype like '%Rowhouse%')"),
        license_="Public Domain (data.seattle.gov)", log=log)
    oc.fetch_url(RAW / "seattle_opcd_adu_report", "OPCD-ADUAnnualReport2024.pdf", oc.SEATTLE_OPCD_URL,
                 license_="City of Seattle public document", log=log)
    oc.fetch_url(RAW / "portland_res_permits", "residential_building_permits.csv", PDX,
                 license_="City of Portland open data (PortlandMaps); no license stated on item", log=log)
    cols = ("permittype,permit_number,permit_class,work_class,description,issue_date,calendar_year_issued,"
            "status_current,housing_units,tcad_id,jurisdiction,permit_location")
    text_classes = ",".join(f"'{c}'" for c in oc.AUSTIN_TEXT_CLASSES)
    oc.fetch_socrata_csv(
        RAW / "austin_permits_socrata", "bp_adu_candidates.csv", AUS, select=cols,
        where=(f"permittype='BP' AND (permit_class='{oc.AUSTIN_ADU_CLASS}' OR "
               f"(permit_class in ({text_classes}) AND {soql_kw('description')}))"),
        license_="Public Domain U.S. Government (data.austintexas.gov)", log=log)
    oc.fetch_socrata_csv(
        RAW / "austin_permits_socrata", "bp_new_houses_2005plus.csv", AUS,
        select="permit_number,tcad_id,issue_date",
        where="permittype='BP' AND permit_class='R- 101 Single Family Houses' AND issue_date >= '2005-01-01'",
        license_="Public Domain U.S. Government (data.austintexas.gov)", log=log)
    oc.fetch_arcgis(
        RAW / "denver_rescon_permits", "residential_construction_permits.csv", DEN, where="1=1",
        fields=("OBJECTID,DATE_ISSUED,PERMIT_NUM,ADDRESS,CLASS,UNITS,VALUATION,FINAL_DATE,CANCEL,DATE_RECEIVED,"
                "CO_REQUIRED,ADDRESS_UNIT,SCHEDNUM,STAT_CODE_1,STAT_CODE_2,STAT_CODE_3,NEIGHBORHOOD"),
        license_="City and County of Denver open data, use constraints as stated (no warranty)", log=log)
    oc.fetch_arcgis(
        RAW / "minneapolis_ccs_permits", "ccs_permits_res_adu_text.csv", MSP,
        where="permitType='Res' AND (UPPER(comments) LIKE '%ADU%' OR UPPER(comments) LIKE '%ACCESSORY DWELLING%')",
        fields=("OBJECTID,APN,permitNumber,dwellingUnitsNew,dwellingUnitsEliminated,permitType,occupancyType,"
                "workType,status,milestone,issueDate,completeDate,comments,Neighborhoods_Desc"),
        license_="City of Minneapolis open data", log=log)


def load_permits() -> tuple[pd.DataFrame, pd.DataFrame]:
    sea = pd.read_csv(RAW / "seattle_permits_socrata" / "building_permits_adu_subset.csv", dtype=str)
    sea_houses = pd.read_csv(RAW / "seattle_permits_socrata" / "new_single_family_permits.csv", dtype=str)
    # a permit listing ADU types is itself excluded from the house list
    sea_houses = sea_houses[~sea_houses["dwellingunittype"].fillna("").str.contains("Accessory Dwelling")]
    pdx = pd.read_csv(RAW / "portland_res_permits" / "residential_building_permits.csv", dtype=str, encoding="utf-8-sig")
    aus = pd.read_csv(RAW / "austin_permits_socrata" / "bp_adu_candidates.csv", dtype=str)
    houses = pd.read_csv(RAW / "austin_permits_socrata" / "bp_new_houses_2005plus.csv", dtype=str)
    den = pd.read_csv(RAW / "denver_rescon_permits" / "residential_construction_permits.csv", dtype=str)
    den["DATE_ISSUED"] = pd.to_numeric(den["DATE_ISSUED"], errors="coerce")
    msp = pd.read_csv(RAW / "minneapolis_ccs_permits" / "ccs_permits_res_adu_text.csv", dtype=str)
    msp["issueDate"] = pd.to_numeric(msp["issueDate"], errors="coerce")
    main = pd.concat([oc.classify_seattle(sea, sea_houses), oc.classify_portland(pdx), oc.classify_austin(aus, houses),
                      oc.classify_denver(den), oc.classify_minneapolis(msp)], ignore_index=True)
    aus_text = oc.classify_austin(aus, houses, include_text=True)
    return main, aus_text


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    a = ap.parse_args()
    if a.fetch:
        fetch()
    permits, aus_text = load_permits()

    # ---- annual series ---------------------------------------------------
    series = oc.annual_series(permits, YEARS)
    series["units_incl_new_house"] = series["adu_units"] + series["excluded_with_new_house"]
    # data-quality status per city-year
    def status(r):
        c, y = r.city, r.year
        if c == "austin" and y >= oc.AUSTIN_HOME_BREAK:
            return "not_comparable_category_retired"
        if c == "denver" and y < 2016:
            return "incomplete_pre_accela"
        if c == "minneapolis" and y < 2017:
            return "missing_before_data_start"
        if c == "seattle" and y >= 2025:
            return "incomplete_field_coverage"
        return "observed"
    series["status"] = series.apply(status, axis=1)
    counts = [c for c in series.columns if c not in ("city", "year", "status")]
    series[counts] = series[counts].astype("Float64")
    series.loc[series["status"] != "observed", counts] = pd.NA  # missing is never zero
    opcd = oc.seattle_opcd_table()
    series = series.merge(opcd[["year", "total_units"]].assign(city="seattle").rename(columns={"total_units": "published_units"}),
                          on=["city", "year"], how="left")
    at = oc.annual_series(aus_text, YEARS)[["city", "year", "adu_units"]].rename(columns={"adu_units": "units_incl_text_matches"})
    series = series.merge(at, on=["city", "year"], how="left")
    series.loc[series["status"] != "observed", "units_incl_text_matches"] = pd.NA

    # ---- ACS ---------------------------------------------------------------
    mkt = RAW / "census_acs5_2024_tbsf_market"
    acs = oc.acs_places(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25024.dat",
                        {t: mkt / f"acsdt5y2024-{t}.dat" for t in ("b25077", "b25064", "b19013")})
    homes = dict(zip(acs.city, acs.homes))

    # ---- period rates ------------------------------------------------------
    rates = [oc.period_rates(series, homes, measure="adu_units")]
    rates.append(oc.period_rates(series, homes, measure="units_incl_new_house"))
    rates.append(oc.period_rates(series, homes, [p for p in oc.PERIODS if p.city == "seattle"], measure="published_units"))
    rates.append(oc.period_rates(series, homes, [p for p in oc.PERIODS if p.city == "austin"], measure="units_incl_text_matches"))
    rates = pd.concat(rates, ignore_index=True)

    # ---- regression / validation candidate points -----------------------------
    pts = []
    for city in ["seattle", "portland", "austin", "denver", "minneapolis"]:
        s = series[series.city == city].set_index("year")
        def win(y0, y1, col="adu_units"):
            v = s.loc[y0:y1, col].dropna()
            return float(v.sum()), len(v)
        pre_u, pre_n = win(*oc.PRE_WAVE3)
        pl_u, pl_n = win(*oc.PLATEAU)
        pre_rate = 1000 * pre_u / (homes[city] * pre_n) if pre_n else float("nan")
        pl_rate = 1000 * pl_u / (homes[city] * pl_n) if pl_n else float("nan")
        grp = ("active" if pre_n and pre_rate >= 1.038 and pre_u >= 3 else
               "restrictive" if pre_n and pre_u == 0 else "middle" if pre_n else "unknown")
        r = acs[acs.city == city].iloc[0]
        pts.append({"city": city, "place": r.place, "geoid": r.geoid, "homes": r.homes,
                    "pre_window": f"{oc.PRE_WAVE3[0]}-{oc.PRE_WAVE3[1]}", "pre_years_observed": pre_n,
                    "pre_units": pre_u, "pre_rate": pre_rate, "ca_wave3_group_rule": grp,
                    "plateau_window": f"{oc.PLATEAU[0]}-{oc.PLATEAU[1]}", "plateau_years_observed": pl_n,
                    "plateau_units": pl_u, "plateau_exposure_thousand_home_years": r.homes * pl_n / 1000,
                    "plateau_rate": pl_rate, "value": r.value, "rent": r.rent, "income": r.income})
    pts = pd.DataFrame(pts)
    pts["suggested_use"] = pts.city.map(lambda c: oc.POINT_SUITABILITY[c][0])
    pts["data_quality"] = pts.city.map(lambda c: oc.POINT_SUITABILITY[c][1])
    pts["caveat"] = pts.city.map(lambda c: oc.POINT_SUITABILITY[c][2])
    pts["method"] = pts.city.map(oc.METHODS)

    # ---- cross-checks against published figures -------------------------------
    sea = series[series.city == "seattle"].set_index("year")
    chk = []
    for y in range(2010, 2025):
        chk.append({"city": "seattle", "year": y, "published": int(opcd.set_index("year").total_units[y]),
                    "published_source": "OPCD 2024 ADU Annual Report Exh. 10 (units, incl. with new house)",
                    "ours": sea.units_incl_new_house[y], "ours_measure": "open data ADU units incl. with new house"})
    pdx = series[series.city == "portland"].set_index("year")
    for y, v, src in [(2016, 615, "Ord. 189050 findings (BPS): ADU permits issued"), (2010, 86, "Ord. 189050 findings (BPS)")]:
        chk.append({"city": "portland", "year": y, "published": v, "published_source": src,
                    "ours": pdx.units_incl_new_house[y], "ours_measure": "IS_ADU permits incl. with new house"})
    den = series[series.city == "denver"].set_index("year")
    chk.append({"city": "denver", "year": "2018-2024 (to May)", "published": 389,
                "published_source": "Denverite May 2024 (secondary, city data): ADU construction permits since 2018",
                "ours": den.loc[2018:2023, "units_incl_new_house"].sum(), "ours_measure": "code 026 permits 2018-2023 (full years only)"})
    chk = pd.DataFrame(chk)

    # ---- write ---------------------------------------------------------------
    series.to_csv(REF / "other_cities_annual.csv", index=False, float_format="%.0f")
    rates.to_csv(REF / "other_cities_period_rates.csv", index=False, float_format="%.4f")
    acs.to_csv(REF / "other_cities_acs.csv", index=False, float_format="%.0f")
    oc.reforms_table().to_csv(REF / "other_cities_reforms.csv", index=False)
    opcd.to_csv(REF / "other_cities_seattle_opcd.csv", index=False)
    pts.to_csv(REF / "other_cities_points.csv", index=False, float_format="%.4f")
    chk.to_csv(REF / "other_cities_crosscheck.csv", index=False)
    with pd.option_context("display.width", 250, "display.max_columns", 30, "display.max_rows", 200):
        print(series.to_string())
        print(rates.to_string())
        print(acs.to_string())
        print(pts.to_string())
        print(chk.to_string())


if __name__ == "__main__":
    main()
