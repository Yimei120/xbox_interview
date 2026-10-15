"""Answer the mandatory case questions using the unchanged repository CSV."""
import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
with (ROOT / 'data/raw/contoso_gaming_pc_app_output.csv').open(newline='') as f:
    rows = list(csv.DictReader(f))
players = defaultdict(list)
seen = set()
for row in rows:
    row['day'] = int(row['DaysSinceStart'])
    key = (row['userid'], row['day'])
    assert key not in seen, f'Duplicate player-day: {key}'
    seen.add(key)
    players[row['userid']].append(row)
for history in players.values():
    history.sort(key=lambda r: r['day'])
    assert history[0]['day'] == 0
n = len(players)
initial_free = {u for u, h in players.items() if h[0]['plan'] == 'Free'}
initial_paid = set(players) - initial_free
ever_paid = {u for u, h in players.items() if any(r['plan'] == 'Paid' for r in h)}
converted = initial_free & ever_paid
cancelled = {u for u, h in players.items() if any(r['Status'] == 'Cancelled' for r in h)}
assert cancelled <= ever_paid

def count_rate(ids, denominator):
    return {'players': len(ids), 'denominator': denominator, 'percent': round(100 * len(ids) / denominator, 2)}

result = {
    'source': 'https://github.com/vejadu/InterviewCase-Gaming-PC-App/blob/main/contoso_gaming_pc_app_output.csv',
    'rows': len(rows),
    'new_accounts': {'total': n, 'Free': len(initial_free), 'Paid': len(initial_paid)},
    'daily_retention': {str(d): count_rate({u for u, h in players.items() if any(r['day'] == d for r in h)}, n) for d in [1, 7, 14, 30, 59]},
    'weekly_retention': {f'W{w} (days {1 + (w-1)*7}-{w*7})': count_rate({u for u, h in players.items() if any(1 + (w-1)*7 <= r['day'] <= w*7 for r in h)}, n) for w in range(1, 9)},
    'conversion': count_rate(converted, len(initial_free)),
    'paid_cancellations': count_rate(cancelled, len(ever_paid)),
    'cancellations_by_initial_plan': {'initially_Paid': count_rate(cancelled & initial_paid, len(initial_paid)), 'upgraded_from_Free': count_rate(cancelled & converted, len(converted))},
}
output = ROOT / 'outputs/answers.json'
output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
