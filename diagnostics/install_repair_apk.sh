#!/usr/bin/env bash
set -Eeuo pipefail
mkdir -p verification-output
old=artifacts/previous/Titanium-Kiwi-core-157.0.8103.50-arm64-v8a.apk
new=artifacts/repair/Titanium-Kiwi-core-157.0.8103.78-arm64-v8a.apk
printf '%s  %s\n' 601a74984a84b7e654da9ffcc36dace7dfe579e0a7f464cd2d9968b171f079c3 "$old" | sha256sum -c -
adb wait-for-device
adb shell getprop ro.build.version.sdk > verification-output/android-api.txt
adb shell getprop ro.product.cpu.abilist > verification-output/android-abis.txt
adb logcat -c
set +e
adb install --no-streaming "$old" > verification-output/install-previous.txt 2>&1
old_status=$?
adb install --no-streaming -r "$new" > verification-output/update-repair.txt 2>&1
new_status=$?
set -e
adb logcat -d -v threadtime > verification-output/package-install-logcat.txt
cat verification-output/install-previous.txt verification-output/update-repair.txt
(( old_status == 0 && new_status == 0 ))
grep -qx Success verification-output/install-previous.txt
grep -qx Success verification-output/update-repair.txt

# Test returning to the previous .50 release without adb's downgrade override.
adb install --no-streaming -r "$old" > verification-output/return-to-previous.txt 2>&1
cat verification-output/return-to-previous.txt
grep -qx Success verification-output/return-to-previous.txt
# Leave the disposable test profile on the repaired version.
adb install --no-streaming -r "$new" > verification-output/reapply-repair.txt 2>&1
cat verification-output/reapply-repair.txt
grep -qx Success verification-output/reapply-repair.txt
