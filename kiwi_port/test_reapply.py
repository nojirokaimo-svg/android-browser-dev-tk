"""Exercise conflict handling on disposable git trees, never build outputs."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent


class ReapplyTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.src = self.root / 'src'
        self.src.mkdir()
        self.port = self.root / 'port'
        (self.port / 'patches').mkdir(parents=True)
        shutil.copy2(HERE / 'apply.py', self.port / 'apply.py')
        self.git('init', '-q')
        self.git('config', 'user.name', 'Test')
        self.git('config', 'user.email', 'test@example.invalid')
        for name in ('a.txt', 'b.txt'):
            (self.src / name).write_text('before\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'baseline')
        manifest = {'files': {}}
        features = []
        for index, name in enumerate(('a.txt', 'b.txt')):
            (self.src / name).write_text('after\n')
            patch = self.git('diff', '--', name).stdout
            patch_name = f'{index}.patch'
            (self.port / 'patches' / patch_name).write_text(patch)
            features.append(dict(id=f'feature-{index}', name=f'Feature {index}',
                                 patch=patch_name, files=[name],
                                 sha256=hashlib.sha256(patch.encode()).hexdigest()))
            manifest['files'][name] = dict(
                before_sha256=hashlib.sha256(b'before\n').hexdigest(),
                after_sha256=hashlib.sha256(b'after\n').hexdigest())
            (self.src / name).write_text('before\n')
        (self.port / 'manifest.json').write_text(json.dumps(manifest))
        (self.port / 'patches/series.json').write_text(json.dumps({'features': features}))

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.src), *args],
                              check=True, capture_output=True, text=True)

    def apply(self, *args):
        import sys
        return subprocess.run([sys.executable, str(self.port / 'apply.py'),
                               str(self.src), *args], capture_output=True, text=True)

    def repair(self, feature_id, files):
        spec = importlib.util.spec_from_file_location('reapply_under_test', self.port / 'apply.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.repair_known_context_drift(self.src, feature_id, files)

    def test_omnibox_repair_never_overwrites_changed_upstream_method(self):
        relative = 'chrome/android/java/src/org/chromium/chrome/browser/ntp/NewTabPage.java'
        target = self.src / relative
        target.parent.mkdir(parents=True)
        original = (
            '        public boolean isLocationBarShownInNtp() {\n'
            '            if (mIsDestroyed) return false;\n'
            '            return upstreamNewRule();\n'
            '        }\n\n'
            '        @Override\n'
        )
        target.write_text(original)
        reject = Path(str(target) + '.rej')
        reject.write_text('unresolved')
        self.assertEqual(self.repair('kiwi-omnibox-history', [relative]), [relative])
        self.assertEqual(target.read_text(), original)
        self.assertTrue(reject.is_file())

    def test_multi_anchor_repair_is_atomic_on_unknown_upstream(self):
        relative = 'chrome/android/chrome_java_resources.gni'
        target = self.src / relative
        target.parent.mkdir(parents=True)
        original = '  "java/res/layout/radio_button_group_homepage_preference.xml",\n'
        target.write_text(original)
        reject = Path(str(target) + '.rej')
        reject.write_text('unresolved')
        self.assertEqual(self.repair('kiwi-tab-switcher', [relative]), [relative])
        self.assertEqual(target.read_text(), original)
        self.assertTrue(reject.is_file())

    def test_known_omnibox_context_drift_is_still_repaired(self):
        relative = 'chrome/android/java/src/org/chromium/chrome/browser/ntp/NewTabPage.java'
        target = self.src / relative
        target.parent.mkdir(parents=True)
        target.write_text(
            '        public boolean isLocationBarShownInNtp() {\n'
            '            if (mIsDestroyed) return false;\n'
            '            return isInSingleUrlBarMode() && !mNewTabPageCoordinator.urlFocusAnimationsDisabled();\n'
            '        }\n\n'
            '        @Override\n'
        )
        reject = Path(str(target) + '.rej')
        reject.write_text('context drift')
        self.assertEqual(self.repair('kiwi-omnibox-history', [relative]), [])
        self.assertIn('return false;\n        }', target.read_text())
        self.assertFalse(reject.exists())

    def test_known_two_anchor_context_drift_is_still_repaired(self):
        relative = 'chrome/android/chrome_java_resources.gni'
        target = self.src / relative
        target.parent.mkdir(parents=True)
        target.write_text(
            '  "java/res/layout/radio_button_group_homepage_preference.xml",\n'
            '  "java/res/xml/main_preferences.xml",\n'
        )
        reject = Path(str(target) + '.rej')
        reject.write_text('context drift')
        self.assertEqual(self.repair('kiwi-tab-switcher', [relative]), [])
        self.assertIn('radio_button_group_tabswitcher_preference.xml', target.read_text())
        self.assertIn('tabswitcher_preferences.xml', target.read_text())
        self.assertFalse(reject.exists())

    def test_apply_and_idempotence(self):
        self.assertEqual(self.apply().returncode, 0)
        before = self.git('diff').stdout
        self.assertEqual(self.apply().returncode, 0)
        self.assertEqual(self.git('diff').stdout, before)

    def test_strict_conflict_is_atomic(self):
        (self.src / 'a.txt').write_text('upstream change\n')
        before = self.git('diff').stdout
        result = self.apply()
        self.assertEqual(result.returncode, 1)
        self.assertIn('feature-0', result.stderr)
        self.assertIn('a.txt', result.stderr)
        self.assertEqual(self.git('diff').stdout, before)

    def test_strict_preflight_applies_dependent_features_in_order(self):
        (self.src / 'a.txt').write_text('after\n')
        self.git('add', 'a.txt')
        self.git('commit', '-qm', 'first feature baseline')
        (self.src / 'a.txt').write_text('final\n')
        second = self.git('diff', '--', 'a.txt').stdout
        (self.port / 'patches/2.patch').write_text(second)
        self.git('reset', '--hard', 'HEAD~1')
        series_path = self.port / 'patches/series.json'
        series = json.loads(series_path.read_text())
        series['features'].append(dict(id='feature-2', name='Dependent feature',
                                       patch='2.patch', files=['a.txt'],
                                       sha256=hashlib.sha256(second.encode()).hexdigest()))
        series_path.write_text(json.dumps(series))
        manifest_path = self.port / 'manifest.json'
        manifest = json.loads(manifest_path.read_text())
        manifest['files']['a.txt']['after_sha256'] = hashlib.sha256(b'final\n').hexdigest()
        manifest_path.write_text(json.dumps(manifest))

        result = self.apply()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.src / 'a.txt').read_text(), 'final\n')

    def test_audit_only_tolerates_only_omitted_post_hashes(self):
        manifest_path = self.port / 'manifest.json'
        manifest = json.loads(manifest_path.read_text())
        manifest['files']['a.txt']['after_sha256'] = None
        manifest_path.write_text(json.dumps(manifest))
        self.assertEqual(self.apply().returncode, 1)
        # Create a fresh test tree so the first failing call cannot influence the audit run.
        for name in ('a.txt', 'b.txt'):
            (self.src / name).write_text('before\n')
        result = subprocess.run(
            [sys.executable, str(self.port / 'apply.py'), str(self.src)],
            capture_output=True, text=True,
            env={**os.environ, 'KIWI_MANIFEST_AUDIT_ONLY': 'true'})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.src / 'a.txt').read_text(), 'after\n')

    def test_conflict_keeps_independent_feature(self):
        (self.src / 'a.txt').write_text('upstream change\n')
        report = self.root / 'report.md'
        result = self.apply('--best-effort', '--report', str(report))
        self.assertEqual(result.returncode, 2)
        self.assertEqual((self.src / 'a.txt').read_text(), 'upstream change\n')
        self.assertEqual((self.src / 'b.txt').read_text(), 'after\n')
        self.assertTrue((self.src / 'a.txt.rej').exists())
        self.assertIn('feature-0', report.read_text())
        self.assertIn('a.txt', report.read_text())


if __name__ == '__main__':
    unittest.main()
