"""Focused descriptive EDA, with first-week exposures and later outcomes."""
import csv, json, statistics
from collections import defaultdict, Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
with (ROOT/'data/raw/contoso_gaming_pc_app_output.csv').open() as f: rows=list(csv.DictReader(f))
features=['AI_AutoComplete','AI_Chat','AI_Agent']
players=defaultdict(list)
for r in rows:
    r['day']=int(r['DaysSinceStart'])
    for k in features:
        for suffix in ['_Success','_Error']: r[k+suffix]=int(r[k+suffix])
    players[r['userid']].append(r)
summ=[]; upgrades=[]
for u,h in players.items():
    h.sort(key=lambda r:r['day'])
    early=[r for r in h if r['day']<=6]
    upgrade=next((r['day'] for r in h if r['plan']=='Paid'),None) if h[0]['plan']=='Free' else None
    if upgrade is not None: upgrades.append(upgrade)
    s={'id':u,'early_days':len(early),'retained':any(28<=r['day']<=34 for r in h),'eligible':h[0]['plan']=='Free' and (upgrade is None or upgrade>=7),'converted':upgrade is not None and upgrade>=7,'initial':h[0]['plan']}
    for k in features:
        attempts=sum(r[k+'_Success']+r[k+'_Error'] for r in early)
        s[k]=sum(r[k+'_Success'] for r in early)
        s[k+'_rate']=sum(r[k+'_Error'] for r in early)/attempts if attempts else 0
    s['total']=sum(s[k] for k in features)
    summ.append(s)
def stats(group):
    eligible=[s for s in group if s['eligible']]
    return {'n':len(group),'retention_pct':round(100*sum(s['retained'] for s in group)/len(group),1),'free_at_day7_n':len(eligible),'later_upgrades':sum(s['converted'] for s in eligible),'conversion_pct':round(100*sum(s['converted'] for s in eligible)/len(eligible),1) if eligible else None,'early_active_days_mean':round(statistics.mean(s['early_days'] for s in group),2)}
result={'outcome_definitions':{'early':'days 0–6','retention':'any activity days 28–34','conversion':'upgrade days 7–59 among initially Free with no upgrade before day 7'},'usage':{},'errors':{}}
for k in ['total']+features:
    ranked=sorted(summ,key=lambda s:s[k]); split=len(ranked)//2
    result['usage'][k]={'lower_half':stats(ranked[:split]),'upper_half':stats(ranked[split:]),'lower_max':ranked[split-1][k],'upper_min':ranked[split][k]}
for k in features:
    ranked=sorted(summ,key=lambda s:s[k+'_rate']); split=len(ranked)//2
    result['errors'][k]={'lower_half':stats(ranked[:split]),'upper_half':stats(ranked[split:]),'median_rate':round(statistics.median(s[k+'_rate'] for s in summ)*100,2),'overall_error_rate':round(100*sum(r[k+'_Error'] for r in rows)/sum(r[k+'_Error']+r[k+'_Success'] for r in rows),2)}
# First-week dominant feature by fraction of plan allowance, avoiding raw scale bias.
limits={'Free':[100,10,5],'Paid':[200,50,20]}
groups=defaultdict(list)
for s in summ:
    scores=[s[k]/limits[s['initial']][i] for i,k in enumerate(features)]
    groups[features[max(range(3),key=lambda i:scores[i])]].append(s)
result['dominant_feature_normalized']= {k:stats(v) for k,v in groups.items()}
# Weekend activity as share of possible player-days, using full day0–59 denominator.
weekend_possible=weekday_possible=0
from datetime import datetime,timedelta
for h in players.values():
    start=datetime.strptime(h[0]['startdate'],'%m/%d/%Y')
    for d in range(60):
        if (start+timedelta(days=d)).weekday()>=5: weekend_possible+=1
        else: weekday_possible+=1
result['weekend']={}
for label,flag,possible in [('weekend','True',weekend_possible),('weekday','False',weekday_possible)]:
    subset=[r for r in rows if r['Weekend']==flag]
    result['weekend'][label]={'observed_days':len(subset),'possible_days':possible,'activity_pct':round(100*len(subset)/possible,1),'attempts_per_active_day':round(statistics.mean(sum(r[k+'_Success']+r[k+'_Error'] for k in features) for r in subset),1)}
result['upgrade_timing']={'count':len(upgrades),'median_day':statistics.median(upgrades),'min':min(upgrades),'max':max(upgrades),'windows':dict(Counter('D4–6' if d<7 else 'D7–13' if d<14 else 'D14–20' if d<21 else 'D21–27' if d<28 else 'D28–34' if d<35 else 'D35–41' if d<42 else 'D42–45' for d in upgrades))}
# Pre-upgrade history: Free rows only, never classify upgrade-day events as Free.
journey=[]
for u,h in players.items():
    if h[0]['plan']!='Free':continue
    paid=next((r for r in h if r['plan']=='Paid'),None)
    if not paid:continue
    prior=[r for r in h if r['day']<paid['day']]
    recent=[r for r in prior if r['day']>=paid['day']-7]
    cap=lambda r:any(r[k+'_Success']+r[k+'_Error']>=limit for k,limit in zip(features,[100,10,5]))
    journey.append({'day':paid['day'],'active_days_before':len(prior),'cap_before':any(cap(r) for r in prior),'cap_recent':any(cap(r) for r in recent)})
result['journey']={'median_active_days_before':statistics.median(x['active_days_before'] for x in journey),'ever_hit_free_cap_before':sum(x['cap_before'] for x in journey),'hit_free_cap_prior_7_days':sum(x['cap_recent'] for x in journey)}
(ROOT/'outputs/additional_answers.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
# Transparent thresholds: exclude players with no attempts, keep tied rates together.
error_checks={}
for k in features:
    valid=[]
    for s in summ:
        early=[r for r in players[s['id']] if r['day']<=6]
        attempts=sum(r[k+'_Success']+r[k+'_Error'] for r in early)
        if attempts: valid.append(s)
    threshold=statistics.median(s[k+'_rate'] for s in valid)
    error_checks[k]={'threshold_pct':round(100*threshold,2),'excluded_no_attempts':len(summ)-len(valid),'at_or_below_median':stats([s for s in valid if s[k+'_rate']<=threshold]),'above_median':stats([s for s in valid if s[k+'_rate']>threshold])}
result['errors_threshold_groups']=error_checks
result['upgrade_windows_at_risk']=[]
for lo,hi in [(0,6),(7,13),(14,20),(21,27),(28,34),(35,41),(42,48),(49,55),(56,59)]:
    at_risk=232-sum(d<lo for d in upgrades)
    count=sum(lo<=d<=hi for d in upgrades)
    result['upgrade_windows_at_risk'].append({'days':[lo,hi],'upgrades':count,'not_yet_upgraded_at_start':at_risk,'pct':round(100*count/at_risk,1)})
(ROOT/'outputs/additional_answers.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'error_checks':error_checks,'upgrade_windows':result['upgrade_windows_at_risk']},indent=2))
