# Disclosures

AI-assisted development is welcome. This document exists so reviewers can
confirm that your tool's code, models, services, and dependencies are compatible
with the challenge's open-source and downstream-use requirements. Disclose
material use; incidental use of a general coding assistant is lower risk but
should still be noted if its terms affect your submission.

# AI-Assisted Code Generation

The code and documentation in this repository were developed with Anthropic's Claude, used through Claude Code (Anthropic's command-line coding agent). Coding agents wrote most of the pipeline (`missing_middleware/`, `scripts/`), the tests (`tests/`, `ui/tests/`), the interactive tool (`ui/`) and the gate documents (`docs/`), working from the owner's instructions and decisions (recorded in [ASSUMPTIONS_AND_QUESTIONS.md](ASSUMPTIONS_AND_QUESTIONS.md)). Commits made this way carry a `Co-Authored-By: Claude …` trailer, so `git log` shows which commits were AI-assisted. The owner reviewed and adopted each gate's outputs; the automated tests (`bash scripts/test.sh`, `bash scripts/test_ui.sh`, run in CI) check the code against the stated method and outputs.

Anthropic's terms assign to the user Anthropic's rights in the outputs and place no restriction on releasing them under an open-source licence, so the generated code can be submitted and released under this repository's Apache-2.0 licence (TODO (owner): confirm against the terms of the plan you used). The team remains responsible for understanding, testing and securing it.

No AI model runs inside the tool or the pipeline: the tool reads a precomputed JSON bundle, and every number comes from deterministic Python code in this repository.

TODO (owner): confirm whether any other AI tools were used in a material way (for example to produce the early design mockups, `adu-mockup-*.png` and `adu-map-*.png`, which were used as design references only; see [gate1/INTERFACE_WORKFLOW.md](gate1/INTERFACE_WORKFLOW.md)), and add them here with their terms.

# Pretrained Models, Weights, and Embeddings

[List any pretrained models, model weights, embeddings, or model libraries your
tool incorporates or requires. For each, give the name, source, and the license
or terms that govern it. Flag any noncommercial, field-of-use, or
acceptable-use restrictions.]

No pretrained models, model weights or embeddings are used: the tool and the pipeline contain no machine-learning model. The only third-party asset bundled with the tool is the font below.

| Model / asset | Source | License / terms | Restrictions |
| ------------- | ------ | --------------- | ------------ |
| Open Sans Semibold map glyphs (signed-distance-field PBF, ranges 0-255, 256-511, 8192-8447; 172 KB) in `ui/public/fonts/open-sans-semibold/` | openmaptiles/fonts, branch `gh-pages`, commit 025ff2b, downloaded 2026-10-26 (details and SHA-256 in that folder's `SOURCE.md`) | Apache-2.0 (the font's licence file is copied beside the glyphs as `LICENSE.txt`) | none; attribution by keeping `LICENSE.txt` with the files |

# External APIs and Hosted Services

[List any API or hosted service your tool needs to function. Note whether there
is a free tier, whether access could lapse, and any terms limiting commercial,
government, or downstream use. Reviewers prioritize tools whose data and services
remain freely available to end users.]

**At run time: none.** The tool (`bash scripts/run_tool.sh`) is served from the user's own machine and reads only the committed bundle in `ui/public/runs/` and the self-hosted font; it calls no external API, basemap or analytics service, and needs no account or key.

**At build time only (data downloads).** The build commands in the README fetch public data once into git-ignored `data/raw/`. None needs a key or a paid account; all are free public download services that could change or move, so exact URLs, vintages and access dates are recorded in [DATA_PROVENANCE.md](DATA_PROVENANCE.md). The main services are:

