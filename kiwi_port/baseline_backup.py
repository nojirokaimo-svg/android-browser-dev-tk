#!/usr/bin/env python3
"""Create and restore a durable split archive of Chromium out/Default."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO, Callable
import os


SCHEMA_VERSION = 1
PART_PREFIX = "out-default.tar.zst.part-"
MANIFEST_NAME = "baseline-manifest.json"
REQUIRED_CHECKPOINT_FILES = ("build.ninja", ".ninja_log", "args.gn", "kiwi-source-state.json")
DEFAULT_SPLIT_BYTES = 1_900_000_000


class BaselineBackupError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_checkpoint(source: Path) -> None:
    if not source.is_dir():
        raise BaselineBackupError(f"checkpoint directory does not exist: {source}")
    for relative in REQUIRED_CHECKPOINT_FILES:
        if not (source / relative).is_file():
            raise BaselineBackupError(f"checkpoint is missing required file: {relative}")


def _part_name(index: int) -> str:
    # Fixed-width decimal ordering keeps shell glob/cat order deterministic.
    return f"{PART_PREFIX}{index:04d}"


def _part_entry(path: Path) -> dict[str, object]:
    return {"name": path.name, "size": path.stat().st_size, "sha256": _sha256(path)}


def _write_split_stream(
    stream: BinaryIO,
    output_dir: Path,
    split_bytes: int,
    *,
    on_part: Callable[[Path, dict[str, object]], None] | None = None,
    delete_part_after_emit: bool = False,
) -> list[dict[str, object]]:
    if split_bytes <= 0:
        raise BaselineBackupError("split_bytes must be positive")
    if delete_part_after_emit and on_part is None:
        raise BaselineBackupError("delete_part_after_emit requires on_part")

    entries: list[dict[str, object]] = []
    index = 0
    current: BinaryIO | None = None
    current_path: Path | None = None
    current_size = 0

    def finish_current() -> None:
        nonlocal current, current_path, current_size
        if current is None or current_path is None:
            return
        current.close()
        current = None
        entry = _part_entry(current_path)
        if on_part is not None:
            on_part(current_path, dict(entry))
            if delete_part_after_emit:
                current_path.unlink()
        entries.append(entry)
        current_path = None
        current_size = 0

    try:
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            offset = 0
            while offset < len(chunk):
                if current is None:
                    current_path = output_dir / _part_name(index)
                    current = current_path.open("wb")
                    index += 1
                    current_size = 0
                available = split_bytes - current_size
                piece = chunk[offset : offset + available]
                current.write(piece)
                current_size += len(piece)
                offset += len(piece)
                if current_size == split_bytes:
                    finish_current()
        finish_current()
    finally:
        if current is not None:
            current.close()

    if not entries:
        raise BaselineBackupError("compressed backup produced no parts")
    return entries


def create_backup(
    source: Path,
    output_dir: Path,
    metadata: dict[str, str],
    *,
    split_bytes: int = DEFAULT_SPLIT_BYTES,
    compression_level: int = 6,
    on_part: Callable[[Path, dict[str, object]], None] | None = None,
    delete_part_after_emit: bool = False,
) -> Path:
    source = Path(source).resolve()
    output_dir = Path(output_dir).resolve()
    _require_checkpoint(source)
    state = json.loads((source / "kiwi-source-state.json").read_text(encoding="utf-8"))
    expected_identity = (
        f"{metadata.get('titanium_commit', '')}:"
        f"{metadata.get('vanadium_commit', '')}:"
        f"{metadata.get('chromium_commit', '')}:validation"
    )
    if state.get("identity") != expected_identity:
        raise BaselineBackupError(
            "checkpoint source provenance identity does not match requested commits"
        )
    output_dir.mkdir(parents=True, exist_ok=True)

    for old in output_dir.glob(f"{PART_PREFIX}*"):
        old.unlink()
    manifest_path = output_dir / MANIFEST_NAME
    if manifest_path.exists():
        manifest_path.unlink()

    tar_proc = subprocess.Popen(
        ["tar", "-C", str(source.parent), "-cf", "-", source.name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert tar_proc.stdout is not None
    zstd_proc = subprocess.Popen(
        ["zstd", "-T0", f"-{compression_level}", "-c"],
        stdin=tar_proc.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    tar_proc.stdout.close()
    assert zstd_proc.stdout is not None

    try:
        parts = _write_split_stream(
            zstd_proc.stdout,
            output_dir,
            split_bytes,
            on_part=on_part,
            delete_part_after_emit=delete_part_after_emit,
        )
    except Exception:
        zstd_proc.kill()
        tar_proc.kill()
        raise
    finally:
        zstd_proc.stdout.close()

    zstd_stderr = zstd_proc.stderr.read().decode("utf-8", errors="replace") if zstd_proc.stderr else ""
    tar_stderr = tar_proc.stderr.read().decode("utf-8", errors="replace") if tar_proc.stderr else ""
    if zstd_proc.stderr:
        zstd_proc.stderr.close()
    if tar_proc.stderr:
        tar_proc.stderr.close()
    zstd_status = zstd_proc.wait()
    tar_status = tar_proc.wait()
    if tar_status != 0 or zstd_status != 0:
        for part in output_dir.glob(f"{PART_PREFIX}*"):
            part.unlink(missing_ok=True)
        raise BaselineBackupError(
            f"archive creation failed: tar={tar_status} zstd={zstd_status}; "
            f"tar stderr={tar_stderr.strip()!r}; zstd stderr={zstd_stderr.strip()!r}"
        )

    manifest = {
        "schema": SCHEMA_VERSION,
        "archive_format": "tar.zst.split",
        "directory_name": source.name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "metadata": dict(metadata),
        "parts": parts,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest_path


def _load_manifest(
    manifest_path: Path, expected_metadata: dict[str, str] | None = None
) -> dict:
    manifest_path = Path(manifest_path).resolve()
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BaselineBackupError(f"cannot read backup manifest: {exc}") from exc

    if manifest.get("schema") != SCHEMA_VERSION:
        raise BaselineBackupError(f"unsupported backup schema: {manifest.get('schema')!r}")
    if manifest.get("archive_format") != "tar.zst.split":
        raise BaselineBackupError("unexpected archive format")
    if manifest.get("directory_name") != "Default":
        raise BaselineBackupError("backup does not contain Chromium out/Default")

    metadata = manifest.get("metadata")
    if not isinstance(metadata, dict):
        raise BaselineBackupError("manifest metadata is missing")
    if expected_metadata:
        for key, expected in expected_metadata.items():
            actual = metadata.get(key)
            if actual != expected:
                raise BaselineBackupError(
                    f"metadata mismatch for {key}: expected {expected!r}, got {actual!r}"
                )

    parts = manifest.get("parts")
    if not isinstance(parts, list) or not parts:
        raise BaselineBackupError("manifest contains no archive parts")

    previous_name = ""
    for index, entry in enumerate(parts):
        if not isinstance(entry, dict):
            raise BaselineBackupError(f"invalid part entry at index {index}")
        name = entry.get("name")
        size = entry.get("size")
        sha256 = entry.get("sha256")
        if not isinstance(name, str) or Path(name).name != name or not name.startswith(PART_PREFIX):
            raise BaselineBackupError(f"unsafe part name at index {index}: {name!r}")
        if previous_name and name <= previous_name:
            raise BaselineBackupError("archive parts are not strictly ordered")
        previous_name = name
        if not isinstance(size, int) or size <= 0:
            raise BaselineBackupError(f"invalid part size for {name}: {size!r}")
        if (
            not isinstance(sha256, str)
            or len(sha256) != 64
            or any(ch not in "0123456789abcdef" for ch in sha256)
        ):
            raise BaselineBackupError(f"invalid part checksum for {name}")

    return manifest


def _verify_part(path: Path, entry: dict[str, object]) -> None:
    name = str(entry["name"])
    if not path.is_file():
        raise BaselineBackupError(f"archive part is missing: {name}")
    actual_size = path.stat().st_size
    if actual_size != entry["size"]:
        raise BaselineBackupError(
            f"size mismatch for {name}: expected {entry['size']}, got {actual_size}"
        )
    actual_sha = _sha256(path)
    if actual_sha != entry["sha256"]:
        raise BaselineBackupError(f"checksum mismatch for {name}")


def verify_backup(manifest_path: Path, expected_metadata: dict[str, str] | None = None) -> dict:
    manifest_path = Path(manifest_path).resolve()
    manifest = _load_manifest(manifest_path, expected_metadata)
    for entry in manifest["parts"]:
        _verify_part(manifest_path.parent / entry["name"], entry)
    return manifest


def restore_backup(
    manifest_path: Path,
    destination_parent: Path,
    expected_metadata: dict[str, str] | None = None,
    *,
    fetch_part: Callable[[Path, dict[str, object]], None] | None = None,
    delete_part_after_use: bool = False,
) -> Path:
    manifest_path = Path(manifest_path).resolve()
    destination_parent = Path(destination_parent).resolve()
    manifest = _load_manifest(manifest_path, expected_metadata)
    destination_parent.mkdir(parents=True, exist_ok=True)
    destination = destination_parent / manifest["directory_name"]
    if destination.exists():
        raise BaselineBackupError(f"restore destination already exists: {destination}")

    zstd_proc = subprocess.Popen(
        ["zstd", "-d", "-c"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert zstd_proc.stdin is not None and zstd_proc.stdout is not None
    tar_proc = subprocess.Popen(
        ["tar", "-C", str(destination_parent), "--no-same-owner", "-xf", "-"],
        stdin=zstd_proc.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    zstd_proc.stdout.close()

    try:
        for entry in manifest["parts"]:
            part = manifest_path.parent / entry["name"]
            if not part.is_file() and fetch_part is not None:
                fetch_part(part, dict(entry))
            _verify_part(part, entry)
            with part.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    zstd_proc.stdin.write(chunk)
            if delete_part_after_use:
                part.unlink()
        zstd_proc.stdin.close()
    except Exception:
        zstd_proc.kill()
        tar_proc.kill()
        raise

    tar_stdout, tar_stderr_bytes = tar_proc.communicate()
    zstd_stderr_bytes = zstd_proc.stderr.read() if zstd_proc.stderr else b""
    if zstd_proc.stderr:
        zstd_proc.stderr.close()
    zstd_status = zstd_proc.wait()
    tar_status = tar_proc.returncode
    if zstd_status != 0 or tar_status != 0:
        raise BaselineBackupError(
            f"archive restore failed: zstd={zstd_status} tar={tar_status}; "
            f"zstd stderr={zstd_stderr_bytes.decode(errors='replace').strip()!r}; "
            f"tar stderr={tar_stderr_bytes.decode(errors='replace').strip()!r}; "
            f"tar stdout={tar_stdout.decode(errors='replace').strip()!r}"
        )

    _require_checkpoint(destination)
    return destination


def _add_metadata_arguments(parser: argparse.ArgumentParser, *, require_source_cache_key: bool) -> None:
    parser.add_argument("--chromium-version", required=True)
    parser.add_argument("--chromium-commit", required=True)
    parser.add_argument("--titanium-commit", required=True)
    parser.add_argument("--vanadium-commit", required=True)
    parser.add_argument("--source-cache-key", required=require_source_cache_key, default="")


def _metadata_from_args(args: argparse.Namespace) -> dict[str, str]:
    metadata = {
        "chromium_version": args.chromium_version,
        "chromium_commit": args.chromium_commit,
        "titanium_commit": args.titanium_commit,
        "vanadium_commit": args.vanadium_commit,
    }
    if getattr(args, "source_cache_key", ""):
        metadata["source_cache_key"] = args.source_cache_key
    return metadata


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="Create a split tar.zst baseline backup")
    create.add_argument("--source", type=Path, required=True)
    create.add_argument("--output-dir", type=Path, required=True)
    create.add_argument("--split-bytes", type=int, default=DEFAULT_SPLIT_BYTES)
    create.add_argument("--compression-level", type=int, default=6)
    create.add_argument(
        "--part-command",
        default="",
        help=(
            "Shell command run after each completed part. Receives BASELINE_PART_PATH, "
            "BASELINE_PART_NAME, BASELINE_PART_SIZE and BASELINE_PART_SHA256."
        ),
    )
    create.add_argument(
        "--delete-part-after-command",
        action="store_true",
        help="Delete each local part after --part-command succeeds.",
    )
    _add_metadata_arguments(create, require_source_cache_key=True)

    verify = subparsers.add_parser("verify", help="Verify manifest metadata and all part checksums")
    verify.add_argument("--manifest", type=Path, required=True)
    _add_metadata_arguments(verify, require_source_cache_key=False)

    restore = subparsers.add_parser("restore", help="Verify and restore out/Default")
    restore.add_argument("--manifest", type=Path, required=True)
    restore.add_argument("--destination-parent", type=Path, required=True)
    restore.add_argument(
        "--fetch-part-command",
        default="",
        help=(
            "Shell command used to fetch a missing part. Receives BASELINE_PART_PATH, "
            "BASELINE_PART_NAME, BASELINE_PART_SIZE and BASELINE_PART_SHA256."
        ),
    )
    restore.add_argument(
        "--delete-part-after-use",
        action="store_true",
        help="Delete each verified local archive part immediately after it is streamed into restore.",
    )
    _add_metadata_arguments(restore, require_source_cache_key=False)
    return parser


def _part_command_callback(command: str):
    def emit(path: Path, entry: dict[str, object]) -> None:
        env = os.environ.copy()
        env.update(
            {
                "BASELINE_PART_PATH": str(path),
                "BASELINE_PART_NAME": str(entry["name"]),
                "BASELINE_PART_SIZE": str(entry["size"]),
                "BASELINE_PART_SHA256": str(entry["sha256"]),
            }
        )
        try:
            subprocess.run(
                ["bash", "-eo", "pipefail", "-c", command],
                env=env,
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            raise BaselineBackupError(
                f"part command failed for {entry['name']}: exit {exc.returncode}"
            ) from exc

    return emit


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.command == "create":
            if args.delete_part_after_command and not args.part_command:
                raise BaselineBackupError(
                    "--delete-part-after-command requires --part-command"
                )
            callback = _part_command_callback(args.part_command) if args.part_command else None
            manifest = create_backup(
                args.source,
                args.output_dir,
                _metadata_from_args(args),
                split_bytes=args.split_bytes,
                compression_level=args.compression_level,
                on_part=callback,
                delete_part_after_emit=args.delete_part_after_command,
            )
            print(manifest)
        elif args.command == "verify":
            verify_backup(args.manifest, _metadata_from_args(args))
            print("baseline backup verified")
        elif args.command == "restore":
            fetch_callback = (
                _part_command_callback(args.fetch_part_command)
                if args.fetch_part_command
                else None
            )
            restored = restore_backup(
                args.manifest,
                args.destination_parent,
                _metadata_from_args(args),
                fetch_part=fetch_callback,
                delete_part_after_use=args.delete_part_after_use,
            )
            print(restored)
        else:
            parser.error(f"unknown command: {args.command}")
    except BaselineBackupError as exc:
        parser.exit(2, f"baseline backup error: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
