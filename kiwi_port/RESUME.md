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

## 2026-10-01 — Build #164 preparation failure and exact-source correction

Build #164 (`c2d3d8e0d1402848d7d541f44f0602199fe8dc30`, run `36801569093`) restored the exact completed #163 cache successfully, then stopped before compilation because two pre-apply manifest hashes differed from the actual runner source. The actual `SharedPrefsUtils.java` uses final default fields and constructor delegation; `theme_preferences.xml` has no final newline. The previous local subset reconstruction did not match these bytes.

The source audit artifact `11135983527` (ZIP SHA-256 `4c4cf1bc9b6b7f573d1c00d6c6be311abbcbd7e419bbd2526269cca776468847`) contains the actual 99-file post-Titanium baseline. The preference registry, Night mode and tab-switcher patches are re-serialized against that baseline, preserving upstream constructor changes. Both before hashes and the resulting preference-helper after hash are measured from the actual sources. Strict pre-apply verification remains enabled. All 25 patches and final 99 hashes are verified against the downloaded runner baseline, including repeat application.

No Ninja compilation ran in #164 and no partial cache was saved. The unchanged exact #163 cache remains the initial restore key for the corrected build; no cache cleanup, overwrite or cold fallback is allowed.

# Current implementation checkpoint

## 2026-10-01: Titanium 154 update

| Upstream | Pinned revision |
|---|---|
| Titanium v154.0.8037.92 | `dd8d8a969fb6af762a3c2445ff455f7e48626993` |
| Vanadium | `826316da0994ebd78601a86ba5c0cb34b46ba32d` |
| Chromium 154.0.8037.92 | `334b65d254ccc35df4fca82706d1753227b01039` |

The unused extra power-saving feature (220) is removed: no menu toggle,
settings switches, renderer limit, reduced-motion override, or Prerender2
suppression is installed by the Kiwi series. Existing saved values are inert.
The independent dark page/card/menu colors, default-hidden tab search,
copied-link row, extensions and backups remain in the 25-feature series.
The Hameln-specific injection remains withdrawn.

All 25 patches were rebased in order against the M154 post-Titanium subset.
The manifest now measures every patch-owned file: 99 before/after hashes,
including ChromeTabbedActivity.java. Strict application must match these
hashes again in the actual runner preparation; unknown drift stops before
compiling. Best-effort mode still identifies feature/file conflicts and applies
independent clean hunks. Full before/after source archives and hashes are uploaded.
Local verification: 38 Python tests, complete patch integrity, strict ordered
reapplication, all 99 final hashes, and idempotence passed. APK compilation
and device behavior remain pending.

The first job restores only Build #163's completed immutable checkpoint:
`kiwi-incremental-153-780689451ec17d83ff74d72a733205b5644fa279-stage-11`.
Its save was confirmed in job 108056714484 on 2026-09-25 at 12:15:56 UTC.
The source transition accepts only the exact prior M153 identity, preserves
Ninja history/objects/generated outputs, and regenerates GN for M154 using
Ninja (`use_siso=false`). Cache miss stops immediately. No deletion, clean,
cache overwrite, or older/empty fallback is permitted.

GitHub-hosted jobs have a six-hour limit. Jobs use 350 minutes with a
maximum 270-minute compile budget; elapsed preparation reduces that budget
when necessary to reserve 45 minutes for shutdown, signing, cache save and
artifact upload. Continuation jobs run only when the APK is unfinished and
the preceding job succeeded in saving its exact checkpoint. Compiler failures
require diagnosis before a new resume, not blind retries or restarting from #163.
Final completion requires Android v2 signing, APK/artifact SHA-256, runner
source verification and updated handoff records. Device claims require device evidence.

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


## 2026-10-01 M154 checkpoint dependency correction

Build #169 stopped before compilation because the auxiliary_search turbine output is absent from `.ninja_deps`; the earlier path-prefix hypothesis was incorrect. Build #170 (`36820039153`) restored the exact #166 key and performed read-only diagnostics without source preparation, compilation, or cache save. Its artifact `11143495032` contains the actual Java depfile.

The old M153 edge is in `gen/chrome/browser/auxiliary_search/java__header.d`, whose SHA-256 is `dabfa69d4762becd172cd7117ed908123bf3d8cc61552f77e5f6a48382e05bec`. It lists `obj/chrome/browser/magic_stack/android/java.turbine.jar` as a dependency of `obj/chrome/browser/auxiliary_search/java.turbine.jar`. `.ninja_deps` SHA-256 from the exact cache is `5ed76c99344522dcc3f5bcf766ac6a3c8779d1f7308d30cd121a37d58fd20717`.

Resume from literal `kiwi-154-6df5931ce5664d898c599acac4bcb0ae005381a4-build`, with empty transition identity. The v3 adjustment runs immediately after exact restore, removes only the obsolete magic_stack token from that one text depfile, backs up the original as `.d.kiwi-m153-backup`, and ages the preserved turbine jar. `.ninja_deps`, `.ninja_log`, other outputs, and cached object contents are unchanged. The v3 marker prevents repeated adjustment.

Local verification: 44 tests passed (including real Ninja), 25 patch checksums passed, YAML parsed. A separate test using the exact downloaded depfile reproduced the cycle before correction and passed Ninja's dry-run after correction. This establishes the targeted checkpoint repair, not a completed APK or device behavior. Resume the normal core workflow and inspect its result before declaring completion.


### Build #171 compile checkpoint

Build #171 passed the dependency repair and compiled through step 20,981 of 63,777. It then exposed one M153 constructor argument left in patch 200: `createKiwiClipboardCandidate()` passed the removed integer between `serializedAnswerTemplate` and `fillIntoEdit`. The actual M154 signature was measured from source audit artifact `11143897964`; removing only that obsolete `0` gives `AutocompleteMatch.java` SHA-256 `0775efb9c35981b428d7d240859c0ee864cdbd1ec2a6210c7761640634ef6b89`. Patch 200 SHA-256 is `4153cb628c5163550dae58a4b3005a3726eb4035ddc3c0028b0aaa81fc3f32f9`.

The 17 GB compile state was saved successfully at 2026-10-01T07:25:25Z under literal key `kiwi-154-e6e4a72c3416e98a333664da572c1731c9871920-build`. Resume only from that key. Local verification after the fix: 45 tests pass, 25 checksums pass, strict application from the #171 actual before-source yields zero manifest mismatches, and a second strict application is idempotent. No final APK exists yet.
