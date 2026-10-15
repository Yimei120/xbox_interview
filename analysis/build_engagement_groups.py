"""Build descriptive groups from first-week total attempts; keep median ties together."""
import contextlib
import io
import json
import statistics
with contextlib.redirect_stdout(io.StringIO()):
    from check_engagement import users, ROOT
threshold = statistics.median(s['attempts'] for s in users)
result = {'threshold': threshold, 'groups': {}}
for label, predicate in [('lower', lambda s: s['attempts'] <= threshold), ('higher', lambda s: s['attempts'] > threshold)]:
    group = [s for s in users if predicate(s)]
    free = [s for s in group if s['eligible']]
    retained = sum(s['retained'] for s in group)
    converted = sum(s['converted'] for s in free)
    result['groups'][label] = {'n': len(group), 'min_attempts': min(s['attempts'] for s in group), 'max_attempts': max(s['attempts'] for s in group), 'retained': retained, 'retention_pct': 100 * retained / len(group), 'free_n': len(free), 'converted': converted, 'conversion_pct': 100 * converted / len(free)}
(ROOT / 'outputs/engagement_groups.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
