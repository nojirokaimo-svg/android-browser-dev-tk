#!/usr/bin/env bash
set -Eeuo pipefail

KIT_ROOT="$(cd "$(dirname "$0")" && pwd)"
BUILD_ROOT="${KIWI_BUILD_ROOT:-$KIT_ROOT/work}"
TITANIUM_DIR="$BUILD_ROOT/titanium"
TITANIUM_REPOSITORY="${TITANIUM_REPOSITORY:-https://github.com/jqssun/android-titanium-browser.git}"
TITANIUM_COMMIT="${TITANIUM_COMMIT:-7584b534f6e1f9c29e8bb98df71d7610960a5db3}"
VANADIUM_COMMIT="${VANADIUM_COMMIT:-02d87ad8e17aee77d0fea49d122349a5da87ed2e}"
CHROMIUM_COMMIT="${CHROMIUM_COMMIT:-507c6ee3e2f3b2ca0e660547e5b9ea4820c67f4c}"
VERSION="${CHROMIUM_VERSION:-153.0.8010.36}"
PHASE="${KIWI_BUILD_PHASE:-all}"
PATCH_MODE="${KIWI_PATCH_MODE:-strict}"

if [[ "$PHASE" != "all" && "$PHASE" != "prepare" && "$PHASE" != "compile" ]]; then
  echo "Unknown KIWI_BUILD_PHASE: $PHASE" >&2
  exit 2
fi

if [[ "$PHASE" != "compile" ]]; then
mkdir -p "$BUILD_ROOT"
if [[ ! -d "$TITANIUM_DIR/.git" ]]; then
  # A resume job restores out/Default before preparing the pinned source tree.
  # Populate the repository in place so the restored Ninja checkpoint remains
  # untouched even though its parent directory is already non-empty.
  mkdir -p "$TITANIUM_DIR"
  git -C "$TITANIUM_DIR" init
fi
if ! git -C "$TITANIUM_DIR" remote get-url origin >/dev/null 2>&1; then
  git -C "$TITANIUM_DIR" remote add origin "$TITANIUM_REPOSITORY"
fi
git -C "$TITANIUM_DIR" fetch --depth 1 origin "$TITANIUM_COMMIT"
git -C "$TITANIUM_DIR" checkout --detach --force "$TITANIUM_COMMIT"
git -C "$TITANIUM_DIR" submodule update --init --recursive --depth 1
test "$(git -C "$TITANIUM_DIR/vanadium" rev-parse HEAD)" = "$VANADIUM_COMMIT"

