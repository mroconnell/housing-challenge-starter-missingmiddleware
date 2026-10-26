"""Quick look (not pre-registered, 2026-10-26): permits before and after parking-minimum repeal
in US places of 5,000-50,000 people, against same-state places of 0.5-2x the population that
have no PRN reform record. Rates are units permitted per 1,000 residents (BPS place population),
mean of the 5 years before the PRN adoption year and the 3 years after.

    uv run python scripts/parking_small_places_quicklook.py
Inputs: data/raw/census_bps_place_us/{ne,mw,so,we}{2012..2025}a.txt (Census BPS, public domain;
_downloads.json records URL, date, bytes, SHA-256), reference/parking_reform_*.csv.
Output: reference/parking_small_places_quicklook.csv
"""
import sys, glob
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from missing_middleware.foundation import parsers
from pathlib import Path
R=str(Path(__file__).resolve().parent.parent)+'/'
fr=[]
for f in sorted(glob.glob(R+'data/raw/census_bps_place_us/*a.txt')):
    d=parsers.read_bps(f,'place',state_fips=None); d['year']=int(f[-9:-5]); fr.append(d)
b=pd.concat(fr,ignore_index=True)
b['mf']=b['2units_units']+b['3_4units_units']+b['5plus_units']
b=b[b.fips_place.str.strip()!='99990']
b['key']=b.state_fips+'|'+b.name.str.strip().str.lower()
FIPS={'Georgia':'13','California':'06','Rhode Island':'44','Michigan':'26','Maine':'23','Ohio':'39','Maryland':'24','Missouri':'29','New York':'36','Texas':'48','New Hampshire':'33','Wisconsin':'55'}
c=pd.read_csv(R+'reference/parking_reform_cases.csv')
allrep=pd.read_csv(R+'reference/parking_reform_taxonomy.csv')
reformed=set((FIPS.get(s,'')+'|'+p.lower()) for s,p in zip(allrep.state,allrep.place) if True)
cases=c[(c.benchmark_rating=='at')&(c.adopted_year<=2022)&(c.population<50000)&(c.population>=5000)].drop_duplicates('prn_key')
pop=b.groupby('key').pop.max()
units=b.pivot_table(index='key',columns='year',values='units_total',aggfunc='sum')
mfu=b.pivot_table(index='key',columns='year',values='mf',aggfunc='sum')
rows=[]
for r in cases.itertuples():
    k=FIPS[r.state]+'|'+r.place.lower()
    cand=[x for x in units.index if x==k or x.startswith(k+' ')]
    if not cand: rows.append(dict(place=r.place,state=r.state,note='not found in BPS')); continue
    k=cand[0]; Y=int(r.adopted_year); P=pop[k]
    pre=[y for y in range(Y-5,Y) if y>=2012]; post=[y for y in range(Y+1,min(Y+4,2026))]
    st=FIPS[r.state]
    ctrl=[x for x in units.index if x.startswith(st+'|') and x not in reformed and 0.5*P<=pop.get(x,0)<=2*P]
    def rate(kk,yrs,tab): v=tab.loc[kk,yrs]; return v.mean()/pop[kk]*1000 if v.notna().all() else np.nan
    for lab,tab in (('all',units),('2plus',mfu)):
        t0,t1=rate(k,pre,tab),rate(k,post,tab)
        cr=pd.DataFrame([(rate(x,pre,tab),rate(x,post,tab)) for x in ctrl]).dropna()
        c0,c1=cr[0].mean(),cr[1].mean()
        rows.append(dict(place=r.place,state=r.state,pop=int(P),year=Y,type=lab,pre=f'{pre[0]}-{pre[-1]}',post=f'{post[0]}-{post[-1]}',
            treat_pre=round(t0,2),treat_post=round(t1,2),ctrl_n=len(cr),ctrl_pre=round(c0,2),ctrl_post=round(c1,2),
            treat_ratio=round(t1/t0,2) if t0 else np.nan, ctrl_ratio=round(c1/c0,2) if c0 else np.nan))
out=pd.DataFrame(rows); pd.set_option('display.width',250); print(out.to_string())
out.to_csv(R+'reference/parking_small_places_quicklook.csv', index=False)
