import os
import sys
from pathlib import Path
RUNTIME = Path(__file__).resolve().parents[2] / "skills/evo-harness-rsi-toolkit/scripts/runtime"
sys.path.insert(0, str(RUNTIME))
"""Real current manifests + synthetic deployment records; no Docker/model score."""
import copy
import json
import os
from pathlib import Path
import shutil
import sys
import tarfile
import unittest

import protocol
import registration
import test_registration

SCRIPT = Path(os.environ['EVO_TOOL'])
sys.path.insert(0, str(SCRIPT.parent))
import benchmarks


class ManifestPipeline(unittest.TestCase):
    def setUp(self):
        self.f = test_registration.RegistrationTests('runTest')
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.contract = benchmarks.discover(self.f.repo, os.environ.get('EVO_TEST_DOMAIN', 'gdpevo-crm'))[0]
        for package in (self.contract['training_package'], self.contract['test_package']):
            shutil.copytree(package['package_path'], self.f.output / package['benchmark_id'])
        runtime = {**self.f.config['runtime'], 'thinking_level': 'max', 'effective_reasoning_effort': 'max'}
        self.plan = benchmarks.bootstrap({'repo': str(self.f.repo), 'project': str(self.f.project),
                                         'benchmark': os.environ.get('EVO_TEST_DOMAIN', 'gdpevo-crm'), 'runtime': runtime,
                                         'budget_usd': 10, 'paid_authorized': True})
        self.assertTrue(self.plan['ready'])
        self.plan_path = self.f.root / 'plan.json'
        self.plan_path.write_text(json.dumps(self.plan))
        self.f.config['deployment']['controller_id'] = 'controller'
        self.f.config['adapter']['penguin_version'] = '0.2.18'
        self.f.config['penguin_version'] = '0.2.18'
        self.f.bundle_meta['penguin_version'] = '0.2.18'
        self.f.config['versions']['benchmark_commit'] = self.plan['source_commit']
        self.f.preflight['pins']['benchmark_commit'] = self.plan['source_commit']
        self.f.preflight['task_ids'] = [self.contract['training_case']['task_name'],
                                         *[t['task_name'] for t in self.contract['test_cases']]]
        self.f.replace_bundle(json.dumps(self.f.bundle_meta).encode())
        self.req = {'op': 'prepare-config', 'repo': str(self.f.repo), 'project': str(self.f.project),
                    'plan': str(self.plan_path), 'plan_sha256': benchmarks.sha(self.plan_path),
                    'contract': self.contract['benchmark'], 'evo_tool': str(SCRIPT),
                    'settings': self.f.config, 'output': str(self.f.root / 'new-profile.json')}

    def prepare(self):
        result = protocol.execute(self.req)
        self.assertTrue(result['ready'])
        return result, protocol.read(self.req['output'])

    def test_v2_native_trial_receipt_reaches_loading_audit(self):
        import acceptance
        import injection
        import test_injection
        import test_protocol
        result, cfg = self.prepare()
        registered = protocol.execute({'op': 'prepare-benchmarks', 'repo': str(self.f.repo),
            'config': self.req['output'], 'config_sha256': result['sha256'], 'output': str(self.f.output)})
        self.assertEqual(cfg['protocol'], 'evo-harness-v2')
        self.assertEqual(cfg['versions']['skill'], '2026.10.28.6')
        evo = protocol.helper(str(SCRIPT))
        state = self.f.root / 'native-state'
        library = self.f.root / 'empty-library.json'; library.write_text('[]')
        evo.export_skill({'library': str(library), 'output': str(state / acceptance.SLOT),
                         'limits': cfg['limits'], 'max_bytes': 16000, 'general_storage': 'description-only'})
        test_protocol.install_package(evo, state / acceptance.SLOT, state)
        (state / 'system_config.yaml').write_text('version: 1\n' + test_protocol.SYNTHETIC_OUTPUT_TOOLS)
        (state / 'AGENTS.md').write_text('Synthetic base\n')
        evo.install_context({'state': str(state)})
        snapshot = self.f.root / 'native-state.tar.gz'
        with tarfile.open(snapshot, 'w:gz') as archive:
            archive.add(state, arcname='agent_state')
        frozen = acceptance.snapshot(snapshot)['files']
        benchmark = self.f.output / cfg['test_benchmark_id']
        cell = {'protocol_version':1, 'status':'ok', 'agent_id':cfg['test_agent_id'],
                'expected_version':1, **cfg['runtime'], 'case_id':registered['test']['case_ids'][0],
                'run':1, 'score':50, 'cost':None, 'duration_ms':1, 'session_id':'harbor:synthetic-v2'}
        trial, trace = test_injection.write_trial(benchmark, cell, frozen, cfg['runtime'])
        raw = protocol.read(trial / 'result.json')
        raw['agent_result']['cost_usd'] = None
        test_injection.save(trial / 'result.json', raw)
        test_injection.save(trial.parent / 'result.json', {'finished_at':raw['finished_at'], 'stats':{'n_running_trials':0}})
        rows = [json.loads(line) for line in trace.read_text().splitlines()]
        rows[0]['payload']['system_prompt'] = (state / 'AGENTS.md').read_text()
        trace.write_text(''.join(json.dumps(row)+'\n' for row in rows))
        request = {'identity':{k:cell[k] for k in ('agent_id','expected_version','provider','model_id','thinking_level','case_id','run')},
                   'session_id':cell['session_id'], 'benchmark':str(benchmark), 'snapshot':str(snapshot),
                   'runtime':cfg['runtime'], 'config_value':cfg,
                   'launch':protocol.read(benchmark/cell['case_id']/'statement/harbor-launch.json')}
        measured = injection.canonical_worker_cell(request, evo, acceptance)
        self.assertFalse(measured['pending'])
        self.assertEqual(measured['cell']['score'], 50)
        self.assertIsNone(measured['cell']['cost'])
        self.assertTrue(measured['audit']['audit_passed'])
        # Supporting v2 cannot waive State integrity or hide an unfinished job.
        test_injection.save(trial.parent / 'result.json', {'finished_at':None, 'stats':{'n_running_trials':1}})
        self.assertTrue(injection.canonical_worker_cell(request, evo, acceptance)['pending'])
        test_injection.save(trial.parent / 'result.json', {'finished_at':raw['finished_at'], 'stats':{'n_running_trials':0}})
        receipt = trial/'agent/penguin-agent-state-before.json'
        changed = protocol.read(receipt); changed['files']['AGENTS.md'] = '0'*64
        test_injection.save(receipt, changed)
        with self.assertRaisesRegex(ValueError, 'fingerprint differs'):
            injection.canonical_worker_cell(request, evo, acceptance)

    def test_config_register_verify_and_state_transport(self):
        result, cfg = self.prepare()
        request = {'op': 'prepare-benchmarks', 'repo': str(self.f.repo), 'config': self.req['output'],
                   'config_sha256': result['sha256'], 'output': str(self.f.output)}
        registered = protocol.execute(request)
        self.assertEqual(registered['training']['case_to_task'], {'CASE-001-train_tasks': 'train_tasks'})
        self.assertEqual(len(registered['test']['case_to_task']), 5)
        self.assertNotEqual(cfg['benchmark_id'], cfg['source_benchmark_ids']['training'])
        self.assertTrue(protocol.execute({**request, 'op': 'verify-benchmarks'}))
        case = next(iter(registered['test']['case_to_task']))
        launch = protocol.read(self.f.output / cfg['test_benchmark_id'] / case / 'statement/harbor-launch.json')
        self.assertEqual(launch['source_package']['id'], cfg['source_benchmark_ids']['test'])
        self.assertIn('scripts/runtime/worker_job.py', launch['wait_command'][2])
        state = self.f.root / 'state'
        state.mkdir()
        for name in ('AGENTS.md', 'system_config.yaml'):
            (state / name).write_text('synthetic State')
        for folder in ('memory', 'schedule'):
            (state / folder).mkdir()
            (state / folder / 'private').write_text('not transported')
        (state / '.vault.toml').write_text('synthetic excluded')
        archive = self.f.root / 'transport.tar.gz'
        protocol.pack_state({'state': str(state), 'evo_tool': str(SCRIPT), 'output': str(archive)})
        with tarfile.open(archive) as packed:
            self.assertEqual(set(packed.getnames()), {'AGENTS.md', 'system_config.yaml'})
        # Source Project imports and their empty scoreboards are not overwritten.
        original = self.f.output / self.contract['training_package']['benchmark_id']
        self.assertTrue(benchmarks.project_package(self.f.project, self.contract['training_package'])['ready'])

    def test_missing_nested_pins_and_cli_version_are_collected_before_write(self):
        broken = copy.deepcopy(self.req)
        broken['settings']['versions'].pop('penguin_commit')
        broken['settings']['adapter'].pop('penguin_version')
        broken['settings'].pop('penguin_version')
        result = protocol.prepare_config(broken)
        self.assertFalse(result['ready'])
        self.assertIn('versions.penguin_commit', result['missing_configuration'])
        self.assertIn('adapter.penguin_version', result['missing_configuration'])
        self.assertIn('penguin_version', result['missing_configuration'])
        self.assertFalse(Path(broken['output']).exists())

    def test_project_mismatch_and_plan_tampering_do_not_freeze(self):
        wrong = copy.deepcopy(self.req)
        wrong['settings']['deployment']['project_id'] = 'wrong'
        with self.assertRaisesRegex(ValueError, 'Project'):
            protocol.prepare_config(wrong)
        self.plan_path.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'plan changed'):
            protocol.prepare_config(self.req)


if __name__ == '__main__':
    unittest.main()
