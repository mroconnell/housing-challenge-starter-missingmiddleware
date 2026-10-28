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
*Numbers superseded 2026-10-26 by AQ-043 (baseline 605; lower 5,538, central 8,757, Strong adoption 16,889; reference line 8,851).*

## AQ-043 Gate 4 review: lower scenario, Milwaukee's current-law rate and the reference line

**Status:** Adopted. **Added:** 2026-10-26. **Related:** AQ-024, AQ-027, AQ-042, [SCENARIO_OPTIONS.md](gate4/SCENARIO_OPTIONS.md), [Gate 3 packet](gate3/README.md).

**Owner decisions (2026-10-26):**
1. **Lower scenario = the average of the two slowest statewide-law states** (option a1). Rhode Island's level is 0.6214 and Oregon's 0.6826 permits per 1,000 single-family homes per year at a typical place with the law in force 4 or more years (`reference/pooled_revision_stage2_levels.csv`). Their mean, 0.6520, is 0.6497 of the central's common level of 1.0035. Every area's central level is multiplied by 0.6497, so places keep the model's differences from one another. The ramp is the pooled ramp recomputed for that level, as for the central and upper (0.6211, 0.7886, 0.8186, 1, 1), not Oregon's observed ramp. It replaces the 10th percentile of the between-state spread (central ÷ 1.885, a level of 0.53 that is below every statewide-law state), which becomes the sensitivity case "Lower as a statistical 10th percentile". Label: "Sluggish adoption"; info text: "Like the average of the two slowest statewide-law states, Rhode Island and Oregon." Parameters: `paths.lower.level_from` in `reference/adu_model_params.json`.
2. **Milwaukee's current-law rate = its measured 2022–2025 rate, held flat.** That is 35 candidate second-home permits ÷ 405.608 thousand home-years (101,402 single-family homes × 4 years) = 0.0863 permits per 1,000 single-family homes per year (95% interval 0.060–0.120). Status *observed*, quality C (unverified open-data candidates). It replaces the assumed ramp from Milwaukee's pre-reform rate to Madison's 0.1876 by mid-2029. The permit file through 2026-06-15 shows no clear post-reform rise (8 candidates ÷ 88.3 thousand home-years = 0.091, 95% interval 0.039–0.179). The ramp is kept as a baseline-only sensitivity case. Revisit when Milwaukee publishes permits after 2026-06-15.
3. **Reference line = the median observed statewide rate across all 8 statewide-law states, California included** (California cap + A2 with 2020 as year 1; the other seven × 0.951 for vacant-lot ADUs). The medians are 0.754, 0.931, 0.869 and 1.293 permits per 1,000 single-family homes per year in years 1–4 (2027–2030), from 7, 5, 5 and 4 states. Only California has a year 5, so 2031 repeats the 2030 median and is flagged `carried_forward` in `reference/adu_model_reference_line_by_year.csv`.

Unchanged: the central and Strong adoption definitions, Madison on the Madison-like path, the Madison floor of 0.2345, and California in the common level.

**Final numbers** (additional second-home permits on single-family lots, statewide, summed over 2027–2031; engine outputs in `reference/adu_model_statewide.csv`):
- **Baseline:** 604.6 permits under current law over 2027–2031 (was 644.9). Milwaukee's own baseline falls from 84.0 to 43.8 permits.
- **Lower 5,538; central 8,757; Strong adoption 16,889** (were 4,407, 8,721 and 16,853).
  - The new lower alone gives 5,502 on the old baseline (+1,095 permits).
  - The Milwaukee change adds 36 permits to each scenario. It removes 40.2 permits of baseline, but the addition is ramped in its first three years and the baseline is not, so the central's total with the law moves from 9,365.5 to 9,361.3 permits (−4.2).
  - Milwaukee's own addition is 185 / 306 / 613 permits in the lower / central / Strong adoption.
- **Reference line: 8,851 permits** (1,267, 1,593, 1,477, 2,257 and 2,257 in 2027–2031). That is 94 permits (1%) above the central's 8,757. Over the four observed years, 2027–2030, it is 6,594 permits against the central's 6,683. On the old 644.9-permit baseline it would be 8,811.

