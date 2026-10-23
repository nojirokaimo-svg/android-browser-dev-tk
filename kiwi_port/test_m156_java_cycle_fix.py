import pathlib
import tempfile
import unittest
from kiwi_port.m156_java_cycle_fix import repair

def wrap(block):
    return 'if (is_android) {\n  '+block+'\n  }\n'

class M156JavaCycleFixTest(unittest.TestCase):
    def _setup(self, good=False):
        tmp=tempfile.TemporaryDirectory()
        root=pathlib.Path(tmp.name)
        (root/'base/version_info/android').mkdir(parents=True)
        (root/'base/BUILD.gn').write_text(
            'if (is_android) {\n'
            '  android_library("base_java") {\n'
            '    public_deps = [ ":build_info_java" ]\n'
            '  }\n'
            '  android_library("build_info_java") {\n'
            '    deps = [\n      '+
            ('"//base/version_info/android:channel_enum_java"' if good
             else '"//base/version_info/android:version_constants_java"')+
            ',\n    ]\n'
            '  }\n}\n')
        (root/'base/version_info/android/BUILD.gn').write_text(
            'if (is_android) {\n'
            '  android_library("version_constants_java") {\n'
            '    deps = [ "//base:base_java" ]\n'
            '  }\n}\n')
        return tmp,root
    def test_exact_single_dep_rewrite(self):
        tmp,root=self._setup()
        with tmp:
            orig=(root/'base/BUILD.gn').read_text()
            out=repair(root)
            new=(root/'base/BUILD.gn').read_text()
            self.assertEqual("fixed",out["status"])
            self.assertEqual(orig.replace(
                '"//base/version_info/android:version_constants_java"',
                '"//base/version_info/android:channel_enum_java"'),new)
    def test_preserve_already_correct_source(self):
        tmp,root=self._setup(good=True)
        with tmp:
            before=(root/'base/BUILD.gn').read_bytes()
            result=repair(root)
            self.assertEqual("already-correct",result["status"])
            self.assertEqual(result["before_sha256"],result["after_sha256"])
            self.assertEqual(before,(root/'base/BUILD.gn').read_bytes())
    def test_no_mutation_on_missing_base_public_dep(self):
        tmp,root=self._setup()
        with tmp:
            file=root/'base/BUILD.gn'
            txt=file.read_text().replace('":build_info_java"','":log_java"')
            file.write_text(txt)
            with self.assertRaisesRegex(RuntimeError,"public-depends"):
                repair(root)
            self.assertEqual(txt,file.read_text())
