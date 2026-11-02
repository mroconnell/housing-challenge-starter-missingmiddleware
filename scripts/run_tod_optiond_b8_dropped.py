import sys; sys.path[:0]=['scripts','.']
import numpy as np, pandas as pd
import run_tod_optiond as O, run_tod_station_lotmodel as L, run_tod_station_model as M
B8=['New York','austin_2009','charlotte_2019','denver_2018','seattle_mount_baker_2014','seattle_othello_2012','slc_2010','stpaul_2011']
OUT=['Philadelphia','chicago_2015','portland_2020']
O.TRAIN=B8+OUT
D,med=O.prepare(O.load(1,False),{'fill','equal'})
cols=O.features(D,['lot','place'])
meas=M.city_level(M.case_effects('permit_est')).set_index(['city','band'])['effect_per_100_acres']
tr=D[D.city.isin(B8)]
m=O.Bag(5).fit(tr[cols].astype(float),tr.y,tr.w)
avg8={b:meas.loc[B8].xs(b,level=1).mean() for b in ['0-1/4','1/4-1/2','1/2-1']}
rows=[]
for c in OUT:
    te=D[D.city==c]
    for b,v in L.effect_by_band(m,te,cols).items():
        rows.append({'city':c,'band':b,'measured':meas.get((c,b)),'model_B8':v,'average_B8':avg8[b]})
R=pd.DataFrame(rows); R['err_model']=(R.model_B8-R.measured).abs(); R['err_avg']=(R.average_B8-R.measured).abs(); R['err_zero']=R.measured.abs()
print(R.round(2).to_string(index=False))
R.round(4).to_csv('reference/tod_optiond_B8_predicts_dropped.csv',index=False)
