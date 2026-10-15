"""Independent, read-only audit of source CSV and slide headline metrics."""
import csv,hashlib,json,statistics,urllib.request
from collections import Counter,defaultdict
from datetime import datetime,timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'data/raw/contoso_gaming_pc_app_output.csv'
raw=source.read_bytes()
with source.open(newline='') as f:
    reader=csv.DictReader(f); header=reader.fieldnames; rows=list(reader)
features=['AI_AutoComplete','AI_Chat','AI_Agent']; columns=['date','userid','startdate','plan','Status','DayOfWeek','Weekend','DaysSinceStart']+[k+t for t in ['_Success','_Error'] for k in features]
issues=Counter(); players=defaultdict(list); seen=set()
for r in rows:
    if set(r)!=set(columns):issues['schema']+=1
    if any(v is None or str(v).strip()=='' for v in r.values()):issues['missing_values']+=1
    day=int(r['DaysSinceStart']); date=datetime.strptime(r['date'],'%m/%d/%Y').date(); start=datetime.strptime(r['startdate'],'%m/%d/%Y').date()
    if (r['userid'],date) in seen:issues['duplicate_player_day']+=1
    seen.add((r['userid'],date))
    if (date-start).days!=day:issues['day_date_mismatch']+=1
    if not 0<=day<=59:issues['outside_day_range']+=1
    if not datetime(2025,3,3).date()<=start<=datetime(2025,3,7).date():issues['outside_signup_cohorts']+=1
    if r['DayOfWeek']!=date.strftime('%A') or r['Weekend']!=str(date.weekday()>=5):issues['calendar_mismatch']+=1
    if r['plan'] not in ['Free','Paid'] or r['Status'] not in ['Active','Cancelled']:issues['invalid_plan_status']+=1
    for k,cap in zip(features,[100,10,5] if r['plan']=='Free' else [200,50,20]):
        vals=[int(r[k+t]) for t in ['_Success','_Error']]
        if min(vals)<0 or sum(vals)>cap:issues['invalid_feature_counts']+=1
    players[r['userid']].append({**r,'day':day,'dt':date,'start':start,'attempts':sum(int(r[k+t]) for k in features for t in ['_Success','_Error'])})
users=[]
for uid,h in players.items():
    h.sort(key=lambda r:r['day'])
    if h[0]['day']!=0:issues['missing_day0']+=1
    if len({r['startdate'] for r in h})!=1:issues['inconsistent_signup_date']+=1
    if any(a['plan']=='Paid' and b['plan']=='Free' for a,b in zip(h,h[1:])):issues['paid_to_free']+=1
    cancels=[i for i,r in enumerate(h) if r['Status']=='Cancelled']
    if any(h[i]['plan']!='Paid' or i!=len(h)-1 for i in cancels):issues['invalid_cancellation_sequence']+=1
    upgrade=next((r['day'] for r in h if r['plan']=='Paid'),None) if h[0]['plan']=='Free' else None
    users.append({'id':uid,'initial':h[0]['plan'],'early_attempts':sum(r['attempts'] for r in h if r['day']<=6),'early_active_days':sum(r['day']<=6 for r in h),'retained':any(28<=r['day']<=34 for r in h),'upgrade':upgrade,'cancelled':bool(cancels),'last_day':h[-1]['day']})
remote=urllib.request.urlopen('https://raw.githubusercontent.com/vejadu/InterviewCase-Gaming-PC-App/main/contoso_gaming_pc_app_output.csv').read()
result={'source_sha256':hashlib.sha256(raw).hexdigest(),'matches_current_repository_bytes':raw==remote,'rows':len(rows),'players':len(players),'issues':dict(issues),'cohorts':dict(Counter(h[0]['startdate'] for h in players.values())),'observation_dates':[min(r['date'] for r in rows if False)] if False else [str(min(r['dt'] for h in players.values() for r in h)),str(max(r['dt'] for h in players.values() for r in h))],'day0_players':sum(h[0]['day']==0 for h in players.values()),'max_day':max(r['day'] for h in players.values() for r in h),'missing_player_days':300*60-len(rows),'zero_AI_attempt_rows':sum(r['attempts']==0 for h in players.values() for r in h),'initial_plans':dict(Counter(u['initial'] for u in users)),'upgrades':sum(u['upgrade'] is not None for u in users),'cancellations':sum(u['cancelled'] for u in users),'last_day_before59_without_explicit_cancellation':sum(u['last_day']<59 and not u['cancelled'] for u in users)}
threshold=statistics.median(u['early_attempts'] for u in users)
def outcome(g):
    f=[u for u in g if u['initial']=='Free' and (u['upgrade'] is None or u['upgrade']>=7)]
    return {'n':len(g),'retained':sum(u['retained'] for u in g),'retention_pct':100*sum(u['retained'] for u in g)/len(g),'free_n':len(f),'converters':sum(u['upgrade'] is not None for u in f),'conversion_pct':100*sum(u['upgrade'] is not None for u in f)/len(f)}
result['slide2_recomputed']={'threshold':threshold,'lower':outcome([u for u in users if u['early_attempts']<=threshold]),'higher':outcome([u for u in users if u['early_attempts']>threshold])}
result['sensitivity_free_only_same_threshold']={'lower':outcome([u for u in users if u['initial']=='Free' and u['early_attempts']<=threshold]),'higher':outcome([u for u in users if u['initial']=='Free' and u['early_attempts']>threshold])}
result['within_early_active_days']=[]
for lo,hi in [(1,3),(4,5),(6,7)]:
    g=[u for u in users if lo<=u['early_active_days']<=hi]
    lower=[u for u in g if u['early_attempts']<=threshold];higher=[u for u in g if u['early_attempts']>threshold]
    result['within_early_active_days'].append({'active_days':[lo,hi],'lower':outcome(lower),'higher':outcome(higher)})
upgrades=Counter(u['upgrade'] for u in users if u['upgrade'] is not None)
result['upgrade_counts_by_day']=dict(sorted(upgrades.items()))
result['first_week_conversion_count']=sum(v for k,v in upgrades.items() if 7<=k<=13)
result['day4_6_free_activity_rows']=sum(r['plan']=='Free' and 4<=r['day']<=6 for h in players.values() for r in h)
result['conversion_journey_prior_active_days_median']=statistics.median(sum(r['day']<u['upgrade'] for r in players[u['id']]) for u in users if u['upgrade'] is not None)
existing=json.loads((ROOT/'outputs/engagement_groups.json').read_text())
result['slide2_matches_saved_metrics']=all(result['slide2_recomputed'][g]['n']==existing['groups'][g]['n'] and abs(result['slide2_recomputed'][g]['retention_pct']-existing['groups'][g]['retention_pct'])<1e-10 and abs(result['slide2_recomputed'][g]['conversion_pct']-existing['groups'][g]['conversion_pct'])<1e-10 for g in ['lower','higher'])
(ROOT/'outputs/data_audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
