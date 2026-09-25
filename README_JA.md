# Titanium-Kiwi Sol v2

## 暗色画面の個別配色と超省電力モード（Build #160）

設定 → 外観で、暗色画面の「地色」「カード・入力欄」「メニュー・ポップアップ」を個別に選ぶ変更を準備しました。未指定なら元の段階的な配色を保ちます。従来の色指定は地色として引き継ぎます。

メニューのNightモード直下には「超省電力モード」の切替を用意し、設定 → タブの切り替えから「Webページの動きを抑える」「同時レンダラ数を制限」「ページの先読み描画を止める」を個別に選べるようにしました。変更は再起動後に適用されます。表示中のページで動くスクリプトや動画のCPU消費まで止めるものではなく、節電率は未計測です。

Build #160 は2026年9月25日に #157 の完全一致キャッシュから完成し、未確定だった3ファイルのハッシュを確定しました。[最終 Build #161](https://github.com/nojirokaimo-svg/android-browser-dev-tk/actions/runs/36093793201) は #160 の不変な完成キャッシュを完全一致で復元し、実ソース14ファイルと完成manifestの照合、関連テスト27件、patch26本、Android v2署名を確認しました。APKの SHA-256 は `10ac551e86e57381a2fc15f10d6b5c89337855d6ff6aca99e4bdc6c78003965a`、配布artifact ZIPの SHA-256 は `3c46fd9a0747edfaf9a78adf91ae66a9f25e6cb156e016ab28b42a9590f69783` です。節電率と全画面への配色反映は実機未計測です。

Titaniumの現行Chromiumと拡張機能基盤を保ち、Kiwi風UIを機能別patchとして再適用できるarm64ビルドキットです。固定版ビルドと、将来のTitanium upstream追従の両方に対応します。

## 実装済み範囲

- 3点メニュー上部の5操作行
- 拡張機能のカラーアイコン・バッジ付き行と既存権限/popup経路での実行
- フラットな「拡張機能」管理行
- 通常メニューのアイコンとKiwiに近いコンパクトpopup（暗色時 `#202124`）
- popupから開くサブメニューも同じKiwi暗色surfaceへ統一
- 6種類のNight mode、renderer contrast/grayscale/high-contrast伝播
- AMOLED時のシステムstatus bar・toolbar・再表示後の合成toolbarを純黒化
- Kiwi密度へ寄せた拡張機能管理画面と、削除前の確認dialog
- Default／Original／Horizontal／Vertical／Grid／List／Desktopの7種類から選べるタブ切り替え
- タブ状態・download・history・bookmarkを含む手動backup/restore
- 「Kiwi Browserから移行」からのネイティブ移行、元日時を保持する履歴取り込み
- Android SAF経由のZIP／CRX／展開済み拡張機能の実読み込み
- 英語・日本語リソース

完全移植ではありません。実機での6種類のNight mode、全7タブ切り替え、backup/restore、各popupの最終確認は継続中です。

## patch構成

`kiwi_port/patches/series.json`が適用順、機能名、対象ファイル、patch SHA-256を管理します。

| 順序 | 機能 | 主な責務 |
|---|---|---|
| 010 | resources | メニューID、英語・日本語ラベル、GN登録 |
| 020 | app-menu-actions | 拡張機能行、実行経路、基本Night mode |
| 030 | menu-presentation | compact popupとdark surface |
| 040 | preference-registry | preference登録と起動クラッシュ修正 |
| 050 | night-mode-presets | 6種類のrenderer Night mode |
| 060 | runtime-night-mode | Night mode即時反映 |
| 070 | renderer-force-dark-runtime | renderer force-dark連携 |
| 080 | extension-mobile-ui | responsive拡張機能管理画面 |
| 090 | black-statusbar-full-backup | OLED黒化と完全backup |
| 100 | kiwi-tab-switcher | 7種類のタブ切り替え |
| 110 | amoled-surfaces | 新しいタブ・omniboxの純黒化 |
| 120 | kiwi-migration-extension-import | Kiwi移行、履歴日時保持、ZIP/CRX/展開済み拡張読み込み |

拡張機能とNight modeは同じActivity/メニュー生成箇所を変更するため、競合しやすいファイルを二重patchにせず、一つの依存単位にしています。

固定対象はTitanium `7584b534f6e1f9c29e8bb98df71d7610960a5db3`、Vanadium `02d87ad8e17aee77d0fea49d122349a5da87ed2e`、Chromium `507c6ee3e2f3b2ca0e660547e5b9ea4820c67f4c` (`153.0.8010.36`)です。`manifest.json`には固定版の適用前後ハッシュを残しています。

## 固定版APKビルド

Actionsの **Build Titanium-Kiwi core** を実行します。GitHub-hosted runnerの6時間制限を避けるため、1段階90分で安全停止し、`out/Default`をActions cacheへ保存して最大5段階で継続します。前段のobjectを復元するので完了済みコンパイルはやり直しません。

成功artifactは `Titanium-Kiwi-core-<version>-arm64` で、APKと `SHA256SUMS.txt` を含みます。テスト版package名は `io.github.nojirokaimo.titaniumkiwi` です。artifact内のAPKはAndroid v2署名を検証し、`SHA256SUMS.txt`を同梱します。

### Night mode等の増分再ビルド

