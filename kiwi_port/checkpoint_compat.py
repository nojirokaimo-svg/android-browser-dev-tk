#!/usr/bin/env python3
"""One-time compatibility adjustments for exact cross-version Ninja checkpoints."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import struct

AGE_NS = 946684800 * 10**9
M154_AUXILIARY_SEARCH_TURBINE = Path(
    "obj/chrome/browser/auxiliary_search/java.turbine.jar"
)
M154_AUXILIARY_SEARCH_MARKER = ".kiwi-m154-auxiliary-search-deps-pruned-v2"

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


def _prune_deps_for_output(deps_path: Path, output: str) -> int:
    original = deps_path.read_bytes()
    records, paths = _parse_ninja_deps(original)
    output_bytes = output.encode()
    try:
        output_id = paths.index(output_bytes)
    except ValueError as exc:
        raise ValueError(f"output is absent from .ninja_deps: {output}") from exc

    kept: list[bytes] = []
    removed = 0
    for is_deps, raw_record in records:
        if is_deps:
            (record_output_id,) = struct.unpack_from("<I", raw_record, 4)
            if record_output_id >= len(paths):
                raise ValueError("dependency record refers to an unknown path id")
            if record_output_id == output_id:
                removed += 1
                continue
        kept.append(raw_record)

    if not removed:
        return 0
    rewritten = NINJA_DEPS_SIGNATURE + struct.pack("<I", NINJA_DEPS_VERSION) + b"".join(kept)
    # Parse the result before the atomic replacement. This preserves every path and
    # unrelated dependency record byte-for-byte while removing only the obsolete edge.
    rewritten_records, rewritten_paths = _parse_ninja_deps(rewritten)
    if rewritten_paths != paths or any(
        is_deps and struct.unpack_from("<I", raw, 4)[0] == output_id
        for is_deps, raw in rewritten_records
    ):
        raise ValueError("failed to verify targeted .ninja_deps rewrite")

    temporary = deps_path.with_name(deps_path.name + ".kiwi-prune.tmp")
    with temporary.open("wb") as stream:
        stream.write(rewritten)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, deps_path)
    return removed


def invalidate_m154_auxiliary_search_cycle(out: Path) -> bool:
    """Invalidate the one M153 turbine output whose recorded dependency reversed in M154.

    Chromium M153 made auxiliary_search:java depend on magic_stack:java. M154 moved the
    module classes into module_java and made magic_stack:java depend on
    auxiliary_search:java. An exact M153 checkpoint can therefore retain the removed edge
    in .ninja_deps and combine it with the new edge into a cycle. Remove every historical
    dependency record for that single output, leave all other records byte-identical, and
    age the output so Ninja rebuilds it. No dependency log or generated output is deleted.
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
    removed = _prune_deps_for_output(deps, M154_AUXILIARY_SEARCH_TURBINE.as_posix())
    if not removed:
        return False
    os.utime(turbine, ns=(AGE_NS, AGE_NS))
    marker.write_text(
        f"Removed {removed} stale M153 auxiliary_search dependency record(s) for M154\n"
    )
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
