"""Checks after the parking all-variables result (not pre-registered): other seeds, without San Francisco,
equal weights, and forest variable importance. Run: uv run --all-extras python scripts/check_parking_allvars.py"""
import sys; sys.path.insert(0,'scripts'); sys.path.insert(0,'.')
import numpy as np, pandas as pd
import run_parking_allvars as ra, run_parking_expanded as rpe
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
v=pd.read_csv('reference/parking_allvars_values.csv')
e=pd.read_csv('reference/parking_expanded_effects.csv'); e=e[(e.status=='included')&(e.outcome=='all')][['prn_key','effect','weight','homes']]
d=v.merge(e,on='prn_key'); feats=[c for c in v.columns if c not in ('prn_key','place','state')]
def score(d, seed, tools=("one average","random forest","gradient boosting")):
    rng=np.random.default_rng(seed); out={t:[] for t in tools}
    for rep in range(10):
        perm=rng.permutation(len(d)); er={t:0 for t in tools}; W=0
        for f in range(10):
            te=perm[f::10]; tr=np.setdiff1d(np.arange(len(d)),te)
            Xtr,Xte=rpe._impute(d.iloc[tr],d.iloc[te],feats)
            for t in tools:
                pr=ra.predict(t,Xtr,d.effect.values[tr],d.weight.values[tr],Xte,rng)
                er[t]+=(np.abs(pr-d.effect.values[te])*d.weight.values[te]).sum()
            W+=d.weight.values[te].sum()
        for t in tools: out[t].append(er[t]/W)
    b=np.mean(out["one average"]); return {t:round(1-np.mean(v)/b,3) for t,v in out.items()}
d=d.reset_index(drop=True)
for s in (1,2,3): print('seed',s,score(d,s))
print('without SF', score(d[d.prn_key!='San Francisco, California, United States'].reset_index(drop=True),1))
print('unweighted', score(d.assign(weight=1.0),1))
# importance
X=d[feats].fillna(d[feats].median()).values
rf=RandomForestRegressor(500,min_samples_leaf=5,random_state=0,n_jobs=-1).fit(X,d.effect,sample_weight=d.weight)
imp=pd.Series(rf.feature_importances_,index=feats).sort_values(ascending=False); print(imp.head(12).round(3))
print('weight share top5', (d.weight.sort_values(ascending=False).head(5)/d.weight.sum()).round(3).tolist(), d.sort_values('weight',ascending=False).head(5).prn_key.str.split(',').str[0].tolist())
