# Option D: do the new candidate places fit the 11?

Owner, 2026-11-02: "verify each of the new places you suggested against how close they come to option D. And then
look at all the places we already include in option D and decide if the new suggestions fit that group reasonably
well or not."

- **Option D:** by-right apartment district near stops.
- **District size:** about 15% of ¼-mile lot acres.
- **Density:** at least about 15 homes per acre.
- **Affordability:** no condition.
- **The 11:** district share under 30% (OPTION_D_PLAN.md section 2).
- **Data file:** reference/tod_optiond_candidates.csv (same rows, sources).
- **Research only.** Nothing here changes a line.

## Codes

| # | Code | Values |
|---|---|---|
| 1 | By right: apartments without a case-by-case rezoning | yes / partly / no |
| 2 | Systematic: city mapped several station areas itself | yes / partly / no; station count |
| 3 | District size: share of ¼-mile land upzoned | % (measured for the 11; estimated for candidates) |
| 4 | Density allowed vs 15 homes per acre | zone, height or floor-area ratio (FAR) |
| 5 | Affordability rule in the 5 years after | mandatory / bonus only / none |
| 6 | Transit running in the 5 years after | yes / partly / no (a trait, not a test) |
| 7 | Land mostly former industrial | yes / partly / no (flag only) |
| 8 | Data: lot permits with homes, about 6 years before and 5 after | have / yes / partly / no |

- "Partly" by right: allowed, but design review or a bonus.
- Over 30% district share means "broad", not district-like.
- ¼-mile circle = 125.7 acres; about 94 net of streets.

## The 11 places already in option D

| Place | 1 By right | 2 Systematic (stations) | 3 Share (measured) | 4 Density | 5 Affordability | 6 Transit | 7 Industrial | 8 Data |
|---|---|---|---|---|---|---|---|---|
| New York (pooled) | yes | yes (many) | 7.6% | FAR about 3–7 | bonus only | yes | partly | have |
| Philadelphia | yes | yes, not station-targeted | 1.7% | RM-1, CMX-2 | bonus only (mandate late, 2 districts) | yes | partly | have |
| Austin 2009 | partly | yes (3) | 25.7% | 40–60 ft, bonus to about 85 ft | bonus only | yes (rail from 2010) | partly (rail yard) | have |
| Charlotte 2019 | yes | yes (20) | 20.4% | 50–130 ft, no unit cap | bonus only | yes | partly | have |
| Chicago 2015 | **no** | **no** (site by site) | 3.4% | FAR 3.0 + 0.5 | mandatory | yes | no | have |
| Denver 2018 | partly | yes (1) | 7.1% | 5–8 storeys, 16 with bonus | bonus only (mandate late) | yes | yes | have |
| Portland 2020 | yes | yes, citywide | 24.7% | FAR 1.0–4.0 | mandatory | yes | no | have |
| Seattle Mount Baker | partly | yes (1) | 3.5% | 85 ft | bonus only (mandate late) | yes | no | have |
| Seattle Othello | partly | yes (1) | 7.3% | 65–85 ft | bonus only | yes | no | have |
| Salt Lake City | partly | yes (several) | 14.7% | 75–90 ft, no unit cap | none | partly (rail from 2013) | partly | have |
| Saint Paul | yes | yes (about 10) | 16.1% | 25–75 ft, min FAR 1.0 | none | partly (rail from 2014) | partly | have |

