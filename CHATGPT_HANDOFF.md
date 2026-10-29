Warning: truncated output (original token count: 16446)
Total output lines: 827

## 2026-10-29 — 156.0.8078.73 update and ZIP investigation in progress

The requested target is Titanium `c21bc5ac921fd9da96c108b40afff202f6e8b0ba`, Vanadium `8ae4b1b8b014862146ff9a09dc8c6fc6e9a0a978`, Chromium `2f9a11097447f226133bc1a31c787291a5eeab98` / `156.0.8078.73`. The workflow is temporarily audit-only: exact M156.47 completed checkpoint restore is required, compile and cache saves are disabled, and new source/patch compatibility must be checked before production. Historical manifest hashes still describe M156.47, not .73; do not treat them as current measurements. ZIP failure investigation/fix is in progress. No .73 APK has been produced or device-tested yet. Preserve all existing 25 features, settings, keys, APKs and checkpoint; no cold/clean build, fallback or cache replacement. Do not push or dispatch while audit is running.

## 2026-10-24 — Titanium-Kiwi 156.0.8078.47 signed arm64 APK completed

Production [Actions #39969342350](https://github.com/nojirokaimo-svg/android-browser-dev-tk/actions/runs/39969342350), source commit `9f808f2686105ca9a2e35078a8d23d737b9e90de`, **success at 2026-10-23T23:42:58Z** (2026-10-24 08:42:58 JST). The build and continue-1 jobs succeeded, require-apk succeeded, and continue-2/3/4 were correctly skipped. The exact checkpoint from #39944202267 was restored by build, and continue-1 restored build's exact immutable checkpoint; no cold/clean build, cache fallback, out/Default deletion or completed-cache overwrite was performed.

- [Signed APK artifact](https://github.com/nojirokaimo-svg/android-browser-dev-tk/actions/runs/39969342350/artifacts/12539097874): `Titanium-Kiwi-core-156.0.8078.47-arm64-v8a.apk`, **332,059,567 bytes**.
- **APK SHA-256:** `822689a01de2f54e787d1da8b0be7c836ff07c7f213a0784f0067e9d8971f457`. The downloaded APK independently matches the CI `SHA256SUMS.txt`.
- **Artifact ZIP SHA-256:** `9f1dab23fb8bf2ebc589b42aff69d7c99bd52004017406b4d13ca9dcb7e26223`, **146,337,384 bytes**; the downloaded ZIP bytes match the GitHub artifact digest.
- Android APK Signature Scheme **v2 verified** by CI `apksigner` and independent local verification: RSA-PKCS1-SHA256 signature over the v2 signed-data block verified, public key matches embedded certificate, and the entire protected-content SHA-256 digest across 319 chunks matches the signed digest. One signer; certificate SHA-256 **`32a2fc74d731105859e5a85df16d95f102d85b22099b8064c5d8915c61dad1e0`** (unchanged from M155).
- Independently decoded APK AndroidManifest.xml: package `io.github.nojirokaimo.titaniumkiwi`, versionName `156.0.8078.47`, versionCode `807804774`, minSdkVersion 29, targetSdkVersion 37. All seven native libraries are `arm64-v8a`.
- Final [source audit artifact](https://github.com/nojirokaimo-svg/android-browser-dev-tk/actions/runs/39969342350/artifacts/12526774906), ZIP SHA-256 `a87b9345fa64d3a4b2e23a71027176389514d691866b4e02bed44456ffbd1002`: all **99 after** hashes independently match actual tar member bytes; the **85 existing before** files match, and the other **14 before** entries correctly represent absent files (null). Both before/after audit mappings match the current GitHub `kiwi_port/manifest.json` across all 99 paths. Pins: Titanium `a3e4b86339a8db237d95d8e8e78248c8f6a1df68`, Vanadium `2ae4335402eabcc6e025f3400185fe25094d8521`, Chromium `1d17a2e2ee147bb7d6ae2ab6abdb3a2510c17775`.
- `kiwi_port/patches/series.json` registers **25 features**, with no 220 power-saving or 225 Hameln injection patch. Strict patch mode was used in both successful production stages; `verify_series.py` and selected **48-test suite** passed without failures in both stages. Saved settings/Photopea JIT exception and the existing Kiwi functionality remain included in the source port; **actual behavior on a physical device has not been tested**.
- Completed immutable cache saved by continue-1 at **2026-10-23T23:42:38.6550214Z**, job `120615034714`: **`kiwi-incremental-15647-9f808f2686105ca9a2e35078a8d23d737b9e90de-39969342350-1-continue-1`**. Earlier partial checkpoint saved by build: `kiwi-15647-9f808f2686105ca9a2e35078a8d23d737b9e90de-39969342350-1-build`. The previous M155.84 completed cache `kiwi-incremental-15584-acdde2860b6a4ee2f777920fbabaafa571cf909c-39044652662-1-continue-2` remains protected and was not altered.
- Main and update-upstream initial defaults now use the **literal M156 completed cache key**, empty transition identity and the verified M156 pins/tag (`v156.0.8078.47`). Exact cache misses must stop without fallback. These completion changes are committed with `[skip ci]`; **do not launch another APK build**. The signed APK artifact is scheduled by GitHub to expire 2026-11-06T23:42:38Z unless retained elsewhere.

Earlier M156 build failure records and the M155.84 completion entry below are historical. This M156 completion supersedes them as the current verified release.

## 2026-10-18 — Titanium 155.0.8059.84 signed APK completed

Build [#180](https://github.com/nojirokaimo-svg/android-browser-dev-tk/actions/runs/39044652662), commit `acdde2860b6a4ee2f777920fbabaafa571cf909c`, completed successfully at **2026-10-18T01:51:38Z**. Build and continue-1 stopped normally at their 270-minute Ninja budgets and saved immutable checkpoints; continue-2 finished and signed the APK. require-apk passed; continue-3/4 were skipped. No cold/clean build, output/cache deletion, overwrite or fallback was used.

- [APK artifact](https://github.com/nojirokaimo-svg/android-browser-dev-tk/actions/runs/39044652662/artifacts/12121033331): `Titanium-Kiwi-core-155.0.8059.84-arm64-v8a.apk`, **331,229,675 bytes**.
- APK SHA-256: `6da83515c7b61947a861b3b5026cce9d633e2851cdec3cc2ba6279fa5d184821`.
- Artifact ZIP SHA-256: `bc30dd842c7ac9299da334a2c91a881568cf595dd4513de7bb7ba5a9957df36c` (**145,819,907 bytes**); downloaded bytes match Actions' digest and the APK matches CI SHA256SUMS.
- Android APK Signature Scheme v2 passed CI apksigner and independent local cryptographic verification of the signature and complete protected-content digest. One signer; independently extracted certificate SHA-256 remains `32a2fc74d731105859e5a85df16d95f102d85b22099b8064c5d8915c61dad1e0`.
- Final [source audit artifact](https://github.com/nojirokaimo-svg/android-browser-dev-tk/actions/runs/39044652662/artifacts/12121111539), ZIP SHA-256 `98156ad5cdb2fc101d2e0a9c496de810344565f5966190ce1a3ceb8d0f83004f`: all **99 before and 99 after** hashes match actual tar bytes, runner reports and the manifest. Strict ordered 25-patch application to the final before archive yields all 99 after hashes; repeat application is idempotent. All 25 patch checksums are unchanged.
- Final local suite: **49 tests, 48 passed, 1 real-Ninja fixture skipped locally**; CI selected suite passed **43 tests without skips in each of all 3 production stages**, including real Ninja. Conflict feature/file diagnostics, independent clean hunks and atomic strict rejection are covered.
- Completed cache saved at **2026-10-18T01:51:17.0600666Z**, job `117549797275`: `kiwi-incremental-15584-acdde2860b6a4ee2f777920fbabaafa571cf909c-39044652662-1-continue-2`. Main/update-upstream initial defaults use this literal completed key, with empty transition identity; update-upstream defaults to `v155.0.8059.84`. Exact misses must still stop without fallback.

Pins: Titanium `e59e03dc83bc940d73cf29a7683286fca390b393`, Vanadium `20526e052e304b62cf3e80114b423934e2d1c540`, Chromium `5869fe313571d75152b77813cf0a4ee26a4e6df0`. All 25 features and saved settings, including the user's Photopea JavaScript JIT exception, are retained in the port; removed 220 power-saving and 225 Hameln injection remain removed. **This APK has not been tested on a physical device.** Completion documentation/default changes use `[skip ci]`; do not launch another APK build. Future user update requests resume completion monitoring.

Earlier launch/preparation/completion records below are historical and superseded by this completed .84 result.

## 2026-10-18 — Titanium 155.0.8059.84 actual sources verified; signed APK production

Target pins: Titanium `e59e03dc83bc940d73cf29a7683286fca390b393`, Vanadium `20526e052e304b62cf3e80114b423934e2d1c540`, Chromium `5869fe313571d75152b77813cf0a4ee26a4e6df0`, version `155.0.8059.84`.

[Audit Build #179](https://github.com/nojirokaimo-svg/android-browser-dev-tk/actions/runs/39039364741) succeeded 2026-10-17T14:25:41Z. The exact #178 completed checkpoint restored at 2026-10-17T14:08:00Z with cache-hit=true and matched key equal to the requested literal, and returned unchanged at 2026-10-17T14:25:35.8185924Z. No compilation or cache save ran in the audit.

Actual source artifact `12104226111`, ZIP SHA-256 `2332bdb37d389c42c2ba7126f0ffba65bf10bc53749bf8ae83917555349415a0`: all 25 features applied, zero conflicts. All 99 before/after hashes match actual archive bytes. Only `chrome/android/BUILD.gn` changed among tracked states relative to .79; its measured manifest hashes are updated. The actual .84 source still provides `chrome_public_apk`, so the existing APK build target remains valid. All 25 patch bytes/checksums are unchanged. Strict ordered reapplication to the actual before archive produces every measured after hash, and a second application is idempotent. Pending source verification is resolved; series baseline and provenance now identify the measured .84 revision. Local suite: 49 tests, 48 passed and only the real-Ninja fixture skipped locally (CI must run it); the audit selected 43-test suite passed without skips, including real Ninja. Conflict feature/file reporting, independent clean hunks and atomic strict rejection are tested.

The main workflow now restores normal 350-minute build + continue-1 through continue-4 and require-apk, strict mode. Initial restore remains literal `kiwi-incremental-15579-4d72ba1aa77606a63f6f57022c2416ffc27cc31b-38576318413-1-continue-2`. The initial source transition is `3f02ed2a05886655b875b21e7c273d8a54fe75ed:8a06a43a04074ab26fa4dc8f8aba915285d56839:a49e2e3d4addfd84e765b52afe230bedb81096db:validation`; continuation identities are empty. Partial/completed keys use immutable unique `kiwi-15584-<sha>-<run_id>-<attempt>-<stage>` / `kiwi-incremental-15584-<sha>-<run_id>-<attempt>-<stage>`. Ninja is capped at 270 minutes, with 45 minutes reserved after preparation. Only normal budget interruption automatically continues in the same run; no concurrent push/dispatch is allowed.

All 25 features and saved settings including Photopea JavaScript JIT exception are retained; removed 220/225 remain removed. No cold/clean build, output/cache deletion, overwrite/fallback or M153 depfile pruning is allowed. Build script mode remains 100755. This is a verified-source production launch checkpoint, **not a completed .84 APK or physical-device test claim**. Continue through actual APK/signature/hashes/tests, completed-cache save and [skip ci] final documentation/default updates. Earlier records below are historical.

## 2026-10-17 — Titanium 155.0.8059.84 update in preparation

Formal release v155.0.8059.84 was published 2026-10-16T14:08:32Z. Pins: Titanium `e59e03dc83bc940d73cf29a7683286fca390b393`, Vanadium `20526e052e304b62cf3e80114b423934e2d1c540`, Chromium `5869fe313571d75152b77813cf0a4ee26a4e6df0`.

The protected audit-only workflow restores literal completed #178 cache `kiwi-incremental-15579-4d72ba1aa77606a63f6f57022c2416ffc27cc31b-38576318413-1-continue-2`. Its save was confirmed again at 2026-10-15T02:43:08.2993435Z, job 116171785375. Current existence must be proved by the new exact restore logs. Require cache-hit=true AND matched-key=requested literal. An exact miss stops; no cold/clean build, out/Default deletion, gn clean, cache deletion/overwrite or fallback is permitted.

**This is preparation, not a completed .84 APK.** Compile and cache save are disabled in the audit stage; its restored checkpoint is protected and returned unchanged. The 99 hashes and series baseline remain their prior measured .79 values, explicitly recorded in pending_source_verification with compile_permitted=false. Actual .84 before/after tar/hash reports must be obtained, measured and strict ordered 25-patch reapplication/idempotence verified before compilation. Do not describe old measurements as new measurements.

After audit, continue without waiting for another user instruction: restore normal production from `ffc8df14cb0c359a1594b4e6c0d4d8762ddd7749`, update pins/version/unique keys, use the verified .79 source identity for the first transition and empty continuation transitions. Preserve 350-minute jobs, max 270-minute Ninja and 45-minute finalization reserve. Only normal budget interruption auto-continues. Do not push or start another workflow while production is active.

Preserve all 25 features and saved settings including Photopea JavaScript JIT exception; removed 220/225 stay removed. Final completion requires actual signed APK/ZIP hashes, v2 signature and same certificate, source/patch/tests verification, saved completed cache and [skip ci] documentation/default updates. Physical device behavior is not yet tested. The .79 completion below is historical, not .84 completion.

## 2026-10-15 — Titanium 155.0.8059.79 signed APK completed

Build [#178](https://github.com/nojirokaimo-svg/android-browser-dev-tk/actions/runs/38576318413), commit `4d72ba1aa77606a63f6f57022c2416ffc27cc31b`, completed successfully at **2026-10-15T02:43:29Z**. Build and continue-1 stopped normally at their Ninja budgets and saved exact immutable checkpoints; continue-2 finished all APK build steps and signed the APK. require-apk passed; continue-3/4 were skipped. No cold/clean build, output/cache deletion, overwrite or fallback was used.

- [APK artifact](https://github.com/nojirokaimo-svg/android-browser-dev-tk/actions/runs/38576318413/artifacts/11945395037): `Titanium-Kiwi-core-155.0.8059.79-arm64-v8a.apk`, **331,229,458 bytes**.
- APK SHA-256: `ee0eb88a5ff4613e39111e3bb3496c5f82f6fda3b93af658e57629eaa7cbadba`.
- Artifact ZIP SHA-256: `dbb0ac79869bcbf3cde6b31f84ce8edfbd1fd855bc088da35093a70671211518` (**145,812,217 bytes**); downloaded bytes match Actions' digest and the APK matches CI SHA256SUMS.
- Android APK Signature Scheme v2: CI apksigner passed, one signer. Independent verification of the downloaded APK passed its RSA signature, certificate/public-key match, and all protected-content digests. Certificate SHA-256 remains `32a2fc74d731105859e5a85df16d95f102d85b22099b8064c5d8915c61dad1e0`.
- Final [source audit artifact](https://github.com/nojirokaimo-svg/android-browser-dev-tk/actions/runs/38576318413/artifacts/11938428426), ZIP SHA-256 `ca2b2e4b9738156db2293d7001879842d1503f1b31dd72f443e89359738f5ea3`: all **99 before and 99 after** hashes match actual tar bytes and the manifest. Strict ordered reapplication of the 25 patches to the final runner's before archive yields all 99 after hashes; repeat application is idempotent.
- All 25 patch checksums/registrations/file lists verify; verification scripts, tests and all patches/series match production Git blobs. Fresh local discovery: **49 tests, 48 passed, 1 real-Ninja fixture skipped locally**. The real-Ninja fixture ran in CI: each of the three executed stages passed its selected **43-test suite, no skips**. Conflict tests cover feature/file reporting, independent clean hunks, atomic strict failure and unknown-source rejection.
- Completed cache saved at **2026-10-15T02:43:08.2993435Z**, job `116171785375`: `kiwi-incremental-15579-4d72ba1aa77606a63f6f57022c2416ffc27cc31b-38576318413-1-continue-2`. Main/update-upstream initial defaults now use this literal completed key, with empty transition identity; update-upstream defaults to `v155.0.8059.79`. Misses must still stop without fallback.

Pins: Titanium `3f02ed2a05886655b875b21e7c273d8a54fe75ed`, Vanadium `8a06a43a04074ab26fa4dc8f8aba915285d56839`, Chromium `a49e2e3d4addfd84e765b52afe230bedb81096db`. Existing 25 features and saved settings, including the user's Photopea JavaScript JIT exception, remain retained. Removed 220 power-saving and 225 Hameln injection remain removed. `build_kiwi_ui_arm64.sh` retains Git mode 100755. **This APK has not been tested on a physical device.**

This completion record and cache-default update use `[skip ci]`; no extra APK build is requested. Earlier launch/audit/checkpoint records below are historical and are not fallback cache candidates.

## 2026-10-14 — Titanium 155.0.8059.79 strict source verification; signed APK production

Target pins: Titanium `3f02ed2a05886655b875b21e7c273d8a54fe75ed`, Vanadium `8a06a43a04074ab26fa4dc8f8aba915285d56839`, Chromium `a49e2e3d4addfd84e765b52afe230bedb81096db`, version `155.0.8059.79`.

Build [#177](https://github.com/nojirokaimo-svg/android-browser-dev-tk/actions/runs/38572128056) completed its protected audit at 2026-10-14T13:50:29Z. Exact #176 completed cache `kiwi-incremental-155-afd27a5830a708ffa9e85d6d02c9fd6f32186bf7-38056044488-1-continue-3` restored at 2026-10-14T13:30:32Z with cache-hit=true and matched key equal to the requested key. It returned unchanged at 2026-10-14T13:50:20.8553284Z. No compilation or cache save occurred.

Actual source audit artifact `11899542218`, ZIP SHA-256 `1ebb8b1e4cc21eb6c84f6c98eba1201a34906b5c3156cb270140c40732fb99d6`, has 25 applied features and zero conflicts. Only `components/password_manager/core/browser/password_manager.cc` changed among the 99 tracked source states. All 99 before/after hashes match actual archive bytes. Existing 25 patch bytes/checksums remain valid; series baseline and manifest hashes are updated from actual 155.79 sources. Ordered strict reapplication from the actual before archive produces all 99 measured after hashes; a second run is idempotent. Pending verification is resolved. Local suite: 49 tests, 48 passed and 1 real-Ninja fixture skipped locally (CI required); conflict feature/file diagnostics and independent clean-hunk tests pass. Audit CI selected suite: 43 passed, no skips.

Main workflow now performs actual signed APK production with 350-minute build + continue-1 through continue-4 and require-apk. First restore uses the literal #176 completed key above; the first transition is `c433018f78b54dea5573f2789ed086022c7ec6f1:c1892f4db7a828b9fcbca9ab6a6898b0a7396fae:3ff7ac5a9224be9156d7f8703a06e22890aafd34:validation`, continuations have empty transition identity. Keys use immutable unique `kiwi-15579-<sha>-<run_id>-<attempt>-<stage>` and `kiwi-incremental-15579-<sha>-<run_id>-<attempt>-<stage>`. Ninja has at most 270 minutes with 45 minutes reserved after preparation for finalization/signing/save/upload. Only normal budget interruption auto-continues; failures require diagnosis.

All existing 25 features and saved settings, including Photopea JavaScript JIT exception, are retained; removed 220/225 remain removed. No M153 depfile pruning is enabled. No cold/clean build, output/cache deletion, overwrite or fallback. Continue monitoring the production run through actual APK, v2 signature/certificate, APK/ZIP hashes, completed cache and documentation verification. This is a source verification and production launch checkpoint, not APK completion or a physical-device claim.


## 2026-10-11 — Titanium 155.0.8059.39 signed APK completed

Build [#176](https://github.com/nojirokaimo-svg/android-browser-dev-tk/actions/runs/38056044488), commit `afd27a5830a708ffa9e85d6d02c9fd6f32186bf7`, completed successfully at 2026-10-11T05:17:01Z. The build restored only exact immutable checkpoints; build, continue-1 and continue-2 stopped normally at their Ninja budgets and saved their states, and continue-3 produced and signed the APK. No cold/clean build, output deletion, cache overwrite or fallback was used.

- [APK artifact](https://github.com/nojirokaimo-svg/android-browser-dev-tk/actions/runs/38056044488/artifacts/11692956311): `Titanium-Kiwi-core-155.0.8059.39-arm64-v8a.apk`, 331,233,395 bytes.
- APK SHA-256: `c325d3b88b366ac6e70d4cc7972432f19e9393fd587d080bb2f6668cf4da7365`.
- Artifact ZIP SHA-256: `6e5a047b5b2668cf6f2f26fb9c3e5389bb486fb1783c2f212721c2ca683b376a` (145,852,130 bytes); downloaded bytes match the Actions digest.
- Android APK Signature Scheme v2: CI `apksigner` verification passed with one signer. The certificate independently extracted from the downloaded APK has SHA-256 `32a2fc74d731105859e5a85df16d95f102d85b22099b8064c5d8915c61dad1e0`, matching the previous release certificate.
- Source verification combines Build #175's actual M155 before-source artifact `11669794988` (ZIP SHA-256 `7e90d238cbc3d398641efb908b188846e7f2ea8b2b797c9666d8ef4345e3c487`) with Build #176's final [after-source artifact](https://github.com/nojirokaimo-svg/android-browser-dev-tk/actions/runs/38056044488/artifacts/11691803591) (ZIP SHA-256 `418479418ca037a02f65bde975010141821181633e4947a013272fc23a0abf15`). All 99 before/after hashes match the manifest and archive bytes.
- All 25 patch byte checksums match `series.json`; registrations and file lists verify. Strict ordered reapplication, second-run idempotence and conflict diagnostics passed. Each executed CI stage passed its selected 43-test suite; preparation discovery had 49 local tests, with 48 passed and only the real-Ninja fixture skipped locally.
- Completed immutable cache saved at **2026-10-11T05:16:41.6695072Z**, job `114385791496`: `kiwi-incremental-155-afd27a5830a708ffa9e85d6d02c9fd6f32186bf7-38056044488-1-continue-3`. Main and update-upstream workflows now restore this literal completed key by default, with empty transition identity; update-upstream defaults to `v155.0.8059.39`.

Pins: Titanium `c433018f78b54dea5573f2789ed086022c7ec6f1`, Vanadium `c1892f4db7a828b9fcbca9ab6a6898b0a7396fae`, Chromium `3ff7ac5a9224be9156d7f8703a06e22890aafd34`. Existing 25 features, saved settings and the user's Photopea JavaScript JIT exception are retained; removed 220 power-saving and 225 Hameln injection remain removed. **This APK has not been tested on a physical device.**

## 2026-10-07 — 154.0.8037.126 signed APK completed

Build [#174](https://github.com/nojirokaimo-svg/android-browser-dev-tk/actions/runs/37564503375), commit `d37b865151e144bd2117984a84109ecdd8ba8c09`, completed successfully at 2026-10-07T14:02:09Z. The initial build and continue-1 preserved exact incremental checkpoints; continue-2 produced and signed the APK. No cold/clean build or output/cache deletion was performed.

- [APK artifact](https://github.com/nojirokaimo-svg/android-browser-dev-tk/actions/runs/37564503375/artifacts/11487127820): `Titanium-Kiwi-core-154.0.8037.126-arm64-v8a.apk`, 326,445,738 bytes.
- APK SHA-256: `ee174ad5f0db4a6a59641b50ded11cc9e3b9276a652298ca3ddeca00e535d076`.
- Artifact ZIP SHA-256: `540c53192d2fbd59a8360456e46d50f5181a6e913feb006ee5488f40a3120156` (143,722,096 bytes); downloaded bytes match the Actions digest.
- Android v2 signature: verified by CI apksigner and independently from the downloaded APK (RSA signature, certificate/public-key match, and full APK protected-content digest). Certificate SHA-256: `32a2fc74d731105859e5a85df16d95f102d85b22099b8064c5d8915c61dad1e0`.
- Final source audit artifact `11484109132`, ZIP SHA-256 `e2e111e7072016200993e45683747eb50c2843fdef3ad431503284c021eb4d11`: all 99 before/after hashes match the manifest and actual tar contents. Strict ordered 25-patch reapplication from the actual runner baseline succeeds; all final hashes match; second application is idempotent.
- All 25 patch checksums, registrations and file lists verify. CI's 39 relevant tests pass, including the real Ninja fixture. Local discovery: 45 tests, 44 passed and the real Ninja test skipped because Ninja is unavailable locally. Conflict diagnostics and independent clean-hunk application tests pass.
- Completed immutable cache saved at **2026-10-07T14:01:46.2023505Z**, job `112800237132`: `kiwi-incremental-154126-d37b865151e144bd2117984a84109ecdd8ba8c09-37564503375-1-continue-2`. Main and update-upstream workflows now restore this literal co…4446 tokens truncated…01c1333`,
ended with `require-apk` failing because the 90-minute stage-5 budget
expired before the APK completed. The stage-5 job itself succeeded and logged
`Cache saved with key: kiwi-153-d7d74a667baca929bea9be32749c8a7c301c1333-stage-5`
after preserving the 15 GB `out/Default`. Ninja reached about 4,976/16,863
edges during stage 5. This was a timed checkpoint, not a compile error.

The normal build workflow now resumes at stage 6 using that exact literal
stage-5 key. It does not repeat the upstream transition. Its composite action
rejects cache misses and checks `.ninja_log`, `.ninja_deps`, `build.ninja`,
and `args.gn` before continuation. Stages 7-10 use only new immutable
checkpoints created by their immediate predecessor. Do not derive stage-5
key from a new `${{ github.sha }}`, delete `out/Default`, invoke `gn clean`,
or fall back to old/empty cache. Verify the next workflow's stage-6 restore
log before claiming any resumed work or APK success.

## 2026-09-23: v153.0.8010.52 target and Android resume/omnibox fixes

- User baseline: Build #146 / commit `8816925c2c1c0f2b96c723a4b5f7509c2816cb56`.
- Target release: Titanium `97a21b7a98e4446142a39bd38190023ebb34cd74`,
  Vanadium `2aaf9dfc919e620564409f94beedaedca5301e81`,
  Chromium `78e5e45d4bb41035e17ea4da2cc257f496416ac9`
  (`153.0.8010.52`).
- Feature `190` hides the “Continue with this tab” Magic Stack card; feature
  `195` disables the inactive-startup NTP switch so the selected tab stays in
  front. It does not remove restored tabs.
- Feature `200` lets only Chromium's clipboard provider run on an empty
  Android NTP omnibox. Typed input and other pages retain ordinary suggestions;
  clipboard URL/text selection follows Chromium's existing navigation/search.
- The pinned build restores only exact Build #146 completed `out/Default` key
  `kiwi-incremental-153-8816925c2c1c0f2b96c723a4b5f7509c2816cb56-stage-1`;
  no clean build, cache deletion, overwrite or fallback. The upstream-update
  workflow now uses exact restore and source identity too.
- Build #147 on the earlier .47 attempt failed in stage 1; its job-log redirect
  returned BlobNotFound when retrieved. Do not claim .47 succeeded or use it as a
  checkpoint. Inspect current Actions run before further changes.
- `manifest.json` records the verified raw .52 omnibox hashes. The
  ChromeTabbedActivity hash after Titanium's upstream patch and features
  `020`/`195` required a prepared .52 checkout. This historical gap was
  resolved by the Build #160 source audit described below.

## 2026-09-23: v153.0.8010.47 transition from Build #146

- Baseline: Build #146 / `8816925c2c1c0f2b96c723a4b5f7509c2816cb56`.
- Target Titanium: `1c05bb4cb552b54bbcfc29ee6f208be4d8129b36`.
- Target Vanadium: `9919fca315ddb291441122f7c694bd1cb74be33e`.
- Target Chromium: `73934a44f61e6b3878d1943064c141a5a820f5f7`
  (`153.0.8010.47`).
- Stage 1 restores only the immutable Build #146 completed cache. The explicit
  source-identity transition preserves Ninja history, stamps the new source
  epoch, installs the prepared `.47` GN arguments, and regenerates GN metadata.
  Later stages retain that epoch so rebuilt outputs are reused and remaining
  old edges stay dirty. No clean, cache deletion, overwrite, or fallback is
  permitted.
- Feature patch `190-disable-single-tab-resumption.patch` disables only the
  Single Tab Magic Stack module that shows “Continue with this tab”. It does
  not delete restored tabs or alter `TabPersistentStore`.
- GitHub Actions is authoritative for APK, v2 signature, artifact hash,
  feature-patch reapplication, and final cache verification.

Last updated: 2026-09-19 JST

## Start here

This file exists so a different ChatGPT account can resume the project after connecting the same GitHub account.

Repository: `nojirokaimo-svg/android-browser-dev-tk` (renamed from `android-titanium-browser`)
Visibility: **Public**
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


## 2026-09-19 Actions #138 immediate integrity failure

Run #138 (Run ID `35394663024`) failed immediately in `Verify complete patch series integrity` before any cache restore or source preparation.

Cause: the checksum recorded for `170-context-menu-shape.patch` after changing the long-press context-menu minimum width from 320dp to 336dp was incorrect.

- incorrect recorded SHA-256: `dffb52e3490547b7b543c753ffde12550c9b97b5a715ef306b12fa0ea6fa2e00`
- actual patch SHA-256 reported by `verify_series.py`: `da3133bf83aafea1ccb0635fc44e390712e279470a2a4a9e905bb4c256ef483b`

`kiwi_port/patches/series.json` is corrected to the actual checksum. No `out/Default` cache was restored, modified, or cleaned in the failed run.


## 2026-09-19 Actions #139 immediate test failure

Run #139 (Run ID `35395133551`) passed patch checksum/registration verification, then failed in the repository unit tests before cache restore or source preparation.

Cause: `kiwi_port/test_night_mode_patch.py` still asserted the old context-menu width string `"320"` after the implementation was intentionally widened to `336dp`.

The assertion is updated to `"336"`. This is a test expectation sync only; no browser behavior was changed beyond the already-intended 336dp long-press link menu width.

No `out/Default` cache was restored, modified, or cleaned in Run #139.


## 2026-09-19 post-#140 UI follow-up

Run #140 (Run ID `35395385484`) succeeded for HEAD `116f9e32593e860cc1bb9b5eff192c919399980e`.

Device verification found two follow-up issues:

1. The History page still showed the card containing “You may see the history from other apps that open links in Titanium.” The earlier `isInfoHeaderAvailable() = false` change only suppressed info availability/menu state; the actual privacy/app-history header visibility is controlled separately through `getShouldShowPrivacyDisclaimersIfAvailable()`. The Kiwi patch now forces that getter false too, which removes the entire informational card/frame while leaving the separate **Clear browsing data** header untouched.
2. The working omnibox focus scrim was still too opaque. Phone scrim alpha changed from `179/255` to `140/255` so more of the current web page remains visible. Tapping the dimmed area still calls `clearOmniboxFocus()` and returns to the page.

The M153 context-drift repair for `SuggestionListViewBinder.java` was updated to use the same alpha 140 value. A repository unit test now checks the hidden history-card behavior marker, lighter scrim value, and dismiss callback.

Preserve the exact M153 cache; do not clean `out/Default`.


## 2026-09-19 Actions #141 integrity correction

Run #141 (Run ID `35400020438`) failed immediately in patch-series integrity verification because the recorded SHA-256 for `180-kiwi-omnibox-history.patch` did not match the exact checked-in bytes.

Actual SHA-256 reported by `verify_series.py`:
`18be9a0d6aee41a7f0ef32d1f4517d44200aa599791c2de315b89888ea9489d3`

`series.json` is corrected to that exact value. The run failed before cache restore, so `out/Default` was not touched.


## 2026-09-19 portable full-backup upgrade and lighter omnibox scrim

Run #142 (Run ID `35400060482`) succeeded for HEAD `5357c39d34c4a85aa32bf554d5be7422445efb74`.

A new feature patch `185-portable-full-backup.patch` adds a second backup mode:

- **Normal backup** keeps the existing raw Chromium profile/tab-state ZIP behavior.
- **Migration backup** additionally exports the regular-profile cookies and the password store credentials through Chromium APIs, serializes them, and encrypts the sensitive migration payload with a user passphrase using PBKDF2-HMAC-SHA256 (200,000 iterations) + AES-256-GCM.
- The portable sensitive payload is stored as `portable/sensitive-v1.bin` inside the ZIP; plaintext passwords/cookies are not written to the archive.
- During restore, the raw profile/tab state is staged as before. If a portable payload exists, the browser restarts into the backup activity, asks for the passphrase again, starts the regular profile, restores saved credentials into the local profile password store, and restores canonical cookies through the Chromium cookie service.
- The Chromium cookie restore helper is deliberately relaxed from OTR-only to permit this explicit user-initiated regular-profile restore path.
- Old format-1 backups without a portable payload remain accepted.

The omnibox focus scrim was also made slightly more transparent again: black alpha changed from **140/255 to 115/255**. The dim-area tap-to-dismiss behavior is unchanged.

Preserve the exact M153 build cache and do not clean `out/Default`.


## 2026-09-19 migration-backup startup crash fix

User reported that normal backup works but **Create migration backup** crashes. Root cause in `185-portable-full-backup.patch`: the standalone `KiwiFullBackupActivity` export path called `ProfileManager.getLastUsedRegularProfile()`, `PasswordStoreBridge`, and cookie JNI before Chromium native/profile startup. The restore path already performed synchronous startup, but export did not.

Fix: `createPortableBackup()` now calls `ChromeBrowserInitializer.getInstance().handleSynchronousStartup()` before obtaining the regular profile. No cache/build workflow changes; preserve the exact M153 `out/Default` cache and never clean/fall back.

## 2026-09-25: Build #160 and exact post-Titanium manifest audit

Build #158 (commit `29c99d3dd1b822a85022f4678f99d9595fe9ae83`)
was canceled at the user's request. The user's new base is the successful Build
#157 source commit `7c2a317e5db05e1b647eeba4e5010081906f0615`; the #158
startup switches and modified patches 050/205 are not used. Build #157's logs
show Android v2 signing and an exact completed out/Default checkpoint saved at
`kiwi-incremental-153-7c2a317e5db05e1b647eeba4e5010081906f0615-stage-11`.
Do not remove/overwrite that cache or fall back to a different key.

Two new feature patches 215 and 220 add independent page/card/popup dark colors
and a default-off extra power saving menu toggle below Night mode. Its three
settings independently request reduced web animations, limit renderers to two,
and disable Prerender2 only when the master toggle is on. CPU/battery benefits
are unmeasured and active JavaScript, extensions, and videos still run.

Build #160 (commit `e5b7f2f3c17d4066478dd07a23fe4a0a3c32bac9`, run
`36078045905`) restored that exact #157 key, applied 26 patches, compiled an
arm64 APK, verified Android v2 signing, and saved the immutable completed key
`kiwi-incremental-153-e5b7f2f3c17d4066478dd07a23fe4a0a3c32bac9-stage-11`.
Its APK SHA-256 is `b364caef95756437a01610615e366599391a7dfca16273fa17f7d60f52c10d29`.
The source audit artifact supplied the three previously unknown exact
post-Titanium hashes in `manifest.json`; the other 11 audited files matched.
The final build must restore #160's completed key exactly and run with
`KIWI_MANIFEST_AUDIT_ONLY=false`; it must not invalidate or overwrite it.

Reapplication safety was tightened for future Chromium major versions:
`NewTabPage.java`'s known context drift is repaired only when its original
method body matches exactly. The `chrome_java_resources.gni` two-anchor repair
is atomic. If upstream changes either pattern, the feature and affected file
remain visible as a conflict while independent features can still apply.
Continue updating manifest hashes against actual post-Titanium source after
any upstream version bump; a clean compile alone cannot establish UI behavior
or measured battery savings.

## 2026-09-25: Final Build #161

Build #161 (commit `08c395a3d081164839a2fbc4638d45abdf03e1d2`, run
`36093793201`) restored the exact completed Build #160 checkpoint, verified
26 feature patches and 27 tests, matched all 14 archived prepared-source files
against `manifest.json`, and produced an Android v2 signed arm64 APK. APK
SHA-256: `10ac551e86e57381a2fc15f10d6b5c89337855d6ff6aca99e4bdc6c78003965a`.
Artifact ZIP SHA-256: `3c46fd9a0747edfaf9a78adf91ae66a9f25e6cb156e016ab28b42a9590f69783`.
The completed immutable checkpoint is
`kiwi-incremental-153-08c395a3d081164839a2fbc4638d45abdf03e1d2-stage-11`.
Battery reduction and device-wide visual coverage are not measured; neither
an APK build nor a source hash proves either user-facing behavior.

## 2026-09-25: Roll back Hameln crash and default-enable extra power saving

The user reports that the site-specific Hameln behavior in Build #162 causes
the browser to crash when syosetu.org opens. The crash has no captured device
stack trace; do not assert the precise faulting Java method. Remove feature
`225-novel-dark-background.patch` entirely and restore Build #161's patch
series and pre-site ChromeTabbedActivity bytes. Build #161 remains the
previous signed APK the user can reinstall immediately.

The master extra power saving mode defaults to on only when no preference is
stored. Respect users' existing explicit on/off selections. Three individual
switches under Settings > Tabs and tab groups default to on: reduce motion,
renderer count of two, and no Prerender2. The menu, settings screen and startup
must use the same default. A restart applies changed flags. This does not cap
the active Photopea tab's CPU or GPU usage or establish measured battery saving.

The #161 source audit archive permits recomputing hashes after the four Java
default changes by reversing the old `220` patch and applying the new patch.
Restore the exact completed #161 cache literal shown above; do not clean,
delete, overwrite, or fall back from `out/Default` when making a new APK.
