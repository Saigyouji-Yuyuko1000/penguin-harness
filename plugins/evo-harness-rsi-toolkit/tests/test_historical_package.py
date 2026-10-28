"""Exact .6-rendered synthetic fixtures; no experimental scores or answers."""
import base64
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/evo-harness-rsi-toolkit/scripts'))
import evo
import test_evo

FIXTURE=Path(__file__).parent/'fixtures/v6-package-compatibility.json'


class HistoricalPackageTests(unittest.TestCase):
    def setUp(self):
        self.samples=json.loads(FIXTURE.read_text())['samples']

    def files(self, sample):
        return {k:base64.b64decode(v) for k,v in sample['files'].items()}

    def test_original_bytes_hashes_loading_and_budget_preserved(self):
        for sample in self.samples:
            with self.subTest(name=sample['name']):
                files=self.files(sample); before=copy.deepcopy(files)
                evo.validate_package_files(files)
                self.assertEqual({k:evo.digest(v)for k,v in files.items()},sample['hashes'])
                context=evo.model_context(files)
                self.assertEqual({k:v for k,v in context.items()if k not in ('text','block')},sample['context'])
                self.assertNotIn('PRIVATE GENERAL SYNTHETIC BODY',context['text'])
                self.assertEqual(evo.render_reference_package(sample['library'],16000,files),files)
                self.assertEqual(files,before)

    def test_historical_exact_budget_is_not_checked_against_new_reader(self):
        sample=next(s for s in self.samples if s['name']=='general-stored-16000')
        files=self.files(sample)
        self.assertEqual(sum(map(len,files.values())),16000)
        with self.assertRaises(ValueError):evo.render_package(sample['library'],16000)
        self.assertEqual(evo.render_reference_package(sample['library'],16000,files),files)
        grown=copy.deepcopy(sample['library']);grown[-1]['body']+='x'
        with self.assertRaises(ValueError):evo.render_reference_package(grown,16000,files)

    def test_known_absolute_plan_relocates_without_rewriting_files(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'relocated-state'
            sample=self.samples[1];files=self.files(sample)
            for rel,raw in evo.package_state_files(files).items():
                path=root/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
            before=evo.filemap(root)
            plan=evo.native_read_plan({'state':str(root)})
            self.assertTrue(plan['calls'])
            for call in plan['calls']:
                self.assertTrue(Path(call['file_path']).is_relative_to(root))
                self.assertNotIn(evo.GDPEVO_STATE,call['file_path'])
            self.assertEqual(before,evo.filemap(root))
            method=Path(plan['calls'][0]['file_path']);method.unlink();method.symlink_to('/etc/passwd')
            with self.assertRaises(ValueError):evo.native_read_plan({'state':str(root)})

    def test_tampering_traversal_and_unknown_reader_are_rejected(self):
        original=self.files(self.samples[1])
        for mutation in ('body','unknown_reader','foreign_root','traversal','omit_page','relative_in_old_format','extra_file'):
            files=copy.deepcopy(original)
            manifest=evo.parse_reader(files['SKILL.md'])
            prefix=evo.reader_variant(files['SKILL.md'])[2]
            if mutation=='body':files[manifest['entries'][0]['path']]+=b'tampered'
            elif mutation=='unknown_reader':files['SKILL.md']=files['SKILL.md'].replace(b'No selector',b'Use a selector',1)
            elif mutation=='extra_file':files['extra']=b'unknown'
            else:
                call=manifest['read_calls'][0]
                if mutation=='foreign_root':call['file_path']='/another-agent/'+manifest['entries'][0]['state_path']
                if mutation=='traversal':call['file_path']=evo.GDPEVO_STATE+'/../other/SKILL.md'
                if mutation=='omit_page':manifest['read_calls']=[]
                if mutation=='relative_in_old_format':call['file_path']=manifest['entries'][0]['state_path']
                files['SKILL.md']=prefix+evo.encoded(manifest)+evo.FULL_SKILL_CLOSE.encode()
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):evo.validate_package_files(files)

    def test_old_h0_actual_initial_context_is_recognized(self):
        files=self.files(self.samples[0])
        context=evo.model_context(files)
        view={'binding':{'agent_state':'/original/state'},'metas':[{'system_prompt':context['block']}]}
        result=evo.solver_skill_observation(view,{'max_bytes':16000,'context_transport':evo.CONTEXT_TRANSPORT},'train_001','attempt-1')
        self.assertEqual(result['sha256'],evo.digest(files['SKILL.md']))
        view['metas'][0]['system_prompt']=context['block'].replace('normal H0','altered H0')
        with self.assertRaises(ValueError):evo.solver_skill_observation(view,{'max_bytes':16000,'context_transport':evo.CONTEXT_TRANSPORT},'train_001','attempt-1')

    def test_audited_compilation_matches_old_package_without_reexport(self):
        f=test_evo.BatchTests('runTest');f.setUp();self.addCleanup(f.doCleanups)
        files=self.files(self.samples[1]);dest=f.root/'old-package'
        for name,raw in files.items():
            p=dest/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
        before=evo.filemap(dest)
        verified=test_evo.evo.verify_compilation({**f.req,'max_bytes':16000,'skill':str(dest)})
        self.assertEqual(verified['files'],before)
        self.assertEqual(evo.filemap(dest),before)
        self.assertFalse((dest/'publication.json').exists())


if __name__=='__main__':unittest.main()