**Sensitivity cases** (`reference/adu_model_sensitivities.csv`, now with a `moves` column naming the number each case changes, and a plain-language `description`). Central [lower, upper] where computed, permits over 2027–2031:
- *Statewide addition:* Lower as a statistical 10th percentile [4,443] (central and upper unchanged); Madison at its pooled level 8,948 [5,599, 17,410]; California out of the common level 7,657 [5,538, 11,226]; LA-calibrated multifamily correction 8,438 [5,446, 15,206]; eligible-property basis 8,164 [upper 15,318] (its own 636-permit baseline; Gate 3 run, not rerun, lower left out); no ramp 10,268; rural and small-community places at the floor 4,765; multiplicative law 666 (was 722); California-only regression 2,390 (was 2,361). The multiplicative and California-only cases depend on current-law rates, so they were recomputed from a refit of the adopted model.
- *Baseline only* (baseline; change in the central addition): Milwaukee on the assumed ramp 644.9 (−36.0); uncoded places like prohibited 418.3 (+158.6); no ramp for recently liberalized places 606.3 (−1.2); Madison at its 2026 pace 813.8 (−129.4); Madison 2024–2025 617.1 (−12.5); Madison without the templated programme 595.9 (+8.8).
- *Local distribution only:* none of the current cases.

**Decision:** Adopted 2026-10-26.

## AQ-044 TOD: "major transit stop" definitions and city-specific studies

**Status:** Adopted (owner, 2026-10-26). **Added:** 2026-10-26. **Related:** [docs/tod/MAJOR_TRANSIT_STOP.md](tod/MAJOR_TRANSIT_STOP.md), [docs/tod/GATE1_PLAN.md](tod/GATE1_PLAN.md).

**Owner decisions (2026-10-26):**
1. **Stop definitions are shown as a ladder from narrowest to widest**, all measured from the transit agencies' own published schedules:
   - rail and bus rapid transit only;
   - California's definition;
   - 15-minute bus plus rail and rapid transit, the main case;
   - 20-minute bus plus rail and rapid transit, the widest defensible case.

   Under the main case, 469,352 of Wisconsin's 2,727,726 homes (2020 census) are within ½ mile of a qualifying stop. "Any stop" (1,003,823 homes) is shown for context only, not as "major" transit.
2. **Focus on city-specific policies.** Model Milwaukee and Madison (and their counties) with their own evidence and data, and the rest of the state with a simpler statewide rule. Milwaukee County and Dane County hold 304,215 of the 330,804 homes near stops under the main distance rule (92%), and 93.5% of the 10,708 baseline permits allocated near stops for 2027–2031.

**Open:** how to handle Madison Metro's data licence (asked 2026-10-26).

## AQ-045 TOD: federal National Transit Map as the common stop source; Madison's file not used

**Status:** Adopted (owner, 2026-10-26). **Related:** AQ-044, office-hours questions 24 and 25, [docs/tod/research/WI_TRANSIT_DATA.md](tod/research/WI_TRANSIT_DATA.md).

**Owner decisions (2026-10-26):**
1. **Do not use Madison Metro's GTFS file for now**, while we ask office hours and possibly write to the City (question 24).
2. **Prefer one consistent method for every city and state studied:** stop locations and route shapes from the federal National Transit Map (BTS NTAD, CC BY 3.0, compiled 2026-09-23). The owner judged that consistency across places matters more than whatever extra precision city-specific files would add.

**What follows, and the gap to close:** the National Transit Map has stop locations and route shapes, but no timetables. So it cannot by itself say whether a stop is served every 15 minutes. The frequency test will therefore be made at the route level, applied the same way everywhere. Each route's peak frequency is taken from a source whose terms allow our use, and that source is recorded per agency:
- the agency's own schedule file where its licence is permissive (for example Milwaukee County Transit System, whose terms require notices);
- the agency's published route descriptions where it is not, as for Madison. The National Transit Map routes layer carries Madison's own route descriptions, such as "at least every 15 minutes" for Routes A, B, C, D and 80.

Stops count as qualifying when they lie on a qualifying route shape. Rail and rapid transit stops come from route type and route names in the same layer.

The figures published on 2026-10-26 in [docs/tod/MAJOR_TRANSIT_STOP.md](tod/MAJOR_TRANSIT_STOP.md) used Madison's file. They were replaced the same day by a rerun on the National Transit Map, with a route-level frequency test. The rerun gives:
- Main case: 318,394 of 2,727,726 homes (11.7%), against 330,804 before.
- 15-minute service within ½ mile: 407,832 homes (15.0%).
- 20-minute service within ½ mile: 455,821 homes (16.7%).
- Milwaukee County and Dane County hold 97.2% of the main case.

These supersede the 2026-10-26 figures quoted in AQ-044.

## AQ-046 Parking: evidence by city size; one model with size and market variables

**Status:** Adopted (owner, 2026-10-26). **Added:** 2026-10-26. **Related:** [docs/parking/GATE1_PACKET.md](parking/GATE1_PACKET.md), [docs/parking/POLICY_TAXONOMY.md](parking/POLICY_TAXONOMY.md) section 6.

**Finding:** no published study measures housing after a parking-minimum repeal in a place under 50,000 people. A quick look (not pre-registered) at 16 US repeal places of 5,000–50,000 people found 7 rising faster than same-state comparison places, 8 slower and 1 with no permits. The median after/before ratio was 0.84 times the comparison places' ratio.

