#!/usr/bin/env python3
"""Build an isolated M156 patch-rebase candidate from verified GitHub audit sources.
No compilation, repository push, cache writes, or old release alterations.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import traceback

ROOT = Path(__file__).resolve().parents[1]
PORT = ROOT / "kiwi_port"
AUDIT = Path(os.environ["RUNNER_TEMP"]) / "kiwi156-audit"
OUTPUT = ROOT / "output" / "kiwi156-rebase-candidate"
SRC = Path(os.environ["RUNNER_TEMP"]) / "kiwi156-rebase-src"
REPLAY = Path(os.environ["RUNNER_TEMP"]) / "kiwi156-strict-replay"
STATUS = OUTPUT / "results.json"
OUTPUT.mkdir(parents=True, exist_ok=True)
events = []
candidate = OUTPUT / "patches"
candidate.mkdir(parents=True, exist_ok=True)

def run(cmd, cwd=None, check=True):
    p = subprocess.run(list(map(str, cmd)), cwd=cwd, capture_output=True, text=True)
    if check and p.returncode != 0:
        raise RuntimeError("command failed: " + " ".join(map(str,cmd)) +
                           "\n" + (p.stdout + p.stderr)[-8000:])
    return p

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None

def archive_extract(target):
    target.mkdir(parents=True, exist_ok=True)
    archive = AUDIT / "kiwi-sources-before.tar.gz"
    with tarfile.open(archive, "r:gz") as inp:
        for member in inp.getmembers():
            dest = target / member.name
            if not dest.resolve().is_relative_to(target.resolve()) or not member.isfile():
                raise RuntimeError("unsafe or unexpected archive item: " + member.name)
        inp.extractall(target, filter="data")

def write_status(reason, done=False):
    STATUS.write_text(json.dumps({
        "status": "pass" if done else "incomplete",
        "reason": reason, "events": events
    }, indent=2, ensure_ascii=False)+"\n")

def repair_known_m156_theme_reject(feature_id, rejected):
    """Only repair a confirmed M156 layout change without discarding existing settings."""
    relative = "chrome/browser/ui/android/night_mode/java/src/org/chromium/chrome/browser/night_mode/settings/ThemeSettingsFragment.java"
    if feature_id != "night-mode-presets" or rejected != [relative + ".rej"]:
        return False
    path = SRC / relative
    data = path.read_text(encoding="utf-8")
    if data.count('    static final String PREF_KIWI_NIGHT_MODE_PRESET = "kiwi_night_mode_preset";') != 1:
        return False
    def add_once(anchor, addition):
        nonlocal data
        if addition.strip() in data:
            return
        if data.count(anchor) != 1:
            raise RuntimeError("unsafe M156 night-mode anchor: " + anchor)
        data = data.replace(anchor, anchor + addition, 1)
    add_once("import android.os.Bundle;\n",
             "\nimport androidx.preference.ListPreference;\nimport androidx.preference.Preference;\n")
    add_once("import org.chromium.base.shared_preferences.SharedPreferencesManager;\n",
             "import org.chromium.base.CommandLine;\nimport org.chromium.base.shared_preferences.SharedPrefsUtils;\n")
    add_once("import org.chromium.chrome.browser.flags.ChromeFeatureList;\n",
             "import org.chromium.chrome.browser.lifetime.ApplicationLifetime;\n")
    block = """
        ListPreference nightModePreset = findPreference(PREF_KIWI_NIGHT_MODE_PRESET);
        assert nightModePreset != null;
        nightModePreset.setPersistent(false);
        nightModePreset.setValue(
                Integer.toString(SharedPrefsUtils.SharedPrefsExt.NIGHT_MODE_PRESET.get()));
        Preference restart = findPreference("kiwi_night_mode_restart");
        assert restart != null;
        restart.setVisible(!SharedPrefsUtils.getNightModeSettingsSwitchValue().equals(
                CommandLine.getInstance().getSwitchValue("dark-mode-settings")));
        restart.setOnPreferenceClickListener(preference -> {
            ApplicationLifetime.terminate(true);
            return true;
        });
        nightModePreset.setOnPreferenceChangeListener(
                (preference, newValue) -> {
                    if (!(newValue instanceof String)) return false;
                    final int preset;
                    try {
                        preset = Integer.parseInt((String) newValue);
                    } catch (NumberFormatException exception) {
                        return false;
                    }
                    if (!SharedPrefsUtils.SharedPrefsExt.NIGHT_MODE_PRESET.validateValue(preset)) {
                        return false;
                    }
                    if (!SharedPrefsUtils.SharedPrefsExt.NIGHT_MODE_PRESET.putSync(preset)) {
                        return false;
                    }
                    restart.setVisible(!SharedPrefsUtils.getNightModeSettingsSwitchValue().equals(
                            CommandLine.getInstance().getSwitchValue("dark-mode-settings")));
                    return true;
                });

