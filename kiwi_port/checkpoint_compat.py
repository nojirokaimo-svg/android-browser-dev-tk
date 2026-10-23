#!/usr/bin/env python3
"""One-time compatibility adjustments for exact cross-version Ninja checkpoints."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import struct

AGE_NS = 946684800 * 10**9
M154_AUXILIARY_SEARCH_TURBINE = Path(
    "obj/chrome/browser/auxiliary_search/java.turbine.jar"
)
M154_AUXILIARY_SEARCH_MARKER = ".kiwi-m154-auxiliary-search-depfile-pruned-v3"
M154_AUXILIARY_SEARCH_DEPFILE = Path("gen/chrome/browser/auxiliary_search/java__header.d")
M153_MAGIC_STACK_TURBINE = b"obj/chrome/browser/magic_stack/android/java.turbine.jar"

NINJA_DEPS_SIGNATURE = b"# ninjadeps\n"
NINJA_DEPS_VERSION = 4


def _parse_ninja_deps(data: bytes) -> tuple[list[tuple[bool, bytes]], list[bytes]]:
    header_size = len(NINJA_DEPS_SIGNATURE) + 4
    if len(data) < header_size or not data.startswith(NINJA_DEPS_SIGNATURE):
        raise ValueError("invalid .ninja_deps signature")
    (version,) = struct.unpack_from("<I", data, len(NINJA_DEPS_SIGNATURE))
    if version != NINJA_DEPS_VERSION:
        raise ValueError(f"unsupported .ninja_deps version: {version}")

    records: list[tuple[bool, bytes]] = []
    paths: list[bytes] = []
    offset = header_size
    while offset < len(data):
        if len(data) - offset < 4:
            raise ValueError("truncated .ninja_deps record size")
        (raw_size,) = struct.unpack_from("<I", data, offset)
        is_deps = bool(raw_size & 0x80000000)
        size = raw_size & 0x7FFFFFFF
        end = offset + 4 + size
        if size == 0 or end > len(data):
            raise ValueError("truncated .ninja_deps record")
        raw_record = data[offset:end]
        payload = data[offset + 4 : end]
        if is_deps:
            if size < 12 or size % 4:
                raise ValueError("invalid .ninja_deps dependency record")
        else:
            if size < 5:
                raise ValueError("invalid .ninja_deps path record")
            path_field = payload[:-4]
            path = path_field.rstrip(b"\0")
            if not path or len(path_field) - len(path) > 3:
                raise ValueError("invalid .ninja_deps path padding")
            (checksum,) = struct.unpack_from("<I", payload, size - 4)
            expected = (~len(paths)) & 0xFFFFFFFF
            if checksum != expected:
                raise ValueError("invalid .ninja_deps path checksum")
            paths.append(path)
        records.append((is_deps, raw_record))
        offset = end
    return records, paths


def invalidate_m154_auxiliary_search_cycle(out: Path) -> bool:
    """Remove the proven M153 reverse edge from the Java action's text depfile.

    Build #170's exact checkpoint audit showed that GN's Java action reads
    gen/chrome/browser/auxiliary_search/java__header.d, without deps=gcc.
    The turbine output is absent from .ninja_deps. Preserve that log entirely;
    remove only the magic_stack turbine token from this one text depfile,
    keep its original bytes in a backup, and age the preserved jar for rebuild.
    """
    out = Path(out)
    marker = out / M154_AUXILIARY_SEARCH_MARKER
    if marker.exists():
        return False
    turbine = out / M154_AUXILIARY_SEARCH_TURBINE
    if not turbine.is_file():
        return False
    deps = out / ".ninja_deps"
    if not deps.is_file():
        raise ValueError("restored checkpoint has no .ninja_deps")
    _parse_ninja_deps(deps.read_bytes())
    depfile = out / M154_AUXILIARY_SEARCH_DEPFILE
    if not depfile.is_file():
        return False
    original = depfile.read_bytes()
    outputs, separator, inputs = original.partition(b":")
    if separator != b":" or outputs.strip() != M154_AUXILIARY_SEARCH_TURBINE.as_posix().encode():
        raise ValueError(f"unexpected output in {depfile}: {outputs!r}")
    pattern = rb"[ \t]+" + re.escape(M153_MAGIC_STACK_TURBINE) + rb"(?=\s|$)"
    rewritten_inputs, removed = re.subn(pattern, b"", inputs)
    if not removed:
        return False
    if removed != 1:
        raise ValueError(f"expected one stale magic_stack dependency in {depfile}, found {removed}")
    rewritten = outputs + separator + rewritten_inputs
    backup = depfile.with_suffix(".d.kiwi-m153-backup")
    if backup.exists() and backup.read_bytes() != original:
        raise ValueError(f"refusing to overwrite different dependency backup: {backup}")
    if not backup.exists():
        with backup.open("xb") as stream:
            stream.write(original)
            stream.flush()
            os.fsync(stream.fileno())
    temporary = depfile.with_name(depfile.name + ".kiwi-prune.tmp")
    with temporary.open("wb") as stream:
        stream.write(rewritten)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, depfile)
    os.utime(turbine, ns=(AGE_NS, AGE_NS))
    marker.write_text(
        f"Removed magic_stack turbine from {M154_AUXILIARY_SEARCH_DEPFILE}; .ninja_deps unchanged\n"
    )
    print(f"Removed the stale M153 magic_stack edge from {depfile}; original backed up at {backup}")
    return True



# The exact M156 checkpoint's GN edge is already channel_enum_java. However,
# M155-derived Java build-config JSON and text depfiles still reference
# version_constants_java, creating build_info -> version_constants -> base_java
# -> build_info. This is independently proven by diagnostic artifact 12485750919.
def invalidate_m156_build_info_cycle(out: Path) -> bool:
    import hashlib
    import json
    out = Path(out)
    marker = out / ".kiwi-m156-build-info-generated-deps-fixed-v1"
    for name in (".ninja_log", ".ninja_deps", "build.ninja", "args.gn", "toolchain.ninja"):
        if not (out / name).is_file():
            raise ValueError("Missing M156 checkpoint prerequisite: " + name)
    gn = (out / "toolchain.ninja").read_text()
    edges = (
        ("phony/base/build_info_java__header.harddeps",
         "phony/base/version_info/android/channel_enum_java__header",
         "phony/base/version_info/android/version_constants_java__header"),
        ("phony/base/version_info/android/version_constants_java__header.harddeps",
         "phony/base/base_java__header", None),
        ("phony/base/base_java__header.harddeps",
         "phony/base/build_info_java__header", None),
    )
    for target, required, forbidden in edges:
        matches = [line.split() for line in gn.splitlines()
                   if line.startswith("build " + target + ": phony ")]
        if len(matches) != 1 or required not in matches[0] or (
            forbidden is not None and forbidden in matches[0]
        ):
            raise ValueError("Unverified M156 GN edge: " + target)

    old_t = "obj/base/version_info/android/version_constants_java.turbine.jar"
    new_t = "obj/base/version_info/android/channel_enum_java.turbine.jar"
    old_j = "obj/base/version_info/android/version_constants_java.javac.jar"
    new_j = "obj/base/version_info/android/channel_enum_java.javac.jar"
    configs = (
        ("gen/base/build_info_java.turbine.build_config.json",
         "interface_classpath", old_t, new_t),
        ("gen/base/build_info_java.javac.build_config.json",
         "javac_full_interface_classpath", old_t, new_t),
        ("gen/base/build_info_java.build_config.json",
         "javac_full_classpath", old_j, new_j),
    )
    depfiles = (
        ("gen/base/build_info_java__header.d",
         "obj/base/build_info_java.turbine.jar"),
        ("gen/base/build_info_java__compile_java.d",
         "obj/base/build_info_java.javac.jar"),
    )
    if marker.exists():
        for relative, key, old, new in configs:
            values = __import__("json").loads((out / relative).read_text())[key]
            if old in values or new not in values:
                raise ValueError("M156 stale config returned: " + relative)
        for relative, _ in depfiles:
            raw = (out / relative).read_bytes()
            if old_t.encode() in raw or new_t.encode() not in raw:
                raise ValueError("M156 stale depfile returned: " + relative)
        return False

    changes = {}
    for relative, key, old, new in configs:
        raw = (out / relative).read_bytes()
        data = json.loads(raw)
        values = data.get(key)
        if not isinstance(values, list) or values.count(old) != 1 or values.count(new) != 1:
            raise ValueError("Unverified M156 generated config: " + relative)
        data[key] = [value for value in values if value != old]
        changes[relative] = (raw, (json.dumps(data, indent=2) + "\n").encode())
    for relative, target in depfiles:
        raw = (out / relative).read_bytes()
        output, separator, inputs = raw.partition(b":")
        if separator != b":" or output.strip() != target.encode():
            raise ValueError("Unverified M156 depfile target: " + relative)
        pattern = rb"[ \t]+" + re.escape(old_t.encode()) + rb"(?=\s|$)"
        new_pattern = rb"[ \t]+" + re.escape(new_t.encode()) + rb"(?=\s|$)"
        if len(re.findall(pattern, inputs)) != 1 or not re.search(new_pattern, inputs):
            raise ValueError("Unverified M156 stale depfile edge: " + relative)
        changes[relative] = (raw, output + separator + re.sub(pattern, b"", inputs, count=1))
    for relative, (before, after) in changes.items():
        backup = out / (relative + ".kiwi-m156-backup")
        if before == after or (backup.exists() and backup.read_bytes() != before):
            raise ValueError("M156 backup conflict: " + relative)
    before_log = hashlib.sha256((out / ".ninja_log").read_bytes()).hexdigest()
    before_deps = hashlib.sha256((out / ".ninja_deps").read_bytes()).hexdigest()
    for relative, (before, after) in changes.items():
        path = out / relative
        backup = out / (relative + ".kiwi-m156-backup")
        if not backup.exists():
            with backup.open("xb") as stream:
                stream.write(before)
                stream.flush()
                os.fsync(stream.fileno())
        temporary = path.with_name(path.name + ".kiwi-m156-tmp")
        with temporary.open("wb") as stream:
            stream.write(after)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    for relative in ("obj/base/build_info_java.turbine.jar",
                     "obj/base/build_info_java.javac.jar"):
        target = out / relative
        if target.is_file():
            os.utime(target, ns=(AGE_NS, AGE_NS))
    if (hashlib.sha256((out / ".ninja_log").read_bytes()).hexdigest() != before_log or
        hashlib.sha256((out / ".ninja_deps").read_bytes()).hexdigest() != before_deps):
        raise ValueError("Ninja history changed during M156 repair")
    marker.write_text("Verified M156 generated Java dependency repair; five originals backed up\n")
    print("M156 generated Java classpaths and depfiles repaired with backups; Ninja history preserved")
    return True

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("out", type=Path)
    parser.add_argument("--m156-build-info", action="store_true")
    args = parser.parse_args()
    if args.m156_build_info:
        changed = invalidate_m156_build_info_cycle(args.out)
        print("M156 build_info generated dependency repair:", "repaired" if changed else "already fixed")
        return 0
    changed = invalidate_m154_auxiliary_search_cycle(args.out)
    print(
        "Invalidated the stale M153 auxiliary_search turbine dependency."
        if changed
        else "No M153 auxiliary_search turbine invalidation was needed."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
