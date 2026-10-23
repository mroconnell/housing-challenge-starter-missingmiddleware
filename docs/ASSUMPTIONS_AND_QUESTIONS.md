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

**Decision (2026-10-23):** The user selected New Berlin as the provisional restrictive-policy example alongside Madison. Proceed with its policy and permit-data audit. This selection does not establish permit-data suitability, zero ADU production, or representativeness of Wisconsin as a whole.

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
