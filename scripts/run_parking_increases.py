"""Parking increases (docs/parking/SIGNAL_PLAN.md): the standard comparison for cities that raised housing parking minimums.

    uv run --all-extras python scripts/run_parking_increases.py
Output: reference/parking_increases_effects.csv
"""
import sys; sys.path.insert(0,'scripts'); sys.path.insert(0,'.')
import run_parking_comparison as rpc, run_parking_improve_r1 as R1, pandas as pd
from missing_middleware.parking import comparison as cmp
from missing_middleware.paths import RAW
bps=rpc.read_bps_us(); p=cmp.panel(bps)
geo=p.drop_duplicates('key',keep='last').set_index('key')
homes=geo.acs_geoid.map(rpc.acs_table(RAW/'census_acs5_2024_tbsf'/'acsdt5y2024-b25002.dat','B25002_E001')); homes=homes[homes>0]
popn=geo.acs_geoid.map(rpc.acs_table(RAW/'census_acs5_2024_tbsf'/'acsdt5y2024-b01003.dat','B01003_E001'))
cases=[('53','Kirkland',2015),('41','Portland',2013),('04','Lake Havasu City',2023),('12','North Miami Beach',2023)]
rows=[]
for st,nm,y in cases:
    k=cmp.match_place(p,st,nm,None); print(nm,k)
    if not k: continue
    rows.append({'key':k,'event_year':y})
cmp.controls=R1.controls_nation
e=cmp.effects(p,pd.DataFrame(rows),set(),homes,popn,min_post=1)
print(e[[c for c in ['key','event_year','status','outcome','pre_years','post_years','n_controls','rate_before','rate_after','ctrl_before','ctrl_after','effect'] if c in e]].round(2).to_string())
e.to_csv('reference/parking_increases_effects.csv', index=False)
