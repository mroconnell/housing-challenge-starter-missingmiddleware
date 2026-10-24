"""Madison vs Sun Prairie difference-in-differences (pre-registered Wisconsin check, CA_COMPARISON_PLAN.md).

Written by the Gate 3 validation agent; denominators are ACS one-unit detached homes
(thousands) from reference/wi_baseline_observed.csv. Run: uv run python scripts/check_madison_sun_prairie.py
"""
import numpy as np, pandas as pd
from pathlib import Path
R=str(Path(__file__).resolve().parent.parent/'reference')+'/'
m=pd.read_csv(R+'madison_adu_permits_by_year.csv'); s=pd.read_csv(R+'sun_prairie_adu_equivalent_by_year.csv')
mad=m[m.category=='second_home_sf_lot'].set_index('year').units
madA=m[m.category.isin(['second_home_sf_lot:adu_detached','second_home_sf_lot:adu_attached','second_home_sf_lot:adu_conversion','second_home_sf_lot:adu_two_unit'])].groupby('year').units.sum()
sp=s[(s.series=='second_home_sf_lot')&(s.restrictive_period)].groupby('year').units.sum()
spA=s[(s.series.isin(['second_home_sf_lot:adu_detached','second_home_sf_lot:adu_attached','second_home_sf_lot:adu_conversion','second_home_sf_lot:adu_two_unit']))&(s.restrictive_period)].groupby('year').units.sum()
HM,HS=53.292,8.118
rng=np.random.default_rng(20261024); N=400000
def ci(c,e):
    g=np.random.default_rng(1)
    lo=np.percentile(g.gamma(c,1,400000),2.5)/e if c>0 else 0.0; hi=np.percentile(g.gamma(c+1,1,400000),97.5)/e; return lo,hi
def did(pre,post,mserie,sserie,label):
    mp,mq=mserie.loc[pre[0]:pre[1]].sum(),mserie.loc[post[0]:post[1]].sum()
    sp_,sq=sserie.loc[pre[0]:pre[1]].sum(),sserie.loc[post[0]:post[1]].sum()
    ny0=pre[1]-pre[0]+1; ny1=post[1]-post[0]+1
    e=dict(mp=HM*ny0,mq=HM*ny1,sp=HS*ny0,sq=HS*ny1)
    r=dict(mp=mp/e['mp'],mq=mq/e['mq'],sp=sp_/e['sp'],sq=sq/e['sq'])
    d=(r['mq']-r['mp'])-(r['sq']-r['sp'])
    # Jeffreys gamma posterior draws
    dr=lambda c,ex: rng.gamma(c+0.5,1,N)/ex
    D=(dr(mq,e['mq'])-dr(mp,e['mp']))-(dr(sq,e['sq'])-dr(sp_,e['sp']))
    ratio_m=(dr(mq,e['mq'])/dr(mp,e['mp']))
    print(f"{label}: Madison {mp}->{mq} ({r['mp']:.3f}->{r['mq']:.3f}); SunPrairie {sp_}->{sq} ({r['sp']:.3f}->{r['sq']:.3f}); DiD={d:.3f} [{np.percentile(D,2.5):.3f},{np.percentile(D,97.5):.3f}] P(DiD>0)={np.mean(D>0):.3f}; Madison ratio {np.median(ratio_m):.2f} [{np.percentile(ratio_m,2.5):.2f},{np.percentile(ratio_m,97.5):.2f}]")
    print('   exact Poisson CIs: M pre',[round(v,3) for v in ci(mp,e['mp'])],'M post',[round(v,3) for v in ci(mq,e['mq'])],'S pre',[round(v,3) for v in ci(sp_,e['sp'])],'S post',[round(v,3) for v in ci(sq,e['sq'])])
    return d
print(mad.loc[2014:2026].to_dict()); print(sp.to_dict())
did((2016,2021),(2022,2025),mad,sp,'main second homes, pre 2016-21, post 2022-25')
did((2016,2021),(2024,2025),mad,sp,'post = benchmark years 2024-25')
did((2016,2021),(2022,2025),madA,spA,'ADU-type only')
did((2016,2019),(2022,2025),mad,sp,'pre 2016-19 (drop 2020-21 COVID/transition)')
# placebo: pre-trend 2016-18 vs 2019-21
did((2016,2018),(2019,2021),mad,sp,'placebo pre-trend 2016-18 vs 2019-21')
# conditional binomial test: is Sun Prairie's post share consistent with Madison's? test equality of rates in post
# Madison ramp shape vs CA
v=mad.loc[2022:2025].values/ HM; print('Madison yearly rate 2022-25',v.round(3),'share of 2024-25 avg', (v/v[2:].mean()).round(2))
# CA central implied increment vs DiD
print('central implied increment restricted->with law', 1.23-0.062, 'lower', 0.229-0.062)
# Madison 2026 provisional
print('2026 provisional rate all', 42/43.2, 'excl templated', 13/43.2, ci(13,43.2))