**Owner decision (2026-10-26):** the mixed small-place result is evidence in its own right, and fits expectations. Where low-parking development is still seen as risky, developers do not use the freedom as often. Proceed with the before/after method on repeal cities, and model places of different sizes differently. Use a regression across many variables to find where the cut-offs between city types lie and how effective repeal is in each. Held-out cities decide the variables and cut-offs, following the project rule.

**Conductor notes:** with about 50 repeal cities the regression can support only a few variables. Candidates (population, density, metro status, market strength, pre-repeal permit trend, region) will be compared by leave-one-city-out prediction, not by fit. The small-place quick look was seen before the comparison plan was written. The plan records it as a deviation, and the formal test reruns it under the registered rules. Gate 1 decisions P1–P4 and P7–P9 are still open.

## AQ-047 TOD Gate 1 decisions (owner reply on the packet)

**Status:** Adopted in part (owner, 2026-10-26). **Related:** AQ-044, AQ-045, [docs/tod/GATE1_PACKET.md](tod/GATE1_PACKET.md) (the owner's points 3 to 8 answer the packet's recommendations 3 to 8, which are decisions T4 to T10).

**Owner decisions (2026-10-26):**
1. **Density floors come from measured cases (T4).** The modelled law takes its height and density rules from the cities and programs that have permit data before and after their reform, not from a statute chosen in advance. If there are many such cases, the weaker-policy ones are dropped, so the modelled law is the most effective design that is still well measured and predictive. The choice of design must not rest on one lucky case: each design's effect is judged on held-out cases.
2. **No affordability mandate (T5).** This part of T5 is accepted.
3. **Parking minimums are not removed in the TOD scenario (T5).** Parking is left to the parking scenario. Results will show each reform alone and the two combined: TOD alone, parking alone, and TOD plus parking. This updates the earlier "no combinations for now" direction for these two reforms.
4. **Two methods, with the Madison test deciding and Chicago as the fallback hold-out (T6).** Approved.
5. **Scenario names from real cases (T7).** Approved for now.
6. **Places already at the law (T8, T9) depend on the case evidence.** If the cases show a rule set that clearly raises permits per acre above what Madison's overlay and Milwaukee's zoning near CONNECT 1 already allow, the modelled law may go beyond them there. Otherwise the tool says plainly that Wisconsin gains little in those corridors because they already have TOD zoning. Two exceptions are worth testing: a benefit when most of a state's large cities adopt TOD, and an extra benefit from TOD plus parking reform that these cities do not have everywhere.
7. **The "Where" screen shows station areas and corridors in the two metros (T10).** Approved.

8. **Rate (owner, 2026-10-26):**
   - **Measure:** homes permitted per year per acre of eligible parcel land in the station area. Eligible means land where the law raises allowed density; streets, water, parks and land already at the law are excluded.
   - **Comparing cases:** each case's rate is scaled per unit of added allowed floor area.
   - **Secondary number:** permits per 1,000 existing homes in the station area, so TOD can be compared with ADUs. A held-out test decides which denominator predicts better.
9. **Existing density as a fallback (owner, 2026-10-26):** where a comparison city has no permits by year, its existing homes per acre near stops is still collected. Census blocks and parcels give this for any US city.
   - It describes where decades of rules have led, not a five-year response, so it is not used directly as the law's effect.
   - It serves three purposes: as a check on how dense station areas get under different rules, as a guide to the headroom between current and allowed density, and as an input to sharing the Wisconsin baseline across station areas.

10. **T2 and T3 (owner, 2026-10-26):** the stylized start date of 1 January 2027 is approved. Amtrak stations are dropped, because SB 79 counts commuter rail only at 48 or more trains a day. The main case is therefore 313,357 homes near stops.
11. **T1:** the outcome is housing units at permit issuance, by building size. This is taken as approved with item 8, since the owner approved a rate measured in homes permitted.

## AQ-048 Parking Gate 1 and Gate 2 decisions

**Status:** Adopted (owner, 2026-10-26: "Yes to all for now"). **Added:** 2026-10-26. **Related:** [docs/parking/GATE1_PACKET.md](parking/GATE1_PACKET.md), [docs/parking/GATE2_PACKET.md](parking/GATE2_PACKET.md), AQ-046.

- **Gate 1 (P1–P9, as recommended):**
  - outcome is housing units at permit issuance, by building size;
  - the stylized law starts 1 January 2027;
  - full removal of minimums for all housing;
  - developer-provided parking taken from post-repeal studies;
  - evidence from US repeal places, each checked against its ordinance;
  - places already at the benchmark get no addition;
  - Milwaukee's 3–4 and 5+ unit permit series is replaced by an estimate from the city's property file (MPROP), as a labelled adjustment, with Census-as-published kept as a sensitivity (P8);
  - the baseline range is Wisconsin's long-run 10th–90th percentile (P9).
