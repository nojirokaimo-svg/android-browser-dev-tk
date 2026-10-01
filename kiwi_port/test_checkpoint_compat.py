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
    def test_invalidates_only_stale_auxiliary_search_turbine_dependency(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            turbine = out / M154_AUXILIARY_SEARCH_TURBINE
            turbine.parent.mkdir(parents=True)
            turbine.write_bytes(b"preserved turbine jar")
            deps = out / ".ninja_deps"
            target = M154_AUXILIARY_SEARCH_TURBINE.as_posix()
            stored_target = "../../out/Default/" + target
            target_path = path_record(stored_target, 0)
            old_dependency_path = path_record(
                "obj/chrome/browser/magic_stack/android/java.turbine.jar", 1
            )
            unrelated_path = path_record("obj/unrelated/java.turbine.jar", 2)
            stale_target_record = deps_record(0, [1])
            unrelated_record = deps_record(2, [1])
            deps.write_bytes(
                ninja_deps(
                    [
                        target_path,
                        old_dependency_path,
                        unrelated_path,
                        stale_target_record,
                        unrelated_record,
                        # The latest record wins in Ninja. Remove every historical
                        # record for the target so recompaction cannot revive one.
                        deps_record(0, [2], mtime=456),
                    ]
                )
            )

            self.assertTrue(invalidate_m154_auxiliary_search_cycle(out))

            self.assertEqual(b"preserved turbine jar", turbine.read_bytes())
            self.assertEqual(AGE_NS, turbine.stat().st_mtime_ns)
            self.assertEqual(
                ninja_deps(
                    [target_path, old_dependency_path, unrelated_path, unrelated_record]
                ),
                deps.read_bytes(),
            )
            self.assertTrue((out / M154_AUXILIARY_SEARCH_MARKER).is_file())

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

    @unittest.skipUnless(shutil.which("ninja"), "ninja is required")
    def test_targeted_rewrite_breaks_the_real_ninja_dependency_cycle(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            auxiliary = M154_AUXILIARY_SEARCH_TURBINE.as_posix()
            magic = "obj/chrome/browser/magic_stack/android/java.turbine.jar"
            auxiliary_file = out / auxiliary
            auxiliary_file.parent.mkdir(parents=True)
            auxiliary_file.write_bytes(b"old auxiliary output")
            (out / magic).parent.mkdir(parents=True)
            (out / magic).write_bytes(b"magic output")
            (out / "input").write_text("source\n")
            (out / "build.ninja").write_text(
                "rule compile\n"
                "  command = touch $out\n"
                "  deps = gcc\n"
                "  depfile = $out.d\n"
                "build " + auxiliary + ": compile input\n"
                "build " + magic + ": phony " + auxiliary + "\n"
                "default " + auxiliary + "\n"
            )
            (out / ".ninja_deps").write_bytes(
                ninja_deps(
                    [
                        path_record(auxiliary, 0),
                        path_record(magic, 1),
                        # Ninja treats a deps record as valid while the output is
                        # not newer than the recorded mtime.
                        deps_record(0, [1], mtime=2_000_000_000 * 10**9),
                    ]
                )
            )

            before = subprocess.run(
                ["ninja", "-C", str(out), "-n", auxiliary],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            self.assertNotEqual(0, before.returncode)
            self.assertIn("dependency cycle", before.stdout)

            self.assertTrue(invalidate_m154_auxiliary_search_cycle(out))
            after = subprocess.run(
                ["ninja", "-C", str(out), "-n", auxiliary],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            self.assertEqual(0, after.returncode, after.stdout)


if __name__ == "__main__":
    unittest.main()
