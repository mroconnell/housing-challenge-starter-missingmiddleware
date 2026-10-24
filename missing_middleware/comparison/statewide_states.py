"""States with statewide ADU laws: law dates and post-law ADU permit data (Gate 3 add-on).

Owner question (2026-10-24): do any of the 18 states with statewide ADU laws in the
Mercatus 2025 taxonomy (Hamilton and Peterson, "A Taxonomy of State Accessory Dwelling
Unit Laws 2025") have ADU permit data for 1-5 years after the law took effect, so the
statewide-law ("industry formation") effect assumed for Wisconsin (AQ-024, AQ-027,
AQ-034) can be checked outside California?

This module holds, as plain data with a source and status on every row:
  * ``STATES``  - the 18 states, Mercatus class (10 strong / 8 weaker), key laws,
    effective and local-compliance dates, provisions, data source and years covered;
  * ``SERIES``  - annual ADU counts transcribed or extracted from official sources (or
    the best proxy), each with its geography, unit definition and denominator geography;
  * ``PERIODS`` - before / after windows for descriptive rates;
and pure functions that turn ACS 2020-2024 5-year B25024 / B25077 / B25064 rows into
rates per 1,000 one-unit detached homes per year and a transparent usefulness ranking.

Everything is descriptive. A rate that rose after a state law is *associated with* the
law; there is no comparison state and markets, rates and costs changed at the same time.
Counts here are counted at permit issuance unless the series says otherwise. Missing is
never zero: years a source does not cover are absent, not 0.
"""
from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from missing_middleware.comparison.other_cities import poisson_interval

ACCESSED = "2026-10-24"
MERCATUS_URL = ("https://www.mercatus.org/research/policy-briefs/"
                "taxonomy-state-accessory-dwelling-unit-laws-2025")
# Co-author's page naming the ten strong states (verified 2026-10-24).
PETERSON_URL = "https://accessorydwellings.org/2025/08/07/strong-statewide-adu-reform-matrix/"

STRONG = ("AZ", "AR", "CA", "CO", "IA", "ME", "MA", "MT", "OR", "WA")
WEAKER = ("CT", "HI", "MD", "NV", "NH", "RI", "UT", "VT")

STATE_FIPS = {"AZ": "04", "AR": "05", "CA": "06", "CO": "08", "CT": "09", "HI": "15", "IA": "19",
              "ME": "23", "MD": "24", "MA": "25", "MT": "30", "NV": "32", "NH": "33", "OR": "41",
              "RI": "44", "UT": "49", "VT": "50", "WA": "53", "WI": "55"}

