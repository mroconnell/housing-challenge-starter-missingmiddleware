# Disclosures

AI-assisted development is welcome. This document exists so reviewers can
confirm that your tool's code, models, services, and dependencies are compatible
with the challenge's open-source and downstream-use requirements. Disclose
material use; incidental use of a general coding assistant is lower risk but
should still be noted if its terms affect your submission.

# AI-Assisted Code Generation

[List any AI coding tools you used in a material way (e.g., for generating core
logic). Confirm that the tool's terms permit submitting and openly licensing the
generated output. You remain responsible for understanding, testing, and
securing all code you submit.]

# Pretrained Models, Weights, and Embeddings

[List any pretrained models, model weights, embeddings, or model libraries your
tool incorporates or requires. For each, give the name, source, and the license
or terms that govern it. Flag any noncommercial, field-of-use, or
acceptable-use restrictions.]

| Model / asset | Source | License / terms | Restrictions |
| ------------- | ------ | --------------- | ------------ |
| [name] | [URL] | [license] | [none / noncommercial / etc.] |

# External APIs and Hosted Services

[List any API or hosted service your tool needs to function. Note whether there
is a free tier, whether access could lapse, and any terms limiting commercial,
government, or downstream use. Reviewers prioritize tools whose data and services
remain freely available to end users.]

# Dependency Licenses

[Confirm that your runtime dependencies are permissively licensed and compatible with closed-source downstream integration. Copyleft (GPL, AGPL, LGPL, MPL, EUPL), source-available-but-not-open-source, noncommercial, or unknown-license dependencies must be flagged here and resolved. Your SBOM (exported from GitHub's dependency graph) is the source of truth; summarize any exceptions.]

| Dependency | License | Runtime or dev-only | Notes |
| ---------- | ------- | ------------------- | ----- |
| [name] | [license] | [runtime / dev] | [ok / flagged] |

# Generated or Copied Code

[Note any code copied or adapted from external sources, and the license it came under. Ensure attribution requirements (e.g., an entry in NOTICE) are met.]

# Third-Party Datasets

The repository's Apache-2.0 license covers code only. Each dataset keeps its own terms. Raw data is downloaded into git-ignored `data/raw/` and is not redistributed; only small samples (`data/sample/`) and team-built aggregates (`reference/`) are committed. Versions, access dates and URLs are in [DATA_PROVENANCE.md](DATA_PROVENANCE.md); open compliance items are in [DATA_COMPLIANCE.md](DATA_COMPLIANCE.md). "not stated" means no license or terms statement was found.

| Dataset | Publisher | License / terms | Restrictions |
| ------- | --------- | --------------- | ------------ |
| ACS 5-year, TIGER/Line, CBSA, PEP housing units, Building Permits Survey, 2020 place codes | U.S. Census Bureau | Public domain | none |
| IPEDS HD2023 | NCES | Public domain | none |
| BLS CES/PPI, BLS QCEW, FHFA HPI, NTD, USGS NLCD (samples only) | Federal agencies | Public domain | none |
| NASA MODIS land cover (sample only) | NASA | NASA open data, no restrictions | none |
| Microsoft Global ML Building Footprints (sample only) | Microsoft | ODbL | share-alike for derived databases |
| Google Open Buildings (sample only) | Google | CC BY 4.0 or ODbL | attribution; ODbL share-alike if chosen |
| HUD/USPS vacancy | HUD | Restricted to government and nonprofit users | not used |
| Madison permit report, Pleasant Prairie SmartGov report, Sun Prairie Power BI report | Local governments | not stated (public records) | owner and contractor fields dropped; raw not redistributed |
| Madison parcels, address points, zoning | City of Madison | City of Madison open data terms | none known |
| Wisconsin V-series / V12 statewide parcels | Wisconsin DOA / State Cartographer's Office | Public (Wis. Stat. 59.72) | owner fields not used |
| Wisconsin Assembly districts | Wisconsin LTSB | open, use at own risk | none known |
| Wisconsin DOA Comp Plan and Land Regs Inventory; county zoning pages | Wisconsin DOA; counties | not stated (public records) | none known |
| Wisconsin city permit reports: Green Bay, De Pere, Howard, Kaukauna, Neenah, Verona, Watertown, Waunakee, Fitchburg | Local governments | not stated (public records) | raw files hold names; not redistributed |
| Milwaukee building permits and MPROP | City of Milwaukee | CC-BY | attribution |
| State parcel and land-use samples: AZ, CT, OR (Metro RLIS, GEOHub), HI, PA (PASDA), UT (LIR, HUI), VA, RI, NH | State and regional GIS offices | varies; see each item page (not yet recorded) | samples only |
| California HCD APR tables (incl. Table A2 project rows); HCD ADU ordinance list | California HCD | not stated (data.ca.gov: "License not specified") | APN rows not redistributed |
| BuildinganADU.com California ADU compilation | BuildinganADU.com (Google Sheets) | not stated | cite compiler and HCD |
| Terner TCRLUS 2018; CCI ADU Scorecard; ADU California grades; CA YIMBY report | UC Berkeley Terner Center and CCI; ADU California; California YIMBY | not stated | cited; not redistributed |
| Washington OFM; Oregon DLCD; NH OPD; RI EOH; MA EOHLC; Maine MOCA; Utah DWS; Vermont CCRPC and DHCD | State and regional agencies | not stated | none known |
| Seattle, Austin permits | Cities of Seattle and Austin | Public domain | none |
| Seattle OPCD ADU report; Portland, Denver, Minneapolis, Honolulu, Montgomery County, Bozeman permit data | Local governments | not stated, or the portal's general open-data terms (Denver: use constraints as stated, no warranty) | none known |
| News and vendor figures (Portland Press Herald, Tucson Agenda, KOAA, Phoenix vendor analysis); Mercatus, Peterson, Boston Indicators, dmvadu.com, Maxable | Third parties | not stated | cited only; marked `source_lead` |
| Statutes, session laws, municipal codes and ordinances (incl. Municode, ecode360, Internet Archive copies) | Legislatures, municipalities, code hosts | public law; host terms not checked | cited; coded by the team. Zoneomics (a commercial mirror) is no longer cited: its terms allow personal, non-commercial use only (`docs/DATA_COMPLIANCE.md`, D4) |