"""
    if 'ListPreference nightModePreset = findPreference(PREF_KIWI_NIGHT_MODE_PRESET);' not in data:
        anchor = ("        if (ChromeFeatureList.isEnabled(\n"
                  "                ChromeFeatureList.DARKEN_WEBSITES_CHECKBOX_IN_THEMES_SETTING)) {\n"
                  "            WebContentsDarkModeMessageController.notifyEventSettingsOpened(getProfile());\n")
        if data.count(anchor) != 1:
            raise RuntimeError("M156 night-mode settings method layout changed; stop")
        data = data.replace(anchor, block + anchor, 1)
    path.write_text(data, encoding="utf-8")
    (SRC / (relative + ".rej")).unlink(missing_ok=True)
    return True

def repair_upstream_native_theme_target(feature_id, rejected):
    """M156 already supplies the standalone theme target; avoid redefining it."""
    relative = "chrome/browser/android/BUILD.gn"
    if feature_id != "web-contents-theme-target" or rejected != [relative + ".rej"]:
        return False
    path=SRC/relative
    data=path.read_text(encoding="utf-8")
    obsolete_added = """  # A leaf target so extension popup WebContents can opt into the Android
  # app theme without depending on the monolithic :android target.
  source_set("web_contents_theme_client") {
    sources = [ "web_contents_theme_client.cc" ]
    public = [ "web_contents_theme_client.h" ]
    public_deps = [ "//content/public/browser" ]
    deps = [
      "//base",
      "//chrome/browser/ui/android/night_mode:jni_headers",
    ]
  }

"""
    if data.count(obsolete_added)!=1:
        raise RuntimeError("M156 theme target different from audited upstream; refuse guessed repair")
    data=data.replace(obsolete_added,"",1)
    if data.count('source_set("web_contents_theme_client")')!=1:
        raise RuntimeError("M156 upstream theme target not unique")
    if data.count('":web_contents_theme_client",')!=1:
        raise RuntimeError("M156 upstream theme target dependency missing or duplicated")
    if data.count('"web_contents_theme_client.cc"')!=1 or data.count('"web_contents_theme_client.h"')!=1:
        raise RuntimeError("M156 upstream theme client source/public declaration unexpected")
    upstream_anchor="  # A leaf target so that it can be used by targets that \":android\" itself\n"
    mark="  # Kiwi extension popup: reuse the upstream-provided standalone WebContents theme target.\n"
    if data.count(upstream_anchor)!=1 or mark in data:
        raise RuntimeError("M156 theme target context unsafe for provenance marker")
    data=data.replace(upstream_anchor,mark+upstream_anchor,1)
    path.write_text(data,encoding="utf-8")
    (SRC/(relative+".rej")).unlink(missing_ok=True)
    return True

def repair_m156_clipboard_enum_transition(feature_id, rejected):
    """Adapt the two rejected Android NTP clipboard hunks to the M156 scoped enum."""
    cc="components/omnibox/browser/clipboard_provider.cc"
    test="components/omnibox/browser/clipboard_provider_unittest.cc"
    if feature_id!="new-tab-clipboard-only" or set(rejected)!={cc+".rej",test+".rej"}:
        return False
    ccp=SRC/cc
    data=ccp.read_text(encoding="utf-8")
    anchor = ("void ClipboardProvider::UpdateClipboardMatchWithContent(\n"
              "    base::WeakPtr<AutocompleteMatch> match,\n"
              "    ClipboardMatchCallback callback) {\n  DCHECK(match);\n")
    code = """#if BUILDFLAG(IS_ANDROID)
  if (ntp_clipboard_mode_ &&
      match->type == omnibox::AutocompleteMatchType::kClipboardUrl) {
    // Use the current clipboard item at selection time to support both links
    // and text without displaying clipboard contents in the NTP suggestion.
    ui::DataTransferEndpoint data_dst(
        ui::EndpointType::kDefault, {.notify_if_restricted = false});
    ui::Clipboard::GetForCurrentThread()->ReadText(
        ui::ClipboardBuffer::kCopyPaste, data_dst,
        base::BindOnce(
            [](base::WeakPtr<ClipboardProvider> provider,
               base::WeakPtr<AutocompleteMatch> match,
               ClipboardMatchCallback callback, std::u16string text) {
              if (provider && match && !text.empty()) {
                provider->UpdateClipboardTextContent(text, match.get());
              }
              std::move(callback).Run();
            },
            callback_weak_ptr_factory_.GetWeakPtr(), std::move(match),
            std::move(callback)));
    return;
  }
