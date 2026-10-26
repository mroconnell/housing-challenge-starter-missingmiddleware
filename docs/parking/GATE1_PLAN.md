# Parking requirement reduction: Gate 1 plan

Written 2026-10-26 by the parking conductor. Status: plan for owner review; no Gate 1 work has been accepted yet.

The question, in the owner's terms: **if Wisconsin reduced or eliminated minimum parking requirements statewide at the challenge benchmark, how many additional homes would be permitted over 2027–2031 compared with current law, how confident are we, why, and where?**

Benchmark (verbatim, [CHALLENGE_SPEC.md](../CHALLENGE_SPEC.md)): *Reduce or eliminate minimum parking requirements. Specify assumptions about developer-provided parking absent mandates.*

## 1. Research questions

1. **Which reforms really happened?** Which states and cities removed parking minimums for housing everywhere, and which made partial or hollow changes (transit-only, affordable-only, small-project-only, coastal or county carve-outs, minimums replaced by discretionary review, caps rather than removal)? Adoption, effective and local-compliance dates recorded separately.
2. **How much parking do developers build without a mandate?** For each case that measured it: spaces per unit built after reform, compared with the old minimum, by project type (multifamily size, small infill, single-family), and the share of projects that built below the old minimum (the "binding share"). This is the benchmark's required assumption and becomes a range, not one number.
3. **What happened to homes, not just parking?** Before/after permits in the cities with citywide removal (Buffalo 2017, Minneapolis 2021, Portland and Eugene 2023, San Jose 2022, others found), against comparison cities, by year since reform. Each figure marked "observed" or "source lead".
4. **What does a space cost, and how does cost turn into homes?** Cost per surface, tuck-under and structured space; land per space; how a saved cost per unit moves the number of projects that pencil (a supply response taken from published elasticities, not chosen).
5. **Where would minimums bind in Wisconsin?** A statewide proxy using data already in the repo: structure type (5+, 2–4, 1-unit), density or urban context, lot size, and a small set of coded local minimums (Milwaukee, Madison, plus a mid-size and a suburban place) as spot checks only.
6. **Does it transfer?** Do Wisconsin's softer markets respond like Minneapolis or Buffalo? A pre-registered check on comparison cities of similar size and market, as the Madison-like-cities test did for ADUs.

## 2. Policy-taxonomy search

Step 1, check existing classifications: the Parking Reform Network's mandates map and database (coverage, method, how it codes "removed" versus "reduced", licence); Mercatus, Pew, Sightline, Strong Towns and Institute for Justice trackers; academic reviews (Shoup; Gabbe, Pierce and Clowers; Hess and Rehler).

Step 2, if none separates real from weak reform, build the classification from statute and ordinance text, one row per law: scope (all uses / housing / multifamily only), geography (statewide, transit areas, city size), project-size limits, affordability conditions, replacement mechanism (discretionary review, caps, in-lieu fees), dates, and a benchmark rating (at, near, weaker) with the reasoning. Starting leads from the one-off scan, all unverified: North Carolina HB 162 (2027), Connecticut PA 25-1, Oregon CFEC, California AB 2097, Colorado HB24-1304, Washington SB 5184, Illinois People Over Parking Act, Maine, Montana, Minnesota, New Hampshire, Texas, Virginia, Rhode Island.

Expectation: state laws are too recent for post-law permit data, so the response will probably come from city reforms plus a cost-per-unit model. Both channels will be built and tested against each other on held-out cities if the data allow.

## 3. Mechanism options (decided at Gate 3 by held-out tests)

- **A. Before/after permits:** the change in multifamily permits per 1,000 homes in cities that removed minimums, applied to Wisconsin places where minimums bind.
- **B. Cost × supply response:** spaces no longer required (old minimum minus what developers choose to build) × cost per space ÷ cost per unit → percentage cost cut × supply elasticity × baseline permits in binding segments.
- **C. Both,** with B as the transferable method and A as its check.

## 4. Data candidates (licence to be checked for each before use)

| Need | Candidate | Notes |
| --- | --- | --- |
| All-housing baseline | Census Building Permits Survey, already in `data/processed/foundation/` | Shared piece; see section 6 |
| Reform taxonomy | Parking Reform Network database; statute and ordinance text | Licence of PRN data to confirm |
| Parking built after reform | Seattle, Buffalo, Minneapolis, San Diego, Portland studies and permit records | Study tables as source leads unless the city publishes the file |
| Before/after permits | Census BPS by place (all US places, already fetched for some states); city open data | BPS is public domain |
| Cost per space | Published construction-cost surveys and studies (e.g. Shoup, RSMeans-based estimates via public reports) | Avoid paywalled sources |
| Where minimums bind | BPS structure types, census block density, V12 parcels (lot size), coded spot-check codes | Mostly already in the repo |
| Transit areas (for partial-reform comparisons) | The TOD session's GTFS stop layer | Shared, not fetched twice |

## 5. Tool outputs expected (to be confirmed at Gate 2)

From the ADU tool, likely fillable: a baseline line and three scenarios by year labelled by meaning; a median or reference line of real cases if enough exist; sensitivities grouped by what they move, including the developer-provided-parking assumption; the data-versus-assumption trace; pilot pages. The "Where" screen probably needs a different design, because the effect will concentrate in multifamily permits in larger places: likely a ranked list of cities and districts rather than a 1,925-place map. That design is an owner decision at Gate 2.

## 6. Shared piece: the all-housing baseline (built now)

All permitted units by area, year and structure type (1, 2, 3–4, 5+) from the Census Building Permits Survey; a 2027–2031 current-law projection chosen by a held-out-year test; an explicit unallocated row that reconciles to the state; missing reports treated as missing, not zero. Outputs in `reference/housing_baseline_*.csv`, documented in `docs/shared/HOUSING_BASELINE.md`, with tests. The TOD session is waiting on it, so it starts in parallel with the research.

## 7. Decisions needed from the owner

| # | Decision | Recommendation |
| --- | --- | --- |
| P1 | Outcome | All housing units in permits at issuance, the same milestone as ADUs and TOD |
| P2 | Law start | Stylized 1 January 2027, as for ADUs |
| P3 | Law strength | Full removal of minimums for all housing statewide (the benchmark's "eliminate"), with a "reduce" variant (e.g. caps at 0.5 or 1 per unit) as a sensitivity if the taxonomy finds enough such laws |
| P4 | Developer-provided parking | Taken from the post-reform studies as a range (spaces per unit by project type), not chosen; shown as its own sensitivity |
| P5 | Mechanism | Build both A and B; held-out cities decide at Gate 3 |
| P6 | Baseline projection | Chosen by a held-out-year test among simple candidates (recent average, trend, structure-type mix held fixed) |
| P7 | Start the baseline now | Yes, in parallel with research, since TOD depends on it |