- **Gate 2 (G2-1 to G2-5, as recommended):**
  - option A: the central case is no measurable change;
  - the upper case is the high end of the likely range for all units, +2.21 permits per 1,000 existing homes per year (about 29,700 over 2027–2031), with the apartments-only bound (about 14,200) and the without-San Francisco bound (about 41,700) as sensitivities;
  - years 4–5 are held at the year 1–3 level, labelled as an assumption;
  - one average, with the size-and-metro model as a sensitivity;
  - no cost-based line for now.

## AQ-049 TOD Gate 2 decisions

**Status:** Adopted (owner, 2026-10-26: "Approve all recommendations"). **Related:** [docs/tod/GATE2_PACKET.md](tod/GATE2_PACKET.md) section 7, AQ-047.

1. **G2-1:** the Wisconsin data is fit for Gate 3, with the gaps shown in the tool's trace.
2. **G2-2:** one area rule for every case. Treatment is lots whose allowed density rose; comparison is lots with no zoning change. The first results are kept as a sensitivity.
3. **G2-3:** measure more cases before fitting, in this order:
   - the New York pooled set;
   - Philadelphia 2012, Raleigh 2021 and Phoenix 2015 (moderate rent);
   - Ann Arbor 2021, as a second test case;
   - then the higher-rent medium-design cases if time allows.

   Each is added to the case plan with its date before its permits are counted.
4. **G2-4:** the law stays on the SB 79 floors from Gate 1 unless the Madison test or the new cases point to a design that holds up on the test cases.
5. **G2-5:** test whether the effect per added density rises with rent, fitting on the fitted cases only. Chicago, Ann Arbor and Madison judge the result.
6. **G2-6:** code Milwaukee's 2025 "Growing MKE" amendments before Gate 3.
7. **G2-7:** "TOD alone" rests on the New York cases, the only ones that kept parking minimums.
8. **G2-8:** single-family lots near stops stay eligible, with a sensitivity that leaves them out.
9. **G2-9:** build the suburbs' fallback at Gate 3. It uses existing homes per acre and the modelled law, with zoning marked "not coded".

## AQ-050 TOD: size the law's effect by citywide net effects

**Status:** Adopted (owner, 2026-10-27, "That sounds great", replying to the recommendation). **Related:** [docs/tod/GATE3_MODEL_SPEC.md](tod/GATE3_MODEL_SPEC.md) section 9, [docs/tod/MADISON_TEST_RESULTS.md](tod/MADISON_TEST_RESULTS.md), [docs/tod/research/NET_EFFECT_SOURCES.md](tod/research/NET_EFFECT_SOURCES.md).

1. **The statewide addition is a share of the housing stock in the station areas**, taken from studies that measured whole-city net effects after upzoning:
   - little: Los Angeles;
   - typical: Stacy et al. 2023;
   - strong: Auckland.

   Each value is corrected as in the source check: Los Angeles's figure is over six years, and Auckland's yearly profile is rescaled to its stated total. Each is divided by its study's own coverage share, so it applies per upzoned home. The as-published reading is a sensitivity.
2. **Placement:** the per-acre response is used only to place the total across station areas.
3. **Sensitivity:** the per-acre method with the Wisconsin-measured response, about 0.23 extra homes per acre per year per added floor area ratio (the mean of Madison's and Chicago's), capped at the 95th percentile of peer metros' apartment permitting.
4. **Reason:** the Madison test confirmed the per-acre prediction only weakly. Spread over all land near stops, the per-acre rates exceed anything comparable metros have absorbed, because block-level gains partly move building from nearby blocks.

## AQ-051 TOD Gate 3 decisions

**Status:** Adopted (owner, 2026-10-27, "Approved", replying to the five recommendations). **Related:** [docs/tod/GATE3_PACKET.md](tod/GATE3_PACKET.md) section 7, AQ-050.

1. **G3-1:** three scenarios over 2027–2031, as extra homes permitted on top of 14,464 baseline homes near stops:
   - little (Los Angeles): about 171;
   - typical (Stacy et al. 2023): about 2,509;
   - strong (Auckland): about 17,148.

   The reference line equals the typical scenario and is shown as a dotted line.
2. **G3-2:** additions are placed in the uncoded suburbs near stops too, using their capacity-based dose. Totals are unchanged.
3. **G3-3:** year 5 of the New York build-up uses the mean of years 3–5. The single measured year is kept as a sensitivity.
4. **G3-4:** the tool states plainly that the typical scenario places within five years an effect measured 3 or more years after reform.
5. **G3-5:** go to Gate 4, the TOD pilot in the tool using preview mode. The pilots are Milwaukee CONNECT 1, Madison Rapid Route A, and Eau Claire as the transfer check.

