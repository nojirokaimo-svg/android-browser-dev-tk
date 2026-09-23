#!/usr/bin/env python3
"""Restore source timestamps without rewriting a restored Ninja checkpoint.

Checkpoint continuations run on a fresh hosted runner, so an identical source tree
has newer mtimes than the cached objects.  Age only source files and keep every
file under out/Default intact apart from the small provenance/plan metadata that
travels with the next checkpoint.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import time

HERE = Path(__file__).resolve().parent
AGE_NS = 946684800 * 10**9
STATE = "kiwi-source-state.json"
PLAN = "kiwi-incremental-plan.json"


def digest(path):
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def checked_path(source, name):
    p = Path(name)
    if p.is_absolute() or ".." in p.parts or "out" in p.parts or ".git" in p.parts:
        raise RuntimeError(f"Invalid source path: {name}")
    result = source / p
    if result.is_symlink():
        raise RuntimeError(f"Patch-owned symlink is unsupported: {name}")
    return result


def verify_resume_args(out):
    """Validate the Stage-1 GN configuration without modifying it or running gn gen."""
    args = out / "args.gn"
    if not args.is_file():
        raise RuntimeError(f"Missing restored GN args: {args}")

    lines = {line.strip() for line in args.read_text(encoding="utf-8").splitlines()}
    required = {
        'target_cpu = "arm64"',
        'chrome_public_manifest_package = "io.github.nojirokaimo.titaniumkiwi"',
        "is_debug = false",
        "is_official_build = true",
        "symbol_level = 0",
        "generate_linker_map = false",
        "blink_symbol_level = 0",
        "v8_symbol_level = 0",
        "treat_warnings_as_errors = false",
    }
    forbidden = {
        "is_debug = true",
        "is_official_build = false",
        "symbol_level = 1",
        "generate_linker_map = true",
    }
    missing = sorted(required - lines)
    bad = sorted(forbidden & lines)
    if missing or bad:
        raise RuntimeError(
            "Restored args.gn does not match the Stage-1 release checkpoint; "
            f"missing={missing}, forbidden={bad}. Preserving cache and stopping"
        )
    print("Verified restored args.gn; no GN arguments were changed and gn gen is not required.")


def patch_owned_files():
    series = json.loads((HERE / "patches/series.json").read_text(encoding="utf-8"))
    return {
        name
        for feature in series["features"]
        for name in feature.get("files", [])
    }


def restore(source, cache_key, manifest, legacy, identity, bootstrap_current=False,
            transition_from_identity=None):
    out = source / "out/Default"
    state_path = out / STATE
    previous = None
    bootstrapped = False
    upstream_transition = False
    source_epoch_ns = None

    if state_path.is_file():
        state = json.loads(state_path.read_text())
        if state["identity"] != identity and state["identity"] != transition_from_identity:
            raise RuntimeError(
                "Cache source/toolchain identity changed; preserving cache and stopping"
            )
        upstream_transition = state["identity"] != identity
        source_epoch_ns = state.get("source_epoch_ns")
        previous = state["files"]
    elif cache_key == legacy["cache_key"]:
        previous = {
            p: {"sha256": h, "mtime_ns": AGE_NS}
            for p, h in legacy["files"].items()
        }
    elif bootstrap_current:
        # This path is only enabled after the workflow proves that every
        # source-producing repository input is unchanged from the revision that
        # created the restored cache.  Therefore the freshly prepared pinned tree
        # is the exact source state the cached objects were built from.
        bootstrapped = True
    else:
        raise RuntimeError(
            "No source provenance for this cache; preserving cache and stopping"
        )

    names = sorted(
        set(manifest["files"])
        | set(previous or {})
        | patch_owned_files()
    )
    paths = {name: checked_path(source, name) for name in names}
    current = {name: digest(p) for name, p in paths.items()}

    if bootstrapped:
        previous = {
            name: {"sha256": current[name], "mtime_ns": AGE_NS}
            for name in names
        }

    if upstream_transition:
        # This is an explicit one-way transition from an immutable completed
        # checkpoint.  Make the prepared upstream tree newer than cached outputs,
        # while leaving enough wall-clock margin for GN/Ninja writes.
        source_epoch_ns = time.time_ns() - 2 * 10**9

    # Fresh checkouts have new mtimes and would make Ninja rebuild already cached
    # objects.  Age source files only.  Never enter any out/ or .git/ directory,
    # and never touch .ninja_log, build.ninja, args.gn, objects, or generated files
    # inside the restored out/Default checkpoint.
    for directory, dirs, files in os.walk(source):
        dirs[:] = [
            d
            for d in dirs
            if d not in (".git", "out")
            and not (Path(directory) / d).is_symlink()
        ]
        for name in files:
            p = Path(directory) / name
            if name != ".git" and not p.is_symlink():
                stamp = source_epoch_ns if source_epoch_ns is not None else AGE_NS
                os.utime(p, ns=(stamp, stamp))

    now = time.time_ns()
    changed = []
    records = {}
    for name, p in paths.items():
        old = previous.get(name)
        different = old is None or old["sha256"] != current[name]
        if source_epoch_ns is not None:
            stamp = source_epoch_ns
        else:
            stamp = now if different else old["mtime_ns"]
        if different:
            changed.append(name)
        if p.is_file():
            os.utime(p, ns=(stamp, stamp))
        records[name] = {"sha256": current[name], "mtime_ns": stamp}

    verify_resume_args(out)

    # Only metadata is written into out/Default.  The Ninja database, GN files,
    # object files and generated build outputs remain byte-for-byte untouched.
    state_path.write_text(
        json.dumps({
            "identity": identity,
            "source_epoch_ns": source_epoch_ns,
            "files": records,
        }, indent=2) + "\n"
    )
    plan = {
        "cache_key": cache_key,
        "identity": identity,
        "bootstrapped_exact_checkpoint": bootstrapped,
        "changed_sources": (
            ["<upstream-source-transition>", *changed]
            if upstream_transition else changed
        ),
        "tracked_sources": len(records),
        "upstream_transition": upstream_transition,
        "source_epoch_ns": source_epoch_ns,
    }
    (out / PLAN).write_text(json.dumps(plan, indent=2) + "\n")
    print(json.dumps(plan, indent=2))
    return plan["changed_sources"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--cache-key", required=True)
    parser.add_argument("--identity", required=True)
    parser.add_argument(
        "--bootstrap-current",
        action="store_true",
        help=(
            "Trust the freshly prepared source tree as the restored cache source "
            "state. The caller must first prove source-producing inputs are unchanged."
        ),
    )
    parser.add_argument(
        "--transition-from-identity",
        help=(
            "Allow a single explicit source transition from this exact previous "
            "identity while preserving the restored output checkpoint."
        ),
    )
    args = parser.parse_args()
    restore(
        args.source.resolve(),
        args.cache_key,
        json.loads((HERE / "manifest.json").read_text()),
        json.loads((HERE / "legacy-cache-source-hashes.json").read_text()),
        args.identity,
        bootstrap_current=args.bootstrap_current,
        transition_from_identity=args.transition_from_identity,
    )


if __name__ == "__main__":
    main()
