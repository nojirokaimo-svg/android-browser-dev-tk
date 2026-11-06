#!/usr/bin/env bash
set -Eeuo pipefail
apk=artifacts/repair/Titanium-Kiwi-core-157.0.8103.38-arm64-v8a.apk
test -s "$apk"
mkdir -p verification-output
sdk="${ANDROID_HOME:?Android SDK is required}"
signer=$(find "$sdk/build-tools" -type f -name apksigner | sort -V | tail -n1)
badger=$(find "$sdk/build-tools" -type f -name aapt2 | sort -V | tail -n1)
test -x "$signer"
test -x "$badger"
"$signer" verify --verbose --print-certs "$apk" | tee verification-output/apk-signature.txt
grep -Fq 'Verified using v2 scheme (APK Signature Scheme v2): true' verification-output/apk-signature.txt
grep -Fq 'Number of signers: 1' verification-output/apk-signature.txt
grep -Eiq '^(Signer #1|V2 Signer):? certificate SHA-256 digest: 32a2fc74d731105859e5a85df16d95f102d85b22099b8064c5d8915c61dad1e0$' verification-output/apk-signature.txt
"$badger" dump badging "$apk" > verification-output/apk-badging.txt
python3 kiwi_port/pin_version_code.py --badging verification-output/apk-badging.txt --version 157.0.8103.38
sha256sum "$apk" | tee verification-output/SHA256SUMS.txt
python3 - "$apk" <<'PY'
import sys, zipfile
with zipfile.ZipFile(sys.argv[1]) as archive:
    bad = archive.testzip()
    if bad: raise SystemExit('Damaged APK entry: ' + bad)
PY
