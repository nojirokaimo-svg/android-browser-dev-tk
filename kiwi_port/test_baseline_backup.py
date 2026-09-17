import json
import tempfile
import unittest
from pathlib import Path

import baseline_backup


class BaselineBackupTest(unittest.TestCase):
    def make_default(self, root: Path) -> Path:
        default = root / "Default"
        (default / "obj").mkdir(parents=True)
        (default / ".ninja_log").write_text("ninja log\n", encoding="utf-8")
        (default / "build.ninja").write_text("rule cc\n", encoding="utf-8")
        (default / "args.gn").write_text("target_cpu=\"arm64\"\n", encoding="utf-8")
        (default / "kiwi-source-state.json").write_text(
            json.dumps({"identity": "t" * 40 + ":" + "v" * 40 + ":" + "c" * 40 + ":validation", "files": {}}),
            encoding="utf-8",
        )
        (default / "obj" / "sample.o").write_bytes(b"object-data" * 200)
        return default

    def metadata(self):
        return {
            "chromium_version": "153.0.8010.36",
            "chromium_commit": "c" * 40,
            "titanium_commit": "t" * 40,
            "vanadium_commit": "v" * 40,
            "source_cache_key": "kiwi-incremental-153-test-stage-1",
        }

    def test_create_verify_restore_round_trip(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = self.make_default(root / "source")
            backup = root / "backup"
            manifest = baseline_backup.create_backup(
                source, backup, self.metadata(), split_bytes=80
            )

            data = baseline_backup.verify_backup(manifest, self.metadata())
            self.assertGreater(len(data["parts"]), 1)
            self.assertTrue(all(part["size"] <= 80 for part in data["parts"]))

            restore_parent = root / "restored"
            baseline_backup.restore_backup(manifest, restore_parent, self.metadata())
            self.assertEqual(
                (restore_parent / "Default" / "obj" / "sample.o").read_bytes(),
                (source / "obj" / "sample.o").read_bytes(),
            )

    def test_create_can_emit_and_delete_parts_after_each_part(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = self.make_default(root / "source")
            emitted = []

            def on_part(path, entry):
                emitted.append((path.name, entry["size"], entry["sha256"]))

            manifest = baseline_backup.create_backup(
                source,
                root / "backup",
                self.metadata(),
                split_bytes=80,
                on_part=on_part,
                delete_part_after_emit=True,
            )
            data = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertGreater(len(emitted), 1)
            self.assertEqual([row[0] for row in emitted], [p["name"] for p in data["parts"]])
            self.assertTrue(all(not (manifest.parent / p["name"]).exists() for p in data["parts"]))

    def test_restore_can_fetch_verify_and_delete_parts_one_at_a_time(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = self.make_default(root / "source")
            backup = root / "backup"
            manifest = baseline_backup.create_backup(
                source, backup, self.metadata(), split_bytes=80
            )
            data = json.loads(manifest.read_text(encoding="utf-8"))
            remote = root / "remote"
            remote.mkdir()
            for entry in data["parts"]:
                name = entry["name"]
                (remote / name).write_bytes((backup / name).read_bytes())
                (backup / name).unlink()

            fetched = []

            def fetch_part(path, entry):
                fetched.append(entry["name"])
                path.write_bytes((remote / entry["name"]).read_bytes())

            restore_parent = root / "restored"
            baseline_backup.restore_backup(
                manifest,
                restore_parent,
                self.metadata(),
                fetch_part=fetch_part,
                delete_part_after_use=True,
            )
            self.assertEqual(fetched, [entry["name"] for entry in data["parts"]])
            self.assertTrue(all(not (backup / entry["name"]).exists() for entry in data["parts"]))
            self.assertEqual(
                (restore_parent / "Default" / "obj" / "sample.o").read_bytes(),
                (source / "obj" / "sample.o").read_bytes(),
            )

    def test_verify_rejects_tampered_part(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = self.make_default(root / "source")
            manifest = baseline_backup.create_backup(
                source, root / "backup", self.metadata(), split_bytes=300
            )
            manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
            part = manifest.parent / manifest_data["parts"][0]["name"]
            payload = bytearray(part.read_bytes())
            payload[0] ^= 0x01
            part.write_bytes(payload)

            with self.assertRaisesRegex(baseline_backup.BaselineBackupError, "checksum"):
                baseline_backup.verify_backup(manifest, self.metadata())

    def test_verify_rejects_metadata_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = self.make_default(root / "source")
            manifest = baseline_backup.create_backup(
                source, root / "backup", self.metadata(), split_bytes=300
            )
            expected = self.metadata()
            expected["chromium_version"] = "154.0.0.0"
            with self.assertRaisesRegex(baseline_backup.BaselineBackupError, "metadata"):
                baseline_backup.verify_backup(manifest, expected)

    def test_create_requires_ninja_checkpoint_files(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            default = root / "Default"
            default.mkdir()
            with self.assertRaisesRegex(baseline_backup.BaselineBackupError, "build.ninja"):
                baseline_backup.create_backup(
                    default, root / "backup", self.metadata(), split_bytes=300
                )


if __name__ == "__main__":
    unittest.main()
