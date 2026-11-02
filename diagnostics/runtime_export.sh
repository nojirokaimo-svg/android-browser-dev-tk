#!/usr/bin/env bash
set -Eeuo pipefail
pkg=io.github.nojirokaimo.titaniumkiwi
python3 diagnostics/fetch_vm.py
adb root
adb wait-for-device
if (( $(adb shell getprop ro.build.version.sdk | tr -d "\r") >= 33 )); then
  adb shell pm grant "$pkg" android.permission.POST_NOTIFICATIONS
fi
adb push diagnostics/extension-export-probe /data/local/tmp/export-probe
adb push diagnostics-output/vm2 /data/local/tmp/vm2
adb push diagnostics-output/vm3 /data/local/tmp/vm3
adb shell "mkdir -p /data/user/0/$pkg/files/export-probe; cp -R /data/local/tmp/export-probe/. /data/user/0/$pkg/files/export-probe/; cp -R /data/local/tmp/vm2 /data/user/0/$pkg/files/; cp -R /data/local/tmp/vm3 /data/user/0/$pkg/files/; chown -R \$(stat -c %u /data/user/0/$pkg):\$(stat -c %g /data/user/0/$pkg) /data/user/0/$pkg/files; restorecon -RF /data/user/0/$pkg/files"
adb shell "echo '_ --no-first-run --disable-fre --enable-logging=stderr --load-extension=/data/user/0/$pkg/files/export-probe,/data/user/0/$pkg/files/vm2,/data/user/0/$pkg/files/vm3 --remote-debugging-port=9222 --remote-allow-origins=*' > /data/local/tmp/chrome-command-line"
adb shell am force-stop "$pkg"
# The emulator's native ARM translator requires executable memory. This is a
# test-profile preference only, not a product default or the user's profile.
printf '%s\n' '{"profile":{"default_content_setting_values":{"javascript_jit":1,"javascript_optimizer":1}}}' > diagnostics-output/test-preferences.json
adb push diagnostics-output/test-preferences.json /data/local/tmp/test-preferences.json
adb shell "mkdir -p /data/user/0/$pkg/app_chrome/Default; cp /data/local/tmp/test-preferences.json /data/user/0/$pkg/app_chrome/Default/Preferences; chown -R \$(stat -c %u /data/user/0/$pkg):\$(stat -c %g /data/user/0/$pkg) /data/user/0/$pkg/app_chrome; restorecon -RF /data/user/0/$pkg/app_chrome"
adb shell am start -a android.intent.action.VIEW -d about:blank -p "$pkg"
python3 diagnostics/runtime_export.py || status=$?
adb logcat -d -v threadtime > diagnostics-output/runtime-logcat.txt
adb shell uiautomator dump /sdcard/runtime.xml || true
adb pull /sdcard/runtime.xml diagnostics-output/runtime-ui.xml || true
exit "${status:-0}"
