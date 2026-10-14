# Missing Middleware Project Plan

Updated October 14, 2026. Status: planning and data exploration.

Missing Middleware will help a Wisconsin legislator or legislative aide understand where housing development opportunities exist and how state reforms might change housing production over five years. Census data will establish housing-stock and production baselines; Wisconsin parcels will locate potential development opportunities; local records will improve detail where available.

## Legislative decisions and adoption

The central decision is which bill, or combination of bills, to support. Let users compare policy provisions and explain the resulting statewide housing improvement to people in specific legislative districts. Describe each scenario as a set of modeled provisions; attach an actual bill name or number only after checking its text, scope, and effective dates.

For each comparison, show the baseline, additional permitted homes over five years, the range of outcomes, where the effect occurs, and the assumptions that matter most. Provide a district view and an exportable plain-language brief that carries its sources, assumptions, model version, and limitations with it. Use conditional language rather than presenting a scenario as a promise of construction.

Design for continued use in state capitols: a reproducible Wisconsin example, documented input formats, replaceable state profiles, inspectable calculations, and outputs that legislative staff can explain without the development team present. Prioritize analytical credibility, reusable assumptions, and a compelling geographic explanation. The project is an intensive solo-team effort; weekly capacity remains unspecified.

## Scope and initial scenarios

Wisconsin is the initial application state. ADUs are a firm priority; transit-oriented density and parking-requirement reduction are the other leading scenarios. Keep common baseline, parameter, and output definitions usable for all five contest reforms, while concentrating initial research on these three. Missing middle and development-fee reduction remain candidates as the evidence develops.

Use a five-year horizon and a baseline reflecting current policy and already-scheduled changes. Homes permitted is the initial candidate outcome because Census provides a consistent production series. Confirm that choice during the data audit. Permitted units, completed homes, and net housing-stock growth must remain separate measures; replacement permits do not automatically represent net additions to the stock.

## Part One Configure My State

Provide a prepared Wisconsin profile and allow users to replace or supplement supported datasets. Begin with reproducible data preparation and a small number of documented input formats; develop the upload workflow once the useful inputs are established.

The diagnostic map should combine neighborhood housing conditions with parcel-level development opportunities. Users should be able to inspect housing counts and types, recent permitted production, transit access by radius and walking network, and candidate redevelopment sites. Show the source geography, vintage, coverage, and uncertainty beside each finding.

Label inputs and outputs as **observed**, **calculated**, or **assumed**. Housing counts assigned from a neighborhood to individual parcels are modeled allocations, not observed parcel counts. Missing records must not appear as zero homes or zero construction.

Investigate low development near transit and projects below plausible density benchmarks. Distinguish legal limits, project economics, physical constraints, owner participation, and data gaps. A density gap alone does not establish political obstruction or the number of homes a reform would produce.

The output of this stage is a versioned state profile containing the baseline data, geographic joins, coverage report, policy assumptions, and parameters passed to Part Two.

## Defaults when local evidence is limited

Use documented averages or other representative defaults for numerical parameters when reliable local estimates are unavailable. Prefer comparable housing types, market conditions, development forms, and transit contexts over one national average. Choose the pooling method and parameter values during exploration; no default values are established yet.

Each default must include its definition and units, source population and period, selection or weighting method, central value, plausible range, geographic applicability, and version. Identify where it is used and let the user inspect or override it. Assess local evidence quality before replacing a default; weak or noisy observations can inform the range without automatically determining the central value. Widen uncertainty where transferability is poor, and show whether a different reasonable default changes the preferred bill or package.

Missing local evidence does not validate a default. Legal eligibility, binding physical exclusions, and known local restrictions require explicit rules rather than an average. Do not silently substitute an average for an unknown legal condition or label an assumed value as observed.

## Census and parcel data strategy

