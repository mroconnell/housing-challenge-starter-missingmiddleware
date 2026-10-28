# Parking: Los Angeles transit-program projects, how much parking they built, plan written before reading

Written 2026-10-28 by the parking conductor. Ryan chose option B ("Option B for LA"): read about 50 project files by hand. No project has been read for this check before this file was committed.

## Question

Los Angeles's Transit Oriented Communities (TOC) program, from 2017, lets projects near major transit build with less parking. How much parking did those projects actually build per home? How does that compare with what the old rule required, and with the program's own minimum?

## Source

**Project files:** the state CEQA database (CEQAnet, public), which holds the City of Los Angeles's environmental filings. Most TOC projects file a Notice of Exemption whose description gives the number of homes and parking spaces. The search covers documents from the City of Los Angeles containing "TOC", by year, 2018 to 2026.

## Sample

1. Gather every matching document, 2018–2026, and keep Notices of Exemption.
2. Draw 50 at random (seed 20261028), at most 10 per year.
3. Read each description and record:
   - homes;
   - car parking spaces;
   - TOC tier, if stated;
   - whether it is 100% affordable.
4. Draws that are not a residential TOC project, or that give no parking count, are replaced with the next random draw. Replacements are counted and reported.

## Comparisons

- **Old rule (Los Angeles code, section 12.21 A.4):** 1 space per home with fewer than 3 habitable rooms, 1.5 with 3, and 2 with more than 3. Unit mix is rarely given, so the old requirement is shown as a range: at least 1 space per home, up to 2.
- **TOC program minimum:** 0.5 spaces per home, or 0.5 per bedroom in lower tiers, or none in tier 4. From 2023 the state's AB 2097 removed minimums near major transit.

## Reported

- the home-weighted spaces per home;
- the median spaces per home;
- the share of projects with no parking;
- the share building more than their program minimum;
- the share building at least 1 space per home (the old floor);
- each by period: 2018–2022 and 2023–2026.

## Use

A check on how developers respond to lower parking minimums, reported as evidence. It does not change the tool.

## Changes after writing
