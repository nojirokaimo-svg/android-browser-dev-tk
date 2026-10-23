import json
import tempfile
import unittest
from pathlib import Path
from checkpoint_compat import invalidate_m156_build_info_cycle

class M156CheckpointTest(unittest.TestCase):
    def fixture(self, invalid=False):
        temp = tempfile.TemporaryDirectory()
        out = Path(temp.name)
        for name in (".ninja_log", ".ninja_deps", "build.ninja", "args.gn"):
            (out / name).write_bytes(b"preserved")
        edges = [
            "build phony/base/build_info_java__header.harddeps: phony phony/base/version_info/android/channel_enum_java__header",
            "build phony/base/version_info/android/version_constants_java__header.harddeps: phony phony/base/base_java__header",
            "build phony/base/base_java__header.harddeps: phony phony/base/build_info_java__header",
        ]
        if invalid:
            edges[0] = edges[0].replace("channel_enum_java", "version_constants_java")
        (out / "toolchain.ninja").write_text("\n".join(edges) + "\n")
        old = "obj/base/version_info/android/version_constants_java"
        new = "obj/base/version_info/android/channel_enum_java"
        for name, key, ext in (
            ("build_info_java.turbine", "interface_classpath", "turbine"),
            ("build_info_java.javac", "javac_full_interface_classpath", "turbine"),
            ("build_info_java", "javac_full_classpath", "javac"),
        ):
            path = out / ("gen/base/" + name + ".build_config.json")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({key: [old + "." + ext + ".jar", new + "." + ext + ".jar"]}))
        for name, output in (("header", "turbine"), ("compile_java", "javac")):
            path = out / ("gen/base/build_info_java__" + name + ".d")
            path.write_text("obj/base/build_info_java." + output + ".jar: " +
                            old + ".turbine.jar " + new + ".turbine.jar\n")
        return temp, out

    def test_exact_repair_and_idempotence(self):
        temp, out = self.fixture()
        with temp:
            original = (out / "gen/base/build_info_java__header.d").read_bytes()
            self.assertTrue(invalidate_m156_build_info_cycle(out))
            self.assertFalse(invalidate_m156_build_info_cycle(out))
            self.assertEqual(original, (out / "gen/base/build_info_java__header.d.kiwi-m156-backup").read_bytes())
            self.assertNotIn(b"version_constants_java", (out / "gen/base/build_info_java__header.d").read_bytes())
            self.assertEqual(b"preserved", (out / ".ninja_log").read_bytes())
            self.assertEqual(b"preserved", (out / ".ninja_deps").read_bytes())

    def test_unknown_gn_edge_fails_without_changes(self):
        temp, out = self.fixture(invalid=True)
        with temp:
            before = (out / "gen/base/build_info_java__header.d").read_bytes()
            with self.assertRaisesRegex(ValueError, "Unverified M156 GN edge"):
                invalidate_m156_build_info_cycle(out)
            self.assertEqual(before, (out / "gen/base/build_info_java__header.d").read_bytes())
            self.assertFalse((out / ".kiwi-m156-build-info-generated-deps-fixed-v1").exists())

if __name__ == "__main__":
    unittest.main()
