import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "kiwi_port" / "patches" / "130-credentials-security.patch"
SERIES = ROOT / "kiwi_port" / "patches" / "series.json"


class CredentialsPatchTest(unittest.TestCase):
    def test_patch_integrity_and_manifest(self):
        data = PATCH.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        manifest = json.loads(SERIES.read_text(encoding="utf-8"))
        feature = next(item for item in manifest["features"]
                       if item["id"] == "credentials-security")
        self.assertEqual(digest, feature["sha256"])
        self.assertEqual(
            sorted(feature["files"]),
            sorted([
                "chrome/browser/prefs/browser_prefs.cc",
                "components/autofill/core/common/autofill_prefs.cc",
                "components/password_manager/core/browser/password_manager.cc",
                "components/password_manager/core/common/password_manager_pref_names.h",
            ]),
        )

    def test_existing_profiles_are_migrated_only_once(self):
        patch = PATCH.read_text(encoding="utf-8")
        required = [
            "kTitaniumLocalPasswordBackendMigrated",
            "kCredentialsEnableService, true",
            "kAutofillUsingPlatformAutofill, false",
            "IsManagedPreference",
            "BUILDFLAG(USE_LOGIN_DATABASE_AS_BACKEND)",
            "kOfferToSavePasswordsEnabledGMS, true",
        ]
        for token in required:
            self.assertIn(token, patch)
        self.assertEqual(
            patch.count("kTitaniumLocalPasswordBackendMigrated, true"), 1
        )


if __name__ == "__main__":
    unittest.main()
