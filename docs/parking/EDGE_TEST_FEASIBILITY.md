# Parking edge-test feasibility (2026-11-06)

**Feasibility only. No outcome was read.**

- **Ryan's question (18:39–18:41 UTC):** can we find cities where an edge test gives a causal estimate, learn what they share, and carry it to the rest?
- **Rule:** cities are chosen for whether an edge test can be run cleanly, never for what it shows.

**Where an edge can be:**
- **Citywide repeals (our 74):** the only edge is the city limit, so the neighbour must not have reformed.
- **Mapped reforms:** minimums removed only inside a drawn district give an edge inside one city, with the same city rules on both sides.

**Screens applied:**
- At least 3 years after repeal (repeal in 2022 or earlier): 37 of the 74 pass.
- **Neighbours:** from 2024 Census place and county-subdivision boundaries, the share of each city's border shared with each neighbour, and whether that neighbour appears in the Parking Reform Network list. That list's coverage is incomplete, so "none in PRN" is not proof of no reform.
- **Parcel data:** a public bulk source with year built, building type or units, and parcel geometry, covering both sides of the edge. This was checked by a helper from web metadata only; "NV" = not verified.

## Citywide repeals with a usable city-limit edge

| City (repeal) | Neighbours across the limit | Parcel data | Note |
| --- | --- | --- | --- |
| Buffalo NY (2017) | Tonawanda, Cheektowaga, West Seneca, Lackawanna: none in PRN | NYS Tax Parcels (YR_BLT, class; no units field) | Longest after-period; lot data already in hand |
| Raleigh NC (2022) | Wake County towns and unincorporated land: none in PRN (Wake Forest repealed 2025) | Wake County parcels (CC BY 4.0), NC OneMap | |
| Gainesville FL (2022) | Unincorporated Alachua, Alachua city: none in PRN | Florida DOR roll (year built, units) | Field names from memory |
| Gastonia NC (2021) | Gaston County townships: mostly none in PRN | NC OneMap (structyear) | Year-built fill NV |
| Canandaigua (Town) NY (2020) | Rural towns: none in PRN. The City repealed the same year, so that border is excluded. | NYS Tax Parcels | Small |
| Cambridge MD (2021) | Dorchester County districts: none in PRN | MD iMAP parcel points | Small |
| Hartford CT (2017) | West/East Hartford, Wethersfield, Windsor: partial reductions only | CT CAMA (year built; no units field) | Neighbours partly treated |
| Bridgeport CT (2021) | Fairfield, Stratford, Trumbull: partial reductions | CT CAMA | Neighbours partly treated |
| Cambridge MA (2022) | Somerville (repealed 2024), Boston (2025), Belmont/Watertown partial | MassGIS L3 (year built, units) | Clean only until 2023 |

**Weaker:**
- Minneapolis and St. Paul: they border each other, both repealed in 2021, and the other neighbours are partly reformed.
- Tigard: Beaverton, King City and Tualatin repealed in 2023–24; only the unincorporated Bull Mountain side (40%) is clean.

**Not feasible (no free parcel data, or the neighbour repealed):** San Francisco (San Mateo side), Lexington, Ann Arbor, Roanoke, Alameda, Emeryville, Berkeley, Culver City (86% of its border is Los Angeles, inside AB 2097 zones), Corvallis, Mount Pleasant, Windham, Branson, Hudson, Hampden, Portsmouth, Saranac Lake, Ecorse/River Rouge (partial Detroit data only), Bastrop/Bandera (Texas year-built text, fill NV), Plainfield/South Bend (Indiana year-built on request only), Dunwoody/Avondale Estates (DeKalb year built residential only; bulk NV), West Allis (data quality varies).

## Mapped-district reforms (52 in the PRN list, residential, adopted 2012–2022)

**Rated good or near-good for parcel data:**
- Elmwood Park IL (Cook County Assessor, open)
- Reno NV (Washoe Assessor downloads; field check needed)
- Mooresville NC and Mount Airy NC (NC OneMap)
- Norfolk VA (city open parcels)
- Wickenburg AZ (Maricopa Assessor)
- Frenchtown NJ (NJGIN/MOD-IV; year built NV)
- Deer Lodge MT (Montana cadastral)

**Caveats:**
- **District maps:** none was verified as a GIS layer. Small towns mostly have only an ordinance PDF, which would need digitising by hand.
- **District size:** most are small downtowns with few new homes near the edge.
- **Wisconsin's four** (Marshfield, Whitewater, Sparta, Black River Falls) have parcel geometry but no year built. New building would have to be inferred from yearly improvement-value jumps.

## Reading

- **Size of the pool:** about 6–9 citywide cities and about 5–8 mapped-district cities could support an edge test with free public data. That is enough to estimate a few clean effects and form a hypothesis about what they share, but not enough to test that hypothesis on held-out cities. Every candidate would be used up in forming it.
- **Common data limits:**
  - Year built comes from current-stock files, so demolished or replaced buildings are hidden.
  - New York and Connecticut have no units field.
  - Texas year built is free text.
- **Next step, if Ryan wants it:** a locked edge-test plan on this list (chosen now, before any outcome), reported as cases.

## Addendum (2026-11-06 ~19:20 UTC): district maps and permit lists for the 52 mapped-district cities

**What was checked:** whether each city has the two inputs TOD's edge tests used. The check used public pages and layer metadata only, with nothing downloaded.
- **Map:** the district boundary as a GIS layer.
- **Permits:** a bulk building-permit list with locations and unit counts, covering 3 years before and after.

**Result: no city has both.**
- **San Marcos TX** is closest. It has a "Central Business Area" polygon and permits from Oct 2011 with locations, but no unit count.
- **Hayward CA** has a zoning match and state housing-report permits with units, but only from 2018, two years before its reform.
- **Norfolk VA** has an overlay map and permits from 2016, with no unit count, and its district is about 10 acres.
- **Permits are the main gap:** almost every city offers only a search portal.
- **Not actual reforms:** Elmwood Park, Momence, Waterloo, Aurora, Ladue and probably Marshfield only had plan recommendations or case-by-case exceptions. The PRN rows overstate them.
- **Zoning match:** in 14 cities the parking district matches a zoning district in today's GIS. Today's boundaries may differ from the boundaries in the reform year (Reno and Davenport redrew them).

**Reading:** the fresh 52 cannot support an honest edge-test check with free public data. A hybrid would pair a GIS zone with county assessor year built instead of permits. It might work for 2–3 cities (Reno via Washoe Assessor, Mooresville via NC OneMap, San Marcos via Texas parcels plus permits), which is too few to test a hypothesis.
