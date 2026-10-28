"""Full native package identity; all fixture data is synthetic."""
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/evo-harness-rsi-toolkit/scripts'))
import benchmarks


class PackageIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.project = self.root / 'project'
        self.source = self.root / 'packages/train'
        for name in ('train', 'test'):
            pkg = self.root / 'packages' / name
            pkg.mkdir(parents=True)
            (pkg / 'benchmark_config.toml').write_text(f'id="{name}"\nversion="2026.10.28.1"\nstatus="published"\nruns=1\n')
            for rel, text in {'statement/README.md': 'Public task', 'statement/data/input.csv': 'PUBLIC INPUT',
                              'rubric/README.md': 'Private rubric', 'rubric/attachments/score.json': 'PRIVATE SCORE',
                              'case-config.json': 'CASE CONFIG'}.items():
                path = pkg / 'CASE-local' / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text)
            shutil.copytree(pkg, self.project / 'benchmarks' / name)
        self.source_contract = benchmarks.package(self.root, 'packages/train')
        self.target = self.project / 'benchmarks/train'

    def check(self):
        return benchmarks.project_package(self.project, self.source_contract)

    def test_attachment_config_extra_and_missing_changes_are_detected(self):
        self.assertTrue(self.check()['ready'])
        for rel in ('CASE-local/statement/data/input.csv', 'CASE-local/rubric/attachments/score.json',
                    'CASE-local/case-config.json'):
            path = self.target / rel
            original = path.read_bytes()
            path.write_text('CHANGED')
            with self.subTest(rel=rel):
                result = self.check()
                self.assertFalse(result['ready'])
                self.assertEqual(result['files']['changed'], [rel])
            path.unlink()
            self.assertEqual(self.check()['files']['missing'], [rel])
            path.write_bytes(original)
        extra = self.target / 'CASE-local/statement/new.csv'
        extra.write_text('new')
        self.assertFalse(self.check()['ready'])
        self.assertEqual(self.check()['files']['extra'], ['CASE-local/statement/new.csv'])

    def test_manifest_settings_checked_but_import_metadata_and_toml_format_allowed(self):
        manifest = self.target / 'benchmark_config.toml'
        initial = manifest.read_text()
        manifest.write_text(initial + '\n[origin]\nkind="git"\nref="' + 'a'*40 + '"\n')
        self.assertTrue(self.check()['ready'])
        manifest.write_text(initial.replace('runs=1', 'runs = 1 # rewritten by importer'))
        self.assertTrue(self.check()['ready'])
        for text in (initial.replace('runs=1', 'runs=2'), initial + 'title="different"\n', initial + '[new_config]\nvalue=3\n'):
            manifest.write_text(text)
            self.assertFalse(self.check()['ready'])
            self.assertFalse(self.check()['configuration_matches'])

    def test_native_import_normalizes_legacy_manifest_defaults(self):
        manifest = self.source / 'benchmark_config.toml'
        initial = manifest.read_text()
        for extra in ('title=""', 'title=7', 'description=2', 'description_zh=""'):
            with self.subTest(extra=extra):
                manifest.write_text(initial.replace('id="train"\n', '').replace('status="published"', 'status="legacy-published"').replace('runs=1', 'runs=0') + extra + '\n')
                self.source_contract = benchmarks.package(self.root, 'packages/train')
                self.assertTrue(self.check()['ready'])

    def test_native_integral_float_runs_keep_the_same_run_count(self):
        manifest = self.source / 'benchmark_config.toml'
        manifest.write_text(manifest.read_text().replace('runs=1', 'runs=2.0'))
        self.source_contract = benchmarks.package(self.root, 'packages/train')
        self.assertFalse(self.check()['ready'])  # Project still has runs=1.
        actual = self.target / 'benchmark_config.toml'
        actual.write_text(actual.read_text().replace('runs=1', 'runs=2'))
        self.assertTrue(self.check()['ready'])

    def test_runtime_state_does_not_change_package_identity(self):
        for rel in ('scoreboard.yaml', '.jobs/trial/result.json', 'CASE-local/.cache/temporary'):
            path = self.target / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('runtime state')
        self.assertTrue(self.check()['ready'])

    def test_invalid_case_or_symlink_cannot_be_matching(self):
        attachment = self.target / 'CASE-local/statement/data/input.csv'
        attachment.unlink()
        attachment.symlink_to(self.source / 'CASE-local/statement/data/input.csv')
        self.assertFalse(self.check()['ready'])
        attachment.unlink()
        attachment.write_text('PUBLIC INPUT')
        (self.target / 'CASE-local/statement/README.md').unlink()
        self.assertFalse(self.check()['ready'])

    def test_private_attachment_bytes_never_enter_contract(self):
        text = json.dumps(self.source_contract)
        self.assertNotIn('PRIVATE SCORE', text)
        self.assertNotIn('Private rubric', text)
        self.assertEqual(len(self.source_contract['content_files']), 5)

    def test_bootstrap_and_frozen_consumption_recheck_actual_project(self):
        request = {'repo': str(self.root), 'project': str(self.project), 'benchmark': 'train',
                   'test_benchmark': 'test', 'runtime': {'provider':'fixture','model_id':'no-model','thinking_level':'max'},
                   'budget_usd': 1, 'paid_authorized': True}
        with patch.object(benchmarks, 'pin', return_value='a'*40):
            plan = benchmarks.bootstrap(request)
            self.assertTrue(plan['ready'])
            path = self.root / 'plan.json'; path.write_text(json.dumps(plan))
            consume = {**request, 'plan':str(path), 'plan_sha256':benchmarks.sha(path), 'contract':'train'}
            benchmarks.frozen_plan(consume)
            (self.target / 'CASE-local/statement/data/input.csv').write_text('changed')
            self.assertFalse(benchmarks.bootstrap(request)['ready'])
            with self.assertRaisesRegex(ValueError, 'Project package changed'):
                benchmarks.frozen_plan(consume)

    @unittest.skipUnless(os.environ.get("EVO_BENCHMARK"), "set EVO_BENCHMARK for actual-source checks")
    def test_postexit_harbor_is_a_capability_blocker_before_any_dispatch(self):
        repo = Path(os.environ['EVO_BENCHMARK'])
        with patch.object(benchmarks, 'pin', return_value='a'*40), patch.object(benchmarks, 'project_package', return_value={'ready':True}):
            result = benchmarks.bootstrap({'repo':str(repo),'project':str(self.project),
                'benchmark':'penguinharness-benchmark-sec-d','test_benchmark':'penguinharness-benchmark-sec-a',
                'runtime':{'provider':'fixture','model_id':'no-model','thinking_level':'max'},'budget_usd':1,'paid_authorized':True})
        self.assertFalse(result['ready'])
        self.assertIn('original-Solver', result['capability_blockers'][0]['reason'])
        self.assertEqual(result['dispatches'], 0)


if __name__ == '__main__':
    unittest.main()
