# Law-strength coding: OR, CA, ME, VT

This follows the "Law-strength coding rule" in docs/middle/WISCONSIN_PLAN_LOCKED.md. It uses statute and rule text only, with no permit counts or results. No repo files were edited.

- **V** = read in statute, rule or session-law text, or in an official state document.
- **S** = secondary source, or my own approximation.
- **Handbook scenario, for comparison:** 2–6 homes, 3 stories, on every single-family parcel, by right.

## Item 1. Most homes allowed by right on a lot zoned for one house

| State (law, in force) | Area | Most homes per lot | V/S | Note |
| --- | --- | ---: | --- | --- |
| Oregon (ORS 197.758 → 197A.420) | Cities of 25,000+, and cities over 1,000 in Metro, plus counties' Metro urban land | 4 (quadplex); townhouses and cottage clusters too | V | Townhouses: 1 home per new lot; a density cap must allow 4× single-family or 25 per acre (OAR 660-046-0220(3)). Cottage clusters have no density cap, with a minimum of 4 per acre. So a big lot can exceed 4 (V). |
| Oregon | Non-Metro cities over 10,000 and under 25,000 (from June 30, 2021) | 2 (duplex) | V | |
| Oregon | Non-Metro cities of 2,500–10,000 (HB 3395, 2023; deadline June 30, 2025) | 2 (duplex) | V | Bound only in the last half-year of Oregon's 2023–2025 window |
| Oregon, 2025 change (c.476, for 2027 on) | +1 home for an accessible or affordable unit (5–6 on townhouse or cottage lots) | – | V | After the window, so not used |
| California (SB 9; Gov. Code 65852.21, 66411.7) | Single-family zones in cities with any urban area; unincorporated parcels wholly inside one | 4: 2 homes per lot, plus a lot split into 2 lots of 2 each | V | Without a split: 2 primary homes. ADUs need not be allowed on a lot that uses both sections (65852.21(f)). HCD says "up to four" (V). |
| Maine (LD 2003, PL 2021 c.672, amended by PL 2023 c.192; 30-A §4364-A) | Designated growth area, or public water and sewer in a town with no comprehensive plan (empty lot) | 4 | V | |
| Maine | Elsewhere, lot with 1 existing home | 3 (1 + 2 added) | V | |
| Maine | Elsewhere, empty lot | 2 | V | |
| Maine, 2025 changes (c.385, c.733; late 2025) | 3 on every lot, 4 in growth areas or with water and sewer | – | V | Mostly after the window |
| Vermont (Act 47 of 2023; 24 V.S.A. 4412(1)(D); in force July 1, 2023) | Any district allowing year-round homes | 2 (duplex) | V | |
| Vermont | Districts served by town sewer and water | 4 | V | Not 4 if the district requires buildings of more than 4 homes |

## Item 2. Where it applies

| State | Thresholds | Zones | Growth areas | Water and sewer | V/S |
| --- | --- | --- | --- | --- | --- |
| Oregon | Over 10,000 duplex (over 2,500 from 2025); 25,000+ full; Metro full. Excluded: cities of 1,000 or fewer, land outside urban growth boundaries, unincorporated land without urban services | Residential land that allows a detached house; not land zoned mainly commercial, industrial, farm or public | Inside the urban growth boundary only | DLCD may extend deadlines where water, sewer, storm drainage or roads are "significantly deficient" | V |
| California | Any city whose boundary includes part of a Census urban area; unincorporated land only inside one | Single-family residential zone only | – | Septic: a percolation test may be required | V |
| Maine | Statewide, wherever homes are allowed (from Jan 1 or July 1, 2024) | Any area allowing homes, including as a conditional use (wording from 2023) | 4-home tier only in designated growth areas | 4-home tier also on public water and sewer where there is no comprehensive plan; occupancy needs proof of adequate water and waste systems | V |
| Vermont | Every municipality with bylaws | Any district allowing year-round homes | – | 3–4 homes only where served by town sewer and water ("available" connection) | V (statute and DHCD memo) |

