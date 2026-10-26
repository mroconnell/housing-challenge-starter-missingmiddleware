# Modeling Assumptions and Open Questions

Created and last updated: 2026-10-23.

This is the running log of modeling choices, working hypotheses, and research questions for Missing Middleware. The leading proposal is to model housing units authorized by permits, with a separately labeled estimate of completions if the evidence supports it. This choice remains subject to the data audit.

The [project plan](PROJECT_PLAN.md) identifies Wisconsin as the initial state, a five-year modeling horizon, and ADUs, transit-oriented density, and parking reduction as the leading reforms. This log develops unresolved choices within that plan. Record adopted assumptions in [Model and Assumptions](MODEL_AND_ASSUMPTIONS.md) and source details in [Data Provenance](DATA_PROVENANCE.md).

## How to maintain this log

Use stable IDs and one of four statuses: **Open**, **Proposed**, **Adopted**, or **Deferred**. A proposal is not an established fact or an adopted parameter. Keep the rationale and evidence when resolving a question, and record the decision date. Add source geography, period, units, and uncertainty when a numerical assumption is proposed. No numerical conversion rates or policy-effect sizes have been adopted here.

## AQ-001 Choose permits or completions as the primary outcome

**Status:** Proposed. **Added:** 2026-10-23.

**Question:** Should the primary model predict permitted housing units or completed homes?

**Working proposal:** Predict annual housing units authorized by building permits and the cumulative five-year total, comparing each reform with the same no-additional-reform baseline. Count units rather than permit documents or buildings. Treat completions as a possible secondary modeled outcome.

**Rationale from the project discussion:** Permits may provide a clearer, more consistent baseline and an earlier observable response to recent reforms. A completion series can reflect projects already underway before the reform, while projects enabled by the reform may still be in planning or construction. This could leave a short post-reform completion window with little information about the new policy's response. Permit issuance may therefore give us more usable post-reform observations within the same calendar period.

**Evidence needed:** Audit Census BPS and available local permit records for Wisconsin and comparison jurisdictions. Check coverage, unit definitions, reporting changes, ADU identification, and historical availability. The [challenge specification](CHALLENGE_SPEC.md) allows permits, starts, completions, or stock growth if the choice is defined and justified.

**Questions to resolve:**

- Which permit milestone counts: application, entitlement, or building permit issuance? Proposed: building permit issuance; keep the other stages separate.
- How do we handle amendments, duplicate records, renewals, expired permits, and projects that never proceed?
- Can ADUs and the relevant building types be measured consistently across jurisdictions?
- How do we keep gross authorized units separate from net housing-stock additions after demolition or replacement?

**Decision:** Pending the data audit.

## AQ-002 Translate permit cohorts into completed homes

**Status:** Open. **Added:** 2026-10-23. **Depends on:** AQ-001.

**Question:** Can we support transparent assumptions about what share of permitted units becomes completed housing within one through five years?

**Working approach:** Track each permit-year cohort and apply a cumulative completion share at each elapsed year. Define whether same-year completions are included. For a cohort issued in year t, its contribution to cumulative completions by year H would be permitted units in year t multiplied by the share completed by H minus t years after issuance. Sum across cohorts and distinguish modeled results from observed completion records.

**Questions to resolve:**

- What are the cumulative completion shares after one, two, three, four, and five years? They must stay between zero and one and never decrease with elapsed time.
- How do timing and eventual completion rates differ for ADUs, small multifamily buildings, and larger projects, and across markets?
- What share is canceled, expires, or completes after year five? Units unfinished at year five must not automatically be classified as canceled.
- Can local linked project records or California HCD APR support estimates? Audit repeated project reports, stage dates, follow-up length, and transferability to Wisconsin. Recent cohorts without enough follow-up are not evidence of permanent noncompletion.
- Does a reform change construction timing or completion probability as well as permit issuance? If unknown, should both scenarios use common conversion assumptions, with alternatives tested for sensitivity?

**Horizon treatment:** A permit issued late in the five-year forecast has less time to complete before the endpoint. Report completions within the forecast separately from eventual completions of those permits. Keep the pre-forecast project pipeline separate; do not attribute its completions to the new reform without evidence of a policy mechanism affecting it.

**Decision:** Pending evidence. Do not insert an unsupported universal conversion rate.

## AQ-003 Choose the post-reform observation window

**Status:** Proposed. **Added:** 2026-10-23.

**Question:** How much post-reform evidence do we need to calibrate policy response?

**Working proposal:** Seek two to five years of post-reform observations where available, while retaining an adequate pre-reform series. Treat this as a research preference to evaluate, not a universal eligibility rule. Keep the historical observation window separate from the required five-year forecast horizon.

**Rationale from the discussion:** Three years of permit observations after a recent reform may reveal more of the response than three years of completions over the same dates, because completion adds a construction delay. This is a hypothesis to check by project type and jurisdiction. Permits can also lag legislative changes because implementation, design, and approvals take time.

**Questions to resolve:** Which reforms have sufficient comparable observations? Are the latest years complete and reporting definitions stable? How sensitive are results to different start dates, transition periods, and observation windows? Do early permit increases reflect new activity, an existing backlog, or activity brought forward from later years?

**Decision:** Pending comparison-data audit.

## AQ-004 Define when a reform begins and which projects it affects

**Status:** Open. **Added:** 2026-10-23.

Record passage, legal effective date, local implementation, and later amendments separately. Determine which date governs project eligibility. Where possible, distinguish projects applying before implementation from those initiated afterward; a permit issued after a reform does not by itself establish that the reform enabled it. Investigate anticipation and grandfathering rather than assigning every project solely by issuance date.

**Decision needed:** A documented treatment-date and project-cohort rule for each comparison reform.

## AQ-005 Distinguish observed changes from policy effects

**Status:** Open. **Added:** 2026-10-23.

More post-reform permit observations can improve measurement, but a before-and-after increase alone does not establish policy effectiveness. Decide how to address interest rates, construction costs, demand, subsidies, other reforms, and pre-existing trends. Evaluate comparison jurisdictions or other counterfactual methods where evidence permits. Label transferred response assumptions and descriptive evidence explicitly, and test whether reasonable alternatives change the policy ranking.

**Decision needed:** An evidence standard for selecting and transferring policy-response estimates to Wisconsin.

## AQ-012 Keep external economic and construction constraints simple in the MVP

**Status:** Proposed. **Added:** 2026-10-23. **Related:** AQ-005, AQ-006, AQ-008, AQ-010, AQ-011.

**Question:** Should the MVP represent variation in development response with an evidence-informed range around the modeled curve, rather than separately forecasting market conditions, rental returns, interest rates, and construction labor capacity?

**Working proposal:** Concentrate detailed calculations on the provisions that statewide legislation changes. Estimate a central curve for additional permitted units relative to baseline, with lower and upper response paths informed by comparable observed reforms. Explain how the model's inputs and background conditions could move outcomes within or beyond that range, without claiming a precise numerical contribution for each variable. Treat detailed financial modeling and a QCEW-based construction-capacity constraint as candidates for later versions unless evidence shows they are essential to a credible MVP.

**Rationale from the discussion:** More detail can introduce unsupported precision and a large research burden. Many background conditions are outside the scope of the state reform being simulated. A transparent range may communicate their combined influence more credibly than a collection of weakly supported coefficients or forecasts.

**Interpretation and boundaries:**

- Distinguish additional legal capacity from expected permitted units. Legal permission is not a production forecast; the proposed range describes uncertainty in how much development follows the reform.
- Call conditions held outside the policy model background or exogenous assumptions. Being outside legislative control does not establish statistical independence or mean the condition cannot alter a reform's effect. Rental returns may also respond to housing supply; holding them fixed would be an explicit MVP simplification.
- Apply the same background economic setting to baseline and reform cases. Differences should follow the modeled policy provisions, with uncertainty about their response made explicit.
- Simpler forecasting does not remove the need to address market changes and other confounders when selecting historical policy evidence under AQ-005. Raw variation after reforms is not automatically variation caused by those reforms.
- Describe the range as an evidence-informed scenario or sensitivity range unless a statistical interval is justified. Do not present an arbitrary plus-or-minus percentage as observed evidence.
- Avoid counting the same uncertainty twice through both a broad response range and separate input adjustments. Numerical input effects require support; qualitative explanations should identify plausible mechanisms and qualifications without inventing coefficients.

**Questions to resolve:**

- Which comparable reforms and markets establish the central response curve and plausible spread? Record outcome definitions, observation windows, and transferability to Wisconsin.
- Should lower and upper paths be symmetric percentages, asymmetric bounds, or different uptake speeds? Does a percentage around a near-zero response make sense?
- Does the range apply to annual additional permits or cumulative five-year additional permits, and how do the paths remain consistent over time?
- Which inputs change legal eligibility directly, which change the assumed development response, and which are explained qualitatively in the MVP?
- What evidence would justify adding an explicit market, financing, or construction-capacity mechanism later?

**Decision:** Pending scope and evidence review. No percentage, range width, or separate economic-response coefficient is adopted.

## AQ-013 Center California calibration on the January 2020 exemption reform

**Status:** Proposed. **Added:** 2026-10-23. **Related:** AQ-003, AQ-004, AQ-005, AQ-009.

**User direction:** Prioritize the statewide exemption ADU provisions effective January 1, 2020 as a candidate California calibration event. Track the historical provision as Government Code section 65852.2(e), crosswalked to section 66323 after recodification. Do not treat the whole former section 65852.2 as synonymous with the exemption pathway, or treat a section-number change alone as a new policy treatment.