The [data-source plan](../data/DATA_SOURCES.md#project-data-plan-for-wisconsin) links the authoritative sources and records their intended roles.

| Input | Role in the Wisconsin profile | Interpretation |
| --- | --- | --- |
| Census Population Estimates Program housing-unit totals | Annual state and county housing stock | Use one consistent vintage. Annual stock changes reflect net growth, not gross construction. |
| ACS five-year housing tables | Neighborhood totals, occupancy, housing types, and age | Retain margins of error. These are period estimates; differences between overlapping releases are not annual construction counts. |
| 2020 Census block housing counts | Finer spatial baseline around transit | Counts describe 2020 geography and conditions, not current parcel occupancy. |
| Census Building Permits Survey | Annual permitted housing units by state, county, and permit-issuing place | Counts authorized units, not permit rows, starts, or completions. |
| Census TIGER/Line boundaries | Map and join Census statistics using geographic identifiers | Match boundaries to the statistical release; handle boundary changes explicitly. |
| Wisconsin V12 parcels | Parcel geometry, area, identifiers, addresses, and valuation context | The statewide schema does not supply numeric dwelling counts or current zoning capacity. |
| Local zoning, assessor, and permit records | Refine eligible sites, existing units, and development activity | Add detail where accessible; report the remaining geographic coverage gaps. |
| Agency transit schedules and walking-network data | Define qualifying service and accessible land | Validate station entrances, service dates, frequency, and network coverage. Review source reuse terms. |
| Wisconsin legislative district boundaries | Explain the same scenario in Assembly or Senate districts | Pin the boundary vintage. Distinguish observed locations from geographic allocations and reconcile district totals separately for each chamber. |

Keep source years separate: 2020 block counts, 2020–2024 ACS estimates, annual stock estimates through 2025, and 2026 parcel geometry describe different periods. A common analysis date requires explicit update assumptions, not relabeling older observations as current.

Census supplies a statewide baseline without requiring a complete parcel-level permit inventory. Detailed maps can begin in selected Wisconsin urban areas, while statewide outputs retain county or neighborhood resolution elsewhere. Do not extrapolate an urban pilot uniformly across the state.

## Part Two Model the Future

Each policy scenario should trace its output to the state profile through four steps:

1. Define which opportunities are affected and what the policy changes beyond the baseline.
2. Estimate additional legal capacity and the development forms it permits.
3. Evaluate financial and physical feasibility, owner or developer participation, and delivery timing.
4. Compare five-year permitted units with the no-reform baseline under the same economic assumptions, then aggregate to Wisconsin.

For TOD, specify qualifying transit, proximity, allowed height or density, and parking treatment. Compare radius access with walking access. Prevent overlapping station areas from counting the same opportunity twice.

For parking reform, distinguish cost savings on unchanged projects, extra units on existing projects, newly feasible projects, and projects that retain the same parking. Allow developers to provide parking after minimums are removed. Keep parking effects within ADU and TOD scenarios consistent with the standalone parking scenario.

For ADUs, identify eligible existing single-family opportunities, account for current local rights, and investigate construction cost, financing, uptake, and permitting. ACS housing types can inform an aggregate denominator but cannot establish an individual parcel's legal eligibility.

Establish each reform's effect separately before implementing package comparisons. Comparing bills and combinations is a core product requirement. Recompute a package using the combined provisions and shared opportunities; do not add standalone uplifts. For example, a TOD scenario that already eliminates parking minimums cannot receive the same parking benefit a second time. Report ranges as assumption-based scenarios unless statistical confidence intervals can be justified.

## District explanations

Provide separate Wisconsin Assembly and Senate views using documented boundaries. Allocate scenario results from the finest defensible source geography and show the method and uncertainty where neighborhoods cross district boundaries. For each chamber, district results plus any explicitly unallocated portion must reconcile to the statewide result from the same scenario run; do not combine Assembly and Senate totals.

The district brief should explain the estimated housing change, the kinds of opportunities contributing to it, the leading assumptions, and how the district relates to the statewide result. Include geographic coverage and avoid implying that inferred parcel allocations identify projects that will actually be built. A low modeled local uplift can coexist with a substantial statewide benefit.

## Optional economic scenarios

Economic scenarios are a nice-to-have after the core diagnostics, bill comparisons, and district explanations work. If time or evidence is insufficient, present this layer as a narrative next step rather than shipping unsupported economic responses.

Explore borrowing rates and credit availability, construction-cost growth, rents or sale prices, and homeowner cash or equity as distinct inputs. A named preset such as high inflation must specify these inputs rather than applying an unexplained multiplier to every policy. Apply the same economic conditions to the baseline and reform cases, and keep nominal and inflation-adjusted amounts consistent.

Treat increased ADU investment during inflation as a hypothesis to test, not a preset direction. Financing conditions can work against participation: [Federal Reserve guidance](https://www.federalreserve.gov/faqs/why-do-interest-rates-matter.htm) explains the role of interest rates in borrowing and spending, and [CFPB guidance](https://www.consumerfinance.gov/ask-cfpb/what-is-a-home-equity-line-of-credit-heloc-en-107/) notes that home-equity lines typically have variable rates. Likewise, a fixed nominal fee saving can shrink relative to rising project costs, but its effect on project feasibility depends on revenues, financing, and the project's starting position.

## Comparison evidence

Use Minneapolis, Salt Lake City and other Utah station areas, and Austin as candidate TOD and parking comparisons. Include slow or unsuccessful development as well as successful projects. Record actual zoning effective dates, transit openings, subsidies, market conditions, and project milestones separately. Peer densities inform plausible development patterns; they do not identify a causal policy uplift by themselves.

Utah's [Housing Unit Inventory](https://gis.utah.gov/products/sgid/planning/housing-unit-inventory/) is a promising source for existing housing density and type. It is an assessor-derived inventory, with varying coverage and vintages, rather than a permit ledger. Salt Lake City's active-permit layer requires a historical-coverage and date-quality audit before use in production estimates.

California [HCD Annual Progress Reports](https://www.hcd.ca.gov/apr) are a candidate source for ADU uptake and project progression, and possibly SB 9 evidence. Audit reporting coverage, repeated projects and stages, and differences between California and Wisconsin before transferring assumptions. SB 9 is not identical to the contest's 2–6-unit missing-middle scenario.

## First implementation milestones

- [ ] Acquire a pinned Census baseline for Wisconsin: annual county stock estimates, ACS housing tables with margins of error, 2020 block counts, BPS unit counts by structure category, and matching boundary files.
- [ ] Record source URLs, versions, geographic coverage, units, access dates, reuse terms, and transformations in Data Provenance. Keep raw data outside version control.
- [ ] Produce county summaries and one neighborhood map. Reconcile differing definitions and vintages, and retain missingness and reporting-quality indicators. Document that some Census products share underlying inputs rather than treating agreement as independent validation.
- [ ] Establish documented numerical defaults and their ranges, evidence-selection rules, and user overrides. Identify which results depend heavily on transferred assumptions.
- [ ] Join Wisconsin parcels to the pilot geography and audit addresses, area, valuations, parcel overlaps, and local availability of dwelling counts and zoning. Start with Madison and Milwaukee as candidate pilots.
- [ ] Build one TOD access experiment comparing radius and walking access. Display Census housing counts at their observed geography and distinguish any finer modeled allocations.
- [ ] Define one concrete TOD reform and a transparent feasibility and uptake calculation. Demonstrate its five-year result against baseline before extending to ADU and parking scenarios.
- [ ] Compare individual reforms and a combined package, accounting for shared opportunities and overlapping provisions.
- [ ] Add Assembly and Senate district summaries and an exportable district brief. Check reconciliation to statewide results and communicate uncertainty from geographic allocation.
- [ ] Add sensitivity analysis for market conditions, participation, timing, parking, and geographic allocation. Identify which assumptions reverse scenario rankings.
- [ ] Implement reproducible setup, acquisition, run, and test commands. Core checks should cover geographic aggregation, district reconciliation, duplicate opportunities, overlapping package provisions, baseline equivalence when reform inputs are unchanged, and the distinction between permits and stock.

Economic presets follow these core milestones if evidence and time support them; otherwise include their proposed mechanisms in the presentation's next steps.

The first milestone is complete when a clean acquisition process produces the documented Wisconsin stock and permitted-production summaries plus a neighborhood housing map. It does not depend on resolving every parcel's dwelling count.

## Decisions to resolve through exploration

Choose the pilot geography, baseline projection method, analysis date, specific TOD policy, and initial parameter ranges after the data audit. Determine whether local records justify parcel-level existing-unit estimates or whether the first diagnostic should retain block and block-group counts. Technology choices and statewide generalization should follow that experiment.

Keep the contest's three required reforms and five-year horizon fixed. If fee reduction is implemented, retain its prescribed $50,000-to-$25,000 total-development-fee benchmark separately from scenarios using observed local fees. The [challenge specification](CHALLENGE_SPEC.md) summarizes requirements; the linked official rules and handbook govern.