#endif
"""
    if data.count(anchor)!=1:
        raise RuntimeError("M156 clipboard callback signature changed")
    if "if (ntp_clipboard_mode_ &&" in data[data.index(anchor):data.index(anchor)+500]:
        raise RuntimeError("clipboard handler already modified or ambiguous")
    data=data.replace(anchor,anchor+code,1)
    ccp.write_text(data,encoding="utf-8")
    tp=SRC/test
    td=tp.read_text(encoding="utf-8")
    start="TEST_F(ClipboardProviderTest, Android_NTPClipboardLinkWithUnknownTimestamp) {"
    if td.count(start)!=1:
        raise RuntimeError("M156 clipboard test rename hunk not applied uniquely")
    after="TEST_F(ClipboardProviderTest, Android_StandaloneSuggestionOnSearchActivity) {"
    if td.count(after)!=1:
        raise RuntimeError("M156 clipboard next test marker ambiguous")
    idx=td.index(start)
    end=td.index(after,idx)
    replacement = """TEST_F(ClipboardProviderTest, Android_NTPClipboardLinkWithUnknownTimestamp) {
  // Verify NTP obtains a real link even when Android has not reported age.
  auto* system_clipboard = ui::TestClipboard::CreateForCurrentThread();
  system_clipboard->WriteText(kClipboardURL);
  system_clipboard->SetLastModifiedTime(base::Time());
  client_->set_template_url_service(
      search_engines_test_environment_.template_url_service());

  AutocompleteInput input(std::u16string(), metrics::OmniboxEventProto::NTP,
                          classifier_);
  input.set_focus_type(metrics::OmniboxFocusType::INTERACTION_FOCUS);
  provider_->Start(input, false);

  ASSERT_EQ(provider_->matches().size(), 1U);
  auto& match = provider_->matches().back();
  EXPECT_EQ(omnibox::AutocompleteMatchType::kClipboardUrl, match.type);
  EXPECT_EQ(omnibox::GROUP_MOBILE_CLIPBOARD, match.suggestion_group_id);
  EXPECT_TRUE(match.destination_url.is_empty());

  system_clipboard->WriteText("https://example.org/latest");
  CreateMatchWithContentCallbackWaiter waiter(provider_, &match);
  waiter.WaitForMatchUpdated();
  EXPECT_EQ(GURL("https://example.org/latest"), match.destination_url);
  ui::Clipboard::DestroyClipboardForCurrentThread();
}

