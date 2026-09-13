# Current implementation checkpoint

The existing Night mode feature patch is a work in progress, not yet a validated
six-mode implementation. An incremental validation build is now authorized from
this checkpoint; never clean or fall back to an older/empty cache.

Completed in this continuation:

- Retained the existing preference registry crash fix and source provenance code.
- Compared the LAB formula with Kiwi commit
  `7be7edd1532148f22103cb4c5a1964d96297836f` and connected the contrast setting
  to the LAB lightness pivot (100 + contrast * 100), clamping L to [0, 100].
- Rejected nonfinite renderer settings before conversion to float.
- Disabled AndroidX persistence in XML so preference inflation cannot write
  an unregistered setting. Restart now requires successful synchronous storage.
- Preset selection no longer silently enables global website darkening.
- Pinned Chromium 152 APIs used by the restart and contrast paths were checked
  before starting the incremental validation build.

Validation/build work in progress:

- Fractional image grayscale is implemented with SkColorMatrix saturation and
  cc::ColorFilter::MakeMatrix, following the old Kiwi image-filter path. The
  Chromium renderer path compiled successfully in run 35; device rendering remains unvalidated.
- High contrast is connected to foreground/list-symbol PaintFlags using Chromium
  BlendForMinContrast, preserving author alpha. The Chromium target compiled in
  run 35; the three renderer C++ regression tests still need to be executed.
- The lifetime Java dependency is //chrome/browser/lifetime/android:java. Presets
  save synchronously and expose an explicit restart action when the saved renderer
  switch differs from the running process. Invalid values/storage failure do not
  restart. Java type/lint validation passed through the successful incremental build gate.
- Continue with executed renderer/persistence tests, device startup, then
  settings/toolbar/tab work and whole-series upstream conflict tests. Do not
  redo completed work or substitute old tab modes with aliases to GRID.
- Workflow explicitly restores only completed cache
  `kiwi-incremental-15a277216c780215b11a17ce021e12caaae7a7e0-stage-1`
  and requires restore. A cache miss must stop before compilation.

The local workspace has no out/Default. No clean operation is permitted. The
incremental GitHub Actions run triggered by this checkpoint is the source of truth
for Java/lint/native compile errors before further implementation changes.

- Chromium 152 SkColorMatrix API was corrected to use an explicit 20-float row-major buffer; patch/manifest/series hashes were updated together.
- The original read-only incremental workflow is restored; resume compile validation from the completed checkpoint.

- Run 35 completed the APK in one resume stage from the exact Stage 1 checkpoint. The completed out/Default cache above is now the only workflow default; older or empty fallback keys remain forbidden.
