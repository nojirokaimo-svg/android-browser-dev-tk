# Current implementation checkpoint

The current target is Titanium `v153.0.8010.52` with upstream commits
`97a21b7a98e4446142a39bd38190023ebb34cd74` (Titanium),
`2aaf9dfc919e620564409f94beedaedca5301e81` (Vanadium), and
`78e5e45d4bb41035e17ea4da2cc257f496416ac9` (Chromium). Build #146 is
the most recent completed baseline, with exact immutable cache
`kiwi-incremental-153-8816925c2c1c0f2b96c723a4b5f7509c2816cb56-stage-1`.
See `CHATGPT_HANDOFF.md` for build status and unresolved validation. Later
sections document the historical 153.0.8010.36 checkpoint.

## Historical 153.0.8010.36 checkpoint

Chromium/Titanium 153.0.8010.36 release build, including native Kiwi migration
and extension-file loading, completed successfully in GitHub Actions run 87.
Do not use its old cache for current work.

Pinned upstream revisions:

- Titanium: `7584b534f6e1f9c29e8bb98df71d7610960a5db3`
- Vanadium: `02d87ad8e17aee77d0fea49d122349a5da87ed2e`
- Chromium: `507c6ee3e2f3b2ca0e660547e5b9ea4820c67f4c`
- Chromium version: `153.0.8010.36`

Completed build checkpoint:

- Run: https://github.com/nojirokaimo-svg/android-titanium-browser/actions/runs/35112848810
- Commit built: `3fefd81c80ff80f5dadee212aabcc4d98329b09c`
- APK: `Titanium-Kiwi-core-153.0.8010.36-arm64-v8a.apk`
- APK size: 324,012,949 bytes
- Artifact: https://github.com/nojirokaimo-svg/android-titanium-browser/actions/runs/35112848810/artifacts/10455408574
- APK SHA-256: `154917e8c30f4d673185aa85c60676ca856b8651e0afcedcacf486dd4209cdab`
- libchrome.so: approximately 221.1 MB
- Android v2 signature verification passed.
- Completed incremental baseline:
  `kiwi-incremental-153-3fefd81c80ff80f5dadee212aabcc4d98329b09c-stage-1`

That was the workflow default at this historical checkpoint; the active default
is now the exact Build #146 cache listed above.
Exact cache misses fail immediately; no restore-key fallback is permitted.

Compiled feature series retained:

- Kiwi menu resources, compact `#202124` overflow/flyout surfaces, and extension actions
- formal preference registry startup fix
- six Night mode presets and runtime renderer contrast/grayscale/high-contrast propagation
- pure-black AMOLED system bar, toolbar, omnibox, new-tab and search surfaces
- responsive Chromium extension manager layout and its standard removal confirmation
- selectable seven-mode Kiwi tab switcher
- full manual browser-state backup/restore
- native “Kiwi Browserから移行” flow
- native bookmark/tab/history import with original history visit timestamps
- Android SAF ZIP/CRX/unpacked extension loading

Patch/update validation:

- `verify_series.py` verifies all 12 feature patches, checksums and file lists.
- Reapplication tests cover strict atomic conflicts, idempotence, and best-effort
  partial application where independent features apply and only conflicting
  feature/file hunks remain as `.rej`.
- Fixed-M153 build applied the complete series and produced the signed APK.
- The upstream update workflow reuses the same five-stage checkpoint/cache action
  and emits feature/file-specific conflict reports.

Remaining device validation:

- Install and launch the run-87 APK on arm64.
- Exercise the Kiwi migration picker with a real Kiwi export and confirm original
  history timestamps, bookmarks and tabs.
- Load one ZIP, one CRX and one unpacked extension through SAF.
- Verify all six Night modes, all seven tab switchers, restart persistence,
  backup/restore, toolbar/status-bar transitions and extension UI.
- If a device-only defect is found, repair only its feature patch and resume from
  the exact completed cache above.
