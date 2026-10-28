"""Six domains each train once and retain three fixed-State test repetitions.

Aggregate within round before variance; retain low scores and per-domain spread.
Missing/failed/duplicate cells never become a complete overall score. Model or
State changes cannot be pooled. One repetition has no sample variance.
"""
import json
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/evo-harness-rsi-toolkit/scripts'
sys.path.insert(0, str(SCRIPTS / 'runtime'))
import statistics_report as report


class StatisticsTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.request = {'common_scale': '0-100', 'runs': 3, 'domains': []}
        for d in range(6):
            item = {'benchmark': 'domain-' + str(d)}
            for condition in ('base', 'skill'):
                prefix = str(d) + '-' + condition
                identity = {'agent_id': prefix, 'expected_version': 1,
                            'provider': 'fixture', 'model_id': 'no-model', 'thinking_level': 'max'}
                rows = []
                for run, offset in enumerate((-10, 0, 10), 1):
                    # Domains move in opposite directions. Overall variance is zero,
                    # although each domain's test score has sample variance 100.
                    score = 50 + (offset if d % 2 else -offset) + (2 if condition == 'skill' else 0)
                    for case in ('a', 'b', 'c', 'd', 'e'):
                        rows.append({'protocol_version': 1, 'status': 'ok', **identity,
                                     'case_id': case, 'run': run, 'score': score, 'cost': None,
                                     'duration_ms': 1, 'session_id': f'{prefix}-{run}-{case}'})
                cells = self.root / (prefix + '-cells.json'); cells.write_text(json.dumps(rows))
                matrix = {'cells': str(cells), 'evo_tool': str(SCRIPTS / 'evo.py'),
                          'case_ids': ['a', 'b', 'c', 'd', 'e'], 'runs': 3, 'identity': identity,
                          'time': '2026-10-28T00:00:00Z', 'summary_title': 'fixture', 'summary': ''}
                path = self.root / (prefix + '.json'); path.write_text(json.dumps(matrix))
                item[condition] = str(path)
            self.request['domains'].append(item)

    def test_round_first_statistics_preserve_domain_scores_costs_and_files(self):
        before = {p.name: p.read_bytes() for p in self.root.iterdir()}
        result = report.summarize(self.request)
        self.assertTrue(result['complete'])
        self.assertEqual(result['overall']['base']['round_scores'], [50, 50, 50])
        self.assertEqual(result['overall']['base']['sample_variance'], 0)
        self.assertEqual(result['overall']['skill']['mean'], 52)
        self.assertEqual(result['overall']['paired_delta']['mean'], 2)
        self.assertEqual(result['domains'][0]['conditions']['base']['sample_variance'], 100)
        self.assertEqual(result['domains'][0]['conditions']['base']['sample_stddev'], 10)
        self.assertFalse(result['domains'][0]['conditions']['base']['cost_complete'])
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.iterdir()})

    def test_missing_cell_does_not_yield_partial_roster_overall(self):
        p = self.root / '0-skill-cells.json'; rows = json.loads(p.read_text()); rows.pop()
        p.write_text(json.dumps(rows))
        result = report.summarize(self.request)
        self.assertFalse(result['complete']); self.assertIsNone(result['overall'])
        self.assertEqual(result['missing'][0]['cells'], [{'case_id': 'e', 'run': 3}])

    def test_duplicate_or_changed_state_refused_instead_of_selecting_best(self):
        p = self.root / '0-skill-cells.json'; rows = json.loads(p.read_text())
        p.write_text(json.dumps(rows + [rows[0]]))
        with self.assertRaisesRegex(ValueError, 'duplicate'): report.summarize(self.request)
        rows[0]['expected_version'] = 2; p.write_text(json.dumps(rows))
        with self.assertRaisesRegex(ValueError, 'mismatch'): report.summarize(self.request)

    def test_one_repetition_is_not_zero_variance(self):
        self.request['runs'] = 1
        for d in self.request['domains']:
            for condition in ('base', 'skill'):
                p = Path(d[condition]); req = json.loads(p.read_text()); req['runs'] = 1
                p.write_text(json.dumps(req)); c = Path(req['cells'])
                c.write_text(json.dumps([r for r in json.loads(c.read_text()) if r['run'] == 1]))
        result = report.summarize(self.request)
        self.assertIsNone(result['overall']['base']['sample_variance'])
        self.assertIsNone(result['overall']['base']['sample_stddev'])

    def test_native_usage_keeps_unknowns_and_avoids_cache_double_count(self):
        p = self.root / 'trial.json'
        p.write_text(json.dumps({'id': 'unique-trial', 'started_at': '2026-10-28T00:00:00Z',
            'finished_at': '2026-10-28T00:00:12Z', 'agent_result': {'cost_usd': 0.2,
            'n_input_tokens': 100, 'n_cache_tokens': 80, 'n_output_tokens': 25}}))
        entries = [{'phase': 'train', 'trial_result': str(p)}]
        before = p.read_bytes(); result = report.measurements(entries)
        row = result['records'][0]
        self.assertEqual((row['uncached_input'], row['total_tokens'], row['elapsed_sec']), (20, 125, 12))
        self.assertEqual(result['totals']['train']['cost_usd']['total'], 0.2)
        self.assertEqual(p.read_bytes(), before)
        copied = self.root / 'copy.json'; copied.write_bytes(before)
        with self.assertRaisesRegex(ValueError, 'duplicate native trial'):
            report.measurements(entries + [{'phase': 'test', 'trial_result': str(copied)}])
        p.write_text(json.dumps({'id': 'unknown', 'agent_result': {'n_output_tokens': 25}}))
        result = report.measurements(entries)
        self.assertIsNone(result['records'][0]['uncached_input'])
        self.assertIsNone(result['totals']['train']['cost_usd']['total'])
        self.assertEqual(result['totals']['train']['cost_usd']['unknown_records'], 1)



if __name__ == '__main__': unittest.main()
