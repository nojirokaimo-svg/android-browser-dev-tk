import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest

from checkpoint_compat import (
    AGE_NS,
    M154_AUXILIARY_SEARCH_MARKER,
    M154_AUXILIARY_SEARCH_TURBINE,
    invalidate_m154_auxiliary_search_cycle,
)


def path_record(path: str, node_id: int) -> bytes:
    encoded = path.encode()
    padding = b"\0" * ((4 - len(encoded) % 4) % 4)
    payload = encoded + padding + struct.pack("<I", (~node_id) & 0xFFFFFFFF)
    return struct.pack("<I", len(payload)) + payload


def deps_record(output_id: int, dependency_ids: list[int], mtime: int = 123) -> bytes:
    payload = struct.pack(
        "<" + "I" * (3 + len(dependency_ids)),
        output_id,
        mtime & 0xFFFFFFFF,
        mtime >> 32,
        *dependency_ids,
    )
    return struct.pack("<I", len(payload) | 0x80000000) + payload


def ninja_deps(records: list[bytes]) -> bytes:
    return b"# ninjadeps\n" + struct.pack("<I", 4) + b"".join(records)


class CheckpointCompatibilityTest(unittest.TestCase):
    def test_rejects_wrong_depfile_output_without_touching_checkpoint(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            target = out / M154_AUXILIARY_SEARCH_TURBINE
            target.parent.mkdir(parents=True)
            target.write_bytes(b"preserved")
            (out / ".ninja_deps").write_bytes(ninja_deps([]))
            depfile = out / "gen/chrome/browser/auxiliary_search/java__header.d"
            depfile.parent.mkdir(parents=True)
            original = b"obj/other.jar: obj/chrome/browser/magic_stack/android/java.turbine.jar\n"
            depfile.write_bytes(original)
            with self.assertRaisesRegex(ValueError, "unexpected output"):
                invalidate_m154_auxiliary_search_cycle(out)
            self.assertEqual(original, depfile.read_bytes())
            self.assertFalse((out / M154_AUXILIARY_SEARCH_MARKER).exists())

    def test_does_not_overwrite_existing_dependency_backup(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            target = out / M154_AUXILIARY_SEARCH_TURBINE
            target.parent.mkdir(parents=True)
            target.write_bytes(b"preserved")
            (out / ".ninja_deps").write_bytes(ninja_deps([]))
            depfile = out / "gen/chrome/browser/auxiliary_search/java__header.d"
            depfile.parent.mkdir(parents=True)
            original = (M154_AUXILIARY_SEARCH_TURBINE.as_posix() +
                        ": obj/chrome/browser/magic_stack/android/java.turbine.jar\n").encode()
            depfile.write_bytes(original)
            backup = depfile.with_suffix(".d.kiwi-m153-backup")
            backup.write_bytes(b"previous backup")
            with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
                invalidate_m154_auxiliary_search_cycle(out)
            self.assertEqual(original, depfile.read_bytes())
            self.assertEqual(b"previous backup", backup.read_bytes())

    @unittest.skipUnless(shutil.which("ninja"), "ninja is required")
    def test_java_depfile_cycle_is_removed_without_changing_ninja_deps(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            auxiliary = M154_AUXILIARY_SEARCH_TURBINE.as_posix()
            magic = "obj/chrome/browser/magic_stack/android/java.turbine.jar"
            depfile = out / "gen/chrome/browser/auxiliary_search/java__header.d"
            depfile.parent.mkdir(parents=True)
            original_depfile = f"{auxiliary}: input {magic}\n".encode()
            depfile.write_bytes(original_depfile)
            for relative in (auxiliary, magic):
                path = out / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"preserved output")
            (out / "input").write_text("source\n")
            original_deps = ninja_deps([path_record("obj/unrelated.o", 0)])
            (out / ".ninja_deps").write_bytes(original_deps)
            (out / "build.ninja").write_text(
                "rule compile\n"
                "  command = touch $out\n"
                "  depfile = gen/chrome/browser/auxiliary_search/java__header.d\n"
                f"build {auxiliary}: compile input\n"
                f"build {magic}: phony {auxiliary}\n"
                f"default {auxiliary}\n"
            )
            def plan():
                return subprocess.run(["ninja", "-C", str(out), "-n", auxiliary],
                                      text=True, stdout=subprocess.PIPE,
                                      stderr=subprocess.STDOUT, check=False)
            before = plan()
            self.assertNotEqual(0, before.returncode, before.stdout)
            self.assertIn("dependency cycle", before.stdout)
            self.assertTrue(invalidate_m154_auxiliary_search_cycle(out))
            self.assertEqual(original_deps, (out / ".ninja_deps").read_bytes())
            self.assertEqual(f"{auxiliary}: input\n".encode(), depfile.read_bytes())
            self.assertEqual(original_depfile, depfile.with_suffix(".d.kiwi-m153-backup").read_bytes())
            self.assertEqual(b"preserved output", (out / auxiliary).read_bytes())
            after = plan()
            self.assertEqual(0, after.returncode, after.stdout)
            self.assertFalse(invalidate_m154_auxiliary_search_cycle(out))

    def test_marker_makes_invalidation_one_time(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            turbine = out / M154_AUXILIARY_SEARCH_TURBINE
            turbine.parent.mkdir(parents=True)
            turbine.write_bytes(b"rebuilt")
            (out / ".ninja_deps").write_bytes(ninja_deps([]))
            (out / M154_AUXILIARY_SEARCH_MARKER).write_text("done\n")
            current_ns = 1_800_000_000 * 10**9
            os.utime(turbine, ns=(current_ns, current_ns))

            self.assertFalse(invalidate_m154_auxiliary_search_cycle(out))
            self.assertEqual(current_ns, turbine.stat().st_mtime_ns)

    def test_missing_old_target_does_not_create_marker(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)

            self.assertFalse(invalidate_m154_auxiliary_search_cycle(out))
            self.assertFalse((out / M154_AUXILIARY_SEARCH_MARKER).exists())

    def test_malformed_deps_log_is_left_untouched(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            turbine = out / M154_AUXILIARY_SEARCH_TURBINE
            turbine.parent.mkdir(parents=True)
            turbine.write_bytes(b"preserved")
            deps = out / ".ninja_deps"
            malformed = b"# ninjadeps\n" + struct.pack("<I", 4) + struct.pack("<I", 99)
            deps.write_bytes(malformed)

            with self.assertRaises(ValueError):
                invalidate_m154_auxiliary_search_cycle(out)

            self.assertEqual(malformed, deps.read_bytes())
            self.assertFalse((out / M154_AUXILIARY_SEARCH_MARKER).exists())



if __name__ == "__main__":
    unittest.main()