# ---------------------------------------------------------------------------
# 1. Laws and data availability, one row per state
# ---------------------------------------------------------------------------
# Provision columns describe what the state law forbids localities to do (or requires),
# coded yes / partial / no. "treatment_date" is the date local rules had to allow ADUs
# (owner input AQ-034: the treatment is when a place reached near-benchmark rules).
# data_kind: official_statewide | official_partial | official_regional | city_proxy |
#            not_adu_specific | none.
# years_after_*: whole years of usable ADU data after that date (reporting years where the
# source does not use calendar years). "5" means 5 or more.
STATES: list[dict] = [
    dict(abbr="CA", state="California", mercatus_class="strong",
         key_laws="AB 2299 / SB 1069 (2016); AB 494 / SB 229 (2017); AB 68, AB 881, SB 13 (2019)",
         effective_date="2017-01-01", compliance_date="2017-01-01 (2020-01-01 for the 2019 package)",
         treatment_date="2017-01-01",
         coverage="all cities and counties",
         by_right="yes (ministerial; 60-day decision)", owner_occupancy_banned="yes (from 2020)",
         parking_limit="yes (none within 1/2 mile of transit; max 1 space)",
         min_size="800 sq ft must be allowed", fee_limits="yes (no impact fees under 750 sq ft)",
         attached_and_detached="yes",
         law_status="verified (repo: docs/gate3/CA_COMPARISON_PLAN.md and CA_STUDY_RESULTS.md)",
         law_source="https://www.hcd.ca.gov/policy-and-research/accessory-dwelling-units",
         data_source="HCD Annual Progress Report Table A2 (ADUs a separate unit category) plus the 2012-2019 compilation; already in the repo",
         data_kind="official_statewide", years_covered="2012-2025",
         unit_definition="ADU building permits issued by jurisdiction (HCD A2); includes most ADUs built with new houses",
         access="CSV (data.ca.gov); repo data/processed/comparison_ca",
         years_after_effective=5, years_after_compliance=5, before_baseline=True,
         notes="The fitting state for the regression; not an independent test. Rates are the CA study's non-holdout grouped jurisdictions."),
    dict(abbr="WA", state="Washington", mercatus_class="strong",
         key_laws="EHB 1337 (2023 c 334; RCW 36.70A.680-.681); earlier RCW 43.63A.215 (1993, repealed 2023)",
         effective_date="2023-07-23",
         compliance_date="six months after each county's periodic plan update: 2025-06-30 (King, Pierce, Snohomish, Kitsap); about 2025-12-31 (Clark, Thurston, Whatcom and others); 2026-12-31 or later (Spokane and eastern counties)",
         treatment_date="2025-06-30",
         coverage="GMA cities and counties, inside urban growth areas",
         by_right="yes (standards no stricter than for the house)", owner_occupancy_banned="yes",
         parking_limit="yes (none within 1/2 mile of major transit; else max 1-2 spaces)",
         min_size="cap may not be below 1,000 sq ft", fee_limits="yes (impact fees max 50% of the house's)",
         attached_and_detached="yes (two ADUs per lot, any mix)",
         law_status="verified (RCW text; Commerce guidance)",
         law_source="https://app.leg.wa.gov/RCW/default.aspx?cite=36.70A.681",
         data_source="OFM April 1 postcensal estimates: Reported Permits, Completions and Demolitions by Structure Type (ADUs a separate column, 2011-2026)",
         data_kind="official_statewide", years_covered="estimate years 2011-2026 (each April 2 to April 1)",
         unit_definition="ADU permits reported by each city and county to OFM (attached or detached unit on a single-family lot; tiny homes as long-term housing count); with-new-house ADUs not separable; unincorporated areas report ADUs only from EY2021",
         access="Excel (ofm.wa.gov), one row per jurisdiction-year",
         years_after_effective=2, years_after_compliance=0, before_baseline=True,
         notes="Best data of the 18, but HB 1337 compliance is too recent: EY2026 (Apr 2025-Mar 2026) is the only partly post-compliance year, for King/Pierce/Snohomish/Kitsap only."),
    dict(abbr="OR", state="Oregon", mercatus_class="strong",
         key_laws="SB 1051 (2017) as fixed by HB 4031 (2018), ORS 197.312(5); HB 2001 (2019) ADU parking and owner-occupancy bans",
         effective_date="2018-07-01", compliance_date="2018-07-01 (2020-01-01 for HB 2001's parking and owner-occupancy rules)",
         treatment_date="2018-07-01",
         coverage="cities over 2,500 and counties over 15,000, inside urban growth boundaries",
         by_right="partial (subject to reasonable siting and design rules)",
         owner_occupancy_banned="yes (from 2020)", parking_limit="yes (from 2020)",
         min_size="not set by statute", fee_limits="no", attached_and_detached="yes (one ADU per house)",
         law_status="verified (DLCD guidance quoting the statutes)",
         law_source="https://www.oregon.gov/lcd/Publications/ADU_Guidance_updatedSept2019.pdf",
         data_source="DLCD Permitted and Produced Housing Reporting (HB 4006) annual summaries, cities over 10,000 (ADU column)",
         data_kind="official_partial", years_covered="2018-2023 (2023 incomplete; 2024+ moved to PSU, not found)",
         unit_definition="building permits issued for ADUs, self-reported by cities over 10,000; not split by existing vs new house",
         access="PDF tables (State Library of Oregon digital collections)",
         years_after_effective=4, years_after_compliance=4, before_baseline=False,
         notes="Reporting began in 2018, the law's own year, so there is no pre-law year. Portland is already in OTHER_CITIES.md; the panel here excludes it."),
    dict(abbr="MT", state="Montana", mercatus_class="strong",
         key_laws="SB 528 (2023 ch. 502, MCA 76-2-345); SB 532 (2025) extends to zoned counties",
         effective_date="2024-01-01",
         compliance_date="2024-01-01, but enjoined 2023-12-29 until the Montana Supreme Court reversed on 2024-09-03 (MAID v. State, 2024 MT 200)",
         treatment_date="2024-09-03",
         coverage="every zoning municipality",
         by_right="yes", owner_occupancy_banned="yes", parking_limit="yes (none)",
         min_size="no minimum; cap 75% of house or 1,000 sq ft", fee_limits="yes (no impact fees; $250 application cap)",
         attached_and_detached="yes",
         law_status="verified (MT Supreme Court opinion; Legislative Services summary)",
         law_source="https://statecourtreport.org/sites/default/files/2024-12/supreme_court_of_montana-opinion.pdf",
         data_source="none statewide; city proxies: Bozeman ADU applications (city table 2020-2025 YTD), Missoula monthly reports",
         data_kind="city_proxy", years_covered="Bozeman 2020-2025 (2025 half year)",
         unit_definition="Bozeman: ADU applications (residential ADU) per calendar year",
         access="PDF (city document archive)",
         years_after_effective=1, years_after_compliance=1, before_baseline=True,
         notes="Bozeman fell after the law (duplex law SB 323 may substitute). Proxy only."),
    dict(abbr="AZ", state="Arizona", mercatus_class="strong",
         key_laws="HB 2720 (Laws 2024 ch. 196; A.R.S. 9-461.18)",
         effective_date="2024-09-14", compliance_date="2025-01-01", treatment_date="2025-01-01",
         coverage="cities and towns over 75,000",
         by_right="yes (permitted use)", owner_occupancy_banned="yes for long-term rentals (owner residence only for short-term-rental ADUs)",
         parking_limit="yes (none)", min_size="no minimum; cap 75% of house or 1,000 sq ft",
         fee_limits="no", attached_and_detached="yes (one attached and one detached)",
         law_status="verified (session law text); effective date source_lead",
         law_source="https://www.azleg.gov/legtext/56leg/2R/laws/0196.htm",
         data_source="none statewide (A.R.S. 9-469 city housing reports have no ADU field); city figures from news and city releases",
         data_kind="city_proxy", years_covered="fragments 2022-2025",
         unit_definition="mixed: Phoenix ADU permits, Tucson ADU applications",
         access="press releases and news (source_lead)",
         years_after_effective=1, years_after_compliance=1, before_baseline=False,
         notes="Phoenix (2023) and Tucson (2021-22) reformed locally before the state law."),
    dict(abbr="CO", state="Colorado", mercatus_class="strong",
         key_laws="HB24-1152 (C.R.S. 29-35-401 to -405)",
         effective_date="2024-05-13", compliance_date="2025-06-30", treatment_date="2025-06-30",
         coverage="67 subject jurisdictions (MPO municipalities of 1,000+ and large CDPs)",
         by_right="yes (administrative, objective standards)", owner_occupancy_banned="yes (proof of residence at application only)",
         parking_limit="yes (no new space)", min_size="cities may not bar ADUs of 500-750 sq ft (DOLA)",
         fee_limits="no (general impact fees allowed)", attached_and_detached="yes",
         law_status="verified (DOLA page; session law)",
         law_source="https://dlg.colorado.gov/accessory-dwelling-units",
         data_source="none statewide (one-time compliance report has no counts); Denver already in OTHER_CITIES.md",
         data_kind="city_proxy", years_covered="fragments",
         unit_definition="city ADU permits (Colorado Springs, news)",
         access="news / city pages (source_lead)",
         years_after_effective=0, years_after_compliance=0, before_baseline=False,
         notes="2026 is the first full post-compliance year."),
    dict(abbr="ME", state="Maine", mercatus_class="strong",
         key_laws="LD 2003 (PL 2021 c. 672; 30-A MRSA 4364-B), dates amended by LD 1706 (2023); owner-occupancy ban added by LD 1829 (PL 2025 c. 385)",
         effective_date="2022-04-27 (signed)",
         compliance_date="2024-01-01 (councils) / 2024-07-01 (town-meeting towns)",
         treatment_date="2024-07-01",
         coverage="all municipalities (narrow exceptions)",
         by_right="partial (conditional-use review can still apply where housing is conditional)",
         owner_occupancy_banned="not until LD 1829 (reported 2027)", parking_limit="yes (none beyond the house's)",
         min_size="190 sq ft statutory minimum (towns set maximums)", fee_limits="no",
         attached_and_detached="yes",
         law_status="verified (statute text; MOCA guidance)",
         law_source="https://legislature.maine.gov/statutes/30-A/title30-Asec4364-B.html",
         data_source="Maine Office of Community Affairs, 2025 Statewide Housing Data Collection (5 MRSA 3241(5)); ADUs a permit category",
         data_kind="official_partial", years_covered="2025 only (pilot year)",
         unit_definition="dwelling units permitted, ADU category; 182 municipalities (~73% of population)",
         access="PDF summary (maine.gov/moca); portal mainestatehousingdata.org",
         years_after_effective=1, years_after_compliance=1, before_baseline=False,
         notes="No statewide count before 2025. Portland ME: 14, 18, 16, 14 ADUs (2022-2025, Press Herald)."),
    dict(abbr="MA", state="Massachusetts", mercatus_class="strong",
         key_laws="Affordable Homes Act, Chapter 150 of the Acts of 2024 (M.G.L. c.40A s.3); 760 CMR 71",
         effective_date="2025-02-02", compliance_date="2025-02-02", treatment_date="2025-02-02",
         coverage="all municipalities except Boston (own by-right rules)",
         by_right="yes (one ADU; no special permit)", owner_occupancy_banned="yes",
         parking_limit="yes (max 1 space; none within 1/2 mile of transit)",
         min_size="no minimum; up to 900 sq ft or half the house protected", fee_limits="no",
         attached_and_detached="yes",
         law_status="verified (M.G.L. text; EOHLC)",
         law_source="https://malegislature.gov/Laws/GeneralLaws/PartI/TitleVII/Chapter40A/Section3",
         data_source="EOHLC Accessory Dwelling Unit Tracker (semi-annual surveys of building officials under 760 CMR 71.04)",
         data_kind="official_partial", years_covered="2025 and Jan-Jun 2026",
         unit_definition="ADU building permits issued ('approved'); 293 of 351 municipalities answered for 2025 (undercount)",
         access="mass.gov dashboard (scripted download blocked; totals from EOHLC and Boston Indicators)",
         years_after_effective=1, years_after_compliance=1, before_baseline=False,
         notes="Strong law with an official count, but no statewide pre-law baseline; high-value market."),
    dict(abbr="AR", state="Arkansas", mercatus_class="strong",
         key_laws="Act 313 of 2025 (HB 1503; Ark. Code 14-56-205)",
         effective_date="2025-08-05", compliance_date="2026-01-01", treatment_date="2026-01-01",
         coverage="municipalities (not unincorporated counties)",
         by_right="yes", owner_occupancy_banned="yes", parking_limit="yes (none)",
         min_size="no minimum; cap 75% of house or 1,000 sq ft", fee_limits="yes ($250 impact and review fee caps)",
         attached_and_detached="yes",
         law_status="verified (act PDF); effective date source_lead",
         law_source="https://www.arkleg.state.ar.us/Home/FTPDocument?path=%2FACTS%2F2025R%2FPublic%2FACT313.pdf",
         data_source="none", data_kind="none", years_covered="", unit_definition="", access="",
         years_after_effective=0, years_after_compliance=0, before_baseline=False,
         notes="Too new."),
    dict(abbr="IA", state="Iowa", mercatus_class="strong",
         key_laws="SF 592 (Acts 2025 ch. 38; Iowa Code 331.301(27), 364.3(20)); SF 2629 (2026) clarifications",
         effective_date="2025-07-01", compliance_date="2025-07-01", treatment_date="2025-07-01",
         coverage="all cities and counties",
         by_right="yes (ministerial)", owner_occupancy_banned="yes", parking_limit="yes (none)",
         min_size="no minimum; cap the larger of 1,000 sq ft or 50% of the house", fee_limits="partial (same impact fees as the house)",
         attached_and_detached="yes",
         law_status="verified (chapter text)",
         law_source="https://www.legis.iowa.gov/docs/publications/iactc/91.1/CH0038.pdf",
         data_source="none", data_kind="none", years_covered="", unit_definition="", access="",
         years_after_effective=0, years_after_compliance=0, before_baseline=False,
         notes="The Midwest strong-law state; first full year is 2026. Worth re-checking in 2027-2028 (Des Moines, Iowa City)."),
    dict(abbr="NH", state="New Hampshire", mercatus_class="weaker",
         key_laws="SB 146 (2016; RSA 674:71-73); HB 577 (2025 ch. 197) detached ADUs by right",
         effective_date="2017-06-01", compliance_date="2017-06-01 (2025-07-01 for HB 577)", treatment_date="2017-06-01",
         coverage="all zoning municipalities",
         by_right="no in 2017 (special exception or CUP allowed); yes from 2025", owner_occupancy_banned="no",
         parking_limit="no (2025: max 1 extra space)", min_size="cap may not be below 750 sq ft",
         fee_limits="no", attached_and_detached="attached only in 2017; both from 2025",
         law_status="verified (HB 577 chaptered text); 2017 provisions source_lead (NHMA, Mercatus)",
         law_source="https://gc.nh.gov/bill_status/billinfo.aspx?id=125&inflect=2",
         data_source="NH OPD annual Dwelling Unit Survey: no ADU field through CY2024 ('Conversions' column used as proxy, 2020-2024); ADU counts start CY2025 (report due ~Jan 2027)",
         data_kind="not_adu_specific", years_covered="2020-2024 (conversions)",
         unit_definition="net units from conversions of any kind, all municipalities (ADUs plus other conversions, minus conversions out)",
         access="CSV (nheconomy.com)",
         years_after_effective=5, years_after_compliance=5, before_baseline=False,
         notes="Proxy only, years 3-7 after the 2017 law, no baseline. Mercatus 2023: 8 towns 0.12-1.46 per 1,000 SF homes/yr in 2017-2021."),
    dict(abbr="VT", state="Vermont", mercatus_class="weaker",
         key_laws="24 V.S.A. 4412(1)(E) (2004, amended 2006); Act 179 (2020); Act 47 HOME Act (2023)",
         effective_date="2020-10-12 (Act 179)", compliance_date="2020-10-12 (Act 47: 2023-07-01; parking cap 2024-12-01)",
         treatment_date="2020-10-12",
         coverage="all municipalities",
         by_right="yes (permitted use since 2004)", owner_occupancy_banned="unclear (no clause in current text)",
         parking_limit="partial (max 1 space per unit in sewer/water areas from 2024-12-01)",
         min_size="cap may not be below the greater of 30% of the house or 900 sq ft", fee_limits="no",
         attached_and_detached="yes (within or appurtenant)",
         law_status="verified (statute text); provisions partly source_lead (VHFA, DHCD)",
         law_source="https://legislature.vermont.gov/statutes/section/24/117/04412",
         data_source="no statewide permit series; Chittenden County RPC ADU inventory by year built (official regional); DHCD E911 'new housing' layer (unverified)",
         data_kind="official_regional", years_covered="Chittenden 2010-2024",
         unit_definition="ADUs by year first occupied/built, from municipal reports (Chittenden)",
         access="ArcGIS feature service (CCRPC)",
         years_after_effective=4, years_after_compliance=4, before_baseline=True,
         notes="Lower-value New England market close to Wisconsin; regional series only."),
    dict(abbr="CT", state="Connecticut", mercatus_class="weaker",
         key_laws="Public Act 21-29 s.6 (CGS 8-2o)",
         effective_date="2022-01-01", compliance_date="2023-01-01 (115 of 169 towns opted out)", treatment_date="2023-01-01",
         coverage="the 54 towns that did not opt out",
         by_right="yes (where not opted out)", owner_occupancy_banned="effectively (no additional standards)",
         parking_limit="yes (max 1 space)", min_size="cap may not be below 30% of house or 1,000 sq ft",
         fee_limits="partial (no new utility connection fees)", attached_and_detached="yes",
         law_status="verified (CGS text); opt-out count source_lead (DesegregateCT)",
         law_source="https://www.cga.ct.gov/current/pub/chap_124.htm#sec_8-2o",
         data_source="none: DECD construction reports have no ADU field; RPA (2026): no statewide source tracks ADUs",
         data_kind="none", years_covered="", unit_definition="", access="",
         years_after_effective=0, years_after_compliance=0, before_baseline=False,
         notes="Fragmentary town figures only (Westport 40 in 2021-2024)."),
    dict(abbr="RI", state="Rhode Island", mercatus_class="weaker",
         key_laws="P.L. 2022 ch. 437/440 (opt-in rules, reporting); P.L. 2024 ch. 284/285 (RIGL 45-24-73, by right in limited cases)",
         effective_date="2024-06-25", compliance_date="2024-06-25", treatment_date="2024-06-25",
         coverage="all municipalities; by right only on lots of 20,000+ sq ft, inside existing footprints, or for family members with disabilities",
         by_right="partial (limited lot types)", owner_occupancy_banned="no (only not required on two routes)",
         parking_limit="yes (max 1 space per bedroom)", min_size="cap may not be below 900 sq ft (1 bed) / 1,200 (2 bed) or 60% of house",
         fee_limits="yes (no more than a new single-family home)", attached_and_detached="yes",
         law_status="verified (statute text; public law)",
         law_source="https://webserver.rilegislature.gov/Statutes/TITLE45/45-24/45-24-73.htm",
         data_source="RI Executive Office of Housing annual ADU report (RIGL 45-24-76), 4th report covering 2024-2025",
         data_kind="official_partial", years_covered="2021-2025",
         unit_definition="ADUs permitted (and issued a CO) per calendar year, self-reported by municipalities; 32 of 39 reported 2025",
         access="PDF tables (housing.ri.gov)",
         years_after_effective=1, years_after_compliance=1, before_baseline=True,
         notes="Only statewide series with official counts both before and after a state law."),
    dict(abbr="UT", state="Utah", mercatus_class="weaker",
         key_laws="HB 82 (2021 ch. 102; now Utah Code 10-21-303)",
         effective_date="2021-10-01", compliance_date="2021-10-01", treatment_date="2021-10-01",
         coverage="all municipalities and counties; internal ADUs only",
         by_right="yes for internal ADUs (permitted use)", owner_occupancy_banned="no (may bar renting when owner not resident)",
         parking_limit="partial (may require 1 space)", min_size="cannot be limited relative to the house",
         fee_limits="no", attached_and_detached="no (internal only; lots under 6,000 sq ft may be excluded)",
         law_status="verified (enrolled bill; code)",
         law_source="https://le.utah.gov/~2021/bills/hbillenr/HB0082.htm",
         data_source="DWS Moderate Income Housing annual reports (ADU building-permit question, ~90 specified cities and counties)",
         data_kind="official_partial", years_covered="report years 2023-2025 (each ~Aug-Jul)",
         unit_definition="building permits issued to construct an ADU (internal and detached), self-reported; definitions vary by city",
         access="compiled PDF of municipal reports (housing.utah.gov); counts parsed by regex and hand-checked",
         years_after_effective=3, years_after_compliance=3, before_baseline=False,
         notes="Law covers internal ADUs only and keeps owner occupancy; 2026 reporting paused."),
    dict(abbr="HI", state="Hawaii", mercatus_class="weaker",
         key_laws="Act 39, SLH 2024 (SB 3202)",
         effective_date="2024-05-28", compliance_date="2026-12-31", treatment_date="2026-12-31",
         coverage="residentially zoned lots in urban districts (many exclusions)",
         by_right="no (standards left to counties)", owner_occupancy_banned="no (long-term rental ban barred)",
         parking_limit="no", min_size="not set", fee_limits="partial (fees scaled to size)",
         attached_and_detached="yes (two ADUs)",
         law_status="verified (session law)",
         law_source="https://data.capitol.hawaii.gov/sessions/sessionlaws/Years/SLH2024/SLH2024_Act39.pdf",
         data_source="none statewide; Honolulu building permits open data (ADU flag), 2005-2025H1",
         data_kind="city_proxy", years_covered="Honolulu 2016-2025 (2025 half year)",
         unit_definition="issued building permits flagged ADU, by issue year (includes ADUs with new houses)",
         access="Socrata API (data.honolulu.gov 4vab-c87q)",
         years_after_effective=0, years_after_compliance=0, before_baseline=True,
         notes="Honolulu series follows its own 2015 ordinance, not the state law."),
    dict(abbr="MD", state="Maryland", mercatus_class="weaker",
         key_laws="HB 1466 (2025 ch. 197; Land Use 4-501 to 4-507)",
         effective_date="2025-10-01", compliance_date="2026-10-01", treatment_date="2026-10-01",
         coverage="counties and zoning municipalities",
         by_right="yes (ministerial within 90 days)", owner_occupancy_banned="no (silent)",
         parking_limit="yes (none within 3/4 mile of transit; else max 1)", min_size="not set",
         fee_limits="yes (none under 750 sq ft)", attached_and_detached="yes",
         law_status="verified (chapter text)",
         law_source="https://mgaleg.maryland.gov/2025RS/Chapters_noln/CH_197_hb1466t.pdf",
         data_source="none statewide; Montgomery County permit text search (rough)",
         data_kind="city_proxy", years_covered="Montgomery 2019-2025",
         unit_definition="issued permits whose description names an ADU (keyword; includes trade permits)",
         access="Socrata API (dataMontgomery m88u-pqki)",
         years_after_effective=0, years_after_compliance=0, before_baseline=True,
         notes="Compliance deadline passed three weeks ago."),
    dict(abbr="NV", state="Nevada", mercatus_class="weaker",
         key_laws="AB 396 (Stats. 2025 ch. 365; NRS 278)",
         effective_date="2026-07-01", compliance_date="2026-07-01", treatment_date="2026-07-01",
         coverage="Clark and Washoe counties; cities of 60,000+",
         by_right="no (local ordinance required)", owner_occupancy_banned="no (silent; long-term rental ban barred)",
         parking_limit="yes (max 1 space, conditional)", min_size="not set", fee_limits="no",
         attached_and_detached="yes",
         law_status="verified (statutes)",
         law_source="https://www.leg.state.nv.us/Statutes/83rd2025/Stats202519.html",
         data_source="none", data_kind="none", years_covered="", unit_definition="", access="",
         years_after_effective=0, years_after_compliance=0, before_baseline=False,
         notes="Too new."),
]

