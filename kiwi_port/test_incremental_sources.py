import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

import incremental_sources
from incremental_sources import AGE_NS, PLAN, STATE, digest, restore


class IncrementalTest(unittest.TestCase):
    def test_upstream_transition_preserves_cache_and_keeps_unrebuilt_edges_dirty(self):
        original_patch_owned_files = incremental_sources.patch_owned_files
        self.addCleanup(
            setattr, incremental_sources, 'patch_owned_files', original_patch_owned_files)
        incremental_sources.patch_owned_files = lambda: set()

        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp)
            out = source/'out/Default'
            out.mkdir(parents=True)
            (out/'args.gn').write_text(
                'target_cpu = "arm64"\n'
                'chrome_public_manifest_package = "io.github.nojirokaimo.titaniumkiwi"\n'
                'is_debug = false\n'
                'is_official_build = true\n'
                'symbol_level = 0\n'
                'generate_linker_map = false\n'
                'blink_symbol_level = 0\n'
                'v8_symbol_level = 0\n'
                'treat_warnings_as_errors = false\n'
            )
            for name in ('unchanged.cc', 'changed.cc'):
                (source/name).write_text(name)
            old_output = out/'unchanged.o'
            old_output.write_text('cached')
            os.utime(old_output, ns=(AGE_NS + 1, AGE_NS + 1))
            state = {
                'identity': 'old-upstream',
                'files': {
                    name: {'sha256': digest(source/name), 'mtime_ns': AGE_NS}
                    for name in ('unchanged.cc', 'changed.cc')
                },
            }
            (out/STATE).write_text(json.dumps(state))
            (source/'changed.cc').write_text('new upstream source')
            manifest = {'files': dict.fromkeys(('unchanged.cc', 'changed.cc'))}

            with contextlib.redirect_stdout(io.StringIO()):
                changed = restore(
                    source, 'build-146', manifest, {'cache_key': '', 'files': {}},
                    'new-upstream', transition_from_identity='old-upstream')

            self.assertIn('<upstream-source-transition>', changed)
            plan = json.loads((out/PLAN).read_text())
            self.assertTrue(plan['upstream_transition'])
            epoch = plan['source_epoch_ns']
            self.assertGreater(epoch, old_output.stat().st_mtime_ns)
            self.assertEqual((source/'unchanged.cc').stat().st_mtime_ns, epoch)
            self.assertEqual((source/'changed.cc').stat().st_mtime_ns, epoch)

            # A later stage must keep source timestamps at the transition epoch so
            # old, not-yet-rebuilt edges stay dirty while completed edges are reused.
            rebuilt = out/'changed.o'
            rebuilt.write_text('rebuilt')
            os.utime(rebuilt, ns=(epoch + 1, epoch + 1))
            with contextlib.redirect_stdout(io.StringIO()):
                restore(
                    source, 'stage-2', manifest, {'cache_key': '', 'files': {}},
                    'new-upstream')
            self.assertEqual((source/'unchanged.cc').stat().st_mtime_ns, epoch)
            self.assertLess(old_output.stat().st_mtime_ns, epoch)
            self.assertGreater(rebuilt.stat().st_mtime_ns, epoch)

    def test_100_actions_restore_edit_and_continue(self):
        original_patch_owned_files = incremental_sources.patch_owned_files
        self.addCleanup(
            setattr, incremental_sources, 'patch_owned_files', original_patch_owned_files)
        incremental_sources.patch_owned_files = lambda: set()

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            src = root/'first'
            out = src/'out/Default'
            out.mkdir(parents=True)
            (out/'args.gn').write_text(
                'target_cpu = "arm64"\n'
                'chrome_public_manifest_package = "io.github.nojirokaimo.titaniumkiwi"\n'
                'is_debug = false\n'
                'is_official_build = true\n'
                'symbol_level = 0\n'
                'generate_linker_map = false\n'
                'blink_symbol_level = 0\n'
                'v8_symbol_level = 0\n'
                'treat_warnings_as_errors = false\n'
            )
            names = [f'input{i}.txt' for i in range(100)]
            for name in names:
                (src/name).write_text(name)
                os.utime(src/name, ns=(AGE_NS, AGE_NS))
            for i, name in enumerate(names):
                p = out/f'output{i}'
                p.write_text(name)
                os.utime(p, ns=(AGE_NS + 1, AGE_NS + 1))
            before = {p.name: (digest(p), p.stat().st_mtime_ns) for p in out.iterdir()}
            legacy = {'cache_key': 'verified-legacy', 'files': {n: digest(src/n) for n in names}}
            fresh = root/'fresh'
            fresh.mkdir()
            shutil.copytree(out, fresh/'out/Default', copy_function=shutil.copy2)
            for name in names:
                (fresh/name).write_text(name)
            (fresh/names[17]).write_text('changed')
            manifest = {'files': dict.fromkeys(names)}
            with contextlib.redirect_stdout(io.StringIO()):
                changed = restore(fresh, 'verified-legacy', manifest, legacy, 'pinned')
            self.assertEqual(changed, [names[17]])
            restored = fresh/'out/Default'
            plan = json.loads((restored/PLAN).read_text())
            self.assertEqual(plan['changed_sources'], [names[17]])
            self.assertEqual(plan['tracked_sources'], 100)
            self.assertEqual(plan['cache_key'], 'verified-legacy')
            for name, data in before.items():
                p = restored/name
                self.assertEqual((digest(p), p.stat().st_mtime_ns), data)
            stale = [i for i, name in enumerate(names)
                     if (fresh/name).stat().st_mtime_ns > (restored/f'output{i}').stat().st_mtime_ns]
            self.assertEqual(stale, [17])
            # Simulate the one-edge rebuild, then verify the next job has zero stale edges.
            (restored/'output17').write_text('changed')
            os.utime(restored/'output17', ns=(changed_stamp := (fresh/names[17]).stat().st_mtime_ns + 1,)*2)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(restore(fresh, 'next', manifest, legacy, 'pinned'), [])
            stale = [i for i, name in enumerate(names)
                     if (fresh/name).stat().st_mtime_ns > (restored/f'output{i}').stat().st_mtime_ns]
            self.assertEqual(stale, [])
            with self.assertRaises(RuntimeError):
                restore(fresh, 'next', manifest, legacy, 'different-upstream')


if __name__ == '__main__':
    unittest.main()
