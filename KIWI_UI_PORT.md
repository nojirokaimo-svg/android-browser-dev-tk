# Titanium-Kiwi UI port

Titanium `154.0.8037.92`へKiwi系UI・拡張機能・移行/バックアップ機能を固定パッチとして移植する構成です。

## 2026-10-02 — Titanium 154 final APK (Build #172)

Build #172 (commit `1a40491d584ff313f1fa36aa34f9131f9877c65d`, run `36835438451`) completed the Titanium `154.0.8037.92` arm64 APK from exact incremental checkpoints without a clean or cold build.

- Run: https://github.com/nojirokaimo-svg/android-browser-dev-tk/actions/runs/36835438451
- APK artifact: https://github.com/nojirokaimo-svg/android-browser-dev-tk/actions/runs/36835438451/artifacts/11194275751
- Artifact ZIP SHA-256: `f128448ffd20872b8a960bd5a45b63821191b0c047112ed710f2732e828ff529`
- APK SHA-256: `a23d6ebcd533862985e45ff6d13b1ae0b6d54684024daf7b1fb62384c1627932`
- Android APK Signature Scheme v2: verified `true`
- Completed exact cache: `kiwi-incremental-154-1a40491d584ff313f1fa36aa34f9131f9877c65d-continue-2`
- Source audit: all 99 before/after hashes match the manifest; all 25 ordered feature patch checksums and file lists match.
- Verification: 39 CI tests passed; the fresh local suite ran 45 tests with 44 passed and only the real-Ninja fixture skipped because Ninja is unavailable locally. Strict apply/idempotence and conflict/best-effort diagnostics are covered and passed.
- Removed features remain removed: ultra power-saving patch 220 and Hameln-specific injection patch 225 are not in the 25-patch series.

The APK was not tested on a physical device, so runtime/UI behavior is not claimed as device-verified.

## 固定ソース

- Titanium: `dd8d8a969fb6af762a3c2445ff455f7e48626993`
- Vanadium: `826316da0994ebd78601a86ba5c0cb34b46ba32d`
- Chromium: `334b65d254ccc35df4fca82706d1753227b01039` (`154.0.8037.92`)

## 保持している範囲

- Kiwi UI、拡張機能、移行、手動フルバックアップ、ローカル認証情報保存
- コピーしたリンク候補、元の選択タブ維持、既定で非表示のタブ検索
- ページ・カード・メニューの3種類の独立した暗色背景
- strictな99ファイルbefore/afterハッシュ検証
- 順序付き25機能パッチ、checksum/file-list検証、再適用idempotence、競合時の機能名・対象ファイル診断

超省電力モード（旧patch 220）とHameln固有注入（旧patch 225）は削除済みで、復活させません。

## 再ビルド

完成キャッシュ `kiwi-incremental-154-1a40491d584ff313f1fa36aa34f9131f9877c65d-continue-2` をexact restoreし、cache miss時は停止します。cold build、`out/Default`削除、`gn clean`、古い/空キャッシュへのfallbackは禁止です。
