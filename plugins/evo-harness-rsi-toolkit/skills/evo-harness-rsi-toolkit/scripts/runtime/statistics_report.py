"""Read existing native result matrices; never dispatch, select or rescore trials."""
import json
from datetime import datetime
import math
from pathlib import Path
import statistics
import sys

import protocol


def moments(values):
    return {'round_scores': values, 'mean': statistics.mean(values),
            'sample_variance': statistics.variance(values) if len(values) > 1 else None,
            'sample_stddev': statistics.stdev(values) if len(values) > 1 else None}


def measurements(entries):
    """Read each native Harbor execution once, including failed attempts.

    Trial totals include container children. Session breakdowns remain linked
    evidence, not another bill added to those same totals.
    """
    records, seen, issues = [], set(), []
    def number(value):
        return value if type(value) in (int, float) and math.isfinite(value) and value >= 0 else None
    def timestamp(value):
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()
        except (AttributeError, TypeError, ValueError):
            return None
    for item in entries:
        protocol.require(item['phase'] in ('train', 'test'), 'unknown measurement phase')
        path = Path(item['trial_result']).resolve()
        raw = protocol.read(path)
        identity = ('trial', str(raw['id'])) if raw.get('id') else ('path', str(path))
        protocol.require(identity not in seen, 'duplicate native trial in cost records')
        seen.add(identity)
        agent = raw.get('agent_result') or {}
        cached = number(agent.get('n_cache_tokens'))
        total_input = number(agent.get('n_input_tokens'))
        output = number(agent.get('n_output_tokens'))
        uncached = total_input - cached if total_input is not None and cached is not None and total_input >= cached else None
        if total_input is not None and cached is not None and cached > total_input:
            issues.append({'trial_result': str(path), 'issue': 'cache exceeds input; uncached unknown'})
        start, end = raw.get('started_at'), raw.get('finished_at')
        a, b = timestamp(start), timestamp(end)
        elapsed = b - a if a is not None and b is not None and b >= a else None
        record = {**item, 'trial_result': str(path), 'trial_sha256': protocol.sha(path),
                  'native_trial_id': raw.get('id'), 'cost_usd': number(agent.get('cost_usd')),
                  'started_at': start, 'finished_at': end, 'elapsed_sec': elapsed,
                  'cached_input': cached, 'uncached_input': uncached, 'output': output,
                  'total_input': total_input,
                  'total_tokens': total_input + output if total_input is not None and output is not None else None,
                  'exception_info': raw.get('exception_info'),
                  'rewards': (raw.get('verifier_result') or {}).get('rewards')}
        records.append(record)
    def totals(rows):
        result = {}
        for key in ('cost_usd', 'elapsed_sec', 'cached_input', 'uncached_input', 'output', 'total_input', 'total_tokens'):
            known = [r[key] for r in rows if r[key] is not None]
            result[key] = {'total': sum(known) if rows and len(known) == len(rows) else None,
                           'known_subtotal': sum(known), 'unknown_records': len(rows) - len(known)}
        return result
    return {'records': records, 'totals': {phase: totals([r for r in records if r['phase'] == phase])
                                           for phase in ('train', 'test')}, 'issues': issues,
            'scope': 'native trial totals; host/controller overhead must be reported separately, once',
            'duration_scope': 'summed trial durations, not experiment wall clock'}


def summarize(request):
    domains = request['domains']
    protocol.require(domains and len({d['benchmark'] for d in domains}) == len(domains),
                     'declare each domain exactly once')
    # Scores must already share the declared scale. No benchmark-dependent
    # rescaling or selection of the best trial takes place in this reporter.
    protocol.require(request.get('common_scale') == '0-100', 'a common 0-100 scale is required')
    repeats = request.get('runs', 3)
    protocol.require(type(repeats) is int and repeats > 0, 'invalid repeats')
    results, missing, runtime = [], [], None
    for domain in domains:
        record = {'benchmark': domain['benchmark'], 'conditions': {}}
        cases = None
        for condition in ('base', 'skill'):
            source = Path(domain[condition])
            req = protocol.read(source)
            protocol.require(req['runs'] == repeats, 'repetition counts differ')
            pair = {key: req['identity'][key] for key in ('provider', 'model_id', 'thinking_level')}
            runtime = pair if runtime is None else runtime
            protocol.require(pair == runtime, 'model configuration differs')
            cases = req['case_ids'] if cases is None else cases
            protocol.require(req['case_ids'] == cases, 'Base/Skill case rosters differ')
            value = protocol.matrix(req)
            result = {'source_request': str(source), 'request_sha256': protocol.sha(source),
                      'cells_sha256': protocol.sha(req['cells']), 'identity': req['identity'],
                      'complete': value['complete']}
            if value['complete']:
                evaluation = value['evaluation']
                scores = [statistics.mean(c['runs'][n]['score'] for c in evaluation['cases'])
                          for n in range(repeats)]
                result.update(moments(scores), cases=evaluation['cases'],
                              cost_complete=value['cost_complete'])
            else:
                result['missing'] = value['missing']
                missing.append({'benchmark': domain['benchmark'], 'condition': condition,
                                'cells': value['missing']})
            record['conditions'][condition] = result
        if all(c['complete'] for c in record['conditions'].values()):
            record['paired_delta'] = moments([s-b for b, s in zip(
                record['conditions']['base']['round_scores'], record['conditions']['skill']['round_scores'])])
        results.append(record)
    overall = None
    if not missing:
        overall = {condition: moments([statistics.mean(
            d['conditions'][condition]['round_scores'][n] for d in results)
            for n in range(repeats)]) for condition in ('base', 'skill')}
        overall['paired_delta'] = moments([s-b for b, s in zip(
            overall['base']['round_scores'], overall['skill']['round_scores'])])
    return {'schema': 'evo-fixed-skill-test-statistics-v1', 'complete': not missing,
            'domain_roster': [d['benchmark'] for d in domains], 'runs': repeats,
            'domains': results, 'overall': overall, 'missing': missing,
            'interpretation': 'test variation of fixed per-domain Skills, not independent learning runs',
            'validation_scope': 'matrix arithmetic; retain original trial/State verification verdicts separately',
            'versions': request.get('versions'),
            'measurements': measurements(request.get('measurements', [])),
            'model_calls': 0}


if __name__ == '__main__':
    print(json.dumps(summarize(protocol.read(sys.argv[1])), ensure_ascii=False, allow_nan=False))
