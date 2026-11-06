#!/usr/bin/env bash
set -Eeuo pipefail
mkdir -p verification-output
old=artifacts/previous/Titanium-Kiwi-core-156.0.8078.79-arm64-v8a.apk
new=artifacts/repair/Titanium-Kiwi-core-157.0.8103.38-arm64-v8a.apk
printf '%s  %s\n' 8c09cf34d74fb7e2f9871600058faf9a0797d980ea0125e9ddce8a853ef4a8af "$old" | sha256sum -c -
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

# Test returning to the previous .79 release without adb's downgrade override.
adb install --no-streaming -r "$old" > verification-output/return-to-previous.txt 2>&1
cat verification-output/return-to-previous.txt
grep -qx Success verification-output/return-to-previous.txt
# Leave the disposable test profile on the repaired version.
adb install --no-streaming -r "$new" > verification-output/reapply-repair.txt 2>&1
cat verification-output/reapply-repair.txt
grep -qx Success verification-output/reapply-repair.txt