**Evidence checked:** HCD's [December 2020 handbook](https://ahcd.assembly.ca.gov/sites/ahcd.assembly.ca.gov/files/adu_december_2020_handbook.pdf) documents the 2019 package, including AB 68, AB 881, and SB 13, and the statutory exemption provisions. HCD's [current handbook](https://www.hcd.ca.gov/sites/default/files/docs/policy-and-research/adu-handbook-update.pdf) crosswalks former section 65852.2(e) to section 66323. Reconstruct the version actually in force in each observation year; later amendments may change the rights even when the provision retains the same label.

**Observation window (updated 2026-10-23):** Use 2017–2019 as a candidate three-year window before the 2020 package, with earlier years for historical context. Earlier state reforms and local rights already applied. The user supplied California YIMBY’s retrospective, and the source trace recovered a public Building an ADU compilation of HCD-attributed annual jurisdiction counts for 2012–2019 (see AQ-017). This provides aggregate pre-2018 observations; the missing 2017 aggregate series is no longer a blocker to the MVP. HCD's [APR page](https://www.hcd.ca.gov/apr) says downloadable raw APR data starts in 2018; its [Data Strategy, Appendix 1](https://www.hcd.ca.gov/docs/data-strategy.pdf) explains that project-specific reporting for all projects and expanded stage tracking began with the 2018 APR. The historical compilation does not create pre-2018 project records or demonstrate unchanged reporting methods. Reconcile overlap, document the source break, preserve reported low counts, and keep unreported activity distinct from zero.

**Local exposure:** The user identifies Los Angeles as already broadly permissive by around January 2018. Record this as a lead to verify provision by provision, not a settled date or proof that LA was unaffected by 2020. LA's [May 2018 FAQ](https://planning.lacity.gov/ordinances/docs/ADU/faq.pdf) documents state-law changes effective January 1, 2017 and a local ordinance still under consideration. Its [2018 housing progress report](https://planning.lacity.gov/odocument/7b7f2d26-d4a2-428b-8c19-0e846fd443a4/Q3_2018/Q3.pdf) also documents pre-2020 activity but counts applications. Do not substitute those for issued permitted units. Distinguish City of Los Angeles from unincorporated Los Angeles County.

**Model implication:** Estimate response relative to the prior rights in each jurisdiction. Already-permissive places may have less new legal capacity; they are not automatically untreated comparison jurisdictions. California's package includes mechanisms beyond the benchmark's detached/semi-detached ADU permission and parking change. Check whether observations distinguish new construction, conversions, JADUs, legalization, multifamily ADUs, and the specific approval pathway. If pathway is unobserved, label estimates as response to the package rather than an isolated section 66323 effect. Consider 2020 pandemic effects, anticipation, other amendments, and jurisdiction-specific trends when selecting evidence.

**Decision:** Prioritized research event; data comparability, treatment coding, and response estimates remain open.

## AQ-014 Include a Wisconsin pilot with restrictive ADU rights

**Status:** Proposed. **Added:** 2026-10-23. **Related:** AQ-006, AQ-007, AQ-008, AQ-010.

**User direction:** Find a Wisconsin municipality with good permit data and little or no ADU allowance, alongside the Madison data pilot, to illustrate production under restrictive current law and the opportunities a state reform would add.

**Leading restrictive-policy candidate:** New Berlin. Its [published zoning code, accessory dwelling provisions](https://library.municode.com/wi/new_berlin/codes/municipal_code?nodeId=PTIIGELE_CH275ZO_ARTVIIIGEDERE) prohibits detached ADUs and restricts attached family dwelling units through owner occupancy, related occupants, and other standards. Its [official Sheds guidance](https://www.newberlinwi.gov/DocumentView.aspx?DID=502) (an accessory-building guide, not ADU-specific guidance; corrected 2026-10-23) also prohibits ADUs/living quarters within accessory buildings. Check the enacted version and any uncodified amendments at the analysis date before adopting the classification.

**Data readiness:** New Berlin's [2025 Housing Affordability Report](https://newberlinwi.gov/DocumentCenter/View/25878/2025-Housing-Affordability-Report) uses permit records and publishes housing and development summaries. This is not yet an audited ADU permit history. The report's permit/application wording also needs reconciliation. Confirm access to individual records, historical coverage, issuance dates, project descriptions, added dwelling units, and parcel/address links. Search descriptions for in-law/family units as well as ADU. Published application forms and summary tables do not establish a usable record-level dataset.

**Other candidates investigated:** Milwaukee has [digital permit records from 2016 onward in LMS](https://city.milwaukee.gov/cityclerk/records/building-planstax-rolls), but its [current ADU guidance](https://city.milwaukee.gov/dcd/planning/planningadministration/zoningresources/accessory-dwelling-units) describes broad permission under an ordinance effective August 2, 2025. Consider its earlier years for historical comparison after auditing the former rules; do not classify present Milwaukee as a no-ADU city. Neenah publishes [monthly detailed permit records](https://neenahwi.gov/departments/inspections/building-activity-reports/) with permit IDs, parcel/address, issuance dates, categories, valuations, and descriptions. Its 2025 housing study described restrictions, but subsequent policy work means current status needs verification; it is not confirmed as a current restrictive-policy pilot. Longer history and bulk access also need checking.

**Baseline interpretation:** A prohibition on new detached ADUs is not evidence of zero existing ADUs, zero attached units, zero exceptions, or zero informal housing. Verify permitted activity separately from legal capacity. Missing records remain unknown. One municipality illustrates a restrictive-law case; it cannot establish a single statewide Wisconsin baseline. Statewide results must account for the distribution of existing local rights and housing opportunities.

**Pilot selection gate:** Confirm both the policy classification and usable multi-year permit records before selecting the restrictive pilot. Seek at least the permit ID, issuance date, parcel/address, project type/description, added units, and disposition; distinguish zoning approval, application, issuance, and completion. Record whether a field is structured, inferred from text, or unavailable.

**Update (2026-10-23, Gate 1):** New Berlin has no publicly accessible record-level permits. The owner replaced it as the restrictive pilot with a mid-size Wisconsin city that has accessible permit records and no ADU allowance, to be found by searching for permit data first (AQ-021). New Berlin remains a documented restrictive-rules example.

**Earlier decision (2026-10-23):** The user selected New Berlin as the provisional restrictive-policy example alongside Madison. Proceed with its policy and permit-data audit. This selection does not establish permit-data suitability, zero ADU production, or representativeness of Wisconsin as a whole.

## AQ-015 Build the policy catalog around effective provisions and dated evidence

**Status:** Proposed. **Added:** 2026-10-23. **Related:** AQ-004, AQ-009, AQ-013.

**Working approach:** The user supplies a spreadsheet of laws and provisions with source links; the team verifies sources and converts the information into dated model rules. Automated legislative ingestion is optional. Use a stable policy/provision ID and a separate jurisdiction ID. Keep bill identity/session, legislative passage date, signing/chaptering date, legal effective date, operative date where different, local implementation date, and repeal/supersession separate. Allow explicit unknowns; do not guess dates from a bill's year or from a webpage's publication date.

**California date convention from the user:** Ordinary legislation passed in 2017 typically takes effect January 1, 2018; ordinary legislation passed in 2019 typically takes effect January 1, 2020. Use this to guide verification, not automatically populate verified dates. [California Constitution Article IV, section 8](https://clerk.assembly.ca.gov/sites/clerk.assembly.ca.gov/files/ARTICLE_IV_Session_2017-18.pdf) provides the general timing rules and exceptions. Urgency statutes require a stated necessity and two-thirds votes in each house; election, tax-levy, and specified appropriation statutes can also take immediate effect. Check the actual bill and any separate operative or phased implementation provisions.

**Minimum substantive fields:** Jurisdiction/geographic scope; historical and current code citation; prior rule; new rule; eligible parcels/buildings; ADU form; unit count/size; setbacks/height; parking/replacement parking; approval process; occupancy/rental limits; fees; exceptions; effective-from/effective-to; primary-source URL and page/section; retrieval date; verification status and notes. Store historical versions rather than overwriting earlier rules. Separate eligibility provisions from other package features so that evidence can be matched to the benchmark scenario.

**Starting index:** The user supplied the [Mercatus 2025 taxonomy and appendix](https://www.mercatus.org/research/policy-briefs/taxonomy-state-accessory-dwelling-unit-laws-2025#appendix). Use it to identify and organize source laws, then cite the enacted text and contemporaneous agency guidance for rule coding. The appendix is selective: its California row includes SB 13 (2019) but does not list AB 68 or AB 881. Add the relevant 2019 package from HCD's contemporaneous guidance rather than treating the appendix as an exhaustive catalog. Distinguish legislative year from effective year throughout.

**Decision (updated 2026-10-23):** Started the [Policy Catalog](POLICY_CATALOG.md) as a Markdown legislation register with 15 California ADU bill entries and source/status notes. Added the further policies identified in the California YIMBY report and checked legislative versus effective years against official guidance where available. The register is ready to transfer into the planned spreadsheet; a full provision-level or municipality-year policy panel remains unfinished.

## AQ-016 Investigate Menlo Park as a California ADU fee-barrier example

**Status:** Proposed. **Added:** 2026-10-23. **Related:** AQ-005, AQ-009, AQ-013, AQ-015.

**User direction:** Include Menlo Park as a California comparison candidate, with the user's report of approximately $50,000 in impact fees as the research lead. The amount, applicable years, covered projects, and fee components have not been independently verified. Do not enter it as a verified historical or current fee, or as an adopted model parameter.

**Evidence to acquire:** Dated city fee schedules, ordinances/resolutions, contemporaneous staff reports or project-level fee calculations, and ADU permit records covering the relevant policy periods. Record whether the reported amount describes impact fees alone or includes permit, utility/connection, school, or other charges; identify the agencies imposing each component. Check ADU size/type, exemptions, waivers, and applicable state-law changes before assigning a fee to a project or year.

**Model relevance:** A candidate for understanding how fees constrained ADU development and how the California reform package changed those constraints. Compare prior and subsequent rights and charges rather than treating all California jurisdictions as exposed to the same change. A fee change coinciding with other reforms does not by itself identify the separate effect of fees. Keep this historical fee lead separate from the challenge's standardized $50,000-per-unit baseline and 50% fee-reduction scenario; matching dollar amounts do not establish matching policies or evidence.

**Decision:** Menlo Park added to the comparison shortlist at the user's request. Verification of the fee history, effective dates, permit-data coverage, and usefulness for calibration remains open.

## AQ-017 Use recovered historical California ADU counts for the MVP

**Status:** Adopted for descriptive historical input; calibration method remains open. **Added:** 2026-10-23. **Related:** AQ-001, AQ-003, AQ-005, AQ-013, AQ-015, AQ-016.

**User direction:** Use the long historical ADU series identified in California YIMBY's report for the MVP, trace its underlying sources where possible, and otherwise cite the report.

**Report:** M. Nolan Gray, California YIMBY, [California ADU Reform: A Retrospective](https://cayimby.org/wp-content/uploads/2024/01/CAY-ADU_Report-2024-v4.pdf), January 2024. Printed page 4 (PDF page 5) shows the statewide 2012–2022 permit chart; printed page 5 (PDF page 6) shows Los Angeles. These are charts, not complete numerical tables. Footnote 3 explicitly says the author combined two HCD datasets and preferred Housing Element Implementation data in overlapping 2018–2019. The embedded source link points to the former HCD APR dashboard URL, now returning 404; the [current dashboard and downloads page](https://www.hcd.ca.gov/housing-open-data-tools/apr-dashboard) identifies the successor source. The report does not name or directly link a recoverable older agency file. Cite the report for its compilation choices, without claiming its exact underlying files have been reproduced.

**Historical source recovered:** [Building an ADU's California charts page](https://www.buildinganadu.com/california-adu-charts) attributes its data to HCD and links the public [California ADU Permits by City from 2012–2019 spreadsheet](https://docs.google.com/spreadsheets/d/10rb8p7DU379vQw9oeS_Z9dwK9F9c5ZBeTw09wQlvwQY/edit). On 2026-10-23 the team read Sheet1, columns A–I: 527 jurisdiction rows, eight annual permit-count columns, with a BuildinganADU.com compilation credit. This is an accessible HCD-attributed third-party compilation; it is not a recovered agency-hosted original or proven to be the exact early file used by Gray. Preserve the compiler's attribution as well as HCD's upstream attribution.

**Recovered annual counts:** Statewide values below are team sums across the 527 published jurisdiction rows; city values are the named rows. Do not add the statewide total to jurisdiction rows. Los Angeles city and Los Angeles County are separate source rows; confirm county coverage before any geographic aggregation beyond reproducing the published compilation.

| Year | California: sum of published rows | City of Los Angeles | Menlo Park |
| --- | ---: | ---: | ---: |
| 2012 | 158 | 0 | 0 |
| 2013 | 745 | 15 | 0 |
| 2014 | 728 | 71 | 2 |
| 2015 | 1,109 | 97 | 7 |
| 2016 | 1,269 | 80 | 4 |
| 2017 | 4,974 | 2,342 | 5 |
| 2018 | 8,900 | 4,079 | 15 |
| 2019 | 14,702 | 6,747 | 4 |

**Use in the MVP:** Accept the recovered historical series as descriptive evidence and a candidate aggregate pre-period. Prefer current HCD APR/implementation data for 2018 onward after checking definitions and reconciling overlap; preserve both versions instead of silently overwriting them. Attach source/version/retrieval date to each observation. Cite Gray's report for report-specific figures and its historical synthesis; do not label the older 2018–2019 compilation as reproducing the report's preferred overlap values. Keep permits separate from applications and completions. Published early zeros remain reported values, not independently verified proof of zero construction; completion data absent from early charts is missing, not zero.

**Interpretation:** Low reported early activity supports a practical descriptive baseline input, but low counts alone do not establish complete reporting or identify the effect of the 2020 exemption provisions. Preserve the nonzero 2017 rise and assess pre-existing trends and policy exposure. The historical city-year counts cannot support pre-2018 parcel-level analysis, exemption-pathway identification, or linked permit-to-completion estimates. No causal effect, transfer rate to Wisconsin, or completion share is adopted here.

**Local research snapshot:** A CSV of the recovered 527-row table and a provenance sidecar were saved in this chat's work folder, outside the repository. No production data pipeline or repository dataset was added.

**Decision:** Historical aggregate input accepted for MVP use with explicit provenance and a documented reporting break; exact source-vintage reconciliation and behavioral calibration remain open.

## AQ-018 Report housing growth for areas rather than individual lots

**Status:** Adopted presentation principle; geographic resolution and allocation method remain open. **Added:** 2026-10-23. **Related:** AQ-006, AQ-007, AQ-008, AQ-010, AQ-011.

**User decision:** Estimate the aggregate number of ADU units likely to be permitted in a neighborhood, region, or map cell. Do not display predictions that particular lots will or will not develop an ADU.

**Map outputs:** Show existing inventory, projected current-law growth, and additional growth relative to that baseline for the same geography and time horizon. Label expected units and uncertainty ranges explicitly. Keep observed permit locations distinct from projected area totals. Parcel information may establish inventory and legal opportunities internally; it does not establish an owner's participation decision.

**Method to choose:** Allocate modeled growth using a documented relationship to eligible single-family inventory, with other geographic differences only where evidence supports them. Choose neighborhoods, regions, or grid cells according to available data and the resolution the model can support. The mockup's 500 m cells are illustrative, not an adopted analytical scale. Test whether reasonable aggregation choices materially change the apparent pattern. Reconcile area totals to the overall scenario totals and propagate shared uncertainty consistently.

**Data acceptance criteria for parts 1–4:** Retain stable parcel/geographic identifiers and boundaries, useful permit location fields, and the links needed to aggregate inventory, policy exposure, and historical activity to common areas. Document unmatched records and spatial coverage; missing locations are not zero activity.

**Decision:** Area-level forecasts adopted for the MVP map. No lot-level participation predictions, geographic resolution, numerical spatial weights, or uncertainty widths adopted.

## AQ-019 Build toward a state-first product through sequential scenario MVPs

**Status:** Adopted. **Added:** 2026-10-23. **Related:** AQ-001, AQ-007, AQ-009, AQ-010, AQ-012, AQ-018.

**User decision:** The finished tool starts with Wisconsin housing conditions and statewide projections. Specific jurisdictions are drill-downs and development pilots. First build the ADU pilot, then expand it to a statewide ADU MVP, iterate until the owner judges it good enough, and only then build MVPs for other scenarios. After those MVPs demonstrate the right approach, deepen components and apply lessons across scenarios. Sequence by evidence and checkpoints, without a date or effort cap.

**Statewide design implication:** Reuse the pilot's software and data contracts, but do not simply multiply two cities' results. Build statewide coverage tracking and aggregation interfaces from the start. Statewide methods must address variation in existing rights, single-family opportunities, relevant development context, and missing evidence; determine defensible grouping and pooling through research and validation. Missing local legal evidence cannot silently become a verified eligibility classification. Communicate reliance on assumptions and its contribution to uncertainty.

**Competition standard:** Evaluate each MVP against transparency, replicability/scalability, usability, methodological soundness, and policy insight. The saved handbook prioritizes state/regional breadth and justified assumptions over parcel precision. An ADU-only MVP is an intermediate product; the final submission still requires statewide impacts and at least three benchmark scenarios. Do not adopt a new causal-study requirement merely to increase complexity; choose evidence and methods that support defensible policy interpretation.

**Decision:** State-first destination and the pilot-to-statewide-to-additional-scenarios sequence adopted. Geographic pooling, response parameters, and the criteria for each numerical validation remain to be specified and reviewed.

## AQ-020 Use agent self-assessment followed by concrete owner gates

**Status:** Adopted. **Added:** 2026-10-23. **Related:** AQ-011, AQ-019.

**User decision:** Use multiple local agent sessions and meaningful checkpoints. Agents first assess each milestone, repair failures, and answer the review questions themselves. They then provide the owner with literal step-by-step instructions, evidence, expected behavior, uncertainties, and the decision requested. Agent self-assessment does not replace the owner's gate decision.

**Working agreement:** Development executes locally. The owner authorizes competent routine GitHub pushes without further approval. Group commits, integration/merges, and explanatory comments around coherent work and milestones that outside observers can understand. PRs and elaborate isolation are optional. Coordinate file ownership and shared interfaces to prevent avoidable collisions and preserve unrelated local work.

**Execution artifact:** See the [MVP Execution Plan](MVP_EXECUTION_PLAN.md) for agent work packages, dependencies, five gate packets, owner review steps, and later scenario/refinement cycles. No gate is considered passed merely because code exists, tests pass, or the owner has not replied.

**Decision:** Agent self-check plus owner review adopted. Detailed implementation work follows the plan's dependencies and review decisions.

## AQ-021 Gate 1 decisions on the ADU model

**Status:** Adopted. **Added:** 2026-10-23. **Related:** AQ-001, AQ-006, AQ-007, AQ-014, AQ-018, [Gate 1 packet](gate1/README.md).

**Owner decisions (2026-10-23):**

- **Dates (D2):** stylized convention. The reform takes effect at the start of forecast year 1; forecast years 1–5 are labeled 2027–2031; current local law is frozen as of 2026-10-31; an implementation lag is a sensitivity.
- **Denominator (D4):** ACS one-unit detached homes are the control total for every rate; parcel and assessor data only allocate within areas and establish eligibility.
- **Production (D5):** new detached and attached ADUs are the headline; conversions are reported separately; legalizations are excluded. The owner also proposed an **ADU-equivalent** rule: a permit adding a dwelling unit on a parcel that already has a dwelling. Adopted as the classification rule for permit records that lack an ADU label (common where ADUs are not a recognized use), applied after parcel matching and audited on a sample.
- **Restrictive pilot (D6, revised):** replace New Berlin with a mid-size Wisconsin city that has accessible record-level permit data and no ADU allowance. Search for permit data first, because it is the rarer condition. New Berlin remains a documented restrictive-rules example without a permit baseline.
- **Schedule (D7):** sequence matters, not calendar dates. The compressed calendar in the Gate 1 packet is withdrawn.
- **Repository (D8):** routine milestone work lands on `main`.

**Decision:** Adopted. D1 and D3 are recorded in AQ-022 and AQ-023.

## AQ-022 Model the benchmark without poison pills

**Status:** Adopted. **Added:** 2026-10-23. **Related:** AQ-009, AQ-015, AQ-021.

**Owner decision (D1):** The modeled statewide bill allows one ADU on every single-family parcel, detached or semi-detached, at least 600 sq ft, with no additional parking, **and no owner-occupancy or related-occupant requirement**. The intent is a bill that policymakers can implement without the restrictions the Mercatus taxonomy identifies as poison pills. Local owner-occupancy, related-occupant, and similar rules are therefore removed by the reform wherever they exist.

**Model implication:** The headline reform class is `compliant`. The "form-only" variant (forms allowed but occupancy rules remain) is kept only as an optional sensitivity to show why the poison-pill provisions matter; it is not a headline scenario.

**Decision:** Adopted.

## AQ-023 Treat unknown local ADU rules as no ADU rights for the MVP, and report baseline "health" consistently across scenarios

**Status:** Adopted for the MVP; refinement deferred. **Added:** 2026-10-23. **Related:** AQ-006, AQ-019, AQ-021.

**Owner decision (D3):** Where no ordinance has been coded, assume ADUs are not allowed: the statewide reform flips them from off to on. Code the largest jurisdictions and the known recent liberalizers, then spot-check. Systematic ordinance coding is deferred until after MVPs of the other scenarios, which face the same coverage problem.

**Owner framing:** Present each scenario against a baseline "health" reading (baseline ADUs, baseline TOD, baseline middle housing): current production and stock indicators for every area, not only whether a permissive policy exists. Like a doctor starting from a patient's current health rather than their stated diet, the tool should show where outcomes are weak even where rules look permissive. The few large cities that already allow ADUs should see a mitigated, not necessarily zero, benefit.

**Conductor interpretation for the MVP (pending owner confirmation):**

- Baseline health indicators (e.g., ADU permits per 1,000 single-family homes, recent trend) are shown for every area in every scenario, using the same layout across ADU, TOD, and middle-housing scenarios.
- The reform's *permit* effect still comes from rights the bill changes, so a statewide bill is not credited with permits that local rights already allowed. Already-permissive cities receive a reduced effect equal to the rights the bill still adds there (for example districts where ADUs are not listed, size or lot limits below the benchmark, conditional-use steps, and the protection of a state guarantee against local rollback), represented as a residual share with a range that includes zero.
- Where health indicators show weak outcomes despite permissive rules, the tool says so and identifies non-zoning barriers (cost, financing, fees, awareness) as complementary measures, without attributing their effect to the zoning bill.

**Bias note:** Treating every uncoded municipality as prohibiting ADUs overstates the reform's effect wherever local rules are already partly permissive. The coded largest jurisdictions limit this; the remaining bias is reported as a stated limitation and checked by the later spot-check.

**Decision:** Unknown = prohibited for the MVP; largest-jurisdiction coding plus spot-checks; consistent baseline-health presentation across scenarios. The owner confirmed the residual-effect interpretation for already-permissive cities on 2026-10-23.

## AQ-024 Use Madison as the lower path and separate models for central and upper paths

**Status:** Adopted direction; calibration at Gate 3. **Added:** 2026-10-23. **Related:** AQ-012, AQ-022, AQ-023.

**Owner direction:** Treat Madison as the reference floor: under the statewide bill, every Wisconsin municipality becomes at least as permissive as Madison and is expected to produce ADUs at least at Madison's observed rate per one-unit detached home. The central and upper paths each come from a different predictive model.

**Working design for Gate 3:**

- **Lower path:** Madison's observed post-reform rate (ADU permits per 1,000 one-unit detached homes per year), with the baseline period fixed before results are seen.
- **Central path:** a separate model built from comparison places with post-reform evidence (for example Massachusetts, Austin, Minneapolis, New Hampshire), with its method and inputs documented.
- **Upper path:** a separate model reflecting a stronger, California-like response, with its method and inputs documented.
- Paths remain one coherent scenario each, applied to all areas together.

**Owner rationale (2026-10-23):** A single-city reform does not catalyze the adoption a statewide reform does. After statewide reform, contractors, lenders, architects, and other professionals specialize in ADUs and market and educate well beyond what one city's reform produces, so Madison's single-city rate is a conservative floor rather than an aggressive one. Very large cities (for example Los Angeles) can attract specialized ADU markets on their own; statewide reform amplifies the effect rather than being its only source. Gate 3 will look for evidence of this statewide market-development effect (for example California after 2017–2020, Oregon and Washington state laws, Massachusetts 2025) and describe it as a stated mechanism with its evidence status.

**Conductor caution:** Madison is Wisconsin's strongest ADU market (high rents, promotion, by-right rules since 2021). Using its rate as a statewide floor may overstate uptake in weaker or rural markets. Gate 3 will show a market-adjusted variant as a sensitivity so the owner can see how much the floor assumption drives the statewide total.

**Decision:** Direction adopted; numerical values, baseline period, and the two predictive models are Gate 3 decisions.

## AQ-025 Treat production-killing provisions as the core of the rights comparison

**Status:** Open; to be developed when rights are coded for the model (Gate 3). **Added:** 2026-10-24. **Related:** AQ-009, AQ-022, AQ-023, AQ-024.

**Owner direction:** Study the challenge ADU scenario closely, then analyze policy nuance. ADUs are often nominally allowed while provisions all but stop production, notably owner-occupancy requirements and the approval pathway. Whether a city approves ADUs ministerially (by right, staff-level, no hearing) or through discretionary review (conditional or special use, plan commission) may be the single biggest difference between a statewide ADU law and current local rules.

**Current evidence (2026-10-24):** Of the 37 coded municipalities ([WI_ADU_RULES.md](gate2/WI_ADU_RULES.md)), 11 have ongoing owner-occupancy requirements and 7 require discretionary (conditional-use or plan-commission) approval; 17 approve ministerially. These are now coded as `approval_pathway` and the `discretionary_review` restriction flag (AQ-026).

**Next steps:** read the benchmark text for what it implies about approval (it says "allow" and is silent on process); add a normalized approval-pathway field (ministerial / discretionary / unknown) to the rule coding; decide whether the modeled bill requires ministerial approval (consistent with the no-poison-pills decision in AQ-022); and test whether rights classes split by approval pathway explain differences in observed ADU rates.

**Decision:** Pending Gate 3.

## AQ-026 Two-pass rights classification with restriction flags

**Status:** Adopted. **Added:** 2026-10-24. **Supersedes:** the rights-class table in [SCOPE_AND_MODEL.md](gate1/SCOPE_AND_MODEL.md). **Related:** AQ-022, AQ-023, AQ-025.

**Owner decision:** Classify local ADU rules in two passes.

1. **First pass, ordinance status:** a simple classifier of whether the code has an ADU ordinance: ADUs mentioned and allowed in some form, ADUs prohibited, or ADUs unmentioned (plus "could not access" when the code host blocks reading).
2. **Second pass, rights class:**

| Class | Meaning | Example |
| --- | --- | --- |
| `scenario_benchmark` | Benchmark rights already granted by right | Madison since Dec 2021 (owner occupancy removed Apr 2024) |
| `restricted` | Some ADU form allowed, with one or more binding restrictions, recorded as flags | New Berlin (attached in-law unit only, related occupants, owner occupancy) |
| `prohibited_explicit` | The code expressly bars ADUs or living space in accessory buildings | Pleasant Prairie §420-30B; Howard §50-868 |
| `prohibited_implicit` | The code permits only listed uses and forms, and ADUs are not listed, so silence is a prohibition | To be identified in the second pass |
| `no_zoning` | No municipal or county zoning applies; building code and septic rules only. The reform adds no zoning rights; originally additional = 0, but the owner revised this (AQ-035, G3-5): unzoned towns get their own predicted rate (statewide-industry effect), about +60 on the central path. Septic and building limits are a stated limitation. 239 towns are unzoned ([WI_UNZONED_TOWNS.md](gate3/WI_UNZONED_TOWNS.md)) | Rural towns without county or town zoning |
| `undetermined` | Not yet coded, or the ordinance could not be found (recorded as such, never replaced) | Most small municipalities at MVP stage |

**Restriction flags** (any combination): a flag applies only when the provision prevents a benchmark ADU (detached or attached, at least 600 sq ft, by right, no extra parking, no occupancy rule) on at least some single-family lots. An absolute size cap of 600 sq ft or more is not a restriction; a percent-of-house, FAR, or coverage cap that can fall below 600 sq ft is (owner clarification, 2026-10-24). Flags follow the Mercatus 2025 taxonomy (Hamilton and Peterson), whose core barriers are the three "poison pills" plus allowing both attached and detached forms:

- *Tier 1, poison pills and form:* owner occupancy; related occupant; extra parking (more than the house alone, including replacement parking); discretionary review; form limited (attached-only, detached-only, or conversions only).
- *Tier 2, design, siting, and cost:* size below benchmark; siting limits (setbacks, height, separation that prevent a 600 sq ft detached unit on typical lots); minimum lot size; district limited; ADU-specific fees; other. The former `forms_with_occupancy_limits` class becomes a `restricted` reform class with the occupancy flags in the form-only sensitivity.

**Towns:** In Wisconsin a town is under county general zoning only where the county has adopted general zoning and the town board has approved it (Wis. Stat. 59.69); a town with village powers may adopt its own zoning. A town is `no_zoning` only when neither applies.

**Modeling:** `undetermined` is modeled as no ADU rights for the MVP (AQ-023). Reform effects for `restricted` places can later vary by which flags the reform removes (AQ-025).

**Decision:** Adopted 2026-10-24.

## AQ-027 Gate 3 design inputs: spillover, path ramps, and unknown-rules behavior

**Status:** Adopted direction for Gate 3; numbers and methods to be specified there. **Added:** 2026-10-24 (owner, in the model-tutoring thread). **Related:** AQ-012, AQ-023, AQ-024, AQ-026, [SCOPE_AND_MODEL.md](gate1/SCOPE_AND_MODEL.md).

1. **Statewide market spillover.** Identical local rules do not mean zero additional permits. Where a city already has benchmark rules but surrounding jurisdictions do not, statewide implementation still raises its ADU production: contractors, lenders, designers, and other vendors specialize and market ADUs once a statewide or regional market exists (see AQ-024). Gate 3 adds an explicit spillover term for `scenario_benchmark` places (for example Madison and Wauwatosa), separate from the rights-change term, with its own evidence and range. This replaces the Gate 1 rule that reform equals baseline wherever classes match; the no-double-counting principle still applies (spillover is not added on top of a rights-change effect already calibrated on statewide-reform evidence that includes it).
2. **Paths.** Lower, central, and upper paths keep moving together across areas, but may differ in ramp speed as well as plateau (for example the upper path ramps faster), as the evidence indicates.
3. **Unknown rules.** `undetermined` places should behave more like `restricted` than `prohibited` (supersedes the AQ-023 MVP default once Gate 3 specifies the restricted-class rate). Hold out a sample of coded places to test this assumption, and later fit a simple regression of observed permit rates on rights class, restriction flags, and context.
4. **Baseline ramp for recently liberalized places (`g` in the baseline equation).** The owner flagged this as important; Gate 3 will show it worked through for Milwaukee (liberalized 2025-08-02) and other 2024–26 reformers.

**Decision:** Direction adopted; Gate 3 specifies the spillover evidence, ramp shapes, restricted-class rate for unknowns, the hold-out design, and the Milwaukee baseline ramp.

## AQ-028 Outcome-based increment, and stock-gap baselines across scenarios

**Status:** Adopted direction for Gate 3 (outcome-based increment); stock-gap approach proposed for all scenarios. **Added:** 2026-10-24. **Related:** AQ-023, AQ-024, AQ-026, AQ-027.

**Owner direction (outcome-based increment):** Answer the legislator's question directly: additional units = homes × (y − x), where y is the expected permit rate per single-family home after the statewide law (Madison as the floor, plus statewide spillover, AQ-024 and AQ-027) and x is the rate a place produces today. Do not model a "share of the way to the benchmark" rights fraction. Where x is observed (Madison, Pleasant Prairie, Sun Prairie, and any place added later), use it. Where it is not (most municipalities), estimate x from the place's ordinance status and the coded places with observed permits, as in the Gate 1 "Case C" calculation, labeled as estimated. Detailed restriction flags (AQ-026) explain results; they are not separate multipliers. Detailed coding beyond the 37 largest places is deferred.

**Owner proposal (stock-gap baseline, all scenarios):** Use a snapshot of existing housing as a "health" baseline: compare a place's current stock (for ADUs, the share of single-family lots with a second dwelling; for middle housing, 2–4 unit buildings; for TOD, units within a distance of qualifying transit) with the level found where rules are healthy, and treat the difference as the room a reform has to work with. This is likely the main approach for TOD.

**Conductor notes for Gate 3:**

- A stock gap shows how much room there is, not how fast it closes; turning it into five-year permits still needs a closing rate from flow evidence (permits after reform). Proposed: permits drive the five-year ADU forecast; the stock gap is the health diagnostic and a sanity check that forecasts do not exceed plausible headroom.
- ADU stock is hard to observe: ACS counts a detached ADU as a separate one-unit structure and an attached ADU can make a building "2 units", which mixes ADUs with duplexes; Wisconsin V12 parcels have no dwelling count, and Madison's assessor counts a house plus ADU as one dwelling. Middle housing and TOD stock are much easier to measure from ACS and block counts.

**Decision:** Outcome-based increment adopted for Gate 3. Stock-gap baseline adopted as the shared health diagnostic; its role in each scenario's forecast is decided per scenario.

## AQ-029 Madison is partially benchmark; scale its floor rate by benchmark completeness

**Status:** Proposed for Gate 3. **Added:** 2026-10-24. **Related:** AQ-024, AQ-026, AQ-027.

**Evidence (2026-10-24, City parcel and TOD-overlay layers):** of Madison's 49,780 single-family parcels, about 8% are zoned Planned Development, where ADUs are not listed and depend on each development's plan; 78% lie outside the TOD overlay, where the house still needs one parking space, so a garage conversion that removes it triggers replacement parking. Of 47 ADU permits matched to parcels, 26 (55%) are inside the overlay, which holds 22% of parcels; 4 of the 6 conversions are inside it. The overlay also covers older, higher-demand neighborhoods and dates only from January 2023, so this is suggestive, not causal.

**Owner view:** Madison is not 90% benchmark; it is partially benchmark, with Planned Development parcels excluded and a parking restriction affecting most single-family lots for some ADU forms.

**Proposal:** estimate Madison's benchmark completeness as `1 − PD share − (share outside TOD × share of ADU demand that would be conversions)`, and scale Madison's observed rate up by it when Madison sets the statewide floor for `y`. The conversion share is the key unknown: Madison's TOD-overlay ADUs are about 15% conversions (4 of 26); California's share after its 2020 ban on replacement parking is a candidate upper value if HCD APR identifies conversions. With a 15–40% conversion share, completeness is about 60–80%. Also proposed: the modeled bill bans replacement parking for converted garages, as California did in 2020 (owner decision pending).

**Decision:** Pending Gate 3.

## AQ-030 Read the benchmark's ADU forms and parking narrowly; Madison is 80% benchmark

**Status:** Adopted. **Added:** 2026-10-24. **Related:** AQ-022, AQ-025, AQ-029.

**Benchmark text (official handbook, checked 2026-10-24):** "Model the effect of allowing one ADU on parcels with existing single-family buildings. Assume detached and semi-detached ADUs of at least 600 square feet are allowed, and no additional parking is required." The text is silent on conversions, owner occupancy, approval process, fees, and setbacks.

**Owner decisions (2026-10-24):**

- **Forms covered:** new detached ADUs, new semi-detached (attached, with their own entrance and walls) ADUs, and conversions of garages or other accessory buildings, which produce detached ADUs. Interior conversions (basement, attic, part of the house) are not required by the benchmark; they remain under current local rules, appear in the baseline where allowed, and receive no reform uplift.
- **Parking:** "no additional parking is required" includes no replacement parking for the house when a garage is converted (as California required from 2020).
- **Madison completeness:** treat Madison as 80% of benchmark (AQ-029). When Madison sets the statewide floor for `y`, its observed rate is divided by 0.8.

**Decision:** Adopted; listed as an office-hours question for confirmation.

## AQ-031 Estimate ramp and spillover from a clean California comparison study

**Status:** Adopted direction for Gate 3. **Added:** 2026-10-24 (owner, in the model-tutoring thread). **Related:** AQ-013, AQ-017, AQ-024, AQ-027.

**Owner direction:** For the MVP, take ramp-up evidence from a straightforward comparison inside California: jurisdictions that were already permissive versus those that were restrictive, before and after each statewide reform wave (effective 2017-01-01, 2018-01-01, and 2020-01-01), using HCD-attributed data for 2012–2025 (the 2012–2019 compilation and HCD APR from 2018, overlap reconciled per AQ-017).

- **No COVID adjustment to the ramp.** The owner regards an ad hoc pandemic correction as arbitrary specification search. The comparison group absorbs shocks common to all jurisdictions. Any check that excludes 2020 must be specified before results are seen and shown only as a sensitivity.
- **Spillover:** the same study tests the AQ-027 spillover claim, whether already-permissive jurisdictions also rose after the statewide laws.
- **Later:** add other places (Portland earlier; states that reformed after California) to strengthen the ramp.
- Keep the analysis descriptive and pre-specified: define permissive and restrictive groups, outcome (ADU permits per 1,000 single-family homes), windows, and comparisons before running them.

- **Different doses by wave:** SB 1069/AB 2299 (effective 2017: ministerial approval, conversions, parking caps); SB 229/AB 494 (effective 2018, a smaller cleanup); and the 2019 package (effective 2020: the 65852.2(e)/66323 exemption floor, SB 13 fee limits and the owner-occupancy pause). Code each wave clause by clause and check that the 2016 bills explain the 2017 rise.
- **Additional check:** Madison versus Sun Prairie (same housing market, different rules) as a Wisconsin difference-in-differences check on the central path.
- **Fire rebuilds (owner caution, 2026-10-24):** after major wildfires, many owners rebuilding a home also permit an ADU at the same time (in Santa Rosa after 2017, roughly 15% of new-home permits, per the owner). Rebuild-area jurisdictions (Santa Rosa, Sonoma, Napa, Butte/Paradise, Ventura, Malibu, Los Angeles 2025, and others) show ADU rates that zoning reform made possible but that a rebuild wave triggered; Wisconsin would not see that trigger without a comparable disaster, so these places overstate the transferable response (owner correction). Check: none are in the wave-3 restrictive group that sets the central level; several are in the permissive and middle groups (spillover, upper path), and Santa Rosa is a holdout place, which explains part of its large holdout miss. A fire-rebuild exclusion is deferred to a future refinement, not run in the first pass (owner decision, 2026-10-24).
- **Owner prior, for comparison only (not an input):** from ADU market experience, the owner expects prohibited places to run well under 0.1 ADU permits per 1,000 one-unit detached homes a year, and benchmark-law places somewhat above 2 per 1,000. This is well above the 0.3 used in the Gate 1 illustrations; Gate 3 reports where the evidence lands relative to it.

**Decision:** Adopted direction; group definitions and windows to be pre-registered in the Gate 3 plan.

## AQ-032 Count second homes on single-family lots; prefer uniform cross-state measures

**Status:** Adopted for now; to be revisited once data limits are clearer per scenario. **Added:** 2026-10-24. **Related:** AQ-021, AQ-028, AQ-030.

**Owner decision:** The headline outcome is **second homes on single-family lots** (tentative name): any legally permitted permanent dwelling with its own kitchen added on a lot that already has a single-family home, whether labeled an ADU, a single-family-to-duplex conversion, or a California SB 9 second home. The distinction between those labels does not matter to the owner; components stay visible as separate lines.

**Guardrails:**

- The same definition applies in every comparison state (California counts ADUs plus single-family-to-duplex conversions and SB 9 second homes where APR allows), so the comparison is not inflated.
- The lot must already have a home; a new two-unit building on a vacant or cleared lot is ordinary new construction, even if its permit says "ADU". The ten Madison "twin home ADU" permits are resolved on this rule using parcel year-built and raze permits.

**Method preference:** A clean, uniform approach that works the same way in every state and scenario is preferred over city-by-city or form-by-form linguistic coding. Ideal: one national data family (Census BPS and ACS, or similar) that measures second dwellings on single-family lots and units per lot or area near transit, giving one health-baseline method for all scenarios.

**Conductor note on feasibility:** BPS records new units by building size, not whether a lot already had a home, and ACS measures stock by structure type, not lots; neither flags a second home on a single-family lot directly. Gate 3 will assess what uniform measures are possible (for example ACS 2-unit and one-unit-attached stock shares as health indicators; BPS one- and two-unit flows; Decennial block counts with transit stops for TOD) and use local permit records only where no uniform measure exists.

**Decision:** Adopted tentatively; revisit after the scenario MVPs.

## AQ-033 Gate 2 decisions

**Status:** Adopted. **Added:** 2026-10-24. **Related:** [Gate 2 packet](gate2/README.md), AQ-029 to AQ-032.

The owner accepted every Gate 2 recommendation: the data is fit for Gate 3 (G2-1); context groups as revised (G2-4); Appleton coded `scenario_benchmark` on its 2026-10-14 guide, as a source lead until the codified §23-43(i) is read (G2-6); California comparison data accepted with its stated limits (G2-7); the amended California comparison plan approved (G2-8); and Madison's floor uses 2022–2025, with 2026 only as a sensitivity (G2-9). The owner confirmed Pleasant Prairie §420-30B on the primary ecode360 page (G2-5), so Pleasant Prairie is now `coded_verified`.

**Decision:** Gate 2 passed 2026-10-24.

## AQ-034 Market-adjusted regression and out-of-state cities (Gate 3 revision)

**Status:** Adopted direction; results pending. **Added:** 2026-10-24. **Related:** AQ-024, AQ-031, [Gate 3 packet](gate3/README.md).

**Owner decision:** Replace the judgment-based California-to-Wisconsin transfer ratio (proposed in G3-1) with a regression fitted on all California jurisdictions after the published holdout test: each place's post-2020 ADU-type rate explained by its pre-2020 group (active, middle, restrictive), its housing market (median home value and rent, ACS), and size, scored by cross-validation. Apply it to each Wisconsin area with its own market values to set area-specific with-law rates. Fire-rebuild areas stay in (exclusion deferred). Add well-documented ADU data from cities outside California (Seattle, Portland, Austin, Denver to start) as out-of-state evidence and, where suitable, extra regression or validation points.

**Owner input on timing (2026-10-24):** The relevant treatment is when a jurisdiction reached near-benchmark rules, not the statewide wave number. Pre-reform activity is likely a better and more practical proxy for early local adoption than hand-coded adoption years, which may be tried but are hard to code. From the owner's ADU-industry experience, California's specialized industry (builders, lenders, plan sets, and investor-backed firms such as Abodu, United Dwelling, Samara, and Villa) formed mainly after the 2019 package took effect in 2020; before that it was a small, beginner market. If so, the post-2020 response in California's restrictive places includes industry formation happening alongside the law, which is the closer analogue to a single Wisconsin statewide law, and the "industry head start" objection is weaker. This is owner experience, recorded as such; the regression and out-of-state cities test it where possible.

**Decision:** Gate 3 revision; the regression result replaces the G3-1 ratio proposal. Extrapolation below California's range of home values is flagged and tested.

## AQ-035 Gate 3 presentation, ramps, benchmark places, unzoned towns, and a state-relative group rule

**Status:** Adopted. **Added:** 2026-10-24. **Related:** AQ-024, AQ-026, AQ-034, [Gate 3 packet](gate3/README.md).

**Owner decisions (2026-10-24):**

- **G3-2:** each place, including those already at benchmark, gets its own regression-predicted with-law rate, never below its current rate; the separate spillover setting is dropped.
- **G3-3:** ramps by path: lower uses the slower California Central Valley first-law ramp; central uses the California restrictive-group ramp; upper uses the faster middle-group ramp.
- **G3-4:** results are presented as **scenarios, not confidence intervals**, rounded to the nearest hundred, with the current-law baseline shown separately, plus a labeled "Midwest local-reform" scenario based on Madison and Minneapolis (permissive local rules, no statewide law).
- **G3-5 (revised by owner):** towns with no zoning get their own predicted rate now; a list of unzoned Wisconsin towns is being compiled (county general zoning approved by the town, or town zoning under village powers, counts as zoned; shoreland and floodplain zoning do not).
- **G3-6 (revised by owner):** no arbitrary state-specific cutoffs. Use one general, state-relative rule, applied to each state's own data: **active** = top quarter of jurisdictions with at least 3 observed permits in the reference window; **restrictive** = zero observed or unmeasured; **middle** = the rest. This is rule v1, to be made robust and representative when the tool is built for other states.

**Decision:** Adopted 2026-10-24.

## AQ-036 Statewide prediction first; no "local-only reform" scenario in the tool

**Status:** Adopted. **Added:** 2026-10-24. **Related:** AQ-034, AQ-035, [Gate 3 packet](gate3/README.md).

**Owner decisions (2026-10-24):**

- The with-law rate must come from a model or measured data, never a judgment anchor. The triangulated 0.75 (R2 in the revised Gate 3 packet) is withdrawn.
- About 90% of the modeling effort goes to the **statewide** predicted rate (second-home permits per 1,000 single-family homes per year for Wisconsin as a whole); where units land within the state is secondary.
- **Upper scenario, "statewide adoption":** apply the measured year-by-year path of states that passed statewide ADU laws to Wisconsin's homes.
- **Central scenario:** a pooled regression across California, the statewide-law states, and the five comparison cities, with home value (with diminishing effect at the high end), income or price-to-income, and a "statewide law in force" indicator, validated by leaving out one state at a time.
- The **"no statewide law, localities act independently"** scenario is outside the challenge remit and is removed from the tool; it remains an internal learning note (Madison and Minneapolis at about 0.17–0.18 per 1,000 homes per year).

**Decision:** Adopted; replaces revised-packet decision R2.

## AQ-037 Coded rules explain but do not assign activity groups; data-collection calls

**Status:** Adopted. **Added:** 2026-10-24. **Related:** AQ-026, AQ-035, [WI_RULES_VS_ACTIVITY.md](gate3/WI_RULES_VS_ACTIVITY.md), [CA_RULES_VS_ACTIVITY.md](gate3/CA_RULES_VS_ACTIVITY.md).

**Evidence:** In California (367 places, pre-2020 rules from the 2018 Terner survey, the 2020 ADU scorecard, HCD's 2019 filing list, and 60 blind hand-codings), coded rules added nothing to home value and income for sorting places into activity groups (cross-validated AUC 0.81 with value and income, 0.56–0.68 with rules alone, 0.81 with both). Discretionary review was the one feature still associated with lower activity after the 2020 statewide law (0.47 times the rate of similar places). In Wisconsin (13 measured places, 2022–2025), rules in force had no rank correlation with second-home permit rates; explicit prohibitions went with zero, but places allowing ADUs also issued none.

**Owner decisions (2026-10-24):** Keep activity-based grouping (rule v1/v1.1) with unmeasured places restrictive; use rule codings to explain results, not to assign groups; add discretionary review as a downside sensitivity. Data-collection calls: keep Green Bay (Internet Archive copies of its reports, since its site blocks scripts); re-check Kaukauna's rules; count Milwaukee as measured, flagged lower quality; public permit search forms (not personal-data submissions) may be used to measure more places.

**Decision:** Adopted.

## AQ-038 Final Gate 3 scenario set

**Status:** Adopted. **Added:** 2026-10-24. **Related:** AQ-036, AQ-037, [POOLED_MODEL.md](gate3/POOLED_MODEL.md).

**Owner decision (2026-10-24):** Use the pooled two-stage model's central and its between-state spread, and also show the measured statewide adoption path:

- **Lower, "like the slower statewide-law states":** about 4,800 additional second-home permits over 2027–2031 (pooled model, 10th percentile of how states differ).
- **Central, "like a typical statewide-law state":** about 9,500 (pooled model).
- **Upper:** about 18,400 (pooled model, 90th percentile). *Final check (2026-10-24): this level, 2.43 permits per 1,000 single-family homes per year, is reached only by California; every other statewide-law state sits between 0.68 and 1.28, so the label "like the faster statewide-law states" is under owner review (Gate 3 packet).*
- **Statewide adoption line:** about 8,650 (the median path that statewide-law states actually reached, applied to Wisconsin's 1,839,569 single-family homes).
- **Named downside sensitivities (not scenarios):** about 760 if the law only multiplied Wisconsin's current rate by the pooled statewide-law factor; about 2,300 if Wisconsin behaved like the California-only market regression.

All figures are additional permits on top of the current-law baseline of about 650 over the same five years. The pooled ramp (0.62, 0.78, 0.81, 1, 1 of the increment) is used; the California ramp is not applied on top.

**Decision:** Adopted. *Numbers superseded 2026-10-25 by AQ-042 (lower 4,407, central 8,721, Strong adoption 16,853; adoption line 8,208).*

## AQ-039 Teardown-rebuild ADUs count; vacant-lot new-house ADUs do not

**Status:** Adopted. **Added:** 2026-10-25. **Related:** AQ-032, AQ-038.

**Owner decision:** An ADU permitted together with a new house counts as a second home on a single-family lot when the lot previously had a home (teardown-rebuild: one net added home, like an ADU behind an existing house; the benchmark covers parcels with existing single-family buildings). It does not count when the lot was vacant (new development, outside the benchmark). The rule applies the same way in Wisconsin and in every comparison state.

**Consequences:** Wisconsin's second-home series adds teardown-rebuild ADUs (a small increase). The adjustment to comparison-state counts becomes the measured share of ADUs built with a new house on a previously vacant lot, replacing the withdrawn 80% placeholder; Seattle and Austin, where condominium rules drive new-house ADUs, are flagged as outliers and shown only as an optional sensitivity.

**Decision:** Adopted 2026-10-25. The same rule applies everywhere for now. The owner's hunch (2026-10-25) is to count the ADU in both cases (a vacant-lot ADU counts as 1, the house stays in ordinary new construction), to revisit after the Madison-like test. Vacant-lot ADUs are therefore tallied separately everywhere, so either rule can be applied.

## AQ-040 Final Gate 3 decisions G3F-1 to G3F-4

**Status:** Adopted. **Added:** 2026-10-25. **Related:** AQ-038, AQ-039.

- **G3F-1, upper scenario:** label it "Strong adoption". An info icon explains its basis in plain words, for example "California's level of permitting in the years after its statewide laws". Show the number; don't sandbag the real data. The value follows the California adjustments below.
- **G3F-2, California in the common level:** let the data decide. Test leave-one-state-out on the non-California states with and without California in the between-state step. Keep California if it improves those predictions and drop it if it hurts them. Covariates such as home value or earnings may set how much weight California gets, if they predict better.
- **G3F-3, new-house ADUs:** replace the arbitrary 80% with the measured share. Vacant-lot new-house ADUs are a median 4.9% of ADUs across 17 cities (AQ-039), so the adjustment is about ×0.95. It may go in the headline or be shown as a named sensitivity.
- **G3F-4:** advance to Gate 4 after these revisions.
- **Follow-up decisions (2026-10-25, after the rerun in docs/gate3/POOLED_REVISION.md):** G3F-2: keep California in the common level; it predicted the non-California hold-outs better (RMS log error 0.113 vs 0.132 without it; ahead in 66% of 5,000 resamples). Madison follows the observed Madison-like path for now (MADISON_LIKE_CITIES.md); it is the only qualifying Wisconsin place. "Strong adoption" stays the model's upper ("the high end of what statewide-law states have reached; only California has gone higher"), not California's own level.
- **Under test:** the owner's reframing of the rate as permits (not units) per 1,000 properties eligible under each state's own law (docs/gate3/ELIGIBLE_BASIS.md).
- **Related owner direction (2026-10-25):** count at most 2 ADUs per parcel (more is beyond benchmark, like condo conversion), and remove ADUs on multifamily lots from comparison numerators, measured from California APR parcel numbers and an ACS cross-city check, with a one-time LA County assessor validation. The rule change allowing 3 ADUs on single-family lots in California dates from January 2023 (owner).

## AQ-041 Multifamily-lot ADUs in comparison counts

**Status:** Adopted. **Added:** 2026-10-25. **Related:** AQ-032, AQ-040.

**Owner decision:** the goal is a model that predicts the benchmark scenario, so ADUs beyond benchmark come out of comparison numerators, using the simplest defensible method: at most 2 ADUs per parcel (cumulative) plus the definite multifamily rule on parcel numbers in HCD APR Table A2 (cutoff 2023-01-01, when HCD began allowing 3 ADUs on single-family lots). This is a known undercount. The LA County-calibrated correction is shown as a named sensitivity; the LA assessor data stay validation-only. Minneapolis is reduced 12.7% for duplex-lot ADUs. Office-hours question 23.

**Why it matters (owner):** part of California's lead over other states, measured as ADUs per 1,000 single-family homes, comes from multifamily-lot ADUs in the numerator whose multifamily homes are not in the denominator.

## AQ-042 Adopted Gate 3 basis and final numbers

**Status:** Adopted. **Added:** 2026-10-25. **Related:** AQ-038 to AQ-041, [Gate 3 packet](gate3/README.md), [POOLED_REVISION.md](gate3/POOLED_REVISION.md), [ELIGIBLE_BASIS.md](gate3/ELIGIBLE_BASIS.md).

**Owner decision (2026-10-25):** the headline is POOLED_REVISION option (ii) "cap + A2", configuration A (California in the between-state common level). It predicts the 7 held-out non-California statewide-law states best: its RMS log error is 0.113, against 0.132 for flattened permits per one-unit detached home and 0.168 and 0.202 for the two eligible-property variants (ELIGIBLE_BASIS.md section 3). It uses no LA County assessor data.

**What the adopted run contains:**
- California ADU counts: at most 2 ADU units per parcel plus the A2 parcel-number multifamily rule (AQ-041).
- Non-California series: × (1 − 0.049) for vacant-lot new-house ADUs (AQ-039); Minneapolis × (1 − 0.127) for duplex-lot ADUs.
- Madison floor 0.2345 permits per 1,000 one-unit detached homes per year (40 second-home units ÷ 213.168 thousand home-years ÷ 0.8); `madison_floor.in_use` = `g3f_revision_2026_10_25`.
- Madison, the only Wisconsin place that meets the Madison-like definition, follows the observed Madison-like median path in every scenario: 0.452, 0.542, 0.601, 0.799, 1.076 permits per 1,000 one-unit detached homes per year in 2027–2031 (an explicit per-area path in the engine, `area_paths` in `reference/adu_model_params.json`, with no ramp on top).
- Labels: lower "Like the slower statewide-law states"; central "Like a typical statewide-law state"; upper "Strong adoption", with the info text "The high end of what statewide-law states have reached; only California has gone higher."

**Final numbers** (additional second-home permits on single-family lots, statewide, summed over 2027–2031, on top of a current-law baseline of 645 permits over the same five years; engine outputs in `reference/adu_model_statewide.csv`):
- Lower 4,407; central 8,721; Strong adoption 16,853.
- Statewide adoption reference line 8,208 (median observed path of statewide-law states, with the vacant-lot factor).
- Madison's own addition is 135 permits over 2027–2031 in every scenario (53.292 thousand homes × (3.470 − 5 × 0.188) per 1,000 homes).
- Against the published POOLED_REVISION figures with Madison at its pooled level (4,424 / 8,912 / 17,374), the path lowers lower by 17, central by 191 and upper by 521, because Madison's pooled additions were 152, 326 and 656.

**Terms (owner, 2026-10-25):** lower, central and Strong adoption are *scenarios*; one-assumption-changed runs are *sensitivity cases* (the *sensitivity analysis*); methodological alternatives scored on the hold-out states (permits vs units, eligible-property basis, California in or out) are *robustness checks*.

**Sensitivity cases** (central [lower, upper] where computed): Madison at its pooled level 8,912 [4,424, 17,374]; California out of the common level 7,621 [5,144, 11,190]; LA-calibrated multifamily correction 8,402 [4,564, 15,170]; eligible-property basis without one-unit attached homes 8,164 [4,254, 15,318] (on its own 636-permit baseline); no ramp 10,228; rural and small-community places at the floor 4,729; multiplicative law 722; California-only regression 2,361. File: `reference/adu_model_sensitivities.csv`; tornado chart `docs/gate3/sensitivity_tornado.png`.

**Decision:** Adopted 2026-10-25. Gate 3 decisions G3F-1 to G3F-4 are closed (AQ-040); the project advances to Gate 4.

## Questions for office hours

Kept here so the owner can take them to mentor office hours or the Administrator (housing.challenge@turnout.rocks). Answers are recorded against the related entry.

**Scenario interpretation (ADU)**

1. Does "detached and semi-detached ADUs" include conversions of garages and other accessory buildings? Are interior conversions (basements, attics) in or out? (AQ-030)
2. Does "no additional parking is required" also bar replacement parking for a converted garage? (AQ-030)
3. Should the modeled ADU law also remove owner-occupancy and related-occupant requirements and require by-right (ministerial) approval, given the scenario is silent? (AQ-022, AQ-025)
4. Is "at least 600 square feet" a minimum size the law must allow (our reading) or the size teams should assume for modeled units?
5. Where local rules already allow ADUs, should the scenario be the change from current local rules (our approach), and is a statewide market spillover effect in already-permissive cities acceptable if documented? (AQ-027)

**Methods and outcome**

6. Is units authorized by issued building permit an acceptable outcome, given permits, starts, completions, and stock growth are all allowed? (AQ-001)
7. Is a stylized timing convention (law effective at the start of forecast year 1, labeled 2027–2031) acceptable, given no real bill could take effect before 2027? (AQ-021)
8. Are evidence-informed scenario ranges (lower, central, upper paths) sufficient uncertainty treatment, or do judges expect statistical intervals? (AQ-012)

**Eligibility and submission** (from [OFFICIAL_MATERIALS_CHECK.md](gate1/OFFICIAL_MATERIALS_CHECK.md))

9. Is a deep single-state (Wisconsin) tool fully eligible? How much weight does the "states with less complete data" preference carry, and is a documented transfer method enough or must a second state be run?
10. Is there an official provided-data package, or is the curated source list advisory?
11. Does "memory-safe language" bind? Is a JavaScript or TypeScript front end with a Python core acceptable?
12. Is the demo video limit "no longer than five minutes"?
13. Will judges evaluate the repository as of the deadline, and do later commits matter?
14. Which SBOM format (SPDX or CycloneDX) is expected, and where should it go?
15. Is there a size threshold for "large source datasets"? Are small committed derived tables (for example our coded ADU rules) acceptable?
16. Fee scenario: must the $50,000-per-unit assumption apply uniformly even where Wisconsin fees are lower, or may teams also show results with local fees?
17. Can the team submit early for a pre-deadline compliance review?
18. Some source data is published only as PDFs, spreadsheets or images (for example Oregon DLCD ADU reports and Washington OFM permit workbooks), so we entered the counts into a table in our code with the source URL, access date and file checksum. Does this count as "fetched automatically from the authoritative source with minimal manual steps", or must the pipeline download and parse each file itself?
19. Our committed sample files once showed street addresses and parcel numbers copied from public government parcel layers (no owner names). They are now masked, but the old values remain in git history. Is that acceptable under "do not use sensitive, confidential, restricted-use, or personally identifiable data", or must history be rewritten? (Owner decision 2026-10-25: leave history.)
20. Many government sources we use (city permit reports, state ADU reports, county zoning pages) state no license. May we treat them as public records and use them, citing the source?
21. Where an official file is no longer online (or the site blocks scripts), may the pipeline fetch an Internet Archive (Wayback Machine) copy, with its capture date and checksum recorded, instead of the live file? This covers Green Bay permit reports, the Wisconsin DOA land-regulations inventory, an HCD 2019 ordinance list and some archived California ordinances.
22. Some local permit data are only reachable through report screens rather than open-data APIs (Madison's report viewer, Pleasant Prairie's SmartGov, Sun Prairie's Power BI, Kaukauna's Municode Meetings). Do these satisfy "fetched automatically from the authoritative source", given they may break when the city changes its software?
23. California's ADU counts include ADUs on multifamily lots, which the benchmark (one ADU on a parcel with an existing single-family home) does not cover. Our denominator is single-family homes, so they inflate California's rate. A one-time LA County assessor check found about 25% of 2023 ADUs on multifamily lots. Our options: (a) the 2-per-parcel cap plus a rule using only parcel numbers in the state permit data, which is simple and uses no new data but undercounts multifamily lots (California 2023–2025: 3.57 per 1,000 single-family homes per year instead of 3.84); (b) the same plus a correction calibrated to county assessor land-use codes (2.93), which is more accurate but adds a dataset and a calibration step; (c) no adjustment. We use (a) and show (b) as a sensitivity. Is that acceptable, or do judges prefer the more accurate (b)?

## Additional questions to develop

All entries below were added on 2026-10-23 and remain **Open**.

| ID | Question | Next evidence or decision needed |
| --- | --- | --- |
| AQ-006 | How do we project annual permits without additional reform? | Select the historical period, projection method, analysis date, and treatment of current law and already-scheduled changes. Apply consistent economic conditions to baseline and reform cases. |
| AQ-007 | Which Wisconsin pilot areas support the model, and how do they inform statewide results? | Audit Madison and the user-selected provisional restrictive-policy example, New Berlin; retain Milwaukee as a historical comparison candidate, document coverage elsewhere, and choose an explicit aggregation or generalization method. Missing observations must remain distinct from zeros. |
| AQ-008 | How do we identify eligible opportunities and estimate five-year participation? | Separate existing building use, legal eligibility, physical suitability, financial feasibility, and owner/developer uptake. Document defaults and ranges where comparable evidence supports them. |
| AQ-009 | What precise provisions define the ADU, TOD, and parking scenarios? | Specify current rights, qualifying transit and proximity, proposed density, and developer-provided parking. Recompute combined packages to account for shared sites and overlapping parking benefits. |
| AQ-010 | Which assumptions should vary by project type and geography? | Assess timing, costs, financing, uptake, and completion-rate differences; document evidence transfer and sensitivity ranges rather than assuming one statewide average fits every project. |
| AQ-011 | How will we validate results and explain uncertainty? | Choose historical checks or holdouts where feasible, reconcile statewide and district outputs, and distinguish assumption ranges from statistically justified confidence intervals. |

## Decision history

| Date | Entries | Update |
| --- | --- | --- |
| 2026-10-23 | AQ-001 through AQ-011 | Started the log. Captured the permits-first proposal, optional completion conversion, post-reform timing rationale, and related research questions. No new modeling assumption was adopted. |
| 2026-10-23 | AQ-012 | Added the MVP proposal to use an evidence-informed development-response range and qualitative explanations of background conditions, with detailed economic and labor-capacity mechanisms considered for later versions. No numerical range was adopted. |
| 2026-10-23 | AQ-013 through AQ-015 | Added the January 2020 California exemption-reform focus, historical code crosswalk, pre-period/reporting audit, restrictive Wisconsin pilot search, and provision-level policy catalog with separate legislative and effective dates. No effect sizes or zero-production assumptions adopted. |
| 2026-10-23 | AQ-007, AQ-014, AQ-016 | Recorded the user’s provisional selection of New Berlin as the restrictive Wisconsin example and added Menlo Park as a California fee-barrier candidate. The approximately $50,000 fee is a user-supplied research lead pending verification, not an adopted parameter. |
| 2026-10-23 | AQ-013, AQ-017 | Accepted the recovered 2012–2019 HCD-attributed jurisdiction series as descriptive MVP input, recorded California YIMBY’s source stitching and fallback citation, and removed the missing 2017 aggregate-data blocker. Reporting comparability and causal calibration remain open. |
| 2026-10-23 | AQ-015; Policy Catalog | Created the California ADU legislation register, including further laws identified in the YIMBY report. Kept legislative years, effective dates, implementation deadlines, local opt-ins, and verification status separate. |
| 2026-10-23 | AQ-018 | Adopted area-level map forecasts for neighborhoods, regions, or cells, with inventory and spatial joins included in the data acceptance criteria. Geographic resolution and allocation weights remain open. |
| 2026-10-23 | AQ-019, AQ-020; MVP Execution Plan | Recorded the state-first destination, sequential ADU pilot/statewide/additional-scenario MVPs, judging alignment, local execution with routine GitHub pushes authorized, and agent self-assessment before step-by-step owner gates. |
| 2026-10-23 | AQ-021 to AQ-023; AQ-007, AQ-014 | Recorded the owner's Gate 1 decisions: stylized dates, ACS denominator, ADU-equivalent permit rule, replacing New Berlin with a permit-data-rich mid-size city without ADU rules, no poison pills in the modeled bill, unknown local rules treated as no ADU rights for the MVP, and baseline-health reporting across scenarios. |
| 2026-10-23 | AQ-023, AQ-024 | Owner confirmed the reduced effect for already-permissive cities and set Madison's observed rate as the lower path, with separate predictive models for the central and upper paths. |
| 2026-10-24 | AQ-025 | Recorded the owner's direction to treat owner occupancy and the approval pathway (ministerial versus discretionary) as the provisions that decide whether nominally allowed ADUs get built. |
| 2026-10-24 | AQ-026 | Adopted the owner's two-pass rights classification (ordinance status, then rights class with restriction flags) and split prohibitions into explicit and implicit. |
| 2026-10-24 | AQ-027 | Logged owner Gate 3 inputs: statewide market spillover for benchmark cities, path-specific ramps, unknown rules treated like restricted with a hold-out test, and the recently-liberalized baseline ramp. |
| 2026-10-24 | AQ-028 | Adopted the outcome-based increment (homes × (y − x)) with estimated x where permits are unobserved, and proposed stock-gap health baselines across scenarios. |
| 2026-10-24 | AQ-029 | Measured Madison's partial benchmark status (8% Planned Development; 78% outside the TOD overlay facing replacement parking) and proposed scaling its floor rate by benchmark completeness. |
| 2026-10-24 | AQ-030; office-hours questions | Adopted the narrow reading of the benchmark's forms and parking, set Madison at 80% of benchmark, and added a consolidated list of questions for office hours. |
| 2026-10-24 | AQ-031 | Adopted a pre-specified California permissive-vs-restrictive comparison across the 2017, 2018, and 2020 reform waves for ramp and spillover evidence, with no COVID adjustment. |
| 2026-10-24 | AQ-032 | Adopted 'second homes on single-family lots' as the tentative headline outcome with cross-state guardrails, and recorded the owner's preference for uniform cross-state measures. |
| 2026-10-24 | AQ-033 | Gate 2 passed; Pleasant Prairie verified by the owner; Appleton coded benchmark; California plan approved; Madison floor years set. |
| 2026-10-24 | AQ-034 | Adopted a market-adjusted California regression (with out-of-state cities) to replace the judgment-based transfer ratio for the central path. |
| 2026-10-24 | AQ-035 | Owner accepted G3-2 to G3-4; unzoned towns get their own rate with a town list to build; adopted a state-relative group rule (v1) instead of state-specific cutoffs. |
| 2026-10-24 | AQ-036 | Statewide rate comes from a pooled multi-state model or measured adoption path, not a judgment anchor; the local-only scenario is removed from the tool. |
| 2026-10-24 | AQ-037 | Coded rules do not predict activity in California or Wisconsin; they explain results, discretionary review is a downside sensitivity; owner accepted data-collection calls. |
| 2026-10-24 | AQ-038 | Final Gate 3 scenarios from the pooled model (about 4,800 / 9,500 / 18,400) with the statewide adoption line (about 8,650) and named downside sensitivities. |
| 2026-10-25 | AQ-039 | Teardown-rebuild ADUs count as second homes; vacant-lot new-house ADUs do not; the new-house adjustment uses the measured vacant-lot share. |
| 2026-10-25 | Data rules | Owner decisions D1–D6 on data compliance (see docs/DATA_COMPLIANCE.md); leave git history; office-hours questions 19–22 added. |
| 2026-10-25 | AQ-040 | G3F-1 upper labelled "Strong adoption" with basis on an info icon; G3F-2 California inclusion decided by non-California hold-out accuracy; G3F-3 measured vacant-lot share (~5%) replaces 80%; G3F-4 advance after revision; 2-ADU-per-parcel cap; multifamily-lot ADUs removed. |
| 2026-10-25 | AQ-041 | Cap at 2 ADUs per parcel plus the A2 parcel-number multifamily rule (main); LA-calibrated correction as a sensitivity; office-hours question 23. |
| 2026-10-25 | AQ-042 | Adopted POOLED_REVISION option (ii) configuration A with the vacant-lot and Minneapolis adjustments, Madison floor 0.2345 and Madison on the Madison-like path: lower 4,407, central 8,721, Strong adoption 16,853 on a 645 baseline; eligible-property basis kept as a sensitivity case and robustness check; advance to Gate 4. |
| 2026-10-25 | Gate 3 | Owner approved the final Gate 3 packet (docs/gate3/README.md; central 8,721, lower 4,407, Strong adoption 16,853 additional permits 2027–2031). Gate 4 (working ADU pilot) starts. |
| 2026-10-26 | Gate 4 review | Madison's 2025–26 templated two-unit ADU programme stays as counted; revisit Madison when 2026 is complete. Owner principle: a statewide law never subtracts from a city already above benchmark (the engine floors each place's addition at zero), e.g. Madison with two ADUs per structure or San Diego's bonus ADU programme. Milwaukee uses its measured 2022–2025 rate (no clear post-reform rise); its ramp is a baseline sensitivity. |
