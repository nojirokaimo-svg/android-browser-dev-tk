#!/usr/bin/env python3
"""Apply feature-scoped Kiwi UI patches to a post-Titanium Chromium tree."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
MANIFEST = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))
SERIES = json.loads((HERE / "patches/series.json").read_text(encoding="utf-8"))


def digest(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def git(source: Path, *args: str, check: bool = False) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(["git", "-C", str(source), *args], text=True, capture_output=True)
    if check and completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(detail or f"git {' '.join(args)} failed")
    return completed


def command_detail(completed: subprocess.CompletedProcess[str]) -> str:
    return completed.stderr.strip() or completed.stdout.strip() or f"exit {completed.returncode}"


def safe_relative(relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise RuntimeError(f"unsafe patch path: {relative}")
    return path


def effective_patch(source: Path, feature: dict[str, object], patch: Path) -> Path:
    """Return the Chromium 153 patch as checked in; no hidden context rewriting."""
    return patch


def _insert_after_unique(path: Path, anchor: str, insertion: str) -> bool:
    """Insert exact text after one verified anchor, or accept an already-applied insertion."""
    text = path.read_text(encoding="utf-8")
    if insertion in text:
        return True
    if text.count(anchor) != 1:
        return False
    path.write_text(text.replace(anchor, anchor + insertion, 1), encoding="utf-8")
    return True


def repair_known_context_drift(
    source: Path, feature_id: str, rejected: list[str]
) -> list[str]:
    """Repair only known M153 context-only rejects after validating unique anchors.

    These are intentionally narrow. Any content change that removes or duplicates an anchor
    remains a hard conflict instead of being silently accepted.
    """
    remaining = list(rejected)

    if feature_id == "black-statusbar-full-backup":
        relative = "chrome/android/java/src/org/chromium/chrome/browser/ui/system/StatusBarColorController.java"
        if relative in remaining:
            anchor = "        @ColorInt int statusBarColor = calculateFinalStatusBarColor();\n"
            insertion = (
                "        int nightMode =\n"
                "                mActivity.getResources().getConfiguration().uiMode\n"
                "                        & android.content.res.Configuration.UI_MODE_NIGHT_MASK;\n"
                "        if (nightMode == android.content.res.Configuration.UI_MODE_NIGHT_YES) {\n"
                "            statusBarColor = Color.BLACK;\n"
                "        }\n"
            )
            target = source / relative
            if target.is_file() and _insert_after_unique(target, anchor, insertion):
                (source / f"{relative}.rej").unlink(missing_ok=True)
                remaining.remove(relative)

    if feature_id == "kiwi-tab-switcher":
        relative = "chrome/android/chrome_java_resources.gni"
        if relative in remaining:
            target = source / relative
            if target.is_file():
                additions = (
                    (
                        '  "java/res/layout/radio_button_group_homepage_preference.xml",\n',
                        '  "java/res/layout/radio_button_group_tabswitcher_preference.xml",\n',
                    ),
                    (
                        '  "java/res/xml/main_preferences.xml",\n',
                        '  "java/res/xml/tabswitcher_preferences.xml",\n',
                    ),
                )
                repaired = True
                for anchor, insertion in additions:
                    if not _insert_after_unique(target, anchor, insertion):
                        repaired = False
                        break
                if repaired:
                    (source / f"{relative}.rej").unlink(missing_ok=True)
                    remaining.remove(relative)

    if feature_id == "kiwi-omnibox-history":
        relative = "chrome/android/java/src/org/chromium/chrome/browser/ntp/NewTabPage.java"
        if relative in remaining:
            target = source / relative
            if target.is_file():
                text = target.read_text(encoding="utf-8")
                method_start = "        public boolean isLocationBarShownInNtp() {\n"
                next_override = "\n        @Override\n"
                start = text.find(method_start)
                end = text.find(next_override, start + len(method_start)) if start >= 0 else -1
                desired = (
                    "        public boolean isLocationBarShownInNtp() {\n"
                    "            if (mIsDestroyed) return false;\n"
                    "            // Kiwi keeps the real toolbar omnibox pinned at the top of a new tab instead of\n"
                    "            // morphing it into Chromium's large in-page fake search box.\n"
                    "            return false;\n"
                    "        }\n"
                )
                if desired in text:
                    repaired = True
                elif start >= 0 and end >= 0:
                    target.write_text(text[:start] + desired + text[end:], encoding="utf-8")
                    repaired = True
                else:
                    repaired = False
                if repaired:
                    (source / f"{relative}.rej").unlink(missing_ok=True)
                    remaining.remove(relative)

        relative = (
            "chrome/browser/ui/android/omnibox/java/src/org/chromium/chrome/browser/"
            "omnibox/suggestions/SuggestionListViewBinder.java"
        )
        if relative in remaining:
            target = source / relative
            if target.is_file():
                text = target.read_text(encoding="utf-8")
                old = "            holder.container.setBackgroundColor(backgroundColor);\n"
                new = (
                    "            // Kiwi leaves the current page visible behind the focused omnibox and darkens it\n"
                    "            // with a translucent scrim instead of an opaque black fill.\n"
                    "            holder.container.setBackgroundColor(Color.argb(179, 0, 0, 0));\n"
                )
                if new in text:
                    repaired = True
                elif text.count(old) == 1:
                    target.write_text(text.replace(old, new, 1), encoding="utf-8")
                    repaired = True
                else:
                    repaired = False
                if repaired:
                    (source / f"{relative}.rej").unlink(missing_ok=True)
                    remaining.remove(relative)

    return remaining


def write_report(report: Path, source: Path, results: list[dict[str, object]]) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    conflicts = [item for item in results if item["status"] == "conflict"]
    lines = [
        "# Kiwi patch reapplication report", "", f"Source: `{source}`", "",
        "| Feature | Status | Files requiring repair |", "|---|---|---|",
    ]
    for item in results:
        files = "<br>".join(f"`{path}`" for path in item.get("conflicts", [])) or "—"
        lines.append(f"| `{item['id']}` — {item['name']} | {item['status']} | {files} |")
    if conflicts:
        lines += ["", "Clean hunks and later independent features were applied. Rejected hunks are in the listed `.rej` files.", "Repair only those files, remove the `.rej` files, then regenerate the feature patches."]
    else:
        lines += ["", "All feature patches applied without conflicts."]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    report.with_suffix(".json").write_text(json.dumps({"source": str(source), "features": results}, indent=2) + "\n", encoding="utf-8")


def file_states(source: Path) -> dict[str, str]:
    states: dict[str, str] = {}
    for relative, expected in MANIFEST["files"].items():
        safe_relative(relative)
        actual = digest(source / relative)
        if actual == expected["after_sha256"]:
            states[relative] = "after"
        elif actual == expected["before_sha256"]:
            states[relative] = "before"
        else:
            states[relative] = "mismatch"
    return states


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="post-Titanium Chromium src directory")
    parser.add_argument("--best-effort", action="store_true", help="apply clean hunks/features and leave .rej files for upstream conflicts")
    parser.add_argument("--report", type=Path, help="write Markdown and JSON reports")
    args = parser.parse_args()
    source = args.source.resolve()
    if not (source / ".git").exists():
        raise RuntimeError(f"not a Chromium git tree: {source}")

    states = file_states(source)
    if all(state == "after" for state in states.values()):
        print("Kiwi UI feature patches are already applied.")
        if args.report:
            write_report(
                args.report.resolve(),
                source,
                [
                    {
                        "id": feature["id"],
                        "name": feature["name"],
                        "patch": feature["patch"],
                        "status": "already-applied",
                        "conflicts": [],
                    }
                    for feature in SERIES["features"]
                ],
            )
        return 0

    pinned_before = all(state == "before" for state in states.values())
    if not args.best_effort:
        # Preflight the complete series before changing any file. Feature
        # patches own disjoint files, so every contextual check can be done
        # against the same untouched tree.
        failures: list[tuple[dict[str, object], str, str]] = []
        for feature in SERIES["features"]:
            patch = HERE / "patches" / safe_relative(feature["patch"])
            if digest(patch) != feature["sha256"]:
                raise RuntimeError(f"patch checksum mismatch: {patch.name}")
            patch_to_apply = effective_patch(source, feature, patch)
            forward = git(source, "apply", "--check", str(patch_to_apply))
            reverse = git(source, "apply", "--reverse", "--check", str(patch_to_apply))
            if forward.returncode != 0 and reverse.returncode != 0:
                failures.append((feature, command_detail(forward), command_detail(reverse)))
        if failures:
            details = "\n".join(
                f"  {feature['id']} ({feature['name']}):\n"
                f"    files: {', '.join(feature['files'])}\n"
                f"    forward: {forward_detail}\n"
                f"    reverse: {reverse_detail}"
                for feature, forward_detail, reverse_detail in failures
            )
            raise RuntimeError(
                "strict preflight failed; source was not changed:\n" + details
                + "\nrerun with --best-effort --report <path> to isolate conflicts"
            )

    results: list[dict[str, object]] = []
    for feature in SERIES["features"]:
        patch = HERE / "patches" / safe_relative(feature["patch"])
        if digest(patch) != feature["sha256"]:
            raise RuntimeError(f"patch checksum mismatch: {patch.name}")
        patch_to_apply = effective_patch(source, feature, patch)
        item: dict[str, object] = {"id": feature["id"], "name": feature["name"], "patch": feature["patch"], "status": "pending", "conflicts": []}
        if git(source, "apply", "--reverse", "--check", str(patch_to_apply)).returncode == 0:
            item["status"] = "already-applied"
        elif git(source, "apply", "--check", str(patch_to_apply)).returncode == 0:
            git(source, "apply", "--whitespace=nowarn", str(patch_to_apply), check=True)
            item["status"] = "applied"
        elif not args.best_effort:
            files = "\n  ".join(feature["files"])
            raise RuntimeError(f"feature {feature['id']} ({feature['name']}) does not apply cleanly:\n  {files}\nrerun with --best-effort --report <path> to apply independent clean changes")
        else:
            partial = git(source, "apply", "--reject", "--whitespace=nowarn", str(patch_to_apply))
            rejected = [str(safe_relative(path)) for path in feature["files"] if (source / f"{path}.rej").is_file()]
            original_rejected = list(rejected)
            if rejected:
                rejected = repair_known_context_drift(source, str(feature["id"]), rejected)
            if partial.returncode == 0:
                item["status"] = "applied"
            elif original_rejected and not rejected:
                item["status"] = "repaired-context-drift"
            else:
                item["status"] = "conflict"
                item["conflicts"] = rejected or feature["files"]
        results.append(item)

    if args.report:
        write_report(args.report.resolve(), source, results)
    conflicts = [item for item in results if item["status"] == "conflict"]
    if conflicts:
        for item in conflicts:
            print(f"CONFLICT {item['id']} ({item['name']}): " + ", ".join(item["conflicts"]), file=sys.stderr)
        return 2
    if pinned_before:
        after = file_states(source)
        bad = [path for path, state in after.items() if state != "after"]
        if bad:
            raise RuntimeError("pinned post-apply verification failed: " + ", ".join(bad))
    print(f"Applied/verified {len(results)} Kiwi UI feature patches.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