Approved before the independent check of the Gate 3 packet finished. That check (2026-10-27) raised two points, and both proposed changes were sent to the owner the same day; they await confirmation:
- **G3-3 reversed:** the measured build-up is kept, because the spec fixed it before results and smoothing would be after-the-fact tuning. The smoothed year 5 becomes a sensitivity.
- **G3-2 amended:** suburbs get a capacity-based dose scaled by 0.719. That is the ratio of the coded capacity to the fallback estimate, measured in Milwaukee and Madison, where the fallback overstated capacity by 41–55%.

## AQ-052 TOD: test California's AB 2097 as a TOD-plus-parking case

**Status:** Adopted (owner, 2026-10-27, "Yeah"). **Related:** [docs/tod/AB2097_TEST_PREREG.md](tod/AB2097_TEST_PREREG.md), docs/shared/SCENARIO_CONTRACT.md section 9.

The owner asked whether AB 2097 (California, 2023: no parking minimums within ½ mile of major transit) shows what happens when parking and TOD reform combine. It is statewide for parking, not for density.

The test compares permits near transit with a comparison ring, before and after 2023, using California's Table A2 permits (2018–2025):
- in areas already upzoned before 2023, such as Los Angeles's transit program areas, it measures TOD plus parking;
- elsewhere near transit, it measures parking alone.

The plan was written before counting. The result is a sensitivity for the combined view's rule (c), and California evidence for the parking scenario.

## AQ-053 TOD Gate 4 decisions

**Status:** Adopted (owner, 2026-10-27, "Approve"). **Related:** [docs/tod/GATE4_PACKET.md](tod/GATE4_PACKET.md), AQ-051.

1. **G4-1:** the TOD screens are accepted, and TOD's registry status is "ready".
2. **G4-2:** both amendments from the Gate 3 independent check are confirmed. The measured New York build-up is kept, with the smoothed year 5 as a sensitivity. The suburbs' placement is scaled by 0.719. Statewide totals are unchanged.
3. **G4-3:** next is Gate 5, the statewide review: reconciliation, a final pass on plain wording, and a fresh-clone check. Then final numbers go to the ADU thread for the submission documents.
4. **Combined view:** the owner approved the recommendation to make "the larger of the two near stops" (rule b) the main rule, with the sum (rule a) as an upper bound. The AB 2097 test found no measurable gain from combining parking relief with earlier upzoning (AQ-052). The parking conductor agreed, and the owner confirmed it in the parking thread the same day ("Sure").

## AQ-054 Cross-reform reporting conventions

**Status:** Adopted. **Added:** 2026-10-27. **Owner decision** (all three reforms):
1. **Shared unit.** Each reform keeps its own modelled outcome. For cross-reform views, every reform also reports **additional homes permitted per year, statewide** (and by area where it can), shown against the shared all-housing baseline (122,619 permitted units over 2027–2031, docs/shared/HOUSING_BASELINE.md). Two caveats go with any shared graph: ADUs are under-counted in the Census permit data behind that baseline, so the ADU line is extra on top of it; and the reforms overlap (TOD homes are part of the all-housing count), so the lines are never stacked or added.
2. **Wisconsin home count.** Every cross-reform figure uses ACS 2020–2024 total housing units (B25002): **2,778,572**. TOD may keep 2020 census blocks inside its station-area calculations but restates its headline shares on the ACS count. The 2025 population-estimate count (2,840,960) is used only on the "Wisconsin today" screen as current context.
3. **Median line.** One definition: "the median of the real cases, applied to Wisconsin", shown only when a reform has at least 4 comparable cases. ADUs (8 states) and parking (24 places; its median rounds to 0, the same as its central) keep the line; TOD (3 whole-city studies) drops it and says why.

## AQ-055 TOD Gate 5: TOD finalized

**Status:** Adopted (owner, 2026-10-27, "Approve all"). **Related:** [docs/tod/GATE5_PACKET.md](tod/GATE5_PACKET.md).

1. **T5-1, numbers frozen.** TOD is finalized with these figures for 2027–2031:
   - 14,464 homes permitted near stops without the law (range 8,386 to 21,874);
   - extra homes permitted with the law: little 171, typical 2,509 (range 665 to 4,352), strong 17,148;
   - in the shared unit: about 502 extra homes a year in the typical case, 2.0% above the statewide all-housing baseline.

   They go to the ADU thread for the submission documents. Later work (the trait test, the permit-count cases) is shown as sensitivity or context unless the owner decides otherwise.
