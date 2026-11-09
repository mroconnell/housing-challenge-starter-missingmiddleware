# Middle housing: smallest effect each test could detect (power check)

Run 2026-11-09 on Ryan's go-ahead ("power first, yes", 2026-11-08). Research only. Nothing is locked.

- **Code:** [`scripts/middle_power_check.py`](../../scripts/middle_power_check.py).
- **Outputs:** `reference/middle_power_test1.csv`, `_test2.csv`, `_test3.csv`.
- **Data:** Census place permits for **2012–2018 only**. The script skips later files when it reads them, so no year from a reform period is touched.
- **Places:** candidate cities are never stand-ins or fake-treated places. States with a candidate law are never fake-treated.
- **Unit:** homes permitted per 1,000 single-family homes (ACS 2020–2024, detached plus attached) per year.
- **No-reform windows:** before 2012–2014, after 2016–2018.
- **Power rule:** an 80% chance of detection with the 90% intervals used elsewhere, so the multiplier is 1.645 + 0.842.

## Measures

| Measure | What it counts |
| --- | --- |
| All homes | Every building size |
| Homes in 1–4 unit buildings | Leaves out every 5+ building (Census cannot cap at 10, 30 or 100) |
| Homes in 2–4 unit buildings | Census's direct middle-housing column; misses most townhouses and split-lot homes, which Census files as 1-unit |

## Results (Census fill-ins included; the reported-only version is in the CSVs)

### Test 1. Two law states (Oregon and California) against similar places elsewhere

Spread from 42 fake law states: each untested state in turn against same-division places in other states, matched by population band.

| Measure | Smallest detectable rise (relative to comparison places) | Typical before rate (median fake state) | Rise in rate terms |
| --- | ---: | ---: | ---: |
| All homes | +89% | 10.7 | about +9.5 |
| Homes in 1–4 unit buildings | +66% | 6.7 | about +4.4 |
| Homes in 2–4 unit buildings | +170% | 0.42 | about +0.7 |

### Test 2. Oregon cities near the 10,000 line (the law's own count)

Spread from non-Metro Oregon cities of 5,000–24,999 outside 9,000–10,999.

| Band | Covered | Left out | All homes | Homes in 1–4 unit buildings | Homes in 2–4 unit buildings |
| --- | ---: | ---: | ---: | ---: | ---: |
| 9,500–10,499 | 4 | 4 | 25.3 | 9.8 | 2.1 |
| 9,000–10,999 | 5 | 6 | 21.7 | 8.4 | 1.8 |
| 7,500–12,499 | 7 | 11 | 17.3 | 6.7 | 1.4 |
| 5,000–14,999 | 9 | 20 | 14.4 | 5.6 | 1.2 |

Values are the smallest detectable gap per 1,000 single-family homes per year. In the 9,000–10,999 band, homes in 1–4 unit buildings need about 26 extra homes per city per year. With reported-only data, the 9,000–10,999 band has just 1 covered city and 3 left out.

### Test 3. One city against at least 20 stand-in cities

| City | All homes | Homes in 1–4 unit buildings | Homes in 2–4 unit buildings | 1–4 bar in homes per year |
| --- | ---: | ---: | ---: | ---: |
| Minneapolis | 23.9 | 10.8 | 1.8 | about 990 |
| Raleigh | 25.2 | 10.7 | 2.1 | about 1,390 |
| Spokane | 15.8 | 8.2 | 1.2 | about 570 |
| Walla Walla | 29.6 | 15.0 | 2.2 | about 150 |
| Portland | 25.1 | 7.5 | 1.3 | about 1,320 |

Values are the smallest detectable gap per 1,000 single-family homes per year. Rule: (stand-ins' 95th percentile − median) + 0.842 × their standard deviation.

## Reading

- **Leaving out 5+ buildings roughly halves the noise** against all homes, in every test. This supports Ryan's proposal to stop at 4.
- **2–4 unit homes has the smallest bar in homes**, because its base is small. It misses most townhouses and split-lot homes, though, so it works as a second measure, not the main one.
- **Caveats:**
  - The no-reform windows (2012–2018) fall in the recovery after the housing crash, so they may overstate normal noise.
  - The Test 1 spread treats Oregon and California like typical states.
  - The Test 3 formula is an approximation.
