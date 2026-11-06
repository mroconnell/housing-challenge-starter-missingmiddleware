"""Minimum detectable difference for Oregon's 10,000 line, from pre-law years only (2012-2019).
Unit: homes permitted in 2- and 3-4-unit buildings per 1,000 single-family homes per year."""
import csv, glob, re, statistics, sys, math
REPO, S = sys.argv[1], sys.argv[2]
t = open(f'{S}/Certified_Population_Estimates_2020_2.txt').read()
psu = {}
for n, v in re.findall(r"([A-Z][A-Za-z\.' ]+?)\s+([\d,]{2,9})(?=\s|$)", t):
    psu.setdefault(n.strip(), int(v.replace(',', '')))
METRO = {'Wood Village','Fairview','Troutdale','Milwaukie','Gladstone','Happy Valley','West Linn','Wilsonville','Sherwood',
         'Cornelius','Forest Grove','Durham','King City','Tualatin','Johnson City','Rivergrove','Maywood Park','Lake Oswego',
         'Oregon City','Tigard','Beaverton','Hillsboro','Gresham','Portland'}
# single-family homes (detached + attached), ACS 2020-2024, Oregon incorporated places
names = {}
for r in csv.DictReader(open(f'{REPO}/data/raw/statewide_states/census_place_codes/st41_or_place2020.txt'), delimiter='|'):
    if r['TYPE'].startswith('INC'): names['1600000US41' + r['PLACEFP']] = r['PLACENAME'].rsplit(' ', 1)[0]
sfh = {}
f = open(f'{REPO}/data/raw/census_acs5_2024_tbsf/acsdt5y2024-b25024.dat'); h = f.readline().strip().split('|')
i2, i3 = h.index('B25024_E002'), h.index('B25024_E003')
for l in f:
    p = l.strip().split('|')
    if p[0] in names: sfh[names[p[0]]] = int(p[i2]) + int(p[i3])
# BPS reported-only units, years 2012-2019 only
YEARS = [str(y) for y in range(2012, 2020)]
mid = {}; months = {}
for fn in sorted(glob.glob(f'{REPO}/data/raw/census_bps_place_us/we20*a.txt')):
    y = fn[-9:-5]
    if y not in YEARS: continue
    L = open(fn, encoding='latin-1').read().splitlines()
    for r in csv.reader(L[3:]):
        if len(r) > 40 and r[1] == '41':
            n = r[16].strip()
            # columns: 2-units rep Units = idx 33, 3-4 units rep Units = idx 36
            mid.setdefault(n, {})[y] = int(r[21] or 0) + int(r[24] or 0)
            months.setdefault(n, {})[y] = r[15].strip()
rows = []
for n, pop in psu.items():
    if n in METRO or n not in sfh or n not in mid: continue
    if not (5000 <= pop < 25000): continue
    if any(y not in mid[n] for y in YEARS): continue
    rate = {y: 1000 * mid[n][y] / sfh[n] for y in YEARS}
    before = statistics.mean(rate[y] for y in YEARS[:5]); after = statistics.mean(rate[y] for y in YEARS[5:])
    rows.append(dict(name=n, pop=pop, sfh=sfh[n], change=after - before))
out = [r for r in rows if not (9000 <= r['pop'] < 11000)]
s_out = statistics.stdev(r['change'] for r in out); s_all = statistics.stdev(r['change'] for r in rows)
print(f'cities 5,000-24,999 non-Metro, 12 months reported 2012-2019: {len(rows)}; outside 9,000-10,999: {len(out)}')
print(f'SD of placebo change (2017-19 mean minus 2012-16 mean), per 1,000 SF homes/yr: outside band {s_out:.3f}; all {s_all:.3f}')
K = 1.645 + 0.8416  # 90% two-sided test, 80% power
for lo, hi in [(9500, 10500), (9000, 11000), (7500, 12500), (5000, 15000)]:
    b = [r for r in rows if lo <= r['pop'] < hi]
    n1 = sum(r['pop'] > 10000 for r in b); n0 = len(b) - n1
    if n1 < 2 or n0 < 2: print(lo, hi, 'n1', n1, 'n0', n0, 'too few'); continue
    mde = K * s_out * math.sqrt(1/n1 + 1/n0); hs = statistics.mean(r['sfh'] for r in b)
    print(f'{lo}-{hi-1}: covered {n1}, left out {n0}; MDE {mde:.2f} per 1,000 SF homes/yr; avg SF homes {hs:,.0f} -> {mde*hs/1000:.1f} homes per city per year')