2. **T5-2:** the AQ-054 reporting conventions are accepted as applied.
3. **T5-3:** the cost-method inputs (two industry reports downloaded by hand) become optional for the model run, and both sources are recorded in DATA_COMPLIANCE.md. No adopted number uses them.
4. **T5-4:** the Madison TOD overlay boundary gets a fetch script and a manifest entry.
5. **T5-5:** legislative districts keep the detached-home split, which is disclosed.
6. **T5-6:** a TOD section and the rebuild order go into the README, in the submission-documents pass with the ADU thread.

## AQ-056 TOD: widen the case set, and let the modelled law follow what can be predicted

**Status:** Adopted (owner, 2026-10-27). **Related:** AQ-047 item 1, AQ-055, [docs/tod/TRAITS_PLAN.md](tod/TRAITS_PLAN.md), [docs/tod/CASE_ANALYSIS_PLAN.md](tod/CASE_ANALYSIS_PLAN.md) section 7.

The owner restated the principle in AQ-047 item 1: the modelled law should rest on a dataset big enough to be predictive.
1. **More cities first.** Eight cities are added and the trait test is rerun with the same pass rule.
2. **If a narrower design predicts well, adopt it.** If, on the wider set, a particular law design or a set of place traits predicts held-out cities better than the plain average, the modelled law may be narrowed to that design. For example, it might apply only where the traits say upzoning works, or use the design that worked. The scenarios would then be re-sized from that predictive model.
3. **The frozen numbers can be unfrozen.** The TOD numbers frozen in AQ-055 stay as they are until the owner approves any such change, which would be brought to him as a short gate packet.

## AQ-057 TOD: control cities with no reform, and the accepted screen updates

**Status:** Recorded (owner request and acceptance, 2026-10-27). **Related:** AQ-050, AQ-055, AQ-056, [docs/tod/CONTROL_CITIES_PLAN.md](tod/CONTROL_CITIES_PLAN.md), [docs/tod/CONTROL_CITIES_RESULTS.md](tod/CONTROL_CITIES_RESULTS.md).

1. **Screens.** The owner accepted ending the search for predictors after the all-variables test. The "How sure" screen now says 12 traits and their 66 pairs, plus 91 census variables, were tested with 8 methods across 8 cities, and none predicts. The "Why" screen adds the cities' own whole-city net effects: 0.04% to 1.24% of a city's homes over five years, with no building lost next door.
2. **Control cities.** At the owner's request, each reform city's whole-city permits were compared with 10 matched US cities that made no transit-area reform, over the same years, under a plan written first. The cities' own results agree with it in 5 of 6 cities, but it can only detect changes of about 4% to 5% of a city's homes over five years. That is far more than any reform added, so it cannot narrow the range. Seattle's citywide boom shows why the within-city comparison is used.
3. **No number changes.** The TOD scenarios stay at 171, 2,509 and 17,148 extra homes over 2027–2031 (AQ-055).

## AQ-058 ADU placebo test: rising baseline as a sensitivity, not the main case

**Status:** Adopted. **Added:** 2026-10-28. **Related:** AQ-043, AQ-054.

- **The test.** It compared strong-law, weak-law and no-law places ([docs/adu/PLACEBO_RESULTS.md](adu/PLACEBO_RESULTS.md)). They ranked strong > weak > none: changes of +0.75, +0.45 and +0.25 ADU permits per 1,000 single-family homes per year.
- **Why the no-law places rose.** Their rise disappears once windows with a local reform are removed.
- **Owner decision.** Keep the adopted model. Show "Wisconsin's baseline rises like no-law places (×1.11 a year)" as a named baseline-only sensitivity: baseline 1,083 instead of 605, central addition 8,324 instead of 8,757, total with the law 9,408 instead of 9,361.
- **Why this departs from the plan.** The pre-registered rule would have made the rising baseline the main case. The decision departs from it because the no-law rise comes from local reforms, and Wisconsin's main local reform (Madison 2021) is already in the measured baseline.

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

**Transit-oriented density (TOD)**

24. **Madison Metro schedule data licence.** Madison Metro publishes its schedules as a standard GTFS feed (https://transitdata.cityofmadison.com/GTFS/mmt_gtfs.zip) under the City of Madison Transit Data Developer License (http://transitdata.cityofmadison.com/MetroTransitDataTermsOfUse.pdf, read 2026-10-26). The licence:
    - is revocable;
    - limits use to "assisting mass transit riders or in furtherance of promoting public transportation";
    - says data derived from the City's data remains the City's property.

    We would use the feed to find stops served at least every 15 minutes, and to count homes within ¼ and ½ mile of them for a statewide transit-oriented density estimate. We would publish the stop list and the counts in an Apache-2.0 repository. Questions:
    - Does this use count as "promoting public transportation"?
    - Does the derived-data clause conflict with the challenge's open-source and data rules?
    - Should we instead avoid the file, or ask the City for written permission?

    Until we have an answer, we do not use the file (AQ-045).
25. **Federal National Transit Map as the stop source.** The U.S. DOT National Transit Map (BTS NTAD stops and routes, CC BY 3.0) compiles each agency's GTFS stops and route shapes. Is it acceptable to use it as the single, consistent stop source for every city, including Madison? Or do the original agency licences (such as Madison's derived-data clause) still apply to data taken from it? (AQ-045)

