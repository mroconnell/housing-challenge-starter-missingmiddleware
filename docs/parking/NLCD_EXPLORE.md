# Exploring satellite hard-surface data as a parking measure (Annual NLCD)

Started 2026-11-03 at Ryan's request. Exploration only. Nothing here changes the tool. Any formal test will be written
down and locked before we count anything.

## 1. What the data is

- **Source.** USGS Annual National Land Cover Database (Annual NLCD), Collection 1. Made from Landsat satellite images.
- **Grid.** The lower 48 states, cut into squares of 30 m by 30 m. One square is 900 square meters, about 0.22 acres
  (about 9,700 square feet).
- **Years.** One map per year. Collection 1.1 covers 1985–2024. Collection 1.2 (June 2026) adds 2025.
- **Two products we use.**
  - Fractional Impervious Surface (FctImp): the percent of each square that is hard surface (0 to 100). Hard surface
    means pavement, concrete, roofs and other built material. 250 means no data.
  - Impervious Descriptor (ImpDsc): a label for each square. 0 = not developed, 1 = road, 2 = other hard surface.
- **License.** CC0 1.0 (public domain). Ryan approved CC0 data on 2026-11-03.

## 2. What it can and cannot see

| It can see | It cannot see |
| --- | --- |
| New surface parking lots and big new roofs | Parking inside garages or underground |
| Roads, separately from other hard surface | Roofs vs lots: both are "other hard surface" |
| Change year by year, back to 1985 | Small changes inside one square (a single backyard ADU is about 6–8% of a square, near the normal error) |

So this is a measure of **hard surface built**, not of parking spaces and not of homes. A drop in new hard surface
per new home after reform would fit "less surface parking". It would not prove it, because roofs are in the same
number.

## 3. How we read it (license rule)

- **Reader.** `missing_middleware/tiff_window.py`, written by us (Apache-2.0). It uses only numpy (BSD-3-Clause) and
  the Python standard library. No new package is added.
- **Why not the usual tools.** rasterio and GDAL ship large bundled C libraries; GEOS (LGPL) can be one of them, and
  GEOS is banned here. tifffile is BSD, but it needs imagecodecs for LZW, and imagecodecs bundles many other
  libraries. Our reader needs neither.
- **What it reads.** Tiled or striped GeoTIFFs, classic or BigTIFF, 8-bit, one band, no compression, LZW or Deflate.
  It fetches only the tiles that cover a city, using HTTP range requests. It refuses any other kind of file.
- **Tests.** `tests/test_tiff_window.py` writes small GeoTIFFs in every supported layout and reads windows back. It
  also checks our LZW decoder against a file written by libtiff (`tests/fixtures/lzw_libtiff.tif`).

## 4. Where we get it

| Route | Cost | What you get | Used? |
| --- | --- | --- | --- |
| Open Storage Network copy, listed by the USGS Water Mission Area STAC catalog | Free, no account | One national file per product and year (Collection 1.1); we read only city windows | **Yes** |
| MRLC direct download | Free | National zip files, about 1 GB per product and year (Collection 1.2) | Later, if we need 2025 |
| USGS AWS bucket | Requester pays (needs an AWS account) | Same files | No |
| EarthExplorer | Free, needs a login | Tiles | No |

The cloud workspace cannot reach USGS or Census hosts, so downloads run on Ryan's Mac. Each window read is logged with
its URL, bytes read and SHA-256 (`data/raw/annual_nlcd_windows/_downloads.json`). No raster goes into the repository.

## 5. First look: Buffalo vs Rochester (descriptive, not a test)

- **Why these two.** Buffalo removed parking minimums citywide (in force 2017-01-03). Rochester, New York, has no
  citywide reform. Both are cold, older, slow-growing upstate cities.
- **Caveat.** Buffalo's repeal came with a full zoning rewrite (the Green Code), so any change cannot be pinned on
  parking alone.
- **Measures, per city and year** (city outline from Census 2024, held fixed):
  - hard surface, in acres; split into road and other hard surface;
  - new hard surface, in acres per year (this year minus last year), plus gross gains and gross losses;
  - new other hard surface per home permitted, in square feet per home (Census permits, same year and the year
    before, because the satellite sees a building after it is built).
- **Question.** Is the yearly line smooth enough that a change after 2017 would stand out?
- **Run.** `uv run --all-extras python scripts/run_nlcd_paved_pilot.py --fetch`, then
  `uv run --all-extras --with matplotlib python scripts/plot_nlcd_pilot.py`.

