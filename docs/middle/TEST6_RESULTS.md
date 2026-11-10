# Test 6 results: how much Census permit counts miss

Locked plan: [TEST_PLAN_LOCKED.md](TEST_PLAN_LOCKED.md). Code: [`scripts/middle_test6_census_gap.py`](../../scripts/middle_test6_census_gap.py), committed before the run. Output: `reference/middle_test6_census_gap.csv`. Run 2026-11-09. Report only.

**Headline.** Census counts of homes in 2–4 unit buildings (M2) see well under half of middle housing once townhouses are counted. Where records include townhouses, they show 1.5 to 3.2 times as many homes as Census M2. In California and Minneapolis, the gap was about the same before and after the reform.

Ratio = townhouse-inclusive record count ÷ Census count, same places and years. Brackets give the 90% bootstrap range: over places for California, over years for the cities.

| Place | Record count (M5) | Before | After |
| --- | --- | --- | --- |
| California, 340 matched places | Progress reports: SFA + "2 to 4" | **2.31 × Census M2** (1.98–2.80) | **2.58 ×** (1.92–3.38) |
| California | Progress reports: "2 to 4" only | 1.22 × (0.79–1.55) | 1.40 × (0.74–2.05) |
| Austin | Two-family + 3–4 family + condominium single-family (townhouse proxy) | **3.24 ×** (2.64–3.93), 2020–2022 | 2.33 ×, 2025 only (one year, no range) |
| Minneapolis | Two-family + 3–4 + townhouse | **1.47 ×** (1.39–1.51), 2017–2018 | **1.45 ×** (1.38–1.54), 2020–2025 |

Against Census M1 (homes in 1–4 unit buildings), the record counts are 0.19–0.62 times as large, because M1 also includes every detached house.

## Reading

- **Census M2 understates the level of middle housing** by a factor of about 1.5 (Minneapolis) to 3 (Austin, California). Any count of homes from M2 needs that stated beside it.
- **For detecting change, what matters is whether the gap moved with the reform.**
  - California: 2.31 → 2.58, with overlapping ranges.
  - Minneapolis: 1.47 → 1.45.
  - Austin's after period is one year only.
  - So there is no sign that Census misses more after reforms in these places. A real change in middle housing should show up in M2, scaled down.
- **Limits:**
  - California matches places by name; 340 of about 480 jurisdictions matched.
  - Austin's townhouse proxy (condominium single-family) is rough.
  - Minneapolis's record series starts in December 2016.
  - Portland is out because no licence is stated for its data.