## Item 3. Share of single-family homes in covered places

- **Source:** ACS 2020–2024 B25024, rows 2 + 3 (one-unit detached + attached).
- **Covered:** by each statute's own thresholds, as in force for most of each state's window.
- **Oregon:** cities from the PSU July 2020 file; the Metro list is from scripts/middle_test2_oregon_line.py.

| State | Covered group | Single-family homes | Most homes per lot | Share of state's single-family homes | V/S |
| --- | --- | ---: | ---: | ---: | --- |
| Oregon | 12 non-Metro cities of 25,000+ | 248,475 | 4 | 19.7% | S (computed) |
| Oregon | 21 Metro cities over 1,000 | 353,801 | 4 | 28.1% | S |
| Oregon | 14 Metro unincorporated places (Aloha, Bethany, …) | 61,763 | 4 | 4.9% | S (approx.) |
| Oregon | 21 non-Metro cities, 10,001–24,999 | 100,046 | 2 | 7.9% | S |
| **Oregon, covered** | | **764,085** of 1,259,021 | | **60.7%** | S |
| Oregon, sensitivity | + 54 cities of 2,500–10,000 (from mid-2025) | +93,840 → 857,925 | 2 | 68.1% | S |
| Oregon, not covered | Cities under 2,500 (incl. 3 Metro ≤1,000), rural, other unincorporated | about 401,000 (with 2025 cities) | – | – | S |
| California | All incorporated places | 7,487,509 of 9,440,507 | 4 | 79.3% | S |
| **California, covered** | + Census places outside cities (counted as covered) | **8,858,087** | 4 | **93.8%** | S (upper; urban-area test not on disk) |
| **Maine, covered** | All (applies statewide) | **545,369** of 545,369 | 2–4 | **100%** | V (scope) |
| Maine | 4-home tier, stand-in: homes in Census places | 196,481 | 4 | 36.0% | S (stand-in for growth areas; no growth-area map on disk) |
| Maine | Rest | 348,888 | 3 | 64.0% | S |
| **Vermont, covered** | All (applies statewide) | **243,133** of 243,133 | 2–4 | **100%** | V (scope) |
| Vermont | 4-home tier, stand-in: homes in Census places | 75,875 | 4 | 31.2% | S (stand-in for sewer-and-water areas) |
| Vermont | Rest | 167,258 | 2 | 68.8% | S |

**What these approximations miss:**
- **California:** not every home in a place sits in a single-family zone, and not every unincorporated place is inside an urban area.
- **Oregon:**
  - The Metro unincorporated list is hand-picked.
  - Stafford and Damascus are left out, because they may be outside the Metro boundary.
  - Mount Vernon has no PSU match, so it is counted as not covered.
- **Maine and Vermont:** Census places are only a rough stand-in for growth areas and for sewer-and-water areas.

## Item 4. Carve-outs