STATE_COLUMNS = list(STATES[0].keys())


def states_table() -> pd.DataFrame:
    df = pd.DataFrame(STATES)[STATE_COLUMNS]
    df["accessed"] = ACCESSED
    return df


# ---------------------------------------------------------------------------
# 2. Annual ADU counts (official sources or best proxy)
# ---------------------------------------------------------------------------
# Each series: id -> metadata + {year: count}. "denominator" lists the ACS geographies
# whose one-unit detached homes form the denominator: ("state", "53"), ("county", "50007"),
# ("place", "5367000"), or ("places_c1_excluding", ("53", "5363000")) for every incorporated
# place in a state except the listed ones. "year_basis" says what a year means.
SERIES: dict[str, dict] = {
    "WA_inc_exSeattle": dict(
        state="WA", geography="Washington incorporated cities and towns, excluding Seattle",
        measure="ADU permits", year_basis="OFM estimate year (Apr 2 of prior year to Apr 1)",
        denominator=("places_c1_excluding", ("53", ("5363000",))),
        source="OFM ofm_april1_postcensal_permits_1990-present.xlsx, column 'Permitted Accessory Dwelling units'",
        status="observed",
        counts={2011: 101, 2012: 91, 2013: 91, 2014: 169, 2015: 140, 2016: 156, 2017: 243, 2018: 256,
                2019: 306, 2020: 368, 2021: 379, 2022: 416, 2023: 617, 2024: 717, 2025: 861, 2026: 888}),
    "WA_statewide": dict(
        state="WA", geography="Washington, all jurisdictions",
        measure="ADU permits", year_basis="OFM estimate year (Apr 2 of prior year to Apr 1)",
        denominator=("state", "53"),
        source="OFM permits workbook; unincorporated areas report ADUs only from EY2021, so only 2021+ is used",
        status="observed",
        counts={2021: 1253, 2022: 1604, 2023: 2110, 2024: 2169, 2025: 2216, 2026: 2133}),
    "WA_spokane": dict(
        state="WA", geography="Spokane city, WA", measure="ADU permits",
        year_basis="OFM estimate year (Apr 2 of prior year to Apr 1)",
        denominator=("place", "5367000"),
        source="OFM permits workbook, City Name = Spokane", status="observed",
        counts={2011: 4, 2012: 2, 2013: 3, 2014: 5, 2015: 0, 2016: 6, 2017: 6, 2018: 9, 2019: 12,
                2020: 6, 2021: 5, 2022: 18, 2023: 46, 2024: 24, 2025: 28, 2026: 40}),
    "OR_panel32_exPortland": dict(
        state="OR", geography="32 Oregon cities over 10,000 reporting every year 2018-2022, excluding Portland",
        measure="ADU permits", year_basis="calendar year",
        denominator=("place_names", ("41", (
            "Albany",
            "Ashland",
            "Bend",
            "Coos Bay",
            "Cornelius",
            "Corvallis",
            "Dallas",
            "Eugene",
            "Forest Grove",
            "Gladstone",
            "Grants Pass",
            "Gresham",
            "Hermiston",
            "Hillsboro",
            "Keizer",
            "La Grande",
            "Lake Oswego",
            "Lebanon",
            "Medford",
            "Milwaukie",
            "Ontario",
            "Redmond",
            "Roseburg",
            "Salem",
            "Sandy",
            "Springfield",
            "St. Helens",
            "The Dalles",
            "Tigard",
            "Tualatin",
            "Wilsonville",
            "Woodburn",
        ))),
        source="DLCD HB 4006 annual summaries 2018-2022 (ADU permitted column), city rows parsed from PDF; state totals 795, 657, 544, 605, 640",
        status="observed",
        counts={2018: 166, 2019: 289, 2020: 357, 2021: 333, 2022: 335}),
    "RI_statewide": dict(
        state="RI", geography="Rhode Island, reporting municipalities", measure="ADU permits",
        year_basis="calendar year", denominator=("state", "44"),
        source="RI EOH 4th annual ADU report (2026), Attachment 3; 2025: 32 of 39 municipalities reported",
        status="observed",
        counts={2021: 62, 2022: 53, 2023: 71, 2024: 163, 2025: 262}),
    "MA_statewide": dict(
        state="MA", geography="Massachusetts, responding municipalities (293 of 351 for 2025)",
        measure="ADU building permits issued", year_basis="calendar year",
        denominator=("state", "25"),
        source="EOHLC ADU Tracker / Boston Indicators ADU one-year report (2025 = 1,224 approvals; undercount)",
        status="observed", counts={2025: 1224}),
    "ME_statewide": dict(
        state="ME", geography="Maine, 182 reporting municipalities (~73% of population)",
        measure="ADUs permitted", year_basis="calendar year", denominator=("state", "23"),
        source="MOCA 2025 Statewide Housing Data Collection Results Summary", status="observed",
        counts={2025: 516}),
    "ME_portland": dict(
        state="ME", geography="Portland city, ME", measure="ADUs permitted", year_basis="calendar year",
        denominator=("place", "2360545"),
        source="Portland Press Herald 2026-05-07 citing city permit counts", status="source_lead",
        counts={2022: 14, 2023: 18, 2024: 16, 2025: 14}),
    "UT_mih": dict(
        state="UT", geography="Utah, ~90 'specified' cities and counties filing MIH reports",
        measure="ADU building permits (self-reported)",
        year_basis="MIH report year (about Aug 1 of prior year to Jul 31)", denominator=("state", "49"),
        source="DWS MIH compiled reports 2023-2025, ADU building-permit answers summed (Cedar Hills 2025 excluded)",
        status="observed", counts={2023: 903, 2024: 836, 2025: 1013}),
    "NH_conversions": dict(
        state="NH", geography="New Hampshire, all municipalities",
        measure="net units from conversions (ADU proxy, not ADU-specific)", year_basis="calendar year",
        denominator=("state", "33"),
        source="NH OPD hse2020-2025-Analysis-Share CSV, 'Convert' column summed", status="observed",
        counts={2020: 309, 2021: 346, 2022: 507, 2023: 324, 2024: 400}),
    "VT_chittenden": dict(
        state="VT", geography="Chittenden County, VT", measure="ADUs by year built/first occupied",
        year_basis="calendar year", denominator=("county", "50007"),
        source="CCRPC VT_Data_Housing_ChittendenCounty feature service (2024 from DHCD CCRPC records)",
        status="observed",
        counts={2010: 2, 2011: 12, 2012: 0, 2013: 1, 2014: 12, 2015: 22, 2016: 18, 2017: 15, 2018: 29,
                2019: 27, 2020: 30, 2021: 26, 2022: 32, 2023: 31, 2024: 57}),
    "HI_honolulu": dict(
        state="HI", geography="City and County of Honolulu", measure="issued building permits flagged ADU",
        year_basis="calendar year", denominator=("county", "15003"),
        source="Honolulu open data 4vab-c87q, accessorydwellingunitadu = Y, by issue year (2025 Jan-Jun omitted)",
        status="observed",
        counts={2016: 101, 2017: 227, 2018: 230, 2019: 266, 2020: 266, 2021: 216, 2022: 111, 2023: 123,
                2024: 222}),
    "MD_montgomery": dict(
        state="MD", geography="Montgomery County, MD", measure="issued permits whose text names an ADU (rough)",
        year_basis="calendar year", denominator=("county", "24031"),
        source="dataMontgomery m88u-pqki keyword count; includes trade permits", status="observed",
        counts={2019: 5, 2020: 36, 2021: 58, 2022: 70, 2023: 88, 2024: 109, 2025: 115}),
    "MT_bozeman": dict(
        state="MT", geography="Bozeman city, MT", measure="ADU applications", year_basis="calendar year",
        denominator=("place", "3008950"),
        source="City of Bozeman 'Residential Livable SQF Data 2020-2025 YTD' (2025 only Jan-Jun, omitted)",
        status="observed", counts={2020: 13, 2021: 23, 2022: 28, 2023: 14, 2024: 9}),
    "AZ_tucson": dict(
        state="AZ", geography="Tucson city, AZ", measure="ADU applications", year_basis="calendar year",
        denominator=("place", "0477000"),
        source="Tucson Agenda citing a city public-records response (2025 'about 80')", status="source_lead",
        counts={2022: 61, 2025: 80}),
    "AZ_phoenix_detached": dict(
        state="AZ", geography="Phoenix city, AZ", measure="detached ADU permits (RES-ADU-DET)",
        year_basis="calendar year", denominator=("place", "0455000"),
        source="vendor analysis of Phoenix open-data export (likely excludes attached/conversions)",
        status="source_lead", counts={2025: 84}),
    "CO_colorado_springs": dict(
        state="CO", geography="Colorado Springs city, CO", measure="ADU permits", year_basis="calendar year",
        denominator=("place", "0816000"), source="KOAA citing city figures", status="source_lead",
        counts={2024: 10}),
}

