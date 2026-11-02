#!/usr/bin/env bash
set -Eeuo pipefail
pkg=io.github.nojirokaimo.titaniumkiwi
adb root
adb wait-for-device
adb push diagnostics/extension-export-probe /data/local/tmp/export-probe
adb shell "mkdir -p /data/user/0/$pkg/files/export-probe; cp -R /data/local/tmp/export-probe/. /data/user/0/$pkg/files/export-probe/; chown -R \$(stat -c %u /data/user/0/$pkg):\$(stat -c %g /data/user/0/$pkg) /data/user/0/$pkg/files; restorecon -RF /data/user/0/$pkg/files"
adb shell "echo '_ --no-first-run --disable-fre --enable-logging=stderr --load-extension=/data/user/0/$pkg/files/export-probe --remote-debugging-port=9222 --remote-allow-origins=*' > /data/local/tmp/chrome-command-line"
adb shell am force-stop "$pkg"
adb shell am start -a android.intent.action.VIEW -d about:blank -p "$pkg"
python3 diagnostics/runtime_export.py || status=$?
adb logcat -d -v threadtime > diagnostics-output/runtime-logcat.txt
adb shell uiautomator dump /sdcard/runtime.xml || true
adb pull /sdcard/runtime.xml diagnostics-output/runtime-ui.xml || true
exit "${status:-0}"
