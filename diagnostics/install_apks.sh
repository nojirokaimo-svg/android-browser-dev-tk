#!/usr/bin/env bash
set -Eeuo pipefail
mkdir -p diagnostics-output
adb wait-for-device
adb shell getprop ro.product.cpu.abilist | tee diagnostics-output/abis.txt
adb shell getprop ro.dalvik.vm.native.bridge | tee diagnostics-output/native-bridge.txt
adb logcat -c
old=$(find artifacts/73 -name '*.apk' -type f)
new=$(find artifacts/79 -name '*.apk' -type f)
[[ -n "$old" && -n "$new" ]]
printf '%s  %s\n' 684b57895cd9b2fa30cf00e75e1b39a2b7c6b3c3ea609b6b8a5c97c9eecc8c00 "$old" | sha256sum -c -
printf '%s  %s\n' 706a7faa285d16cc1b6dbc1ecd85007e4c749fb22c1158393deea99f2cf985e1 "$new" | sha256sum -c -
set +e
adb install --no-streaming "$old" >diagnostics-output/install-73.txt 2>&1
status_old=$?
adb install --no-streaming -r "$new" >diagnostics-output/install-79.txt 2>&1
status_new=$?
set -e
adb logcat -d -v threadtime >diagnostics-output/package-installer-logcat.txt
cat diagnostics-output/install-73.txt diagnostics-output/install-79.txt
python3 - "$status_old" "$status_new" <<'PY'
import json,sys
from pathlib import Path
Path('diagnostics-output/install-result.json').write_text(json.dumps({'install73_exit':int(sys.argv[1]),'update79_exit':int(sys.argv[2]),'physical_device_verified':False},indent=2)+'\n')
PY
# Never call a matching-ABI failure an APK parsing result or a successful install.
if (( status_old != 0 || status_new != 0 )); then exit 1; fi