| Service | Used for | Key or account | Terms |
| ------- | -------- | -------------- | ----- |
| U.S. Census Bureau file server (`www2.census.gov`) and Census Data API (`api.census.gov`, keyless use) | ACS, Population Estimates, Building Permits Survey, TIGER/Line and cartographic boundary files | none | public domain |
| BLS (`api.bls.gov`, keyless v1), FHFA, other federal file servers | comparison and context series | none | public domain |
| ArcGIS REST services and open-data portals of Wisconsin and other state and local governments (for example City of Madison, Wisconsin LTSB, Oregon GEOHub, PASDA) | parcels, zoning, districts, permits | none | each portal's open-data terms (see the datasets table below) |
| City permit reports (Socrata, SmartGov, Power BI and city websites; for example Milwaukee, Seattle, Austin, Pleasant Prairie, Sun Prairie) | observed ADU permits | none | public records or portal terms |
| Municipal code hosts (Municode, eCode360, codepublishing) and the Internet Archive | local ADU rules (`scripts/scan_adu_mentions.py`) | none | public law; host terms not checked |
| data.ca.gov (California HCD) and a public Google Sheet (BuildinganADU.com) | California comparison study | none | see the datasets table below |

GitHub's dependency-graph API is used only by `bash scripts/export_sbom.sh` to refresh the SBOM (needs the GitHub CLI signed in); it is not part of building or running the tool.

# Dependency Licenses