TEST_F(ClipboardProviderTest, Android_NTPClipboardTextSearchesWhenSelected) {
  auto* system_clipboard = ui::TestClipboard::CreateForCurrentThread();
  system_clipboard->WriteText("Search for me");
  system_clipboard->SetLastModifiedTime(base::Time());
  client_->set_template_url_service(
      search_engines_test_environment_.template_url_service());

  AutocompleteInput input(std::u16string(), metrics::OmniboxEventProto::NTP,
                          classifier_);
  input.set_focus_type(metrics::OmniboxFocusType::INTERACTION_FOCUS);
  provider_->Start(input, false);
  ASSERT_EQ(provider_->matches().size(), 1U);
  auto& match = provider_->matches().back();
  CreateMatchWithContentCallbackWaiter waiter(provider_, &match);
  waiter.WaitForMatchUpdated();
  EXPECT_EQ(omnibox::AutocompleteMatchType::kClipboardText, match.type);
  EXPECT_TRUE(match.destination_url.is_valid());
  ui::Clipboard::DestroyClipboardForCurrentThread();
}

"""
    td=td[:idx]+replacement+td[end:]
    tp.write_text(td,encoding="utf-8")
    for rel in (cc,test):
        (SRC/(rel+".rej")).unlink(missing_ok=True)
    return True

def main():
    rawhash = json.loads((AUDIT/"kiwi-source-hashes-before.json").read_text())
    if len(rawhash["files"]) != 99:
        raise RuntimeError("audit did not contain 99 tracked source hashes")
    if rawhash["chromium_commit"] != "5869fe313571d75152b77813cf0a4ee26a4e6df0":
        # The audit reporter carries stale manifest metadata (M155.84).
        events.append({"warning":"before hash JSON contains inherited M155 metadata; verify actual M156 source from run pins"})
    archive_extract(SRC)
    for rel,expected in rawhash["files"].items():
        actual=sha(SRC/rel)
        if actual != expected:
            raise RuntimeError("audit before source digest mismatch: " + rel)
    run(["git","init","-q"],cwd=SRC)
    run(["git","config","user.email","audit@localhost"],cwd=SRC)
    run(["git","config","user.name","Kiwi Audit"],cwd=SRC)
    run(["git","add","-A"],cwd=SRC)
    run(["git","commit","-q","--allow-empty","-m","Verified M156 before baseline"],cwd=SRC)
    series=json.loads((PORT/"patches/series.json").read_text())
    manifest=json.loads((PORT/"manifest.json").read_text())
    newseries={"format":1,"base":"post-Titanium a3e4b86339a8db237d95d8e8e78248c8f6a1df68","features":[]}
    problems=[]
    for feature in series["features"]:
        patch=PORT/"patches"/feature["patch"]
        before=run(["git","apply","--check",patch],cwd=SRC,check=False)
        if before.returncode==0:
            run(["git","apply","--whitespace=nowarn",patch],cwd=SRC)
            how="exact"
            detail=""
        else:
            trial=run(["patch","-d",SRC,"-p1","--batch","--forward","--fuzz=2","-i",patch],check=False)
            how="context-repair-attempt"
            detail=(trial.stdout+trial.stderr)[-9000:]
            rejects=[str(p.relative_to(SRC)) for p in SRC.rglob("*.rej")]
            if rejects and repair_known_m156_theme_reject(feature["id"], rejects):
                rejects = [str(p.relative_to(SRC)) for p in SRC.rglob("*.rej")]
                if not rejects:
                    trial.returncode = 0
            if rejects and repair_upstream_native_theme_target(feature["id"], rejects):
                rejects = [str(p.relative_to(SRC)) for p in SRC.rglob("*.rej")]
                if not rejects:
                    trial.returncode = 0
            if rejects and repair_m156_clipboard_enum_transition(feature["id"], rejects):
                rejects = [str(p.relative_to(SRC)) for p in SRC.rglob("*.rej")]
                if not rejects:
                    trial.returncode = 0
            if trial.returncode!=0 or rejects:
                events.append({"id":feature["id"],"result":"conflict","details":detail,"rejects":rejects})
                problems.append(feature["id"])
                break
        # GNU patch preserves disposable .orig backup files; they are not feature changes.
        for disposable_backup in SRC.rglob("*.orig"):
            disposable_backup.unlink()
        run(["git","add","-A"],cwd=SRC)
        changed=run(["git","diff","--cached","--name-only"],cwd=SRC).stdout.splitlines()
        if set(changed)!=set(feature["files"]):
            events.append({"id":feature["id"],"result":"file-set-mismatch","changed":changed,"expected":feature["files"],"details":detail})
            problems.append(feature["id"])
            break
        patch_text=run(["git","diff","--cached","--binary","--full-index"],cwd=SRC).stdout
        if not patch_text:
            raise RuntimeError("empty feature: "+feature["id"])
        generated=candidate/feature["patch"]
        generated.write_text(patch_text)
        feat=dict(feature)
        feat["sha256"]=sha(generated)
        newseries["features"].append(feat)
        events.append({"id":feature["id"],"result":"candidate","method":how,"detail":detail[:800]})
        run(["git","commit","-q","-m",feature["id"]],cwd=SRC)
    if problems:
        write_status("M156 context repair requires manual correction: " + ",".join(problems))
        raise RuntimeError("Stopped at first nonrecoverable feature; candidate saved for review")
    if len(newseries["features"]) != 25:
        raise RuntimeError("feature count not 25")
    for rel in manifest["files"]:
        if rel not in rawhash["files"]:
            raise RuntimeError("untracked source: "+rel)
        manifest["files"][rel]["before_sha256"]=rawhash["files"][rel]
        manifest["files"][rel]["after_sha256"]=sha(SRC/rel)
    manifest["titanium_commit"]="a3e4b86339a8db237d95d8e8e78248c8f6a1df68"
    manifest["vanadium_commit"]="2ae4335402eabcc6e025f3400185fe25094d8521"
    manifest["chromium_commit"]="1d17a2e2ee147bb7d6ae2ab6abdb3a2510c17775"
    manifest["chromium_version"]="156.0.8078.47"
    (OUTPUT/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n")
    (candidate/"series.json").write_text(json.dumps(newseries,indent=2,ensure_ascii=False)+"\n")
    # Use only disposable runner checkout, then validate the regenerated series.
    # Original branch files and GitHub cache are never written.
    shutil.copy2(OUTPUT/"manifest.json",PORT/"manifest.json")
    for f in candidate.iterdir():
        shutil.copy2(f,PORT/"patches"/f.name)
    run(["python3",PORT/"verify_series.py"])
    archive_extract(REPLAY)
    run(["git","init","-q"],cwd=REPLAY)
    run(["python3",PORT/"apply.py",REPLAY])
    for rel,v in manifest["files"].items():
        if sha(REPLAY/rel)!=v["after_sha256"]:
            raise RuntimeError("strict replay post hash mismatch: "+rel)
    unit=run(["python3","-m","unittest",
              "kiwi_port.test_reapply","kiwi_port.test_incremental_sources",
              "kiwi_port.test_checkpoint_compat","kiwi_port.test_night_mode_patch",
              "kiwi_port.test_credentials_patch","kiwi_port.test_checkpoint_restore",
              "kiwi_port.test_job_budget"],cwd=ROOT,check=False)
    (OUTPUT/"unit-test-log.txt").write_text(unit.stdout+unit.stderr)
    if unit.returncode:
        raise RuntimeError("unit tests failed on candidate, see unit-test-log.txt")
    write_status("All 25 candidate patches strict-replay against actual M156 audited before files, 99 hashes match, unit tests pass",True)
    print("PASS: M156 candidate prepared. Review context repairs and compile constraints before production.")

if __name__=="__main__":
    try:
        main()
    except Exception as exc:
        (OUTPUT/"exception.txt").write_text(str(exc)+"\n"+traceback.format_exc())
        if not STATUS.exists(): write_status(str(exc))
        print("CANDIDATE INCOMPLETE: "+str(exc),file=sys.stderr)
        sys.exit(1)