# California: rates are taken from the CA study (non-holdout grouped jurisdictions), not
# recomputed here. docs/gate3/CA_STUDY_RESULTS.md section 8, column "A per 1,000 homes".
CA_RATES = [
    ("CA_nonholdout", "before", "2014-2016", 2014, 2016, None, 0.12),
    ("CA_nonholdout", "after", "first strong law (2017)", 2017, 2017, "1", 0.66),
    ("CA_nonholdout", "after", "2018-2019", 2018, 2019, "2-3", 1.48),
    ("CA_nonholdout", "after", "2019 package, 2020-2022", 2020, 2022, "4-6", 2.46),
    ("CA_nonholdout", "after", "plateau 2023-2025", 2023, 2025, "7-9", 3.88),
]

# Before / after windows: (series, phase, label, first year, last year, years after treatment)
PERIODS = [
    ("WA_inc_exSeattle", "before", "long before HB 1337 (EY2011-2016)", 2011, 2016, None),
    ("WA_inc_exSeattle", "before", "before HB 1337 (EY2019-2023)", 2019, 2023, None),
    ("WA_inc_exSeattle", "after_enactment", "after enactment, before most compliance (EY2024-2025)", 2024, 2025, "0 (enacted, not yet binding)"),
    ("WA_inc_exSeattle", "after", "first partly post-compliance year (EY2026)", 2026, 2026, "<1"),
    ("WA_statewide", "before", "all jurisdictions (EY2021-2023)", 2021, 2023, None),
    ("WA_statewide", "after_enactment", "after enactment (EY2024-2025)", 2024, 2025, "0 (enacted, not yet binding)"),
    ("WA_statewide", "after", "EY2026", 2026, 2026, "<1"),
    ("WA_spokane", "before", "EY2011-2021", 2011, 2021, None),
    ("WA_spokane", "local_reform", "after Spokane's 2022 interim rules (EY2023-2026)", 2023, 2026, "state law not binding until 2026-12-31"),
    ("OR_panel32_exPortland", "transition", "law year (2018)", 2018, 2018, "0"),
    ("OR_panel32_exPortland", "after", "2019-2022", 2019, 2022, "1-4"),
    ("RI_statewide", "before", "2021-2023", 2021, 2023, None),
    ("RI_statewide", "transition", "law year (2024)", 2024, 2024, "0"),
    ("RI_statewide", "after", "2025", 2025, 2025, "1"),
    ("MA_statewide", "after", "2025", 2025, 2025, "1"),
    ("ME_statewide", "after", "2025", 2025, 2025, "1"),
    ("ME_portland", "before", "2022-2023", 2022, 2023, None),
    ("ME_portland", "after", "2024-2025", 2024, 2025, "0-1"),
    ("UT_mih", "after", "report years 2023-2025", 2023, 2025, "1-4"),
    ("NH_conversions", "after", "2020-2024 (proxy)", 2020, 2024, "3-7"),
    ("VT_chittenden", "before", "before Act 179 (2016-2020)", 2016, 2020, None),
    ("VT_chittenden", "after", "after Act 179 (2021-2024)", 2021, 2024, "1-4"),
    ("HI_honolulu", "local_reform", "Honolulu ordinance years (2016-2023)", 2016, 2023, None),
    ("HI_honolulu", "after_enactment", "after Act 39 enactment (2024)", 2024, 2024, "0 (enacted, not yet binding)"),
    ("MD_montgomery", "local_reform", "after county 2019 reform (2020-2025)", 2020, 2025, None),
    ("MT_bozeman", "before", "2020-2023", 2020, 2023, None),
    ("MT_bozeman", "after", "2024 (law enjoined until Sept)", 2024, 2024, "0"),
    ("AZ_tucson", "before", "2022", 2022, 2022, None),
    ("AZ_tucson", "after", "2025", 2025, 2025, "1"),
    ("AZ_phoenix_detached", "after", "2025 (detached only)", 2025, 2025, "1"),
    ("CO_colorado_springs", "before", "2024", 2024, 2024, None),
]


