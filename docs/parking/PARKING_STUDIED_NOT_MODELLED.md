# Parking minimum repeal: studied, not modelled (draft page, option A)

**Status: draft, kept on the shelf.** On 2026-11-12 (21:58 UTC) Ryan chose to take parking reform off the tool for now (option B), and to keep this page, option A, for later. The tool's parking screens as they stood before removal are preserved at git tag `parking-ui-before-removal-2026-11-12`. All numbers below come from audited results in [WORK_SESSION_RESULTS.md](WORK_SESSION_RESULTS.md).

## In one line

We tested whether repealing parking minimums for housing adds homes. The answer is a tight "we can't tell", so the tool does not put a number on it.

## What we tested

- **Places.** 74 US cities and villages that removed parking minimums for all housing between 2015 and 2024. Each was compared with similar places that kept their minimums.
- **Fake repeals.** The same comparison was run 20,000 times on groups of places that never repealed (9,185 places in all). This shows how big a "result" chance alone produces.
- **Many follow-up checks**, each planned before its count and reviewed by an independent audit.

## What we found

Effects are extra homes permitted in Wisconsin over 2027–2031, with 90% ranges.

| Question | Answer |
|---|---|
| All homes, main method | 15,380 fewer (46,268 fewer to 19,649 more) |
| All homes, second method | 12,873 fewer (44,571 fewer to 4,854 more) |
| Small projects (2–4 unit homes) | 899 fewer (3,930 fewer to 2,360 more) |
| Could the small-project test have seen a real effect? | Yes. A real boost of about 4,700 homes would be caught 86% of the time. |
| Do partial reforms, weighted by how much of a town they cover, tell us more? | No. Pooling 98 places gave the same answer, with no narrower range. |
| Does any city trait predict which places gain? | No. About 90 traits, and dose, population and city type, all did worse than one plain average. |
| New York's 2016 relief near transit, and San Francisco's 2008–09 plan areas | Can't tell. Building near transit was already rising before New York's rule. San Francisco's parking change came bundled with upzoning. |

## Why parking minimums rarely bind in Wisconsin

We fitted a 2–4 unit building onto every residential lot in 11 Wisconsin places (24.4% of the state's homes). We then checked whether the required parking still fit.

| Building | Lots where parking blocks a building that otherwise fits |
|---|---|
| 2 homes | 0.0% to 0.2% |
| 3 homes | 0.0% to 6.5% |
| 4 homes | 1.4% to 17.2% |

The low end assumes every lot has an alley. The high end assumes none does. Blocking concentrates in 4-unit buildings in a few cities: Green Bay, Oshkosh, and Milwaukee on lots already zoned for 3–4 units. Waivers are not modelled, so blocking is somewhat overstated.

## What this means for a policymaker

- **Repealing parking minimums on its own** has no measurable effect on how many homes get built, in either direction. Every range includes zero.
- **A large boost is unlikely.** A boost of 4,700 or more small-project homes would probably have shown up.
- **A small boost can't be ruled in or out,** for example under about 2,500 homes.
- **Parking relief may still matter as part of a package,** such as transit-oriented density or ADU laws, where it removes one of several barriers. Those scenarios already assume no extra parking where their benchmarks allow it.

## What the tool cannot say about parking

- Whether parking repeal changes **what** gets built: fewer garages, cheaper units, different layouts.
- Effects in the few Wisconsin places where parking binds hard, measured on their own.
- Effects of parking reform combined with other changes, beyond what the TOD and ADU scenarios assume.
