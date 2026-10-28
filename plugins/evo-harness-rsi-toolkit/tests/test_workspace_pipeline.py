"""Synthetic native-format execution/worker/continuation, never paid scores."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/evo-harness-rsi-toolkit/scripts'
sys.path.insert(0, str(SCRIPTS))
import benchmarks
import evo
import workspace


class NativeWorkspacePipeline(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        # Synthetic native traces use a preverified Project. Full package drift is
        # exercised independently by test_package_integrity and manifest_pipeline.
        imports = patch.object(benchmarks, 'project_package', return_value={'ready': True})
        imports.start(); self.addCleanup(imports.stop)
        self.state = self.root / 'agents/solver/agent_state'
        self.state.mkdir(parents=True)
        (self.state/'system_config.yaml').write_text('version: 1\nmodel:\n  thinking_level: max\n')
        (self.state/'AGENTS.md').write_text('frozen base')
        self.controller_state=self.root/'agents/controller/agent_state'
        self.controller_state.mkdir(parents=True)
        self.input = self.root / 'input.txt'
        self.input.write_text('Authorized synthetic fact\n')
        self.public_case=self.root/'source/CASE-training/statement/README.md'
        self.public_case.parent.mkdir(parents=True)
        self.public_case.write_text(self.input.read_text())
        self.answer = self.root / 'answer.txt'
        self.answer.write_text('original answer')
        self.candidate = self.root / 'candidates.json'
        self.case = ('CASE-training.with.dots' if self._testMethodName == 'test_case_alias_reaches_capture_and_compile'
                     else 'CASE-training')
        self.task = self.case
        self.runtime = {'provider': 'fixture', 'model_id': 'no-model', 'thinking_level': 'max'}
        self.parent = self.root / 'parent.jsonl'
        self.solver = self.root / 'solver.jsonl'
        self.grader = self.root / 'grader.jsonl'
        self.binding = {'session_id': 'original-solver', 'source': 'subagent',
                        'workspace': str(self.root), 'agent_state': str(self.state),
                        'provider': 'fixture', 'model_id': 'no-model', 'parent_trace': str(self.parent)}
        self.grader_binding = {**self.binding, 'session_id': 'native-evaluator', 'agent_state':str(self.controller_state)}
        contract={'adapter':'native-cases-v1','benchmark':'workspace-train','training_package':{'benchmark_id':'workspace-train'},'capabilities':{'complete_live_rsi':True},
                  'cases':[{'case_id':self.task,'statement':str(self.public_case)}],
                  'test_cases':[{'case_id':'CASE-test'}],'test_package':{'benchmark_id':'heldout'}}
        plan={'schema':'evo-experiment-contract-v2','ready':True,'source_commit':'a'*40,'project':str(self.root),
              'contracts':[contract],'runtime':self.runtime,'budget_scope':'total','budget_allocations':{'workspace-train':7},
              'authorized_total_usd':7,'algorithm':{'limits':{'general':5,'topic':5},'max_bytes':16000,'general_storage':'description-only','test_repeats':1}}
        plan_path=self.root/'initial-plan.json';plan_path.write_text(json.dumps(plan))
        self.profile=self.root/'initial-profile.json'
        with patch.object(benchmarks,'pin',return_value='a'*40):
            workspace.prepare_profile({'plan':str(plan_path),'plan_sha256':benchmarks.sha(plan_path),'contract':'workspace-train',
                                       'repo':str(self.root),'project':str(self.root),'workspace':str(self.root),
                                       'test_agent_id':'solver','output':str(self.profile)})
        prepared=workspace.prepare_solver({'profile':str(self.profile),'profile_sha256':benchmarks.sha(self.profile),
                                           'case_id':self.task,'split':'train','attempt_id':'attempt-1',
                                           'output':str(self.root/'solver-prompt.txt')})
        scope=prepared['scope']
        self.task=scope['task_id']
        self.input=Path(scope['inputs'][0]);self.answer=Path(scope['answer']);self.answer.write_text('original answer')
        self.candidate=Path(scope['candidate'])
        self.initial_prompt = evo.native_prompt(prepared['call'])
        root_binding = {**self.binding, 'source': 'user', 'session_id': 'native-parent', 'agent_state':str(self.controller_state)}
        root_binding.pop('parent_trace')
        parent_rows = [{'type': 'session_meta', 'payload': root_binding}]
        for sid in ('original-solver', 'native-evaluator'):
            parent_rows.append({'type': 'event_msg', 'payload': {'type': 'subagent', 'session_id': sid}})
        parent_rows += self.pair('dispatch', 'run_subagent', prepared['call'],
                                 '[subagent running in background with subagent_id actual-handle; its completion will arrive as a user message]')
        self.write(self.parent, parent_rows)
        self.solver_rows = [{'type': 'session_meta', 'payload': self.binding}, self.text('user', self.initial_prompt, 'parent_agent')]
        self.solver_rows += self.pair('read', 'read_file', {'file_path': str(self.input)}, '     1\tAuthorized synthetic fact')
        self.solver_rows += [self.text('assistant', 'The original answer is ready.')]
        self.write(self.solver, self.solver_rows)
        self.evaluation = {'protocol_version': 1, 'status': 'ok', 'case_id': self.case, 'run': 1,
                           'agent_id': 'solver', 'expected_version': 1, **self.runtime,
                           'score': 50, 'cost': None, 'duration_ms': 1, 'session_id': 'original-solver'}
        self.evaluation_path = self.root / 'evaluation.json'
        self.evaluation_path.write_text(json.dumps(self.evaluation))
        self.write(self.grader, [{'type': 'session_meta', 'payload': self.grader_binding},
                                self.text('assistant', json.dumps(self.evaluation))])
        self.req = {'profile':str(self.profile),'profile_sha256':benchmarks.sha(self.profile),'op': 'prepare-feedback', 'split': 'train', 'task_id': self.task,
                    'case_id': self.case, 'train_ids': [self.task], 'attempt_id': 'attempt-1',
                    'answer': str(self.answer), 'candidate': str(self.candidate),
                    'inputs': [str(self.input)], 'traces': [str(self.solver)], 'binding': self.binding,
                    'evaluation': str(self.evaluation_path), 'evaluator_binding': self.grader_binding,
                    'evaluator_traces': [str(self.grader)], 'subagent_id': 'actual-handle',
                    'output': str(self.root / 'feedback-proof.json')}

    def text(self, role, value, sender=None):
        return {'type': 'model_msg', 'payload': {'type': 'text', 'role': role, 'text': value,
                                               **({'sender': sender} if sender else {})}}

    def pair(self, key, name, arguments, output, status='completed'):
        return [{'type': 'model_msg', 'payload': {'type': 'tool_call', 'tool_call_id': key, 'name': name,
                                                 'arguments': json.dumps(arguments)}},
                {'type': 'model_msg', 'payload': {'type': 'tool_call_output', 'tool_call_id': key,
                                                 'status': status, 'output': output}}]

    def write(self, path, rows):
        path.write_text(''.join(json.dumps(row) + '\n' for row in rows))

    def test_preparation_observation_reflection_capture_compile_and_export(self):
        prepared = workspace.prepare_feedback(self.req)
        proof = evo.read(self.req['output'])
        self.assertEqual(prepared['call']['subagent_id'], 'actual-handle')
        self.candidate.write_text('[]')
        rows = self.solver_rows + [self.text('user', prepared['call']['prompt'], 'parent_agent')]
        rows += self.pair('draft', 'write_file', {'file_path': str(self.candidate), 'content': '[]'}, 'written')
        Path(proof['seal_path']).write_text(json.dumps(proof['seal_request']))
        rows += self.pair('seal-request', 'write_file', {'file_path': proof['seal_path'], 'content': json.dumps(proof['seal_request'])}, 'written')
        rows += self.pair('digest', 'exec_command', {'cmd': proof['seal_command']},
                          json.dumps({'file_path': str(self.candidate), 'sha256': evo.digest(b'[]')}))
        rows += [self.text('assistant', 'Sealed empty candidate set after negative reflection.')]
        self.write(self.solver, rows)
        context = self.root / 'context.json'
        workspace.capture({'feedback_record': self.req['output'], 'traces': [str(self.solver)], 'output': str(context)})
        captured = evo.read(context)
        self.assertEqual(captured['reflection']['session_id'], 'original-solver')
        self.assertTrue(captured['negative'])
        for file in ('library.json', 'decisions.json'):
            (self.root / file).write_text('[]')
        target = self.root / 'compiled.json'
        request = {'train_ids': [self.task], 'contexts': [str(context)], 'candidates': str(self.candidate),
                   'library': str(self.root / 'library.json'), 'decisions': str(self.root / 'decisions.json'),
                   'limits': {'general': 5, 'topic': 5}, 'max_bytes': 16000, 'output': str(target)}
        evo.compile_batch(request)
        self.assertEqual(evo.read(target), [])
        evo.export_skill({'library': str(target), 'limits': request['limits'], 'max_bytes': 16000,
                          'general_storage': 'description-only', 'output': str(self.root / 'skill')})
        self.assertTrue(evo.validate_package(self.root / 'skill')['empty'])
        self.answer.write_text('changed after score')
        with self.assertRaises(ValueError):
            evo.validate_contexts([captured], [self.task])

    def test_wrong_handle_and_failed_public_read_rejected_before_continuation(self):
        with self.assertRaisesRegex(ValueError, 'handle'):
            workspace.prepare_feedback({**self.req, 'subagent_id': 'another-tasks-handle'})
        self.assertFalse(Path(self.req['output']).exists())
        for row in self.solver_rows:
            if row.get('payload', {}).get('type') == 'tool_call_output':
                row['payload']['status'] = 'fatal'
        self.write(self.solver, self.solver_rows)
        with self.assertRaisesRegex(ValueError, 'successful native'):
            workspace.prepare_feedback(self.req)

    def test_case_alias_reaches_capture_and_compile(self):
        self.assertNotEqual(self.case, self.task)
        self.assertEqual(evo.read(self.profile)['members'], [{'case_id': self.case, 'task_id': self.task}])
        self.test_preparation_observation_reflection_capture_compile_and_export()

    def test_frozen_profile_binds_actual_learning_dispatch(self):
        request = {'profile': str(self.profile), 'profile_sha256': benchmarks.sha(self.profile),
                   'case_id': self.task, 'split': 'train', 'attempt_id': 'attempt-1',
                   'output': str(self.root / 'second-prompt.txt')}
        for change in ({'runtime': {**self.runtime, 'thinking_level': 'high'}},
                       {'test_agent_id': 'another-agent'}, {'train_ids': ['CASE-test']},
                       {'case_id': 'CASE-test'}, {'profile_sha256': '0'*64}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                workspace.prepare_solver({**request, **change})
        self.assertFalse(Path(request['output']).exists())
        rows = [json.loads(line) for line in self.parent.read_text().splitlines()]
        call = next(r['payload'] for r in rows if r.get('payload', {}).get('name') == 'run_subagent')
        arguments = json.loads(call['arguments'])
        arguments['thinking_level'] = 'high'
        call['arguments'] = json.dumps(arguments)
        self.write(self.parent, rows)
        with self.assertRaisesRegex(ValueError, 'actual Solver dispatch'):
            workspace.prepare_feedback(self.req)
        self.assertFalse(Path(self.req['output']).exists())

    def test_frozen_state_and_evaluation_version_cannot_drift(self):
        self.evaluation_path.write_text(json.dumps({**self.evaluation, 'expected_version': 2}))
        self.write(self.grader, [{'type': 'session_meta', 'payload': self.grader_binding},
                                self.text('assistant', self.evaluation_path.read_text())])
        with self.assertRaisesRegex(ValueError, 'State/thinking differs'):
            workspace.prepare_feedback(self.req)
        self.evaluation_path.write_text(json.dumps(self.evaluation))
        (self.state / 'AGENTS.md').write_text('changed frozen H0')
        with self.assertRaisesRegex(ValueError, 'State changed'):
            workspace.prepare_feedback(self.req)

    def test_workspace_profile_binds_heldout_budget_and_export_storage(self):
        contract = {'adapter': 'native-cases-v1', 'benchmark': 'workspace-train', 'training_package': {'benchmark_id': 'workspace-train'},
                    'capabilities': {'complete_live_rsi': True},
                    'cases': [{'case_id': self.task, 'statement':str(self.public_case)}], 'test_cases': [{'case_id': 'CASE-test'}],
                    'test_package': {'benchmark_id': 'heldout'}}
        plan = {'schema': 'evo-experiment-contract-v2', 'ready': True, 'source_commit': 'a'*40,
                'project': str(self.root), 'contracts': [contract], 'runtime': self.runtime,
                'budget_scope': 'total', 'budget_allocations': {'workspace-train': 7}, 'authorized_total_usd': 7,
                'algorithm': {'limits': {'general': 5, 'topic': 5}, 'max_bytes': 16000,
                              'general_storage': 'description-only', 'test_repeats': 1}}
        plan_path = self.root / 'plan.json'
        plan_path.write_text(json.dumps(plan))
        profile = self.root / 'profile.json'
        req = {'plan': str(plan_path), 'plan_sha256': benchmarks.sha(plan_path), 'contract': 'workspace-train',
               'repo': str(self.root), 'project': str(self.root), 'workspace':str(self.root),'test_agent_id':'solver','output': str(profile)}
        with patch.object(benchmarks, 'pin', return_value='a'*40):
            workspace.prepare_profile(req)
        value = evo.read(profile)
        self.assertEqual(value['budget_usd'], 7)
        library = Path(value['library'])
        library.parent.mkdir(parents=True)
        library.write_text(json.dumps([{'id': 'general-method', 'level': 'general', 'trigger': 'T', 'scope': 'S',
                                       'description': 'SELF CONTAINED CORE', 'body': 'PRIVATE GENERAL DETAIL'}]))
        export = self.root / 'export.json'
        workspace.prepare_export({'profile': str(profile), 'profile_sha256': benchmarks.sha(profile), 'output': str(export)})
        evo.execute(evo.read(export))
        files = evo.filemap(value['skill_output'])
        texts = ''.join((Path(value['skill_output']) / name).read_text() for name in files)
        self.assertIn('SELF CONTAINED CORE', texts)
        self.assertNotIn('PRIVATE GENERAL DETAIL', texts)


if __name__ == '__main__':
    unittest.main()
