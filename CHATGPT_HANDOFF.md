# ChatGPT Project Handoff — Titanium Android Browser

Last updated: 2026-09-19 JST

## Start here

This file exists so a different ChatGPT account can resume the project after connecting the same GitHub account.

Repository: `nojirokaimo-svg/android-titanium-browser`
Visibility: **Private**
Fork status: **Standalone / detached from the original fork network**
Default branch: `main`
Active development branch: `codex/kiwi-ui-port`

When resuming, read this file first, then inspect the current HEAD of `codex/kiwi-ui-port` and the latest GitHub Actions runs before changing anything.

## Current active state

Last fully validated production-style build baseline:

`493b537ca243a603336738500ee9285bc5d7a5d5`

The active development branch has moved beyond that baseline. Always inspect the live `codex/kiwi-ui-port` HEAD and latest Actions run before resuming.

Normal build workflow:
`.github/workflows/kiwi-ui-build.yml`

Workflow name:
`Build Titanium-Kiwi core`

Successful post-detach normal build:
- Run ID: `35286122194`
- Run number: `136`
- Result: **success**
- stage-1 only; stages 2–5 skipped
- stage-1 wall time: about **40m 48s**
- APK artifact: `Titanium-Kiwi-core-153.0.8010.36-arm64`
- Artifact size: about 142.5 MB

## Pinned M153 baseline

Titanium:
`7584b534f6e1f9c29e8bb98df71d7610960a5db3`

Vanadium:
`02d87ad8e17aee77d0fea49d122349a5da87ed2e`

Chromium:
`507c6ee3e2f3b2ca0e660547e5b9ea4820c67f4c`

Chromium version:
`153.0.8010.36`

Exact reusable Actions Cache key:
`kiwi-incremental-153-fa41ecbd6f784035336214537d19505d52026713-stage-1`

This cache was lost when the repository left the public fork network, then successfully rebuilt from the durable Release baseline on the standalone repository.

Post-rehydration verification:
- Release -> 15 GB `out/Default` restore: success
- Save exact cache on default branch: success
- Exact restore from a different branch/new runner: success
- Private-repository exact restore: success
- Private cache verification Run ID: `35289611306`

## Durable GitHub Release backup

Release display title:
`Titanium M153 build baseline`

Important: the display title intentionally does **not** contain the word "Kiwi".

Internal release tag — DO NOT rename casually because recovery workflows refer to it:
`kiwi-baseline-m153-fa41ecbd6f784035336214537d19505d52026713`

Release target:
`105ca33deb792324e08d1f7fe87ea940a8582e93`

Assets:

1. `baseline-manifest.json`
   - size: 851 bytes
   - SHA-256: `ddd53dbcc844b70d82d38c0f34fe73e9bf9aca4252f1e8f5c2e6b3c9f907b04e`

2. `out-default.tar.zst.part-0000`
   - size: 1,900,000,000 bytes
   - SHA-256: `046ee77cd217aa07efbd718034a50645934342dc3ab037b1700afe19ecf60f0a`

3. `out-default.tar.zst.part-0001`
   - size: 863,690,414 bytes
   - SHA-256: `600bccec5001913278af4798e2a1646a9edb7a10f427340dc881abb8d24d449e`

Backup/recovery workflow:
`.github/workflows/kiwi-baseline-backup.yml`

Backup implementation:
`kiwi_port/baseline_backup.py`

Tests:
`kiwi_port/test_baseline_backup.py`

## Google Drive disaster-recovery copy

A second independent backup exists in Google Drive.

Folder:
`Titanium-Kiwi-baseline-M153`

The durable build-state backup was split for connector transfer into:
- `drive100-manifest.zip`
- `drive100-p0000-c00.zip` through `drive100-p0000-c18.zip`
- `drive100-p0001-c00.zip` through `drive100-p0001-c08.zip`

Verified at upload time:
- expected build-backup files: 29
- present: 29
- missing: 0
- extras: 0
- total: 2,763,696,226 bytes

The same Drive folder also contains:
`titanium-kiwi-source-bundle-before-detach.zip`

That ZIP contains a Git bundle of all branches/tags plus SHA/reference information, created before fork detachment.

## Disaster recovery order

If Actions Cache is missing:

1. Do **not** cold-build immediately.
2. Use the durable GitHub Release baseline first.
3. Restore the full `out/Default`.
4. Save it back into Actions Cache using the exact M153 cache key.
5. Verify that a fresh runner/branch can exact-restore it.
6. Only then run the normal `Build Titanium-Kiwi core` workflow.

The Release-only restore path has already been proven on a fresh runner and has successfully produced an APK.

## Critical build rules

These rules are important and came from repeated expensive failures:

- **Never clean `out/Default`.**
- **Never delete or overwrite the newest known-good build cache.**
- **Never silently fall back to an old or empty cache.**
- Exact cache miss should fail fast rather than start an accidental 10+ hour cold build.
- Preserve `.ninja_log`, `build.ninja`, `args.gn`, generated outputs, and source identity.
- Reuse the successful M153 baseline for normal small Kiwi/Titanium changes.
- Small changes should normally return to roughly the ~40-minute incremental-build range.
- Major Chromium version changes can require a new multi-hour baseline.
- Do not disable `StrictPreferenceKeyChecker` as a workaround.
- Do not use `is_debug=false` to hide preference registry errors.
- Fix preference keys through the proper registry mechanism.
- Do not perform `clean` during Night mode/UI work.