**Parking and TOD (shared)**

26. **City evidence for a statewide law.** No state has post-law permit data for a parking repeal or a transit-oriented density law: the laws are too new, or narrower than the benchmarks. Both scenarios therefore rest on cities that adopted the reform themselves (parking: about 30 US repeal cities compared with similar places; TOD: city programs such as Madison's TOD overlay, Los Angeles TOC, and Auckland). Does evidence from city reforms satisfy "grounded in evidence" for a statewide-law scenario, if we say plainly that the cities chose to reform?
27. **Parking inside the TOD scenario.** May the TOD scenario remove parking minimums inside station areas, as the benchmark allows, with that reported separately and no subtracting of the overlap with the parking scenario?

**Parking**

28. ~~Is a model-based cost-per-unit estimate acceptable as the main method for parking, if before/after city data are too noisy to show an effect?~~ Withdrawn 2026-10-27: the owner chose no cost-based line (AQ-048, G2-4).
29. Is it acceptable to correct a Census permit series (Milwaukee's apartments) from a city's property file, if the adjustment is labelled and the published series is kept as a sensitivity?

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
| 2026-10-26 | Lower scenario | Owner adopted the lower scenario as the average of the two slowest statewide-law states, Rhode Island (0.62) and Oregon (0.68): about 0.65 permits per 1,000 single-family homes per year at a typical place (about 5,502 additional permits 2027–2031 before the Milwaukee change), replacing the 10th-percentile cut. Median line across all 8 states including California, through 2030 (docs/gate4/SCENARIO_OPTIONS.md). |
| 2026-10-26 | AQ-043 | Applied the Gate 4 review decisions: lower = mean of Rhode Island and Oregon, Milwaukee at its measured 2022–2025 rate, reference line = median of all 8 states with 2031 carried forward. Baseline 605; lower 5,538, central 8,757, Strong adoption 16,889; reference line 8,851. The 10th-percentile lower and the Milwaukee ramp are sensitivity cases. |
| 2026-10-26 | Gate 4 | Owner approved the revised Gate 4 tool (docs/gate4/README.md; run adu-ecb5971cce) and directed the project to Gate 5. Carried forward: no cap or pooling for small high-value villages; Madison stays on its path for now and is re-examined when 2026 is complete (December); unknown-rules switch, legislative districts and a screen-reader pass are Gate 5 work. |
| 2026-10-26 | Gate 5 | Owner accepted the recommendation: the statewide ADU foundation is good enough to extend (docs/gate5/README.md section 9). Three small fixes follow: an on-screen sentence on why areas differ, a district table in the brief, and the screen-reader pass. Next: two more benchmark scenarios. |
| 2026-10-26 | Accessibility | Manual VoiceOver/NVDA pass deferred by the owner; must be done before submission (checklist in docs/gate5/ACCESSIBILITY.md). |
| 2026-10-26 | AQ-044 | TOD: owner confirmed the ladder of stop definitions, narrowest to widest, with 15-minute service as the main case, and a focus on city-specific studies (Milwaukee and Madison areas) plus a statewide rule for the rest. Madison data licence route open. |
| 2026-10-26 | AQ-045 | TOD: owner chose the federal National Transit Map as the common stop source for every city, and set Madison Metro's schedule file aside pending office hours (questions 24 and 25). Frequency is to be tested at the route level from sources whose terms allow it. |
| 2026-10-26 | AQ-046 | Parking: owner read the mixed result for small repeal places (7 of 16 above comparison places, 8 below) as evidence that fits expectations. Model different city sizes differently, with a multi-variable regression across US repeal cities to find the cut-offs and the effect by city type; held-out cities decide. |
| 2026-10-26 | AQ-047 | TOD Gate 1: density rules from measured cases, keeping the most effective well-measured designs; no affordability mandate; parking minimums left to the parking scenario, with TOD alone, parking alone and both combined shown; two methods with the Madison test (Chicago fallback); scenario names from real cases; places already at TOD zoning depend on the evidence; "Where" by station areas. T1 to T3 still open. |
| 2026-10-26 | AQ-046 | Parking: first full comparison of 24 US repeal places found no measurable average permit change over 3 years (−1.29 per 1,000 existing homes per year, range −3.68 to +2.33), and no size split beat one average. Owner accepted option A "if necessary": central = no measurable change; upper = top of the range the data allow; no lower case below zero (docs/parking/COMPARISON_RESULTS.md). |
| 2026-10-26 | AQ-048 | Parking: owner approved Gate 1 P1–P9 and Gate 2 G2-1 to G2-5 as recommended ("yes to all for now"): option A with the all-units upper case, flat years 4–5, one average, no cost line; Milwaukee MPROP adjustment to the baseline; long-run baseline range. |
| 2026-10-26 | AQ-049 | TOD Gate 2: owner approved all recommendations G2-1 to G2-9 (more moderate-rent cases first; SB 79 floors unless evidence changes; Growing MKE coded; suburbs fallback; single-family lots eligible). |
| 2026-10-27 | AQ-048 | Parking Gate 3: owner approved G3-1 to G3-3 ("all looks good"): labels "No measurable change" and "High end of the evidence", median place as a reference line at 0; towns kept in the upper case with "towns at zero" as a sensitivity; combined TOD + parking view shows sum and larger-of-two near stops (elsewhere added), per the contract text in docs/parking/GATE3_PACKET.md section 5. North Carolina HB 162 (statewide, effective 2027-01-01) has no post-law permits yet, so it cannot enter the comparison; it is tracked as a future check. |
| 2026-10-27 | AQ-050 | TOD: owner adopted citywide net-effect sizing (Los Angeles, Stacy et al., Auckland, corrected and per upzoned home), per-acre response for placement only, Wisconsin-measured per-acre rate as a capped sensitivity. |
| 2026-10-27 | AQ-051 | TOD Gate 3 approved: three net-effect scenarios (about 171 / 2,509 / 17,148), suburbs placement, year-5 smoothing, timing caveat, go to Gate 4. |
| 2026-10-27 | AQ-048 | Parking Gate 4: owner accepted the parking screens and the three pilot places (Milwaukee, West Allis, Eau Claire) ("Approved. Move forward"); the parking reform is marked ready in the tool. Next: Gate 5. |
| 2026-10-27 | AQ-048 | Parking Gate 5: owner accepted the parking scenario as good enough to submit (G5-1) and asked for a map on the parking Where tab (G5-2). |
| 2026-10-27 | AQ-052 | TOD: owner approved a California AB 2097 test of parking near transit, alone and combined with earlier local upzoning (plan written before counting). |
| 2026-10-27 | AQ-053 | TOD Gate 4 accepted: TOD marked ready; Gate 3 amendments confirmed; Gate 5 next; combined view main rule = larger of the two near stops, sum as upper bound (parking agreed). |
| 2026-10-27 | AQ-048 | Combined TOD + parking view: owner adopted "larger of the two" near transit stops as the headline rule, with the sum shown as an upper bound (2027–2031 high case 43,693 headline, 46,810 upper bound); the California AB 2097 test found no extra gain from combining (Los Angeles −2.62 per 1,000 homes, range includes zero). |
| 2026-10-27 | AQ-054 | Cross-reform conventions: shared unit (additional homes permitted per year), ACS 2020–2024 home count (2,778,572) for cross-reform figures, one median-line rule (≥4 real cases). |
| 2026-10-27 | AQ-055 | TOD finalized (Gate 5): numbers frozen (14,464 baseline near stops; 171 / 2,509 / 17,148 extra homes 2027-2031); housekeeping T5-3 to T5-6 approved. |
| 2026-10-27 | AQ-056 | TOD: widen the case set; if a narrower law design or trait model predicts held-out cities, the modelled law may be narrowed to it (frozen numbers change only with owner approval). |
| 2026-10-27 | AQ-048 | Parking high end: owner chose option B, the placebo-based high end (+0.91 permits per 1,000 existing homes per year; 12,184 permits 2027–2031, was 20,672 from resampling, now a sensitivity). Combined TOD + parking high case: 27,953 headline, 29,331 upper bound (were 35,582 and 37,819). |
| 2026-10-27 | AQ-048 | Parking placebo rerun with the full pool of 3,896 never-repealed cities (owner request): high end +0.96 per 1,000 existing homes per year, 12,947 permits 2027–2031 (was 12,184 from 20 cities per place). Combined high case 28,631 headline, 30,095 upper bound. |
| 2026-10-28 | AQ-048 | Parking: owner approved adding 3 rescued places (South Bend as the combined St. Joseph County permit row, Gastonia and Avondale Estates with missing years trimmed; docs/parking/SALVAGE_RESULTS.md). 74 places: average −1.14; placebo run raised to 20,000 sets for precision; high end +0.95, 12,759 permits 2027–2031 (was 12,947). Combined high case 28,464 headline, 29,907 upper bound. Census-count method: tracks permits for places of 2,500+ homes (about 10–20% below), not for small towns. |
| 2026-10-28 | AQ-058 | ADU placebo: keep the model; rising no-law baseline (605 → 1,083; addition 8,757 → 8,324; total 9,361 → 9,408) shown as a baseline-only sensitivity. |
