import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest


class ExactCheckpointRestoreTests(unittest.TestCase):
    def run_restore_check(self, hit, matched, expected='completed-174'):
        action = (Path(__file__).parents[1] / '.github/actions/kiwi-build-stage/action.yml').read_text()
        step = action.split('    - name: Verify restored checkpoint before preparation\n', 1)[1].split('\n    - name:', 1)[0]
        script = textwrap.dedent(step.split('      run: |\n', 1)[1])
        script = script.replace('${{ inputs.restore-key }}', '${KIWI_EXPECTED_CACHE_KEY}')
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'work/titanium/chromium/src/out/Default'
            output.mkdir(parents=True)
            for name in ('.ninja_log', '.ninja_deps', 'build.ninja', 'args.gn'):
                (output / name).write_bytes(b'preserved checkpoint bytes')
            result = subprocess.run(['bash', '-e', '-c', script], cwd=tmp, capture_output=True, text=True,
                                    env={**os.environ, 'KIWI_CACHE_HIT': hit,
                                         'KIWI_MATCHED_CACHE_KEY': matched,
                                         'KIWI_EXPECTED_CACHE_KEY': expected})
            self.assertTrue(all(p.read_bytes() == b'preserved checkpoint bytes' for p in output.iterdir()))
            return result

    def test_exact_hit_preserves_checkpoint_and_succeeds(self):
        self.assertEqual(self.run_restore_check('true', 'completed-174').returncode, 0)

    def test_prefix_match_is_rejected_before_preparation(self):
        result = self.run_restore_check('false', 'completed-174-unrelated')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('exact', result.stderr.lower())

    def test_missing_hit_is_rejected_even_if_files_exist(self):
        self.assertNotEqual(self.run_restore_check('', '').returncode, 0)

    def test_inconsistent_matched_key_is_rejected(self):
        self.assertNotEqual(self.run_restore_check('true', 'wrong-key').returncode, 0)