| State | Owner occupancy | Lot-size minimum | Parking | Design review | Historic districts | Fire and hazard zones | V/S |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Oregon | None in the statute or rule | Duplex: no larger lot than a house. Triplex ≤5,000 sq ft, quadplex ≤7,000 sq ft (or the house minimum if larger). Townhouse lots average ≤1,500 sq ft | Duplex ≤2 spaces in total. Triplex 1–3 and quadplex 1–4 by lot size. Cottages ≤1 each | Siting and design rules allowed if they don't add "unreasonable costs or delay." Only clear and objective standards | Protections allowed, but no use or density ban on middle housing where houses are allowed (OAR 660-046-0010(3)) | Goal 7 hazard rules (flood, etc.) apply. Goal 5 resource sites can limit types other than duplexes | V |
| California | Lot split: an affidavit to live in one home for 3 years (exempt: land trusts, nonprofits). No other owner rules | New lots ≥1,200 sq ft, each at least 40% of the original lot. Standards can't block 2 homes of 800 sq ft. Side and rear setbacks ≤4 ft | ≤1 space per home. None within ½ mile walk of transit, or 1 block of car share | Objective standards only | Excluded: historic district contributors, listed landmarks | Excluded (65913.4(a)(6)(B)–(K)): very high fire hazard zones (unless mitigated), farmland, wetlands, quake fault and flood zones, habitat, conservation land. Also: homes with tenants in the last 3 years, rent-controlled or deed-restricted homes, Ellis Act exits. No lot split twice. Stays over 30 days. Health-and-safety denial allowed | V |
| Maine (2023–24 text) | None in 4364-A | No larger dimensional rules than a house. Lot area per home allowed, but extra homes can't need more than the first | None in 4364-A. ADUs: no extra parking | Not addressed until 2025 (no planning-board approval for ≤4 homes) | Not addressed | Shoreland zoning applies. Water and waste proof needed for occupancy. The 2025 law adds Lewiston–Auburn watershed, coastal barrier and flood options | V |
| Vermont | None for duplexes or 3–4 homes (only ADUs required an owner-occupied lot) | Duplex: "same dimensional standards" as a house. 3–4 homes: "same size lot" as a house. Small lots without sewer and water may be barred (4412(2)(A)) | From Dec 1, 2024: ≤1 space per home with sewer and water; ≤1.5 for duplexes and multiunits elsewhere | Not limited by 4412(1)(D) | Not addressed in 4412(1)(D) | Flood and river-erosion bylaws are kept for ADUs; not stated for duplexes | V |

## Item 5. Is approval ministerial?

| State | Ministerial? | Basis | V/S |
| --- | --- | --- | --- |
| Oregon | Effectively yes | Same approval process as a house; only clear and objective standards (OAR 660-046-0115, -0215). Cities may offer a discretionary path as an option | V |
| California | Yes | "Considered ministerially, without discretionary review or a hearing." 60 days, then deemed approved (2025 text). Denial only on a written health-and-safety finding | V |
| Maine | No, in 2024–mid-2025 | Applies where homes are allowed "including as a conditional use," so towns could require conditional-use or planning-board review. The 2025 laws add "permitted uses" and no planning board for ≤4 homes, after most of the window | V |
| Vermont | Partly | 3–4 homes: "permitted use." Duplex: "allowed use" in Act 47 as enacted (could be conditional). Site plan review is still possible | V |

## Boost: the plan's fixed scaling rule

Fixed rule: boost = (6 − 1) ÷ (tested by-right maximum − 1). Where the maximum differs within a state, average (max − 1) across covered areas, weighted by homes. Weight the four states by single-family homes in covered places.

**Each state's homes-weighted (max − 1):**

| State | Sum of homes × (max − 1) | ÷ covered homes | Average (max − 1) | Boost = 5 ÷ average |
| --- | --- | ---: | ---: | ---: |
| Oregon | 664,039×3 + 100,046×1 = 2,092,163 | 764,085 | 2.738 | 1.826 |
| California | 8,858,087×3 = 26,574,261 | 8,858,087 | 3.000 | 1.667 |
| Maine | 196,481×3 + 348,888×2 = 1,287,219 | 545,369 | 2.360 | 2.118 |
| Vermont | 75,875×3 + 167,258×1 = 394,883 | 243,133 | 1.624 | 3.079 |
| **Four states** | **30,348,526** | **10,410,674** | **2.915** | **5 ÷ 2.915 = 1.715** |

- **Reading (b), above:** average (max − 1) across all covered homes, then take 5 ÷ it, the same way as within a state. Boost **1.715**.
- **Reading (a):** average the four state boosts, weighted by homes:
  - (764,085×1.826 + 8,858,087×1.667 + 545,369×2.118 + 243,133×3.079) ÷ 10,410,674 = **1.735**.
