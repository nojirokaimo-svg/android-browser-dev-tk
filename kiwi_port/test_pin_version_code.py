import tempfile
from pathlib import Path
import unittest

import pin_version_code as pin


class VersionCodeTest(unittest.TestCase):
    def test_pin_preserves_other_args_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "args.gn"
            original = 'target_cpu = "arm64"\nis_debug = false\n'
            path.write_text(original)
            self.assertTrue(pin.pin_args(path))
            self.assertEqual(path.read_text(), original + 'android_override_version_code = "807807374"\n')
            stamp = path.stat().st_mtime_ns
            self.assertFalse(pin.pin_args(path))
            self.assertEqual(path.stat().st_mtime_ns, stamp)

    def test_prior_override_is_replaced_without_changing_other_args(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "args.gn"
            path.write_text('target_cpu = "arm64"\nandroid_override_version_code = "123"\nis_debug = false\n')
            self.assertTrue(pin.pin_args(path))
            self.assertEqual(path.read_text(), 'target_cpu = "arm64"\nandroid_override_version_code = "807807374"\nis_debug = false\n')

    def test_multiple_overrides_stop_without_modifying_file(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "args.gn"
            original = 'android_override_version_code = "1"\nandroid_override_version_code = "2"\n'
            path.write_text(original)
            with self.assertRaises(ValueError):
                pin.pin_args(path)
            self.assertEqual(path.read_text(), original)

    def test_published_apk_must_match_package_version_and_version_code(self):
        valid = "package: name='io.github.nojirokaimo.titaniumkiwi' versionCode='807807374' versionName='156.0.8078.79' platformBuildVersionName='17'\n"
        pin.verify_badging(valid, "156.0.8078.79")
        for incorrect in (
            valid.replace("807807374", "807807375"),
            valid.replace("titaniumkiwi", "other"),
            valid.replace("156.0.8078.79", "156.0.8078.47"),
            valid.replace("platformBuildVersionName", "versionCodeMajor='1' platformBuildVersionName"),
            valid + valid,
        ):
            with self.assertRaises(ValueError):
                pin.verify_badging(incorrect, "156.0.8078.79")


if __name__ == "__main__":
    unittest.main()