APKを完成させたStageは、APKとは別に最終 `out/Default` を `kiwi-incremental-<commit>-stage-<N>` という不変cache keyで保存します。途中Stageのcacheも自動削除しません。

Night mode実装後は **Build Titanium-Kiwi core** を手動実行し、`incremental_cache_key`へ完成時に表示されたkeyを指定します。指定したcacheが存在しない場合はコンパイル開始前に失敗させ、暗黙にclean buildへ切り替えません。復元後に同じGN出力ディレクトリへ新しい差分だけを投入し、Ninja/Sisoの依存判定で必要なtargetだけを再生成します。

Chromium/Titanium commit、target CPU、GN args、toolchainなどcache互換性を壊す変更が必要な場合は、clean buildへ進む前に理由と対象を報告します。cache容量整理も自動では行わず、削除前に確認します。

ローカルLinuxでは次を実行します。

```bash
./build_kiwi_ui_arm64.sh
```

## Titanium upstream更新

### GitHub Actions

Actionsの **Update Titanium upstream and rebuild Kiwi UI** を手動実行します。`titanium_ref`にbranch/tag/commitを指定でき、空欄ならupstream既定branchのHEADを使います。

workflowは次を自動実行します。

1. 新しいTitanium commit、Vanadium submodule、Chromium version/tag SHAを固定
2. Titanium/Vanadium patch適用後のChromiumへKiwi機能patchをbest-effort適用
3. 競合がなければ、固定版と同じ90分×最大5段階のcache継続ビルド
4. 競合時はビルドせず、機能別レポート、JSON、`.rej`をfailure artifactへ保存

このworkflowはupstreamを検証用のdetached checkoutへ取得します。作業branchを強制merge/force-pushしないため、既存成果や進行中ビルドを壊しません。成功した固定SHAを確認後、必要なら通常のGit操作でforkへmergeします。

### ローカル更新確認

```bash
./update_titanium_upstream.sh --ref main
```

refを省略すると既定branchのHEADを使用します。作業場所は既定で `upstream-update-work/`、レポートは `output/kiwi-patch-report.md` と同名JSONです。これは使い捨てworktreeとして扱います。

## 競合時の復旧

`apply.py --best-effort`は、適用できる独立機能とclean hunkを先に適用し、競合hunkだけを対象ファイル隣の `.rej` に残します。レポートには `feature id → 競合ファイル` が出ます。

1. failure artifactの `kiwi-patch-report.md/.json` と `.rej` を確認
2. レポートにある機能・ファイルだけを新APIへ合わせて修正
3. `.rej`を削除し、Chromium側のコンパイル/対象テストを確認
4. 下記手順で機能patchを再生成
5. 更新workflowを再実行

途中状態からやり直す場合は、**使い捨ての更新worktree内だけ**で `git reset --hard <新しいChromium基準SHA>` と未追跡 `.rej` の削除を行います。Kiwi修正を保持した開発worktreeや本リポジトリでresetしないでください。

厳密適用は次です。固定版で一つでも機能が適用不能なら変更せず停止します。

```bash
python3 kiwi_port/apply.py /path/to/chromium/src
```

更新版の部分適用とレポート生成は次です。競合がある場合の終了コードは `2` です。

```bash
python3 kiwi_port/apply.py /path/to/chromium/src \
  --best-effort --report output/kiwi-patch-report.md
```

## patch再生成

基準commitからKiwi修正を加えたChromium git worktreeを用意し、次を実行します。

```bash
python3 kiwi_port/regenerate_patches.py /path/to/modified/chromium/src --base HEAD
```

`regenerate_patches.py`の `FEATURES` がファイルを機能単位へ割り当てます。ファイルを追加した場合は該当featureの一覧へ追加してから再生成してください。生成後は必ず以下を確認します。

```bash
python3 -m py_compile kiwi_port/apply.py kiwi_port/regenerate_patches.py
python3 -m unittest kiwi_port.test_reapply kiwi_port.test_incremental_sources kiwi_port.test_night_mode_patch
python3 kiwi_port/apply.py /path/to/clean/test-worktree
python3 kiwi_port/apply.py /path/to/clean/test-worktree
git diff --check
```

1回目で全featureが適用され、2回目がalready-appliedで正常終了すること、`series.json`のSHA-256が更新されることを確認します。

## 主要ファイル

- `kiwi_port/patches/`: 機能別patchとseries metadata
- `kiwi_port/apply.py`: strict/best-effort適用、競合レポート
- `kiwi_port/regenerate_patches.py`: 機能patch再生成
- `update_titanium_upstream.sh`: upstream版の解決とローカル適用確認
- `build_kiwi_ui_arm64.sh`: 取得、patch、GN、arm64 APK生成
- `.github/actions/kiwi-build-stage/`: 分割・cache継続ビルド共通処理
- `.github/workflows/kiwi-ui-build.yml`: 固定版ビルド
- `.github/workflows/update-upstream.yml`: upstream更新＋再適用＋同じ分割ビルド
- `DESIGN.md`: 全体設計とAstra判断境界

APK生成・端末動作が確認できるまでは完成扱いにしません。通常のimport/API/Rリソース/patch競合/ビルドエラーはSolで修正し、6種類のNight mode等のレンダラー設計境界だけAstraへ戻します。
