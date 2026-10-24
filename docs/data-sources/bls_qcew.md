# BLS Quarterly Census of Employment and Wages (QCEW), construction

**Status:** Fetched (last fetch 2026-10-24)  
**Source id:** `bls_qcew`  
**Handbook listing:** Bureau of Labor Statistics (construction employment, costs)

## Summary

| | |
|---|---|
| Publisher | U.S. Bureau of Labor Statistics |
| What it is | Establishment counts, employment and wages by industry from unemployment insurance records. Sample is NAICS 23 (Construction). |
| Geography | Nation, state, MSA and county. |
| Time coverage and update frequency | Quarterly and annual. Annual file released about 9 months after year end. |
| Units | Establishments (count), employment (jobs), wages (dollars). Annual pay is dollars per employee per year. |
| Access method | Open data CSV slices, `https://data.bls.gov/cew/data/api/{year}/{qtr or a}/industry/{naics}.csv` (also /area/{fips}.csv). |
| License | Public domain (U.S. federal government work). |
| Use in our model | County-level construction workforce and wages, for local capacity limits and labor cost. |
| Caveats | Cells are suppressed (disclosure_code = N) where few employers exist. Construction wages are an imperfect proxy for build cost. |

## Access details

- Endpoint used for the sample: `https://data.bls.gov/cew/data/api/2025/a/industry/23.csv`
- Annual averages for NAICS 23 (Construction), every area. Other slices: by area, by size.

## Fields (38)

| Field | Type | Meaning |
|---|---|---|
| `area_fips` |  | Area code. 5-digit county FIPS, US000 for nation, Cxxxx for MSA, xx000 for state. |
| `own_code` |  | Ownership. 5 = private. |
| `industry_code` |  | NAICS code (23 = Construction). |
| `agglvl_code` |  | Aggregation level code (geography by industry detail). |
| `size_code` |  | Establishment size class. 0 = all sizes. |
| `year` |  | Year. |
| `qtr` |  | Quarter. A = annual. |
| `disclosure_code` |  | N = not disclosed for confidentiality. |
| `annual_avg_estabs` |  | Average number of establishments. |
| `annual_avg_emplvl` |  | Average employment. |
| `total_annual_wages` |  | Total wages paid, dollars. |
| `taxable_annual_wages` |  |  |
| `annual_contributions` |  |  |
| `annual_avg_wkly_wage` |  | Average weekly wage, dollars. |
| `avg_annual_pay` |  | Average annual pay per employee, dollars. |
| `lq_disclosure_code` |  | Location quotient for disclosure_code: local share of this industry divided by the national share (1.0 = same as nation). |
| `lq_annual_avg_estabs` |  | Location quotient for annual_avg_estabs: local share of this industry divided by the national share (1.0 = same as nation). |
| `lq_annual_avg_emplvl` |  | Location quotient for annual_avg_emplvl: local share of this industry divided by the national share (1.0 = same as nation). |
| `lq_total_annual_wages` |  | Location quotient for total_annual_wages: local share of this industry divided by the national share (1.0 = same as nation). |
| `lq_taxable_annual_wages` |  | Location quotient for taxable_annual_wages: local share of this industry divided by the national share (1.0 = same as nation). |
| `lq_annual_contributions` |  | Location quotient for annual_contributions: local share of this industry divided by the national share (1.0 = same as nation). |
| `lq_annual_avg_wkly_wage` |  | Location quotient for annual_avg_wkly_wage: local share of this industry divided by the national share (1.0 = same as nation). |
| `lq_avg_annual_pay` |  | Location quotient for avg_annual_pay: local share of this industry divided by the national share (1.0 = same as nation). |
| `oty_disclosure_code` |  | Over-the-year change in disclosure_code from the prior year. |
| `oty_annual_avg_estabs_chg` |  | Over-the-year change in annual_avg_estabs from the prior year. |
| `oty_annual_avg_estabs_pct_chg` |  | Over-the-year percent change in annual_avg_estabs from the prior year. |
| `oty_annual_avg_emplvl_chg` |  | Over-the-year change in annual_avg_emplvl from the prior year. |
| `oty_annual_avg_emplvl_pct_chg` |  | Over-the-year percent change in annual_avg_emplvl from the prior year. |
| `oty_total_annual_wages_chg` |  | Over-the-year change in total_annual_wages from the prior year. |
| `oty_total_annual_wages_pct_chg` |  | Over-the-year percent change in total_annual_wages from the prior year. |
| `oty_taxable_annual_wages_chg` |  | Over-the-year change in taxable_annual_wages from the prior year. |
| `oty_taxable_annual_wages_pct_chg` |  | Over-the-year percent change in taxable_annual_wages from the prior year. |
| `oty_annual_contributions_chg` |  | Over-the-year change in annual_contributions from the prior year. |
| `oty_annual_contributions_pct_chg` |  | Over-the-year percent change in annual_contributions from the prior year. |
| `oty_annual_avg_wkly_wage_chg` |  | Over-the-year change in annual_avg_wkly_wage from the prior year. |
| `oty_annual_avg_wkly_wage_pct_chg` |  | Over-the-year percent change in annual_avg_wkly_wage from the prior year. |
| `oty_avg_annual_pay_chg` |  | Over-the-year change in avg_annual_pay from the prior year. |
| `oty_avg_annual_pay_pct_chg` |  | Over-the-year percent change in avg_annual_pay from the prior year. |