Results (first run 2026-11-03 on Ryan's Mac; `reference/nlcd_pilot_buffalo_rochester.csv`, chart
[nlcd_pilot_buffalo_rochester.png](nlcd_pilot_buffalo_rochester.png)):

| Measure | Buffalo | Rochester |
| --- | --- | --- |
| Squares inside the city (30 m) | 120,679 | 105,878 |
| Hard surface, 1985 (acres) | 16,052 | 11,866 |
| Hard surface, 2024 (acres) | 16,121 | 12,112 |
| Years with a net fall in hard surface (of 39) | 16 | 15 |
| Year-to-year spread of new non-road hard surface, 1986–2022 (standard deviation, acres per year) | 14.6 | 13.4 |
| Homes permitted, 2007–2022 average (homes per year) | 172 | 223 |
| New non-road hard surface, 2012–2016 average (acres per year per 1,000 land acres) | −0.58 | −0.09 |
| New non-road hard surface, 2017–2022 average (acres per year per 1,000 land acres) | −0.58 | −0.42 |

What we learned:

1. **The line is not smooth enough at city scale.** The test that matters is the comparison: Buffalo minus
   Rochester, with Rochester scaled to Buffalo's land area. That difference in new non-road hard surface swings by
   about 9.3 acres a year (standard deviation, 1986–2022). A comparison of 5 years before (2012–2016) with 6 years
   after (2017–2022) therefore has a standard error of about 5.6 acres a year. The parking signal is smaller: Buffalo
   permitted 172 homes a year on average in 2007–2022 (208 in 2012–2022). With one surface space each (about
   330 square feet per space), that is about 1.3 to 1.6 acres a year. So the noise is about 3 to 4 times the signal.
2. **The swings are shared by both cities.** Year-to-year change moves together in the two cities, 1986–2022:
   correlation 0.86 for total hard surface and 0.81 for non-road hard surface. Before 2005 both cities zigzag in the
   same years. From 2016 to 2022 both lose road surface, which real cities rarely do. These look like features of how
   the maps were made, not of building. The comparison cancels much of this, but what is left (point 1) is still
   larger than the parking signal.
3. **The newest years behave differently.** In 2023 and 2024 gross change drops to almost nothing in both cities
   (Buffalo gross loss 50.2 acres in 2022, 3.0 acres in 2023). Later releases may revise these years. Do not lean on
   the last two years.
4. **Per-home numbers are not usable.** They swing from about −33,000 to +19,000 square feet per home, because a
   noisy acre change is divided by a few hundred homes.
5. **Buffalo vs Rochester after 2017.** Buffalo's non-road change stayed at −0.58 acres per 1,000 land acres per
   year; Rochester's fell from −0.09 to −0.42. In Buffalo's acres, that is a relative rise of about +9 acres a year
   in Buffalo, the opposite of "less parking". It is about 1.6 standard errors from 0, so we read it as noise, not a
   finding.

Data notes: the Census permit files for 2005 and 2006 did not match either city (older file layout; not fixed).
Buffalo reports 0 months for 2018–2024, so its permit counts in those years are Census estimates. Two squares in
Buffalo have no data. One network timeout on the first run; a plain re-run finished (the reader now retries).

**Bottom line.** City-wide totals of this data cannot show a parking change in a slow-growing city. The noise
in the comparison is about 3 to 4 times the parking we would expect. If we use it at all, it should be
at the scale of individual building sites, where a new surface lot fills most of a few squares.

## 6. Ryan's three ideas, and what each would need

1. **Growth slows after reform.** A before/after line per reform city. Needs a smooth enough line (section 5 checks).
2. **Edges.** Compare squares just inside and just outside a reform zone (Seattle urban villages, Minneapolis,
   San Diego). Needs zone maps by year. The 30 m grid is fine enough for bands a few hundred meters wide.
3. **Difference-in-differences.** The 76 parking evidence places vs their matched comparison cities, using new hard
   surface per new home. This would give a parking measure for every place, not just the 5 with project records.

Each of these will get a locked plan (estimand, data, comparison, pass rule) before we count.

## 7. If we try building sites next (not started; needs Ryan's go-ahead)

Lock these before counting (from the audit review, audit/parking_nlcd_pilot_review_2026-11-03.md):
- how sites are picked: from permit records only, before looking at the NLCD data;
- the outcome per site, with its unit;
- the comparison sites;
- how map artifacts are handled, including leaving out 2023 and 2024.

Caveat: roofs and parking lots are both "other hard surface". A drop could mean smaller buildings, not less parking.