- **California dominates:** 85% of the weight (8,858,087 ÷ 10,410,674).

**Sensitivity** (boost under readings b / a):

| Change | Boost (b) | Boost (a) |
| --- | ---: | ---: |
| California: incorporated places only | 1.723 | 1.745 |
| Oregon: add the 2,500–10,000 cities | 1.725 | 1.747 |
| Maine: empty-lot maximum (2) outside growth areas | 1.735 | 1.776 |
| Maine and Vermont: all homes in the 4-home tier | 1.677 | 1.678 |
| Maine and Vermont: no homes in the 4-home tier | 1.735 | 1.800 |

- **Overall range:** about **1.68–1.80**; the main reading is **1.715**.
- **Plan status:** per the plan, this does not change any line ("Law strength: Unscaled"). It only measures the gap to the handbook's 6.
- **Oregon counted at 4:** this treats townhouses and cottage clusters as 4. Cottage clusters on big lots can exceed 4, which would lower Oregon's boost slightly.

**Other gaps to the handbook, beyond the number of homes:**
- **Coverage:** Oregon covers 61% and California 79–94% of single-family homes, against 100% in the handbook.
- **Ministerial approval:** not in Maine during its window, and only partly in Vermont.
- **Height:** none of the four laws sets 3 stories. Oregon guarantees only 25 ft or 2 stories for triplexes and quadplexes.

## Source log

| Source | Use | Status |
| --- | --- | --- |
| oregonlegislature.gov 2021 ORS ch.197 PDF (197.758) | OR text in force 2021–2022 | V, read |
| oregonlegislature.gov 2023 ORS ch.197A PDF (197A.420; 2019 c.639 §3–4 notes) | OR after HB 3395; deadlines | V, read |
| oregonlegislature.gov current ORS 197A (2025 c.476) | Later changes, not used | V, read |
| oregon.public.law OAR 660-046-0010, -0115, -0120, -0215, -0220 | OR rules (mirror of the SOS text; the SOS site gave an error) | V via mirror |
| leginfo.legislature.ca.gov | **Blocked (403)** | – |
| california.public.law Gov. Code 65852.21, 66411.7 | CA statute text (current, includes the SB 450 2025 changes) | V via mirror |
| HCD SB 9 Fact Sheet (Sept 2024); HCD fact sheet (2026) | "Up to four," ministerial | V (official doc) |
| justia (CA) | Blocked (403) | – |
| legislature.maine.gov 30-A §4364-A (current, 2025 text), §4364 (implementation date) | ME later text; Jan 1 / July 1, 2024 dates | V |
| lldc.mainelegislature.org PL 2021 c.672, PL 2023 c.192 | ME text in force 2024–2025 | V |
| legislature.maine.gov HP1224 (PL 2025 c.385) | 2025 changes | V |
| legiscan LD 2003 PDF | Blocked (403) | – |
| legislature.vermont.gov Act 47 as enacted; 24 V.S.A. 4412 (current) | VT text, effective dates | V |
| VT DHCD Act 47 memo (June 28, 2023) | Effective dates, "served by" meaning | V (official doc) |
| ACS 2020–2024 B25024 (on disk); 2024 place gazetteer (on disk); PSU 2020 city file; Metro list | Item 3 | S (computed) |

- **Fetching:** the user agent was "missing-middleware-research/1.0 (public data)". There were no forms and no email.
- **Not used:** no permit counts or results were looked at.

## Stronger-reform line (computed by the locked rule, 2026-11-10)

- **Boost:** 1.715 (sensitivity 1.68–1.80). It assumes homes rise in proportion to homes allowed per lot, which is untested.
- **Applied to the core lines** (measured slow start), Wisconsin 2027–2031: −490 × 1.715 ≈ **−840**; +1,600 × 1.715 ≈ **+2,740**; +4,530 × 1.715 ≈ **+7,770** homes.
- **Status:** an extra line labelled as a possibility, not the core.
