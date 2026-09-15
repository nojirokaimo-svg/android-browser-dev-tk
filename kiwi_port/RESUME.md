# Current implementation checkpoint

Chromium/Titanium 153.0.8010.36 release build completed successfully in GitHub
Actions run 63. Continue from this point; do not clean, delete out/Default, or
fall back to an older/empty cache.

Pinned upstream revisions:

- Titanium: `7584b534f6e1f9c29e8bb98df71d7610960a5db3`
- Vanadium: `02d87ad8e17aee77d0fea49d122349a5da87ed2e`
- Chromium: `507c6ee3e2f3b2ca0e660547e5b9ea4820c67f4c`
- Chromium version: `153.0.8010.36`

Completed build checkpoint:

- Run: https://github.com/nojirokaimo-svg/android-titanium-browser/actions/runs/34981587196
- Commit built: `e47338cc1af4bd7169b816fc67e2dd7375ec1305`
- APK: `Titanium-Kiwi-core-153.0.8010.36-arm64-v8a.apk`
- APK size: 323,924,934 bytes
- Artifact: https://github.com/nojirokaimo-svg/android-titanium-browser/actions/runs/34981587196/artifacts/10403173735
- Artifact ZIP SHA-256: `7de7665ef5b537aa1b2d83e477a8d1e92c5eba49f7bd83ead73fd6f857b07cdd`
- APK SHA-256: pending re-read of the artifact's `SHA256SUMS.txt` after a transient download 502.
- libchrome.so: approximately 221.1 MB
- Android v2 signature verification passed.
- Completed incremental baseline:
  `kiwi-incremental-153-e47338cc1af4bd7169b816fc67e2dd7375ec1305-stage-1`

The workflow default is pinned to that exact completed M153 baseline. Exact cache
misses must fail immediately; no restore-key fallback is permitted. M152 caches
remain preserved but must never be used for M153.

Compiled feature series retained:

- Kiwi menu resources and application-menu actions
- compact Kiwi-style overflow menu and `#202124` main/flyout dark surfaces
- preference registry crash fix
- six Night mode presets, renderer contrast/grayscale/high-contrast paths
- runtime Night mode and renderer force-dark propagation
- Kiwi-density mobile extensions manager layout with removal confirmation
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