## Current UI / feature priorities

Primary goal: keep modern Titanium/Chromium while restoring useful old Kiwi-style Android behavior.

Outstanding/important areas include:
- Extension settings page should stay dark in dark mode.
- General browser Settings should use a near-black old-Kiwi-like palette rather than gray.
- Tab switcher should keep its layout but use Kiwi-like black background/cards/plus button.
- New-tab/empty-tab/omnibox-focus surfaces should be pure or near black in OLED mode.
- Six Night mode variants and persistence need continued verification.
- Extension ZIP/CRX loading belongs on the Extensions settings page.
- Kiwi -> Titanium extension migration has previously produced `Unsupported migration format`; migration needs formal compatibility rather than a generic importer.
- Passkey and saved-password behavior still needs attention.
- Preference registry fixes must be formal Chromium-compatible fixes.

Historical launch crash to remember:
`KnownPreferenceKeyRegistries.onRegistryUsed -> StrictPreferenceKeyChecker.checkIsKeyInUse -> SharedPreferencesManager.readBoolean -> SharedPrefsUtils$BoolSharedPref.get -> TabPreferencesUtils.shouldCloseTabsOnExit -> ChromeTabbedActivity.initializeState`

Likely area:
`close_tabs_on_exit` / `SharedPrefsExt.CLOSE_TABS_ON_EXIT` registry integration.

## Backup implementation proof already completed

Durable Release backup workflow:
- backup creation: success
- fresh runner with no Actions Cache: Release-only restore success
- restored baseline -> incremental Ninja build -> APK success
- Release -> fresh Actions Cache recreation: success
- fresh runner exact restore from recreated cache: success

Therefore the backup is not only theoretical; the recovery path has been exercised.

## Repository privacy transition

Sequence already completed:
1. durable GitHub Release backup created
2. Release-only recovery proven
3. Google Drive independent copy created
4. all-ref Git bundle copied to Drive
5. public fork detached successfully
6. Actions Cache loss after detach was detected
7. cache rebuilt from Release
8. cross-branch exact restore verified
9. normal ~40-minute build verified
10. repository made Private
11. Private-state exact cache restore verified

## Instructions for a new ChatGPT account

After connecting the same GitHub account and granting access to this private repository, tell ChatGPT:

> Read `CHATGPT_HANDOFF.md` in `nojirokaimo-svg/android-titanium-browser`, inspect the latest `codex/kiwi-ui-port` HEAD and latest GitHub Actions runs, and resume from the current state. Do not clean out/Default or replace the newest good cache.

If Google Drive recovery is needed, connect the same Google Drive account too and use the `Titanium-Kiwi-baseline-M153` folder.

Do not assume chat-memory context survived an account change; trust repository state, this handoff, current Actions results, and the durable backups.


## 2026-09-19 continuation — Kiwi omnibox/history behavior

A new feature-scoped patch was added:

`kiwi_port/patches/180-kiwi-omnibox-history.patch`

Feature id:

`kiwi-omnibox-history`

It implements the requested UI behavior on the pinned Chromium 153 tree:

- New tabs use the real top toolbar omnibox instead of Chromium's oversized centered fake search box.
- The fake NTP search-box view remains instantiated for Chromium plumbing but is `GONE`, so it does not reserve layout space.
- The History page informational banner such as “You may see the history from other apps that open links in Titanium.” is suppressed.
- Focusing the omnibox over an open page leaves the page visible under a translucent dark scrim instead of replacing the unused area with opaque black.
- Tapping the dimmed area below the actual suggestion rows calls `clearOmniboxFocus()`, cancelling URL input and returning to the page.

The patch is registered in `kiwi_port/patches/series.json`. It intentionally does not overlap the existing AMOLED patch files.

Validation rule for this change: inspect the newest `Build Titanium-Kiwi core` Actions run for the current branch HEAD. If it fails, fix only the reported patch/source/build error, preserve the exact M153 cache, and rerun by pushing the fix. Do not clean `out/Default`, do not replace the newest known-good baseline, and do not fall back to an empty/older cache.

The handoff intentionally does not hard-code the Actions run ID for this newest change, because updating this file again solely to record a run ID would itself trigger another expensive build. The latest Actions state is authoritative.


## 2026-09-19 Actions #137 failure and immediate fix

Run #137 (Run ID `35392744649`) failed during patch preparation, before compilation. The exact M153 `out/Default` checkpoint was restored unchanged afterward; the failure did not replace or clean the 15 GB cache.

Reported conflicts were limited to two hunks from `kiwi-omnibox-history`:
- `chrome/android/java/src/org/chromium/chrome/browser/ntp/NewTabPage.java`
- `chrome/browser/ui/android/omnibox/java/src/org/chromium/chrome/browser/omnibox/suggestions/SuggestionListViewBinder.java`

`kiwi_port/apply.py` now contains narrow M153 context-drift repairs for exactly those two files. The NewTabPage repair replaces only the unique `isLocationBarShownInNtp()` method body; the suggestion-list repair replaces only the unique phone-container opaque background line. Unknown drift still remains a hard conflict.

At the same time, the long-press web link context menu was widened slightly: the non-flyout minimum width in `170-context-menu-shape.patch` changed from **320dp to 336dp**. Flyout submenu sizing remains unchanged.

After this fix, validate the newest Actions run. Preserve the exact M153 cache and do not clean `out/Default`.
