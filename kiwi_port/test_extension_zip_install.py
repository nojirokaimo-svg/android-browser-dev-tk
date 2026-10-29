"""Exercise the actual Java ZIP-to-CRX packer from the registered patch."""

import hashlib
import io
import shutil
import struct
import subprocess
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path


PATCH = Path(__file__).parent / "patches/230-extension-zip-crx-install.patch"
JAVA_PATH = "chrome/android/java/src/org/chromium/chrome/browser/backup/KiwiCrxPacker.java"


def new_java_source():
    section = PATCH.read_text(encoding="utf-8").split(
        f"diff --git a/{JAVA_PATH} b/{JAVA_PATH}\n", 1
    )[1].split("\ndiff --git ", 1)[0]
    body = section.split("\n@@ ", 1)[1].split("\n", 1)[1]
    return "\n".join(line[1:] for line in body.splitlines() if line.startswith("+")) + "\n"


def varint(data, pos):
    result = 0
    shift = 0
    while True:
        byte = data[pos]
        pos += 1
        result |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return result, pos
        shift += 7
        if shift > 63:
            raise ValueError("bad varint")


def protobuf_fields(data):
    pos = 0
    fields = {}
    while pos < len(data):
        tag, pos = varint(data, pos)
        if tag & 7 != 2:
            raise ValueError("unexpected wire type")
        length, pos = varint(data, pos)
        fields[tag >> 3] = data[pos : pos + length]
        pos += length
    return fields


@unittest.skipUnless(shutil.which("java") and shutil.which("openssl"), "requires Java and OpenSSL")
class ExtensionZipInstallTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="kiwi-crx-test-")
        cls.root = Path(cls.tmp.name)
        cls.classes = cls.root / "classes"
        cls.classes.mkdir()
        source = cls.root / "KiwiCrxPacker.java"
        source.write_text(new_java_source(), encoding="utf-8")
        runner = cls.root / "PackerTestRunner.java"
        runner.write_text(
            "package org.chromium.chrome.browser.backup;\n"
            "import java.io.File;\n"
            "public final class PackerTestRunner {\n"
            " public static void main(String[] a) throws Exception {\n"
            "  System.out.println(KiwiCrxPacker.pack(new File(a[0]), new File(a[1])));\n"
            " }\n"
            "}\n",
            encoding="utf-8",
        )
        compiler = ["javac"] if shutil.which("javac") else ["java", "-m", "jdk.compiler/com.sun.tools.javac.Main"]
        subprocess.run(compiler + ["-d", str(cls.classes), str(source), str(runner)], check=True, capture_output=True, text=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def archive(self, entries):
        path = self.root / (self.id().split(".")[-1] + ".zip")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
                for name, content in entries:
                    archive.writestr(name, content)
        return path

    def pack(self, path):
        return subprocess.run(
            ["java", "-cp", str(self.classes), "org.chromium.chrome.browser.backup.PackerTestRunner", str(path), str(self.root)],
            capture_output=True, text=True,
        )

    def assert_signed_crx(self, result, expected):
        self.assertEqual(result.returncode, 0, result.stderr)
        data = Path(result.stdout.strip()).read_bytes()
        self.assertEqual(data[:4], b"Cr24")
        version, header_length = struct.unpack_from("<II", data, 4)
        self.assertEqual(version, 3)
        header = protobuf_fields(data[12 : 12 + header_length])
        proof = protobuf_fields(header[2])
        signed_header = header[10000]
        self.assertEqual(protobuf_fields(signed_header)[1], hashlib.sha256(proof[1]).digest()[:16])
        zip_bytes = data[12 + header_length :]
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
            self.assertEqual(set(archive.namelist()), set(expected))
            for name, contents in expected.items():
                self.assertEqual(archive.read(name), contents)
        public_key = self.root / "public.der"
        public_pem = self.root / "public.pem"
        signature = self.root / "signature.bin"
        signed_data = self.root / "signed.bin"
        public_key.write_bytes(proof[1])
        signature.write_bytes(proof[2])
        signed_data.write_bytes(b"CRX3 SignedData\x00" + struct.pack("<I", len(signed_header)) + signed_header + zip_bytes)
        subprocess.run(["openssl", "pkey", "-pubin", "-inform", "DER", "-in", str(public_key), "-out", str(public_pem)], check=True, capture_output=True)
        verify = subprocess.run(["openssl", "dgst", "-sha256", "-verify", str(public_pem), "-signature", str(signature), str(signed_data)], capture_output=True, text=True)
        self.assertEqual(verify.returncode, 0, verify.stderr)

    def test_root_manifest_produces_verified_crx(self):
        entries = {"manifest.json": b'{"manifest_version":3}', "js/main.js": b"hello"}
        result = self.pack(self.archive(list(entries.items())))
        self.assert_signed_crx(result, entries)

    def test_single_wrapping_folder_is_removed(self):
        result = self.pack(self.archive([
            ("__MACOSX/._manifest.json", b"metadata"),
            ("extension-1.0/manifest.json", b'{"manifest_version":2}'),
            ("extension-1.0/code.js", b"test"),
        ]))
        self.assert_signed_crx(result, {"manifest.json": b'{"manifest_version":2}', "code.js": b"test"})

    def test_dot_prefix_is_accepted(self):
        result = self.pack(self.archive([("./manifest.json", b"{}"), ("./code.js", b"x")]))
        self.assert_signed_crx(result, {"manifest.json": b"{}", "code.js": b"x"})

    def test_legacy_japanese_windows_filename(self):
        class WindowsZipInfo(zipfile.ZipInfo):
            def _encodeFilenameFlags(self):
                return self.filename.encode("cp932"), self.flag_bits & ~0x800

        path = self.root / "legacy-japanese.zip"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("manifest.json", b"{}")
            archive.writestr(WindowsZipInfo("日本語.js"), b"script")
        self.assert_signed_crx(self.pack(path), {"manifest.json": b"{}", "日本語.js": b"script"})

    def test_missing_or_ambiguous_manifest_is_rejected(self):
        for entries in [[("code.js", b"x")], [("a/manifest.json", b"{}"), ("b/manifest.json", b"{}")]]:
            with self.subTest(entries=entries):
                self.assertNotEqual(self.pack(self.archive(entries)).returncode, 0)

    def test_traversal_and_duplicate_entries_are_rejected(self):
        for entries in [[("manifest.json", b"{}"), ("../escape.js", b"x")], [("manifest.json", b"{}"), ("manifest.json", b"{}")]]:
            with self.subTest(entries=entries):
                self.assertNotEqual(self.pack(self.archive(entries)).returncode, 0)

    def test_corrupt_archive_is_rejected(self):
        path = self.archive([("manifest.json", b"known-contents")])
        raw = path.read_bytes().replace(b"known-contents", b"bad!!-contents", 1)
        path.write_bytes(raw)
        self.assertNotEqual(self.pack(path).returncode, 0)


if __name__ == "__main__":
    unittest.main()
