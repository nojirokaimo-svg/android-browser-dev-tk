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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    changed = invalidate_m154_auxiliary_search_cycle(args.out)
    print(
        "Invalidated the stale M153 auxiliary_search turbine dependency."
        if changed
        else "No M153 auxiliary_search turbine invalidation was needed."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
