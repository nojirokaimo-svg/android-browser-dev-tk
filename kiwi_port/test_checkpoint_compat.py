import hashlib
import os
from pathlib import Path
import tempfile
import unittest

from checkpoint_compat import (
    AGE_NS,
    M154_AUXILIARY_SEARCH_MARKER,
    M154_AUXILIARY_SEARCH_TURBINE,
    invalidate_m154_auxiliary_search_cycle,
)


class CheckpointCompatibilityTest(unittest.TestCase):
    def test_invalidates_only_stale_auxiliary_search_turbine_dependency(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            turbine = out / M154_AUXILIARY_SEARCH_TURBINE
            turbine.parent.mkdir(parents=True)
            turbine.write_bytes(b"preserved turbine jar")
            deps = out / ".ninja_deps"
            deps.write_bytes(b"preserved dependency log")
            deps_before = (hashlib.sha256(deps.read_bytes()).hexdigest(), deps.stat().st_mtime_ns)

            self.assertTrue(invalidate_m154_auxiliary_search_cycle(out))

            self.assertEqual(b"preserved turbine jar", turbine.read_bytes())
            self.assertEqual(AGE_NS, turbine.stat().st_mtime_ns)
            self.assertEqual(
                deps_before,
                (hashlib.sha256(deps.read_bytes()).hexdigest(), deps.stat().st_mtime_ns),
            )
            self.assertTrue((out / M154_AUXILIARY_SEARCH_MARKER).is_file())

    def test_marker_makes_invalidation_one_time(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            turbine = out / M154_AUXILIARY_SEARCH_TURBINE
            turbine.parent.mkdir(parents=True)
            turbine.write_bytes(b"rebuilt")
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


if __name__ == "__main__":
    unittest.main()