Blank meanings: the publisher gives no description. Check the source's own metadata page before relying on that field.

## Sample rows

First 3 of 5 rows in [`data/sample/bls_qcew.csv`](../../data/sample/bls_qcew.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`.

| Field | Row 1 | Row 2 | Row 3 | Row 4 | Row 5 |
|---|---|---|---|---|---|
| `area_fips` | 01000 | 02000 | 04000 | 05000 | 06000 |
| `own_code` | 5 | 5 | 5 | 5 | 5 |
| `industry_code` | 23 | 23 | 23 | 23 | 23 |
| `agglvl_code` | 54 | 54 | 54 | 54 | 54 |
| `size_code` | 0 | 0 | 0 | 0 | 0 |
| `year` | 2025 | 2025 | 2025 | 2025 | 2025 |
| `qtr` | A | A | A | A | A |
| `disclosure_code` |  | N |  | N |  |
| `annual_avg_estabs` | 12972 | 2611 | 18865 | 8907 | 96643 |
| `annual_avg_emplvl` | 109968 | 0 | 223800 | 0 | 892415 |
| `total_annual_wages` | 8471635021 | 0 | 18546620381 | 0 | 83292325786 |
| `taxable_annual_wages` | 1281650714 | 0 | 2659058766 | 0 | 9384707261 |
| `annual_contributions` | 6976615 | 0 | 35452010 | 0 | 409856722 |
| `annual_avg_wkly_wage` | 1481 | 0 | 1594 | 0 | 1795 |
| `avg_annual_pay` | 77037 | 0 | 82871 | 0 | 93334 |
| `lq_disclosure_code` |  | N |  | N |  |
| `lq_annual_avg_estabs` | 1.01 | 1.33 | 1.07 | 1.04 | 0.66 |
| `lq_annual_avg_emplvl` | 0.98 | 0 | 1.31 | 0 | 0.92 |
| `lq_total_annual_wages` | 1.09 | 0 | 1.38 | 0 | 0.83 |
| `lq_taxable_annual_wages` | 0.93 | 0 | 1.19 | 0 | 0.87 |
| `lq_annual_contributions` | 0.72 | 0 | 0.92 | 0 | 0.68 |
| `lq_annual_avg_wkly_wage` | 1.11 | 0 | 1.06 | 0 | 0.89 |
| `lq_avg_annual_pay` | 1.11 | 0 | 1.06 | 0 | 0.89 |
| `oty_disclosure_code` |  | N |  | N |  |
| `oty_annual_avg_estabs_chg` | 305 | 14 | 448 | 631 | 2646 |
| `oty_annual_avg_estabs_pct_chg` | 2.4 | 0.5 | 2.4 | 7.6 | 2.8 |
| `oty_annual_avg_emplvl_chg` | 3133 | 0 | -2884 | 0 | -21055 |
| `oty_annual_avg_emplvl_pct_chg` | 2.9 | 0 | -1.3 | 0 | -2.3 |
| `oty_total_annual_wages_chg` | 655091123 | 0 | 543670589 | 0 | 1571492853 |
| `oty_total_annual_wages_pct_chg` | 8.4 | 0 | 3.0 | 0 | 1.9 |
| `oty_taxable_annual_wages_chg` | 41211436 | 0 | -37916385 | 0 | -245113449 |
| `oty_taxable_annual_wages_pct_chg` | 3.3 | 0 | -1.4 | 0 | -2.5 |
| `oty_annual_contributions_chg` | -1598107 | 0 | -2654584 | 0 | 10629984 |
| `oty_annual_contributions_pct_chg` | -18.6 | 0 | -7.0 | 0 | 2.7 |
| `oty_annual_avg_wkly_wage_chg` | 74 | 0 | 67 | 0 | 75 |
| `oty_annual_avg_wkly_wage_pct_chg` | 5.3 | 0 | 4.4 | 0 | 4.4 |
| `oty_avg_annual_pay_chg` | 3873 | 0 | 3452 | 0 | 3872 |
| `oty_avg_annual_pay_pct_chg` | 5.3 | 0 | 4.3 | 0 | 4.3 |

## Refresh

```sh
python3 scripts/fetch_samples.py bls_qcew
python3 scripts/build_data_dictionaries.py
```