What the 11 have in common:
- All under 30% (the group's rule).
- All allow far over 15 homes per acre.
- 10 of 11: city-mapped. Chicago: site by site.
- 10 of 11: at least partly by right.
- Mixed on affordability: 2 of 11 mandatory.
- Mixed on transit: 2 of 11 rail opened mid-window.
- Mixed on industrial land: 1 mostly, 6 partly.

So the tests that define the group: under 30%, city-mapped, at least partly by right. Affordability, transit and
industrial land vary inside the group, so they are traits.

**Flag on the group itself:** Chicago 2015 is not by right and not city-mapped (the bonus needs a Council rezoning
per site; ordinance SO2015-5334). Portland 2020 and Philadelphia are not station-targeted. They are in by the size
rule. Owner may want to know.

## The 10 candidates

| Place | 1 By right | 2 Systematic (stations) | 3 Share (estimate) | 4 Density | 5 Affordability | 6 Transit | 7 Industrial | 8 Data |
|---|---|---|---|---|---|---|---|---|
| Ottawa TD 2012/2014 | partly | yes (6) | **about 40%+ (2012); 30–45% (2014)** | min 61–142 homes/acre | none | partly (BRT, then closures) | yes | no (0–2 before years; no parcels) |
| Toronto Eglinton 2014 | partly (appeals) | yes (about 8, frontage) | about 8–12% | 4–8 storeys | none | no (buses; LRT 2026) | no | partly (diagrams to digitise) |
| Minneapolis Hiawatha 2005–12 | partly | yes (4–5, staggered) | about 5–8% (38th St west) | 29–62 homes/acre | none | yes | partly | no (units from 2010) |
| Seattle Roosevelt 2012 | partly | yes (1) | about 21% | 65–85 ft | bonus only | no (rail 2021) | no | yes (in repo) |
| New Rochelle 2015 | yes | yes (1) | **well over 30%** | 6–48 storeys | **mandatory 10%** | yes | no | no |
| Phoenix WU 2015 | partly (rezoning per lot) | **mostly no**; 1 city area (2016) | not measured | no unit cap, 30–100 ft | none | yes | partly | yes (in repo) |
| Raleigh TOD 2021–24 | mostly yes | yes (BRT corridors) | 2022: little raised; 2024 up to about 58% | 2022 kept base zones | bonus only | no (BRT not open) | no | no (units missing) |
| SF Market & Octavia 2008 | partly | yes (about 3) | **about 50–80%** | no unit cap, 40–400 ft | **mandatory** | yes | no | yes |
| White Flint 2010 | **no** | partly (1; approvals per owner) | **near 100%** | CR zones, high | **mandatory** | yes | mostly no | partly (units in text) |
| Tysons 2010 | **no** | **no** (4; per owner) | **near 100%** | high | **mandatory (proffers)** | partly (rail 2014) | no | no |

How the shares were estimated:
- **Ottawa:** TD acres ÷ stations ÷ 125.7 (311.6 ÷ 3 = 104; 167.3 ÷ 3 = 56).
- **Toronto:** 81 acres ÷ about 8 stations.
- **Minneapolis:** about 40 parcels × 0.15 acre ÷ 94.
- **Roosevelt:** about 20 acres (city report) ÷ 94.
- **New Rochelle:** 275–280 acres, centred on the station.
- **Raleigh 2024:** 726.5 acres ÷ 10 stations ÷ 125.7.
- **SF, White Flint, Tysons:** plan maps; not measured.

## Verdicts

| Place | Verdict | Reason |
|---|---|---|
| Seattle Roosevelt | **fits with trait flagged** | Like Othello; rail came 9 years later |
| Toronto Eglinton | **fits with trait flagged** | District-sized; no rail; appeals delayed it |
| Minneapolis Hiawatha | **fits with trait flagged** | Small city districts; no usable data |
| Ottawa TD | doesn't fit | Likely broad; too few before years |
| Phoenix WU | doesn't fit | Owner-by-owner rezonings (2016 area may fit) |
| Raleigh TOD | doesn't fit | 2022 raised nothing; 2024 too new |
| New Rochelle | doesn't fit | Broad; mandatory affordability |
| SF Market & Octavia | doesn't fit | Broad; mandatory; partly discretionary |
| White Flint | doesn't fit | Discretionary; whole station area |
| Tysons | doesn't fit | Rezoning per owner; whole area |

- No candidate is a clean "fits the group".
- Only Roosevelt is fit and measurable now.
- Toronto needs its 2014 lots rebuilt.
- Minneapolis needs units before 2010.

## Uncertain verdicts

- **Ottawa:** share is estimated. If measured under 30%, the 2014 step could fit (still too few before years).
- **Toronto:** by-law in force date unknown (Ontario Municipal Board appeals to 2018). Frontage strip, not station circles.
- **Phoenix:** Eastlake-Garfield (case Z-9-16, 2016) was city-initiated. Its share can be computed from repo files.
- **Minneapolis:** only 38th Street west was sized. By-right detail for 2008–2012 not confirmed.
- **Raleigh:** New Bern BRT opening date conflicts across sources (one says about 2030).
- **Roosevelt:** repo inventory says "+79 units"; city documents say about +600 to +880 homes of capacity. Recheck.

## Sources

- Ottawa: [TOD plans 2014](https://documents.ottawa.ca/sites/default/files/documents/tod2_plan_main_en.pdf); [TD zone text](https://documents.ottawa.ca/sites/default/files/zoning_bylaw_part10_section195-196_en.pdf); [Transitway closures](https://amp.cbc.ca/news/canada/ottawa/oc-transpo-transitway-detours-what-you-need-to-know-to-plan-your-commute-1.3129562)
- Toronto: [staff report 2014](https://www.toronto.ca/legdocs/mmis/2014/pg/bgrd/backgroundfile-72097.pdf); [By-law 1030-2014](https://www.toronto.ca/legdocs/bylaws/2014/law1030.pdf); [OMB PL140905](https://www.omb.gov.on.ca/e-decisions/PL140905-JUL-06-2015.pdf)
- Minneapolis: [Goetz et al. 2010](https://hdl.handle.net/11299/101325); [38th St rezoning study](https://silo.tips/download/38th-street-rezoning-study); [Franklin ordinance 2007-Or-031](https://mcclibraryfunctions-stage.azurewebsites.us/api/ordinanceDownload/11490/254665/pdf)
- Seattle Roosevelt: [DPD Director's Report](https://clerk.seattle.gov/~CFS/CF_311833.pdf); [Ordinance 123816](https://clerk.seattle.gov/~archives/Ordinances/Ord_123816.pdf)
- New Rochelle: [Better Cities case study](https://better-cities.org/wp-content/uploads/2021/06/BCP-New-Rochelle-Case-Study.pdf); [NY DEC 2026 notice](https://dec.ny.gov/news/environmental-notice-bulletin/2026-03-25/seqr/city-of-new-rochelle-proposed-2026-downtown-overlay-zone-doz-amendments-and-updated-theoretical-development-scenario)
- Phoenix: [WU code page](https://www.phoenix.gov/administration/departments/pdd/growth-infrastructure/transit-oriented-communities/walkable-urban-code.html); [A.R.S. 9-461.16](https://codes.findlaw.com/az/title-9-cities-and-towns/az-rev-st-sect-9-461-16/)
- Raleigh: [TOD overlay page](https://raleighnc.gov/planning/what-transit-overlay-district); [Z-92-22](https://cityofraleigh0drupal.blob.core.usgovcloudapi.net/drupal-prod/COR22/Z-092-22.pdf); [Z-19-22](https://engage.raleighnc.gov/V8107)
- San Francisco: [Ordinance 72-08](https://sfbos.org/ftp/uploadedfiles/bdsupvrs/ordinances08/o0072-08.pdf); [DataSF permits](https://docs.datasf.org/i98e-djp9)
- White Flint: [Sector plan 2010](https://mcatlas.org/tiles6/07_Master_Plan_Documents/White_Flint_Sector_Plan_2010.pdf); [Montgomery commercial permits](https://data.montgomerycountymd.gov/resource/i26v-w6bd.json)
- Tysons: [PTC zoning](https://www.fairfaxcounty.gov/tysons/zoning-ordinance-amendment); [workforce housing](https://www.fairfaxcounty.gov/tysons/affordable-and-workforce-housing)
- The 11: by-right and systematic checks in the CSV `sources` column; affordability from INCLUSIONARY_CODING.md; shares from reference/tod_station_area_effects_by_city.csv. Chicago bonus: [SO2015-5334](https://archive.metroplanning.org/uploads/cms/documents/so2015-5334.pdf).
