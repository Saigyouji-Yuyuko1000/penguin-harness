import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/evo-harness-rsi-toolkit/scripts'
sys.path.insert(0, str(SCRIPTS))
import benchmarks
import evo
import workspace

REPO = Path(os.environ.get('EVO_BENCHMARK', '/nonexistent-evo-benchmark-fixture'))


class AdapterTests(unittest.TestCase):
    @unittest.skipUnless(REPO.is_dir(), 'set EVO_BENCHMARK for actual-source checks')
    def test_all_current_gdpevo_packages_explicitly_map_one_continuous_case(self):
        rows = benchmarks.discover(REPO, 'GDPevo子集')
        self.assertEqual(len(rows), 6)
        for row in rows:
            self.assertEqual(row['training_case']['case_id'], 'CASE-001-train_tasks')
            self.assertEqual(row['training_case']['task_name'], 'train_tasks')
            self.assertEqual(len(row['members']), 5)
            self.assertEqual(len(row['test_cases']), 5)
            self.assertNotEqual(row['test_cases'][0]['case_id'], row['test_cases'][0]['task_name'])
            self.assertNotIn('solution', json.dumps(row))
            self.assertNotIn('reference_answer', json.dumps(row))

    @unittest.skipUnless(REPO.is_dir(), 'set EVO_BENCHMARK for actual-source checks')
    def test_no_fixed_group_number_count_port_or_member_id(self):
        import yaml
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = REPO / 'benchmarks/gdpevo-crm'
            shutil.copytree(source, root / 'benchmarks/custom-domain')
            for kind in ('train', 'test'):
                name = 'penguinharness-benchmark-gdpevo-crm-' + kind
                shutil.copytree(REPO / 'packages' / name, root / 'packages' / name)
                for statement in (root / 'packages' / name).glob('*/statement/README.md'):
                    statement.write_text(statement.read_text().replace('benchmarks/gdpevo-crm', 'benchmarks/custom-domain'))
            manifest = root / 'benchmarks/custom-domain/tasks/task_group.yaml'
            value = yaml.safe_load(manifest.read_text())
            value['env']['port'] = 19471
            value['task_group']['task_group_id'] = 'not-a-numeric-group'
            value['train_tasks'] = value['train_tasks'][:2]
            value['training_run']['task_count'] = 2
            manifest.write_text(yaml.safe_dump(value))
            row = benchmarks.gdpevo(root, str(manifest.relative_to(root)))
            self.assertEqual(len(row['members']), 2)
            self.assertEqual(row['training_io']['feedback_url'], 'http://127.0.0.1:19471/api/judge')

    @unittest.skipUnless(REPO.is_dir(), 'set EVO_BENCHMARK for actual-source checks')
    def test_other_harbor_capability_limit_does_not_change_algorithm(self):
        row = benchmarks.ordinary(REPO, 'packages/penguinharness-benchmark-sec-d')
        self.assertEqual(len(row['cases']), 10)
        self.assertTrue(row['capabilities']['evaluation'])
        self.assertFalse(row['capabilities']['complete_live_rsi'])
        self.assertIn('original-Solver', row['limitation'])

    def test_workspace_discovery_and_actual_project_import(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            package = root / 'packages/ordinary'
            package.mkdir(parents=True)
            (package / 'benchmark_config.toml').write_text('id="ordinary"\nversion="1"\nstatus="published"\n')
            for part, text in (('statement', 'Public task'), ('rubric', 'Private grading')):
                p = package / 'CASE-local' / part / 'README.md'
                p.parent.mkdir(parents=True)
                p.write_text(text)
            row = benchmarks.ordinary(root, 'packages/ordinary')
            self.assertTrue(row['capabilities']['original_solver_feedback'])
            self.assertFalse(benchmarks.project_package(root / 'project', row['training_package'])['ready'])
            target = root / 'project/benchmarks/ordinary'
            shutil.copytree(package, target)
            self.assertTrue(benchmarks.project_package(root / 'project', row['training_package'])['ready'])
            (target / 'CASE-local/rubric/README.md').write_text('Changed grading')
            self.assertFalse(benchmarks.project_package(root / 'project', row['training_package'])['ready'])

    def test_ref_resolution_pins_branches_tags_slashes_and_moving_refs(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            def git(*args):
                return subprocess.check_output(['git', '-C', td, *args], stderr=subprocess.DEVNULL, text=True).strip()
            git('init', '-b', 'main')
            folder = root / 'packages/demo'
            folder.mkdir(parents=True)
            (folder / 'x').write_text('v1')
            git('add', '.')
            git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'fixture')
            git('remote', 'add', 'origin', 'https://github.com/example/fixture.git')
            git('branch', 'feature/split')
            git('tag', 'v1')
            for ref in ('main', 'feature/split', 'v1'):
                value = benchmarks.resolve_link(root, 'https://github.com/example/fixture/tree/' + ref + '/packages/demo')
                self.assertEqual(value['requested_ref'], ref)
                self.assertEqual(value['commit'], git('rev-parse', 'HEAD'))
            old = benchmarks.pin(root)
            (folder / 'x').write_text('v2')
            with self.assertRaises(ValueError):
                benchmarks.pin(root)
            git('add', '.')
            git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'move')
            with self.assertRaises(ValueError):
                benchmarks.pin(root, old)

    @unittest.skipUnless(REPO.is_dir(), 'set EVO_BENCHMARK for actual-source checks')
    def test_subset_budget_scope_and_ambiguous_domain_do_not_multiply_authorization(self):
        request={'repo':str(REPO),'project':'/synthetic/project','benchmark':'GDPevo子集',
                 'runtime':{'provider':'fixture','model_id':'no-model','thinking_level':'max'},
                 'budget_usd':10,'paid_authorized':True}
        with patch.object(benchmarks,'pin',return_value='a'*40), patch.object(benchmarks,'project_package',return_value={'ready':True}):
            total=benchmarks.bootstrap(request)
            self.assertFalse(total['ready'])
            self.assertTrue(any('domain selection' in m for m in total['missing_inputs']))
            self.assertAlmostEqual(sum(total['budget_allocations'].values()),10)
            each=benchmarks.bootstrap({**request,'budget_scope':'per-benchmark'})
            self.assertEqual(each['authorized_total_usd'],60)
            selected=benchmarks.bootstrap({**request,'selected_benchmark':'penguinharness-benchmark-gdpevo-crm-train'})
            self.assertTrue(selected['ready'])
            self.assertEqual(selected['budget_allocations'],{'gdpevo-crm':10})

    def test_current_and_legacy_tool_status_never_hide_failure(self):
        self.assertEqual(evo.tool_status({'status': 'completed'}), 'completed')
        self.assertEqual(evo.tool_status({'stop_reason': 'aborted'}), 'aborted')
        self.assertIsNone(evo.tool_status({}))
        for bad in ({'status': 'completed', 'stop_reason': 'fatal'}, {'status': 'unknown'}):
            with self.assertRaises(ValueError):
                evo.tool_status(bad)

    def test_loading_stays_topic_body_general_description_and_total_budget(self):
        entries = [dict(id='method', level='topic', topic='local', trigger='T', scope='S', body='FULL METHOD'),
                   dict(id='general', level='general', trigger='T', scope='S', description='CORE METHOD', body='PRIVATE DETAIL')]
        files = evo.render_package(entries, 16000, general_storage='description-only')
        actual = evo.model_context(files)['text']
        self.assertIn('FULL METHOD', actual)
        self.assertIn('CORE METHOD', actual)
        self.assertNotIn('PRIVATE DETAIL', actual)
        self.assertNotIn('/opt/penguin-bench', files['SKILL.md'].decode())
        with self.assertRaises(ValueError):
            evo.render_package([{**entries[0], 'body': 'x' * 17000}], 16000)


