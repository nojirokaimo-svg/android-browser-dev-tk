#!/usr/bin/env python3
"""Fail fast when the feature-scoped Kiwi patch series is internally inconsistent."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
PATCH_DIR = HERE / "patches"
SERIES_PATH = PATCH_DIR / "series.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def touched_files(text: str) -> list[str]:
    return re.findall(r"^diff --git a/(.+?) b/(.+?)$", text, flags=re.MULTILINE)


def main() -> int:
    series = json.loads(SERIES_PATH.read_text(encoding="utf-8"))
    errors: list[str] = []
    ids: set[str] = set()
    registered: set[str] = set()

    for feature in series.get("features", []):
        feature_id = feature.get("id")
        patch_name = feature.get("patch")
        if not isinstance(feature_id, str) or not feature_id:
            errors.append("feature with missing/invalid id")
            continue
        if feature_id in ids:
            errors.append(f"duplicate feature id: {feature_id}")
        ids.add(feature_id)
        if not isinstance(patch_name, str) or Path(patch_name).name != patch_name:
            errors.append(f"{feature_id}: unsafe/invalid patch name: {patch_name!r}")
            continue
        if patch_name in registered:
            errors.append(f"duplicate patch registration: {patch_name}")
        registered.add(patch_name)
        patch = PATCH_DIR / patch_name
        if not patch.is_file():
            errors.append(f"{feature_id}: missing patch: {patch_name}")
            continue
        actual = digest(patch)
        expected = feature.get("sha256")
        if actual != expected:
            errors.append(
                f"{feature_id}: checksum mismatch for {patch_name}: "
                f"series={expected}, actual={actual}"
            )
        pairs = touched_files(patch.read_text(encoding="utf-8"))
        malformed = [f"{left} -> {right}" for left, right in pairs if left != right]
        if malformed:
            errors.append(f"{feature_id}: renamed/malformed paths: {', '.join(malformed)}")
        actual_files = [left for left, right in pairs if left == right]
        listed_files = feature.get("files")
        if len(actual_files) != len(set(actual_files)):
            errors.append(f"{feature_id}: patch contains a duplicate file section")
        if not isinstance(listed_files, list) or any(
            not isinstance(path, str) for path in listed_files
        ):
            errors.append(f"{feature_id}: files must be a list of paths")
        elif len(listed_files) != len(set(listed_files)):
            errors.append(f"{feature_id}: series contains a duplicate file path")
        elif set(actual_files) != set(listed_files):
            errors.append(
                f"{feature_id}: files set differs from patch: "
                f"series={listed_files!r}, patch={actual_files!r}"
            )

    on_disk = {path.name for path in PATCH_DIR.glob("*.patch")}
    for name in sorted(on_disk - registered):
        errors.append(f"unregistered patch file: {name}")
    for name in sorted(registered - on_disk):
        errors.append(f"registered patch is absent: {name}")

    if errors:
        raise SystemExit("Patch series integrity failed:\n  " + "\n  ".join(errors))
    print(f"Verified {len(ids)} feature patches: checksums, registrations, and file lists match.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
