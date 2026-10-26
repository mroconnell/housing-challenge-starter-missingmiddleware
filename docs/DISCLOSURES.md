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
| Open Sans Semibold map glyphs (signed-distance-field PBF, ranges 0-255, 256-511, 8192-8447; 172 KB) in `ui/public/fonts/open-sans-semibold/` | openmaptiles/fonts, branch `gh-pages`, commit 025ff2b, downloaded 2026-10-26 (details and SHA-256 in that folder's `SOURCE.md`) | Apache-2.0 (the font's licence file is copied beside the glyphs as `LICENSE.txt`) | none; attribution by keeping `LICENSE.txt` with the files |

# External APIs and Hosted Services

[List any API or hosted service your tool needs to function. Note whether there
is a free tier, whether access could lapse, and any terms limiting commercial,
government, or downstream use. Reviewers prioritize tools whose data and services
remain freely available to end users.]

# Dependency Licenses

[Confirm that your runtime dependencies are permissively licensed and compatible with closed-source downstream integration. Copyleft (GPL, AGPL, LGPL, MPL, EUPL), source-available-but-not-open-source, noncommercial, or unknown-license dependencies must be flagged here and resolved. Your SBOM (exported from GitHub's dependency graph) is the source of truth; summarize any exceptions.]

| Dependency | License | Runtime or dev-only | Notes |
| ---------- | ------- | ------------------- | ----- |
| pandas | BSD-3-Clause | runtime (pipeline) | ok |
| pyarrow | Apache-2.0 | runtime (pipeline) | ok |
| geopandas, shapely | BSD-3-Clause | runtime (pipeline, map geometry) | ok |
| pyogrio, pyproj | MIT | runtime (pipeline) | ok |
| matplotlib | Matplotlib License (PSF-style, permissive) | dev-only (Gate 3 charts, `uv run --with`) | ok |
| maplibre-gl 6.15.0 | BSD-3-Clause | runtime (tool map) | ok; its dependencies are MIT, ISC, BSD-2/3-Clause or MIT OR Apache-2.0 |
| vite 7.3.7 | MIT | dev-only (build, local server) | ok; dependencies MIT, ISC, BSD, Apache-2.0 |
| typescript 7.0.2 | Apache-2.0 | dev-only (type check) | ok |
| @playwright/test 1.63.0 | Apache-2.0 | dev-only (smoke tests) | ok |

Checked 2026-10-25 with `cd ui && npm run licenses` (reads every installed package in `ui/package-lock.json`): 113 npm packages, all MIT, ISC, BSD-2-Clause, BSD-3-Clause or Apache-2.0. Two candidates were rejected for the Gate 4 tool: Observable Plot pulls in d3-delaunay → robust-predicates (Unlicense, a public-domain dedication), so the charts are drawn with dependency-free SVG instead; Vite 8 requires lightningcss (MPL-2.0), so the tool uses Vite 7. The tool loads no basemap or other services at run time. Since 2026-10-26 it self-hosts one font for map labels (Open Sans Semibold glyphs from openmaptiles/fonts, Apache-2.0; see the asset table above); `npm run licenses` also checks that its licence file is present. Open Sans was chosen over Noto Sans because the openmaptiles Open Sans files carry the Apache-2.0 licence, while Noto Sans is under the SIL Open Font License 1.1 (OFL), a font licence rather than a code licence: it is permissive for embedding and redistribution but forbids selling the font alone and restricts reserved font names on modified versions, so it would need a separate review.

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