class WorkspaceBoundaryTests(unittest.TestCase):
    def fixture(self):
        candidate = b'[]'
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        profile=Path(temporary.name)/'profile.json'
        profile.write_text(json.dumps({'protocol':'evo-native-workspace-v1','members':[{'case_id':'case','task_id':'case'}],
            'train_ids':['case'],'runtime':{},'test_agent_id':'solver','controller_workspace':temporary.name,
            'private_learning':temporary.name,'public_files':{'case':{'README.md':'fake'}}}))
        record = {'request': {'profile':str(profile),'profile_sha256':benchmarks.sha(profile),'case_id':'case','binding': {'session_id': 'original'}},
                  'answer_sha256': evo.digest(b'answer'), 'prompt': 'COMPLETE AUTHORIZED FEEDBACK',
                  'negative': True, 'initial_trace_sources': [], 'seal_path': '/own/seal-request.json',
                  'seal_request': {'op': 'file-digest', 'path': '/own/candidates.json'},
                  'seal_command': 'python3 -B /installed/evo.py /own/seal-request.json'}
        record['request'],_=workspace.bound_request(record['request'])
        own=record['request']['candidate']
        record['seal_path']=str(Path(own).parent/'seal-request.json')
        record['seal_request']={'op':'file-digest','path':own}
        record['seal_command']='python3 -B /installed/evo.py '+record['seal_path']
        def message(kind, **rest):
            return {'payload': {'type': kind, **rest}}
        feedback = message('text', role='user', sender='parent_agent', text=record['prompt'])
        write = message('tool_call', name='write_file', tool_call_id='write', arguments=json.dumps({'file_path': own, 'content': '[]'}))
        call = message('tool_call', name='exec_command', tool_call_id='seal', arguments=json.dumps({'cmd': record['seal_command']}))
        output = message('tool_call_output', status='completed', tool_call_id='seal', output=json.dumps({'file_path': own, 'sha256': evo.digest(candidate)}))
        view = {'binding': {'session_id': 'original'}, 'messages': [feedback, write, call, output],
                'pairs': [{'call': write, 'observation': message('tool_call_output', status='completed', output='written')}, {'call': call, 'observation': output}], 'denied_calls': []}
        return record, view, candidate

    def test_original_session_full_feedback_then_candidate_and_seal(self):
        record, view, candidate = self.fixture()
        self.assertTrue(workspace.verify_continuation(record, view, b'answer', candidate)['feedback_observed'])
        for mutate in ('foreign_session', 'partial_feedback', 'changed_answer', 'no_reflection', 'new_query', 'duplicate_feedback'):
            r, v, c = copy.deepcopy(record), copy.deepcopy(view), candidate
            answer = b'answer'
            if mutate == 'foreign_session': v['binding']['session_id'] = 'replacement'
            if mutate == 'partial_feedback': v['messages'][0]['payload']['text'] = 'feedback path only'
            if mutate == 'changed_answer': answer = b'changed'
            if mutate == 'no_reflection': v['messages'] = v['messages'][:1]
            if mutate == 'new_query': v['messages'].append({'payload': {'type': 'tool_call', 'name': 'exec_command', 'tool_call_id': 'query', 'arguments': '{"cmd":"curl business"}'}})
            if mutate == 'duplicate_feedback': v['messages'].insert(0, v['messages'][0])
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                workspace.verify_continuation(r, v, answer, c)


if __name__ == '__main__':
    unittest.main()
