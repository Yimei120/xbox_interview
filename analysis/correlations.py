"""Point-biserial correlations; fixed-seed player bootstrap intervals."""
import contextlib,io,json
import numpy as np
with contextlib.redirect_stdout(io.StringIO()):
    from check_engagement import users,features,fit,ROOT
rng=np.random.default_rng(20250303)
variables=[('active_days',lambda s:s['active_days']),('AI_attempts',lambda s:s['attempts']),('attempts_per_active_day',lambda s:s['attempts']/s['active_days'])]+[(k+'_attempts',lambda s,k=k:s[k+'_attempts']) for k in features]
results={}
for outcome in ['converted','retained']:
    group=[s for s in users if s['eligible']] if outcome=='converted' else users
    y=np.array([s[outcome] for s in group]); results[outcome]={'n':len(group),'events':int(y.sum()),'correlations':{}}
    for name,fun in variables:
        x=np.array([fun(s) for s in group],dtype=float)
        r=float(np.corrcoef(x,y)[0,1]); boots=[]
        for _ in range(3000):
            ix=rng.integers(0,len(group),len(group))
            if np.std(y[ix]) and np.std(x[ix]):boots.append(np.corrcoef(x[ix],y[ix])[0,1])
        results[outcome]['correlations'][name]={'r':round(r,3),'ci95':[round(float(v),3) for v in np.quantile(boots,[.025,.975])],'outcome_yes_mean':round(float(x[y==1].mean()),2),'outcome_no_mean':round(float(x[y==0].mean()),2)}
    # Exploratory feature-specific models: shares normalized by total attempts.
    base=[('active_days',lambda s:s['active_days']),('attempts_doubling',lambda s:np.log2(s['attempts']))]
    if outcome=='retained':base+=[('initial_paid',lambda s:s['paid'])]
    results[outcome]['feature_sensitivity']={}
    for k in features:
        results[outcome]['feature_sensitivity'][k]=fit(group,outcome,base+[(k+'_share_per_10pp',lambda s,k=k:s[k+'_attempts']/s['attempts']/.1)])
(ROOT/'outputs/correlations.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