[Confirm that your runtime dependencies are permissively licensed and compatible with closed-source downstream integration. Copyleft (GPL, AGPL, LGPL, MPL, EUPL), source-available-but-not-open-source, noncommercial, or unknown-license dependencies must be flagged here and resolved. Your SBOM (exported from GitHub's dependency graph) is the source of truth; summarize any exceptions.]

| Dependency | License | Runtime or dev-only | Notes |
| ---------- | ------- | ------------------- | ----- |
| pandas | BSD-3-Clause | runtime (pipeline) | ok |
| pyarrow | Apache-2.0 | runtime (pipeline) | ok |
| geopandas, shapely | BSD-3-Clause | runtime (pipeline, map geometry) | ok |
| pyogrio, pyproj | MIT | runtime (pipeline) | ok |
| numpy | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | runtime (pipeline, via pandas) | ok; the `CC0-1.0` part covers one bundled component file, not numpy as a whole (numpy's licence expression lists it beside the permissive licences); CC0-1.0 is a public-domain dedication, accepted here only as a component of an otherwise permissive package |
| packaging, python-dateutil, six, tzdata | Apache-2.0 OR BSD-2-Clause; BSD-3-Clause/Apache-2.0 dual; MIT; Apache-2.0 | runtime (transitive) | ok |
| **certifi** | **MPL-2.0 (flagged exception)** | runtime (transitive, `geo` extra) | see "Flagged exception: certifi" below |
| matplotlib | Matplotlib License (PSF-style, permissive) | dev-only (Gate 3 charts, `uv run --with`) | ok |
| maplibre-gl 6.15.0 | BSD-3-Clause | runtime (tool map) | ok; its dependencies are MIT, ISC, BSD-2/3-Clause or MIT OR Apache-2.0 |
| vite 7.3.7 | MIT | dev-only (build, local server) | ok; dependencies MIT, ISC, BSD, Apache-2.0 |
| typescript 7.0.2 | Apache-2.0 | dev-only (type check) | ok |
| @playwright/test 1.63.0 | Apache-2.0 | dev-only (smoke tests) | ok |

Checked 2026-10-25 with `cd ui && npm run licenses` (reads every installed package in `ui/package-lock.json`): 113 npm packages, all MIT, ISC, BSD-2-Clause, BSD-3-Clause or Apache-2.0. Two candidates were rejected for the Gate 4 tool: Observable Plot pulls in d3-delaunay → robust-predicates (Unlicense, a public-domain dedication), so the charts are drawn with dependency-free SVG instead; Vite 8 requires lightningcss (MPL-2.0), so the tool uses Vite 7. The tool loads no basemap or other services at run time. Since 2026-10-26 it self-hosts one font for map labels (Open Sans Semibold glyphs from openmaptiles/fonts, Apache-2.0; see the asset table above); `npm run licenses` also checks that its licence file is present. Open Sans was chosen over Noto Sans because the openmaptiles Open Sans files carry the Apache-2.0 licence, while Noto Sans is under the SIL Open Font License 1.1 (OFL), a font licence rather than a code licence: it is permissive for embedding and redistribution but forbids selling the font alone and restricts reserved font names on modified versions, so it would need a separate review.

**Python check.** `bash scripts/test.sh` ends with `scripts/check_python_licenses.py`, which reads every distribution installed in the uv environment (`importlib.metadata`) and fails on any licence outside the permissive allowlist (MIT, MIT-0, BSD-2/3-Clause, 0BSD, Apache-2.0, ISC, PSF-2.0, Python-2.0, Zlib, BlueOak-1.0.0, Unicode-3.0, HPND; CC0-1.0 only as a component). Run on 2026-10-26: 13 distributions, 12 permissive, 1 flagged exception (certifi), 0 failures. GitHub's dependency-graph SBOM agrees (13 PyPI packages; certifi is the only non-permissive one); the export is committed as [`sbom/sbom.spdx.json`](../sbom/sbom.spdx.json) (SPDX 2.3, 133 packages: 113 npm, 13 PyPI, 7 GitHub Actions and repository entries) and refreshed with `bash scripts/export_sbom.sh`.

**Flagged exception: certifi (MPL-2.0).** certifi is Mozilla's bundle of trusted root certificates (CA bundle) packaged for Python. It is not a direct dependency: `pyproj` and `pyogrio`, which `geopandas` needs for map geometry and projections (the `geo` extra), both declare it as an unconditional requirement, and `pyproj` imports it whenever it is imported, so it cannot be removed while the pipeline uses `geopandas`. Avoiding it would mean dropping `geopandas`, `pyproj` and `pyogrio` and rewriting the geometry and map-outline steps. The exception is justified because:
- MPL-2.0 is a weak, file-level copyleft licence: its obligations apply only to the MPL-licensed files themselves if they are modified and distributed. It does not extend to code that merely uses them, so it places no conditions on this repository's code or on downstream closed-source integration.
- certifi is used unmodified, only as a CA bundle (pyproj and pyogrio point PROJ and GDAL at its certificate file for HTTPS downloads).
- It is a transitive runtime dependency installed by `uv` from PyPI into the user's own environment. It is not copied into, vendored in, or distributed with the submission code, and the interactive tool does not use it at all.

# Generated or Copied Code

[Note any code copied or adapted from external sources, and the license it came under. Ensure attribution requirements (e.g., an entry in NOTICE) are met.]

# Third-Party Datasets

The repository's Apache-2.0 license covers code only. Each dataset keeps its own terms. Raw data is downloaded into git-ignored `data/raw/` and is not redistributed; only small samples (`data/sample/`) and team-built aggregates (`reference/`) are committed. Versions, access dates and URLs are in [DATA_PROVENANCE.md](DATA_PROVENANCE.md); open compliance items are in [DATA_COMPLIANCE.md](DATA_COMPLIANCE.md). "not stated" means no license or terms statement was found.

| Dataset | Publisher | License / terms | Restrictions |
| ------- | --------- | --------------- | ------------ |
| ACS 5-year, TIGER/Line (incl. 2020 tabulation blocks), CBSA, PEP housing units, Building Permits Survey, 2020 place codes | U.S. Census Bureau | Public domain | none |
| IPEDS HD2023 | NCES | Public domain | none |
| BLS CES/PPI, BLS QCEW, FHFA HPI, NTD, USGS NLCD (samples only) | Federal agencies | Public domain | none |
| NASA MODIS land cover (sample only) | NASA | NASA open data, no restrictions | none |
| Microsoft Global ML Building Footprints (sample only) | Microsoft | ODbL | share-alike for derived databases |
| Google Open Buildings (sample only) | Google | CC BY 4.0 or ODbL | attribution; ODbL share-alike if chosen |
| HUD/USPS vacancy | HUD | Restricted to government and nonprofit users | not used |
| Madison permit report, Pleasant Prairie SmartGov report, Sun Prairie Power BI report | Local governments | not stated (public records) | owner and contractor fields dropped; raw not redistributed |
| Madison parcels, address points, zoning | City of Madison | City of Madison open data terms | none known |
| Wisconsin V-series / V12 statewide parcels | Wisconsin DOA / State Cartographer's Office | Public (Wis. Stat. 59.72) | owner fields not used |
| Wisconsin Assembly and Senate districts, 2024 plan (simplified outlines in the tool bundle) | Wisconsin LTSB | open, use at own risk | none known |
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
