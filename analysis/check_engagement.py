"""Descriptive confounding checks; no causal identification claimed."""
import csv,json,math
from collections import defaultdict
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
with (ROOT/'data/raw/contoso_gaming_pc_app_output.csv').open() as f: rows=list(csv.DictReader(f))
features=['AI_AutoComplete','AI_Chat','AI_Agent']; players=defaultdict(list)
for r in rows:
    r['day']=int(r['DaysSinceStart'])
    for k in features:
        for suffix in ['_Success','_Error']:r[k+suffix]=int(r[k+suffix])
    players[r['userid']].append(r)
users=[]
for uid,h in players.items():
    h.sort(key=lambda r:r['day']); early=[r for r in h if r['day']<=6]
    upgrade=next((r['day'] for r in h if r['plan']=='Paid'),None) if h[0]['plan']=='Free' else None
    attempts=sum(r[k+'_Success']+r[k+'_Error'] for r in early for k in features)
    errors=sum(r[k+'_Error'] for r in early for k in features)
    s=dict(id=uid,active_days=len(early),attempts=attempts,errors=errors,error_rate=errors/attempts if attempts else None,eligible=h[0]['plan']=='Free' and (upgrade is None or upgrade>=7),converted=int(upgrade is not None and upgrade>=7),retained=int(any(28<=r['day']<=34 for r in h)),paid=int(h[0]['plan']=='Paid'),upgrade=upgrade)
    for k in features:
        a=sum(r[k+'_Success']+r[k+'_Error'] for r in early)
        s[k+'_rate']=sum(r[k+'_Error'] for r in early)/a if a else None
        s[k+'_attempts']=a
    users.append(s)
def fit(data,outcome,variables):
    X=np.array([[1]+[f(s) for _,f in variables] for s in data],dtype=float); y=np.array([s[outcome] for s in data])
    b=np.zeros(X.shape[1])
    for _ in range(100):
        p=1/(1+np.exp(-np.clip(X@b,-35,35))); w=np.maximum(p*(1-p),1e-9)
        delta=np.linalg.solve(X.T@(w[:,None]*X),X.T@(y-p)); b+=delta
        if np.max(abs(delta))<1e-8:break
    se=np.sqrt(np.diag(np.linalg.inv(X.T@(w[:,None]*X))))
    return {'n':len(data),'events':int(sum(y)),'terms':{name:{'odds_ratio':round(math.exp(float(v)),3),'ci95':[round(math.exp(float(v-1.96*e)),3),round(math.exp(float(v+1.96*e)),3)]} for (name,_),v,e in zip(variables,b[1:],se[1:])}}
error=('error_rate_per_5pp',lambda s:s['error_rate']/0.05)
engagement=[('active_days',lambda s:s['active_days']),('attempts_doubling',lambda s:math.log2(s['attempts']))]
result={'definitions':{'exposure':'days 0–6','retention':'any activity days 28–34','conversion':'days 7–59, initially Free, no upgrade before day7','model':'logistic regression; approximate Wald 95% confidence intervals; associative only'},'models':{}}
for outcome in ['converted','retained']:
    data=[s for s in users if s['error_rate'] is not None and (s['eligible'] if outcome=='converted' else True)]
    controls=engagement+([('initial_paid',lambda s:s['paid'])] if outcome=='retained' else [])
    result['models'][outcome]={'error_unadjusted':fit(data,outcome,[error]),'error_adjusted':fit(data,outcome,[error]+controls),'usage_unadjusted':fit(data,outcome,[engagement[1]]),'usage_adjusted':fit(data,outcome,controls)}
