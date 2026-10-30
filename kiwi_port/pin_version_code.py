#!/usr/bin/env python3
"""Keep locally distributed Titanium-Kiwi builds mutually installable."""
import argparse
from pathlib import Path
import re

VERSION_CODE = "807807374"
PACKAGE = "io.github.nojirokaimo.titaniumkiwi"
ASSIGNMENT = re.compile(r"^[ \t]*android_override_version_code[ \t]*=.*$", re.MULTILINE)


def pin_args(path):
    """Set only the GN version override; avoid writing when it is already set."""
    text = path.read_text(encoding="utf-8")
    matches = list(ASSIGNMENT.finditer(text))
    if len(matches) > 1:
        raise ValueError("Multiple version-code assignments; preserving args.gn")
    desired = f'android_override_version_code = "{VERSION_CODE}"'
    if matches:
        match = matches[0]
        updated = text[:match.start()] + desired + text[match.end():]
    else:
        updated = text + ("\n" if text and not text.endswith("\n") else "") + desired + "\n"
    if updated == text:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def verify_badging(text, expected_version):
    lines = [line for line in text.splitlines() if line.startswith("package: ")]
    if len(lines) != 1:
        raise ValueError("APK badging did not contain exactly one package line")
    fields = dict(re.findall(r"([A-Za-z][A-Za-z0-9_]*)='([^']*)'", lines[0]))
    expected = {"name": PACKAGE, "versionCode": VERSION_CODE, "versionName": expected_version}
    for name, value in expected.items():
        if fields.get(name) != value:
            raise ValueError(f"APK {name} mismatch: expected {value}, got {fields.get(name)}")
    if fields.get("versionCodeMajor", "0") != "0":
        raise ValueError("APK versionCodeMajor must remain zero")


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--args-gn", type=Path)
    mode.add_argument("--badging", type=Path)
    parser.add_argument("--version")
    args = parser.parse_args()
    if args.args_gn:
        print("changed" if pin_args(args.args_gn) else "unchanged")
    else:
        if not args.version:
            parser.error("--version is required with --badging")
        verify_badging(args.badging.read_text(encoding="utf-8"), args.version)
        print(f"APK package and versionCode {VERSION_CODE} verified")


if __name__ == "__main__":
    main()
