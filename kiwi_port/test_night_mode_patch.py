import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class NightModePatchTest(unittest.TestCase):
    def test_registry_and_all_six_presets_are_present(self):
        registry = (ROOT / "patches/040-preference-registry.patch").read_text()
        self.assertIn('"titanium.night_mode_preset"', registry)
        self.assertIn("new int[] {0, 1, 2, 3, 4, 5}", registry)
        for preset in ("case 2", "case 3", "case 4", "case 5", "default"):
            self.assertIn(preset, registry)
        added_lines = "\n".join(line[1:] for line in registry.splitlines() if line.startswith("+"))
        self.assertNotIn("isKeyInUse(key)", added_lines)

    def test_chromium_152_renderer_path_is_used(self):
        patch = (ROOT / "patches/050-night-mode-presets.patch").read_text()
        self.assertIn('switches::kDarkModeSettings', patch)
        self.assertIn('"dark-mode-settings"', patch)
        self.assertIn("DarkModeColorFilter::Create(settings)", patch)
        self.assertNotIn("is_debug", patch)
        self.assertNotIn("ENABLE_ASSERTS, false", patch)

    def test_extension_pages_follow_browser_dark_theme(self):
        patch = (ROOT / "patches/070-force-dark-runtime.patch").read_text()
        self.assertIn('"chrome-extension".equals(scheme)', patch)
        self.assertIn('"kiwi-extension".equals(scheme)', patch)
        self.assertIn("return isNightModeEnabled(webContents);", patch)
        self.assertIn(
            "WebContentsDarkModeController.isGlobalUserSettingsEnabled(profile)",
            patch,
        )
        added_lines = "\n".join(line[1:] for line in patch.splitlines() if line.startswith("+"))
        self.assertNotIn("FORCE_WEB_CONTENTS_DARK_MODE", added_lines)

    def test_extension_popups_attach_android_theme_client(self):
        patch = (ROOT / "patches/160-extension-popup-menu-fixes.patch").read_text()
        self.assertIn(
            '"chrome/browser/android/web_contents_theme_client.h"',
            patch,
        )
        self.assertIn(
            "night_mode::WebContentsThemeClient::CreateForWebContents(host_->host_contents());",
            patch,
        )
        self.assertIn(
            '"//chrome/browser/android:web_contents_theme_client"',
            patch,
        )
        self.assertIn("ContextUtils.getApplicationContext()", patch)
        self.assertIn("ColorUtils.inNightMode(ContextUtils.getApplicationContext())", patch)

    def test_extension_theme_client_has_leaf_gn_target(self):
        patch = (ROOT / "patches/165-web-contents-theme-target.patch").read_text()
        self.assertIn('source_set("web_contents_theme_client")', patch)
        self.assertIn('public = [ "web_contents_theme_client.h" ]', patch)
        self.assertIn('":web_contents_theme_client"', patch)
        self.assertNotIn('"web_contents_theme_client.cc",\n      "web_contents_theme_client.h"', patch)

    def test_context_menu_matches_chrome_width_and_kiwi_dark_surface(self):
        patch = (ROOT / "patches/170-context-menu-shape.patch").read_text()
        self.assertIn("TypedValue.COMPLEX_UNIT_DIP", patch)
        self.assertIn("336", patch)
        self.assertIn("minAllowedWidth", patch)
        self.assertIn("ColorUtils.inNightMode(getContext())", patch)
        self.assertIn("Color.rgb(32, 33, 36)", patch)
        self.assertIn("PorterDuff.Mode.SRC_IN", patch)
        self.assertIn("PorterDuff.Mode.MULTIPLY", patch)
        series = json.loads((ROOT / "patches/series.json").read_text())
        feature = next(item for item in series["features"] if item["id"] == "context-menu-shape")
        self.assertEqual(
            feature["files"],
            ["chrome/android/java/src/org/chromium/chrome/browser/contextmenu/ContextMenuListView.java"],
        )
        added_lines = "\n".join(
            line[1:]
            for line in patch.splitlines()
            if line.startswith("+") and not line.startswith("+++")
        )
        self.assertNotIn("SemanticColorUtils", added_lines)
        self.assertNotIn("night_mode", added_lines)

    def test_history_info_card_is_hidden_and_omnibox_scrim_is_lighter(self):
        patch = (ROOT / "patches/180-kiwi-omnibox-history.patch").read_text()
        self.assertIn("boolean getShouldShowPrivacyDisclaimersIfAvailable()", patch)
        self.assertIn("header is a separate item and remains visible", patch)
        self.assertIn("Color.argb(140, 0, 0, 0)", patch)
        self.assertIn("setDismissOmniboxCallback(delegate::clearOmniboxFocus)", patch)

    def test_night_mode_toggle_is_present_with_and_without_submenus(self):
        patch = "\n".join(
            [
                (ROOT / "patches/020-app-menu-actions.patch").read_text(),
                (ROOT / "patches/160-extension-popup-menu-fixes.patch").read_text(),
            ]
        )
        self.assertGreaterEqual(patch.count("modelList.add(buildKiwiNightModeItem());"), 2)

    def test_settings_dark_surfaces_match_kiwi_palette(self):
        patch = (ROOT / "patches/150-kiwi-settings-dark.patch").read_text()
        self.assertIn("ColorUtils.inNightMode(context)", patch)
        self.assertIn("Color.rgb(16, 17, 20)", patch)
        self.assertIn("Color.rgb(27, 28, 33)", patch)
        self.assertIn("getSettingsBackgroundColor", patch)
        self.assertIn("getSettingsContainerBackgroundColor", patch)

    def test_new_files_are_incremental_inputs(self):
        manifest = json.loads((ROOT / "manifest.json").read_text())
        series = json.loads((ROOT / "patches/series.json").read_text())
        feature = next(item for item in series["features"] if item["id"] == "night-mode-presets")
        for path in feature["files"]:
            self.assertIn(path, manifest["files"])


if __name__ == "__main__":
    unittest.main()