result['error_groups']={}
valid=[s for s in users if s['error_rate'] is not None]; med=float(np.median([s['error_rate'] for s in valid]))
for name,group in [('lower',[s for s in valid if s['error_rate']<=med]),('higher',[s for s in valid if s['error_rate']>med])]:
    free=[s for s in group if s['eligible']]
    result['error_groups'][name]={'n':len(group),'mean_active_days':round(np.mean([s['active_days'] for s in group]),2),'mean_attempts':round(np.mean([s['attempts'] for s in group]),1),'retention_pct':round(100*np.mean([s['retained'] for s in group]),1),'conversion_pct':round(100*np.mean([s['converted'] for s in free]),1),'free_n':len(free)}
# Within broad baseline engagement groups, retain original pooled-error threshold.
result['within_engagement']=[]
for lo,hi in [(1,3),(4,5),(6,7)]:
    group=[s for s in valid if lo<=s['active_days']<=hi]
    entry={'active_days':[lo,hi]}
    for label,cond in [('lower',lambda s:s['error_rate']<=med),('higher',lambda s:s['error_rate']>med)]:
        g=[s for s in group if cond(s)]; free=[s for s in g if s['eligible']]
        entry[label]={'n':len(g),'retention_pct':round(100*np.mean([s['retained'] for s in g]),1),'free_n':len(free),'conversion_pct':round(100*np.mean([s['converted'] for s in free]),1) if free else None}
    result['within_engagement'].append(entry)
upgrades=[s['upgrade'] for s in users if s['upgrade'] is not None]
result['daily_conversion']=[{'day':d,'upgrades':upgrades.count(d),'at_risk':232-sum(t<d for t in upgrades),'cumulative':sum(t<=d for t in upgrades),'cumulative_pct':100*sum(t<=d for t in upgrades)/232} for d in range(60)]
result['weekly_conversion']=[]
for lo,hi in [(0,6),(7,13),(14,20),(21,27),(28,34),(35,41),(42,48),(49,55),(56,59)]:
    n=232-sum(t<lo for t in upgrades); k=sum(lo<=t<=hi for t in upgrades); p=k/n; z=1.96
    center=(p+z*z/(2*n))/(1+z*z/n); half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
    result['weekly_conversion'].append({'lo':lo,'hi':hi,'n':n,'count':k,'pct':100*p,'ci95':[100*max(0,center-half),100*min(1,center+half)]})
(ROOT/'outputs/engagement_checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='daily_conversion'},indent=2))
# Sensitivity: control for mix, since Agent has a higher baseline error rate.
mix=[('coach_attempt_share',lambda s:s['AI_Chat_attempts']/s['attempts']),('agent_attempt_share',lambda s:s['AI_Agent_attempts']/s['attempts'])]
for outcome in ['converted','retained']:
    data=[s for s in users if s['error_rate'] is not None and (s['eligible'] if outcome=='converted' else True)]
    controls=engagement+mix+([('initial_paid',lambda s:s['paid'])] if outcome=='retained' else [])
    result['models'][outcome]['error_adjusted_feature_mix']=fit(data,outcome,[error]+controls)
    result['models'][outcome]['error_count_unadjusted']=fit(data,outcome,[('errors_per_5',lambda s:s['errors']/5)])
    result['models'][outcome]['error_count_adjusted']=fit(data,outcome,[('errors_per_5',lambda s:s['errors']/5)]+controls)
(ROOT/'outputs/engagement_checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({o:{k:v for k,v in result['models'][o].items() if k in ['error_adjusted_feature_mix','error_count_unadjusted','error_count_adjusted']} for o in ['converted','retained']},indent=2))
for outcome in ['converted','retained']:
    data=[s for s in users if s['error_rate'] is not None and (s['eligible'] if outcome=='converted' else True)]
    controls=engagement+([('initial_paid',lambda s:s['paid'])] if outcome=='retained' else [])
    result['models'][outcome]['error_count_adjusted_engagement']=fit(data,outcome,[('errors_per_5',lambda s:s['errors']/5)]+controls)
print(json.dumps({o:result['models'][o]['error_count_adjusted_engagement'] for o in ['converted','retained']},indent=2))
(ROOT/'outputs/engagement_checks.json').write_text(json.dumps(result,indent=2)+'\n')