export DEBIAN_FRONTEND=noninteractive
sudo rm -f /etc/apt/sources.list.d/google-chrome.list
apt_update() {
  local attempt
  for attempt in 1 2 3; do
    if sudo apt-get -o Acquire::Retries=3 update; then
      return 0
    fi
    echo "APT update attempt $attempt failed; retrying after mirror propagation." >&2
    sudo rm -rf /var/lib/apt/lists/partial/*
    sleep $((attempt * 15))
  done
  echo "APT update failed after 3 attempts." >&2
  return 1
}
sudo dpkg --add-architecture i386
apt_update
sudo apt-get install -y \
  sudo lsb-release file git curl python3 python3-pillow imagemagick librsvg2-bin \
  ninja-build libgcc-s1:i386

if [[ ! -d "$BUILD_ROOT/depot_tools/.git" ]]; then
  git clone --depth 1 https://chromium.googlesource.com/chromium/tools/depot_tools.git \
    "$BUILD_ROOT/depot_tools"
fi
export PATH="$BUILD_ROOT/depot_tools:$PATH"

git config --global user.name "Titanium-Kiwi build"
git config --global user.email "build@example.invalid"

mkdir -p "$TITANIUM_DIR/chromium/src/out/Default"
cd "$TITANIUM_DIR/chromium/src"
if [[ ! -d .git ]]; then git init; fi
if ! git remote get-url origin >/dev/null 2>&1; then
  git remote add origin https://chromium.googlesource.com/chromium/src.git
fi
git fetch --depth 1 origin "+refs/tags/$VERSION:refs/tags/$VERSION"
git checkout --detach --force "refs/tags/$VERSION"
test "$(git rev-parse HEAD)" = "$CHROMIUM_COMMIT"
cp "$TITANIUM_DIR/.gclient" ../.gclient

# Match the exclusions in the pinned Titanium build script exactly.
rm -f "$TITANIUM_DIR"/vanadium/patches/*trichrome-{apk-build-targets,browser-apk-targets}.patch
rm -f "$TITANIUM_DIR"/vanadium/patches/*{detailed,supported}-language*.patch
rm -f "$TITANIUM_DIR"/vanadium/patches/*javascript-optimizer-{site-setting,settings-UI}.patch
rm -f "$TITANIUM_DIR"/vanadium/patches/*component-updates.patch
rm -f "$TITANIUM_DIR"/vanadium/patches/*{pdf,PDF,for-content-public,toolbar-button,configs-from-config-app,new-tab-card,predictive-back*}*.patch

replace_tree() {
  local directory="$1" old="$2" new="$3"
  find "$directory" -type f -exec sed -i "s@${old}@${new}@g" {} +
}
replace_tree "$TITANIUM_DIR/vanadium/patches" VANADIUM TITANIUM
replace_tree "$TITANIUM_DIR/vanadium/patches" Vanadium Titanium
replace_tree "$TITANIUM_DIR/vanadium/patches" vanadium titanium
git -c user.name="Titanium-Kiwi build" -c user.email="build@example.invalid" \
  am --whitespace=nowarn --keep-non-patch "$TITANIUM_DIR"/vanadium/patches/*.patch

gclient sync -D --no-history --nohooks
gclient runhooks
./build/install-build-deps.sh --no-prompt

export SCRIPT_DIR="$TITANIUM_DIR"
version_lt() {
  [[ "$1" != "$2" ]] && [[ "$(printf '%s\n%s\n' "$1" "$2" | sort -V | head -n1)" == "$1" ]]
}
source "$TITANIUM_DIR/patch.sh"
PATCH_ARGS=()
if [[ "$PATCH_MODE" == "best-effort" ]]; then
  PATCH_ARGS+=(--best-effort --report "${KIWI_PATCH_REPORT:-$KIT_ROOT/output/kiwi-patch-report.md}")
elif [[ "$PATCH_MODE" != "strict" ]]; then
  echo "Unknown KIWI_PATCH_MODE: $PATCH_MODE" >&2
  exit 2
fi
python3 "$KIT_ROOT/kiwi_port/apply.py" "$PWD" "${PATCH_ARGS[@]}"

python3 - <<'PY'
from pathlib import Path
p = Path("chrome/browser/password_manager/android/java/src/org/chromium/chrome/browser/password_manager/PasswordManagerHelper.java")
s = p.read_text()
start = s.index("    void launchPasswordCheckup(")
end = s.index("        PasswordCheckupClientHelper checkupClient;", start)
block = s[start:end]
old = "                    context, referrer);"
new = """                    context,
                    referrer == PasswordCheckReferrer.SAFETY_CHECK
                            ? ManagePasswordsReferrer.SAFETY_CHECK
                            : referrer == PasswordCheckReferrer.LEAK_DIALOG
                                            || referrer == PasswordCheckReferrer.PHISHED_WARNING_DIALOG
                                    ? ManagePasswordsReferrer.PASSWORD_BREACH_DIALOG
                                    : ManagePasswordsReferrer.CHROME_SETTINGS);"""
if block.count(old) != 1:
    raise SystemExit("CONFLICT password-check-referrer: " + str(p))
p.write_text(s[:start] + block.replace(old, new) + s[end:])
PY

cp "$TITANIUM_DIR/args.gn" out/Default/args.gn
python3 - <<'PY'
from pathlib import Path
p = Path("out/Default/args.gn")
s = p.read_text(encoding="utf-8")
s = s.replace('target_cpu = "arm"', 'target_cpu = "arm64"')
s = s.replace(
    'chrome_public_manifest_package = "io.github.jqssun.helium"',
    'chrome_public_manifest_package = "io.github.nojirokaimo.titaniumkiwi"',
)
# Keep Titanium's release/official optimization. The old validation build flipped
# these to debug/non-official and inflated libchrome.so by ~86 MB. Save CI time
# without changing generated release code by dropping external symbols/linker map.
s = s.replace('symbol_level = 1', 'symbol_level = 0')
s = s.replace('generate_linker_map = true', 'generate_linker_map = false')
s += '\nblink_symbol_level = 0\nv8_symbol_level = 0\ntreat_warnings_as_errors = false\n'
if 'is_debug = false' not in s or 'is_official_build = true' not in s:
    raise SystemExit('Titanium release optimization flags are missing from args.gn')
p.write_text(s, encoding="utf-8")
PY

gn gen out/Default
fi

if [[ "$PHASE" == "prepare" ]]; then
  exit 0
fi

export PATH="$BUILD_ROOT/depot_tools:$PATH"
cd "$TITANIUM_DIR/chromium/src"

BUILD_STATUS=0
BUILD_COMMAND=(autoninja -C out/Default chrome_public_apk)
if [[ "${KIWI_INCREMENTAL_NINJA:-false}" == "true" ]]; then
  BUILD_COMMAND=(env INVOKED_BY_BUILD_SERVER=1 /usr/bin/ninja -C out/Default -j "${KIWI_NINJA_JOBS:-4}" chrome_public_apk)
fi
printf 'Build command:'
printf ' %q' "${BUILD_COMMAND[@]}"
printf '\n'
if [[ -n "${KIWI_BUILD_BUDGET_MINUTES:-}" ]]; then
  timeout --signal=INT --kill-after=5m \
    "${KIWI_BUILD_BUDGET_MINUTES}m" \
    "${BUILD_COMMAND[@]}" || BUILD_STATUS=$?
else
  "${BUILD_COMMAND[@]}" || BUILD_STATUS=$?
fi

if [[ "$BUILD_STATUS" -ne 0 && "$BUILD_STATUS" -ne 124 && "$BUILD_STATUS" -ne 130 && "$BUILD_STATUS" -ne 137 ]]; then
  exit "$BUILD_STATUS"
fi
if [[ "$BUILD_STATUS" -ne 0 ]]; then
  echo "Build interrupted; preserve checkpoint, do not publish a cached APK."
  exit 0
fi

APK="out/Default/apks/ChromePublic.apk"
if [[ ! -f "$APK" ]]; then
  APK=""
fi
if [[ -z "$APK" ]]; then
  if [[ "$BUILD_STATUS" -eq 124 || "$BUILD_STATUS" -eq 130 || "$BUILD_STATUS" -eq 137 ]]; then
    echo "Build budget reached; out/Default is ready for the next checkpoint stage."
    exit 0
  fi
  echo "APK was not produced (autoninja status: $BUILD_STATUS)." >&2
  exit 1
fi
if [[ -f "$KIT_ROOT/output/incremental-build-start-ns" ]]; then
  BUILD_START_NS="$(<"$KIT_ROOT/output/incremental-build-start-ns")"
  APK_MTIME_NS="$(python3 - "$APK" <<'PY'
import os
import sys
print(os.stat(sys.argv[1]).st_mtime_ns)
PY
)"
  if (( APK_MTIME_NS < BUILD_START_NS )); then
    echo "Ninja succeeded but ChromePublic.apk predates this incremental build; refusing stale APK." >&2
    exit 1
  fi
fi

mkdir -p "$KIT_ROOT/output"
OUTPUT_APK="$KIT_ROOT/output/Titanium-Kiwi-core-$VERSION-arm64-v8a.apk"
cp "$APK" "$OUTPUT_APK"

# Upstream Titanium 153 arm64 is 324,215,805 bytes. Kiwi UI patches should only
# add a small amount; reject a debug-style ~400 MB regression automatically.
python3 - "$OUTPUT_APK" <<'PY'
import os
import sys
import zipfile
apk = sys.argv[1]
size = os.path.getsize(apk)
print(f"Final APK size: {size:,} bytes ({size / 1_000_000:.1f} MB)")
with zipfile.ZipFile(apk) as z:
    print("Largest APK entries:")
    for info in sorted(z.infolist(), key=lambda x: x.file_size, reverse=True)[:12]:
        print(f"  {info.file_size / 1_000_000:7.1f} MB  {info.filename}")
if size > 360_000_000:
    raise SystemExit(
        f"APK size regression: {size:,} bytes exceeds 360,000,000-byte release guard"
    )
PY

APKSIGNER="$(find third_party/android_sdk/public/build-tools -type f -name apksigner | sort | tail -n 1)"
test -x "$APKSIGNER"
"$APKSIGNER" verify --verbose "$OUTPUT_APK"
sha256sum "$OUTPUT_APK" > "$KIT_ROOT/output/SHA256SUMS.txt"
touch "$KIT_ROOT/output/BUILD_COMPLETE"
