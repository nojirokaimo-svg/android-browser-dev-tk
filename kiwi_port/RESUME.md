# Current implementation checkpoint

Chromium/Titanium 153.0.8010.36 release build completed successfully in GitHub
Actions run 59. Continue from this point; do not clean, delete out/Default, or
fall back to an older/empty cache.

Pinned upstream revisions:

- Titanium: `7584b534f6e1f9c29e8bb98df71d7610960a5db3`
- Vanadium: `02d87ad8e17aee77d0fea49d122349a5da87ed2e`
- Chromium: `507c6ee3e2f3b2ca0e660547e5b9ea4820c67f4c`
- Chromium version: `153.0.8010.36`

Completed build checkpoint:

- Run: https://github.com/nojirokaimo-svg/android-titanium-browser/actions/runs/34927670350
- Commit built: `b47e787dc7c2b9633624ebe996fd275155c340a1`
- APK: `Titanium-Kiwi-core-153.0.8010.36-arm64-v8a.apk`
- APK size: 323,925,692 bytes
- APK SHA-256: `be882080da3425092530858e59ab490c7e94ca82d93a6b116f24c9ebfda00fe9`
- libchrome.so: approximately 221.1 MB
- Android v2 signature verification passed.
- Completed incremental baseline:
  `kiwi-incremental-153-b47e787dc7c2b9633624ebe996fd275155c340a1-stage-3`

The workflow default is pinned to that exact completed M153 baseline. Exact cache
misses must fail immediately; no restore-key fallback is permitted. M152 caches
remain preserved but must never be used for M153.

Compiled feature series retained:

- Kiwi menu resources and application-menu actions
- compact Kiwi-style overflow menu and pure-black dark overflow background
- preference registry crash fix
- six Night mode presets, renderer contrast/grayscale/high-contrast paths
- runtime Night mode and renderer force-dark propagation
- mobile extensions manager layout
- pure-black dark status bar and full manual browser-state backup/restore
- selectable Kiwi-style tab switcher

Build configuration remains release optimized: `is_debug=false` and
`is_official_build=true`. APK size checks are warning-only and must not discard
an otherwise completed build, artifact, checksum, or incremental cache.

Remaining validation:

- Install and launch the M153 APK on an arm64 device.
- Verify all six Night mode presets, renderer output, high contrast, persistence,
  restart behavior, Settings, toolbar, overflow menu, extensions UI, and tabs.
- Verify backup/restore of tab state, downloads, history, and bookmarks.
- Run renderer regression tests not exercised by the APK target.
- Regenerate final feature patches, manifest, and series after device fixes.
- Test automatic reapplication onto a fresh upstream checkout, including
  feature/file-specific conflict reporting and partial application behavior.
- Document update, recovery, and patch-regeneration procedures in the README.
