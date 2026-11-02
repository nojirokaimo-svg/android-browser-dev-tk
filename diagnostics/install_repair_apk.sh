#!/usr/bin/env bash
set -Eeuo pipefail
mkdir -p verification-output
old=artifacts/73/Titanium-Kiwi-core-156.0.8078.73-arm64-v8a.apk
new=artifacts/repair/Titanium-Kiwi-core-156.0.8078.79-arm64-v8a.apk
printf '%s  %s\n' 684b57895cd9b2fa30cf00e75e1b39a2b7c6b3c3ea609b6b8a5c97c9eecc8c00 "$old" | sha256sum -c -
adb wait-for-device
adb shell getprop ro.build.version.sdk > verification-output/android-api.txt
adb shell getprop ro.product.cpu.abilist > verification-output/android-abis.txt
adb logcat -c
set +e
adb install --no-streaming "$old" > verification-output/install-73.txt 2>&1
old_status=$?
adb install --no-streaming -r "$new" > verification-output/update-repair.txt 2>&1
new_status=$?
set -e
adb logcat -d -v threadtime > verification-output/package-install-logcat.txt
cat verification-output/install-73.txt verification-output/update-repair.txt
(( old_status == 0 && new_status == 0 ))
grep -qx Success verification-output/install-73.txt
grep -qx Success verification-output/update-repair.txt

# Test returning to the user's .73 without adb's downgrade override.
adb install --no-streaming -r "$old" > verification-output/return-to-73.txt 2>&1
cat verification-output/return-to-73.txt
grep -qx Success verification-output/return-to-73.txt
# Leave the disposable test profile on the repaired version.
adb install --no-streaming -r "$new" > verification-output/reapply-repair.txt 2>&1
cat verification-output/reapply-repair.txt
grep -qx Success verification-output/reapply-repair.txt