# ---------------------------------------------------------------------------
# 3. ACS denominators and market
# ---------------------------------------------------------------------------

def read_acs_rows(path: Path, geo_ids: set[str]) -> pd.DataFrame:
    """Rows of one ACS table-based summary file for the given GEO_IDs (e.g. 0400000US53)."""
    keep, header = [], None
    with open(path, encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("|")
        for line in f:
            gid = line.split("|", 1)[0]
            if gid in geo_ids:
                keep.append(line.rstrip("\n").split("|"))
    df = pd.DataFrame(keep, columns=header)
    for c in df.columns[1:]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
        df[c] = df[c].mask(df[c] < 0)
    return df.rename(columns={"GEO_ID": "geo_id"})


def incorporated_places(codes_file: Path, exclude: tuple[str, ...] = ()) -> list[str]:
    """7-digit place GEOIDs of incorporated places (CLASSFP C*) from a Census place code file."""
    df = pd.read_csv(codes_file, sep="|", dtype=str)
    df = df[df["CLASSFP"].str.startswith("C")]
    ids = (df["STATEFP"] + df["PLACEFP"]).tolist()
    return [g for g in ids if g not in exclude]


def places_by_name(codes_file: Path, names: tuple[str, ...]) -> list[str]:
    """7-digit GEOIDs of incorporated places named '<name> city' (or town); every name must match once."""
    df = pd.read_csv(codes_file, sep="|", dtype=str)
    df = df[df["CLASSFP"].str.startswith("C")]
    base = df["PLACENAME"].str.replace(r" (city|town)$", "", regex=True)
    out = []
    for n in names:
        hit = df[base == n]
        if len(hit) != 1:
            raise ValueError(f"place name {n!r} matched {len(hit)} incorporated places")
        out.append(hit["STATEFP"].iloc[0] + hit["PLACEFP"].iloc[0])
    return out


def geo_ids_for(denominator, place_codes: dict[str, Path] | None = None) -> list[str]:
    kind, arg = denominator
    if kind == "state":
        return [f"0400000US{arg}"]
    if kind == "county":
        return [f"0500000US{arg}"]
    if kind == "place":
        return [f"1600000US{arg}"]
    if kind == "places":
        return [f"1600000US{g}" for g in arg]
    if kind == "place_names":
        st, names = arg
        if not place_codes or st not in place_codes:
            raise ValueError(f"place code file for state {st} needed for {denominator}")
        return [f"1600000US{g}" for g in places_by_name(place_codes[st], names)]
    if kind == "places_c1_excluding":
        st, excl = arg
        if not place_codes or st not in place_codes:
            raise ValueError(f"place code file for state {st} needed for {denominator}")
        return [f"1600000US{g}" for g in incorporated_places(place_codes[st], excl)]
    raise ValueError(kind)


def acs_geographies(b25024: Path, b25077: Path, b25064: Path, series: dict = SERIES,
                    place_codes: dict[str, Path] | None = None, extra_states=STATE_FIPS) -> pd.DataFrame:
    """One row per denominator geography (each series, plus every state and WI): one-unit
    detached homes (sum over member geographies), median home value and rent. For a
    multi-place aggregate, value and rent are the home-weighted mean of place medians
    (an approximation, flagged)."""
    wanted: dict[str, list[str]] = {}
    for sid, s in series.items():
        wanted[sid] = geo_ids_for(s["denominator"], place_codes)
    for ab, st in extra_states.items():
        wanted[f"state_{ab}"] = [f"0400000US{st}"]
    all_ids = {g for ids in wanted.values() for g in ids}
    h = read_acs_rows(b25024, all_ids).set_index("geo_id")
    v = read_acs_rows(b25077, all_ids).set_index("geo_id")
    r = read_acs_rows(b25064, all_ids).set_index("geo_id")
    rows = []
    for key, ids in wanted.items():
        ids = [g for g in ids if g in h.index]
        homes = h.loc[ids, "B25024_E002"]
        val = v.reindex(ids)["B25077_E001"]
        rent = r.reindex(ids)["B25064_E001"]
        if len(ids) == 1:
            value, rent_v, approx = val.iloc[0], rent.iloc[0], False
        else:
            w = homes.where(val.notna())
            value = float((val * w).sum() / w.sum())
            w2 = homes.where(rent.notna())
            rent_v = float((rent * w2).sum() / w2.sum())
            approx = True
        rows.append(dict(key=key, n_geographies=len(ids), homes=float(homes.sum()),
                         median_value=round(float(value)), median_rent=round(float(rent_v)),
                         market_is_weighted_mean_of_places=approx))
    out = pd.DataFrame(rows)
    out["vintage"] = "ACS 2020-2024 5-year (table-based summary file): B25024_002, B25077, B25064"
    return out


# ---------------------------------------------------------------------------
# 4. Rates
# ---------------------------------------------------------------------------

def annual_table(series: dict = SERIES, homes: dict[str, float] | None = None) -> pd.DataFrame:
    rows = []
    for sid, s in series.items():
        for y, n in sorted(s["counts"].items()):
            r = dict(series=sid, state=s["state"], geography=s["geography"], measure=s["measure"],
                     year_basis=s["year_basis"], year=y, adu_count=n, value_status=s["status"],
                     source=s["source"])
            if homes is not None:
                r["homes"] = homes[sid]
                r["per_1000_homes"] = 1000 * n / homes[sid]
            rows.append(r)
    return pd.DataFrame(rows)


def period_rates(series: dict = SERIES, periods=PERIODS, homes: dict[str, float] | None = None) -> pd.DataFrame:
    """Average ADUs per 1,000 one-unit detached homes per year for each window, with a 95%
    Poisson interval on the count (ignores year-to-year swings and reporting gaps)."""
    rows = []
    for sid, phase, label, y0, y1, yrs_after in periods:
        s = series[sid]
        yrs = [y for y in range(y0, y1 + 1) if y in s["counts"]]
        k = sum(s["counts"][y] for y in yrs)
        n_years = len(yrs)
        r = dict(series=sid, state=s["state"], geography=s["geography"], phase=phase, label=label,
                 first_year=y0, last_year=y1, years_observed=n_years, adu_count=k,
                 years_after_treatment=yrs_after, value_status="calculated")
        if homes is not None and n_years:
            hm = homes[sid]
            lo, hi = poisson_interval(k)
            r.update(homes=hm, rate=1000 * k / n_years / hm, rate_lo=1000 * lo / n_years / hm,
                     rate_hi=1000 * hi / n_years / hm)
        rows.append(r)
    return pd.DataFrame(rows)


def ca_rate_rows() -> pd.DataFrame:
    return pd.DataFrame([dict(series=s, state="CA", geography="California non-holdout grouped jurisdictions",
                              phase=ph, label=lab, first_year=a, last_year=b, years_after_treatment=ya,
                              rate=r, value_status="calculated (CA_STUDY_RESULTS.md section 8)")
                         for s, ph, lab, a, b, ya, r in CA_RATES])


# ---------------------------------------------------------------------------
# 5. Usefulness ranking for the Wisconsin statewide-law test
# ---------------------------------------------------------------------------
QUALITY_SCORE = {"official_statewide": 1.0, "official_partial": 0.75, "official_regional": 0.5,
                 "city_proxy": 0.35, "not_adu_specific": 0.25, "none": 0.0}
WEIGHTS = {"post_years": 0.35, "quality": 0.25, "baseline": 0.10, "law": 0.20, "market": 0.10}


def law_score(row: dict) -> float:
    """1 = benchmark-like strong law; weaker laws and narrow coverage score lower."""
    s = 1.0 if row["mercatus_class"] == "strong" else 0.5
    if str(row["attached_and_detached"]).startswith(("no", "attached only")):
        s -= 0.25
    if str(row["by_right"]).startswith(("partial", "no")):
        s -= 0.1
    return max(s, 0.0)


def market_score(value: float, wi_value: float) -> float:
    """1 when the median home value equals Wisconsin's, 0 at three times (or a third of) it."""
    return max(0.0, 1.0 - abs(math.log(value / wi_value)) / math.log(3))


def rank_states(states: list[dict], values: dict[str, float], wi_value: float) -> pd.DataFrame:
    """Score = weighted sum of: post-law years (after the law's effective date, as the owner's
    question asks; capped at 5), data quality,
    same-source pre-law baseline, closeness of law to the benchmark, and closeness of the
    data geography's median home value to Wisconsin's. Weights in ``WEIGHTS``. The score
    orders states for follow-up; it is a judgment aid, not a statistic. A sensitivity score
    counts years after the local compliance date instead (AQ-034 timing note)."""
    def components(st: dict, years_key: str) -> dict:
        has_data = st["data_kind"] != "none"
        post = min(st[years_key], 5) / 5 if has_data else 0.0
        return dict(post_years=post,
                    quality=QUALITY_SCORE[st["data_kind"]],
                    # a pre-law baseline only helps a test if there are post-law years to compare
                    baseline=1.0 if (st["before_baseline"] and post > 0) else 0.0,
                    law=law_score(st),
                    market=market_score(values[st["abbr"]], wi_value) if has_data else 0.0)

    rows = []
    for st in states:
        comp = components(st, "years_after_effective")
        score = sum(WEIGHTS[k] * v for k, v in comp.items())
        comp_c = components(st, "years_after_compliance")
        score_c = sum(WEIGHTS[k] * v for k, v in comp_c.items())
        rows.append(dict(abbr=st["abbr"], state=st["state"], mercatus_class=st["mercatus_class"],
                         years_after_effective=st["years_after_effective"],
                         years_after_compliance=st["years_after_compliance"], data_kind=st["data_kind"],
                         before_baseline=st["before_baseline"], market_value=values[st["abbr"]],
                         **{f"s_{k}": round(v, 3) for k, v in comp.items()}, score=round(score, 3),
                         score_compliance_basis=round(score_c, 3)))
    out = pd.DataFrame(rows).sort_values(["score", "abbr"], ascending=[False, True]).reset_index(drop=True)
    out.insert(0, "rank", range(1, len(out) + 1))
    return out


# The geography whose market (median home value) represents each state's usable data.
DATA_GEOGRAPHY = {"CA": "state_CA", "WA": "WA_inc_exSeattle", "OR": "OR_panel32_exPortland",
                  "MT": "MT_bozeman", "AZ": "AZ_tucson", "CO": "CO_colorado_springs",
                  "ME": "ME_statewide", "MA": "MA_statewide", "AR": "state_AR", "IA": "state_IA",
                  "NH": "NH_conversions", "VT": "VT_chittenden", "CT": "state_CT", "RI": "RI_statewide",
                  "UT": "UT_mih", "HI": "HI_honolulu", "MD": "MD_montgomery", "NV": "state_NV"}
