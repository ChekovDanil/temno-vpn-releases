import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_catalog", ROOT / "scripts" / "validate_catalog.py")
catalog = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(catalog)


class ReleaseCatalogTests(unittest.TestCase):
    def setUp(self):
        self.latest = json.loads((ROOT / "updates" / "latest.json").read_text(encoding="utf-8"))

    def assertRejected(self, value, platform="android", channel="beta"):
        with self.assertRaises(catalog.CatalogError):
            catalog.validate_release(value, platform, channel, "fixture")

    def test_repository_catalog_is_valid(self):
        catalog.validate(ROOT)

    def test_debug_android_cannot_enter_public_channels(self):
        item = copy.deepcopy(self.latest["channels"]["beta"]["windows"])
        item.update({"artifact": "TEMNO-debug.apk", "url": "https://github.com/ChekovDanil/temno-vpn-releases/releases/download/android-v0.2.0/TEMNO-debug.apk", "buildType": "debug", "signed": True})
        self.assertRejected(item)

    def test_public_ipa_is_rejected(self):
        self.assertRejected({"version": "1.0.0", "published": True, "automaticUpdate": False, "artifact": "TEMNO.ipa", "url": "https://github.com/ChekovDanil/temno-vpn-releases/releases/download/ios-v1.0.0/TEMNO.ipa"}, "ios")

    def test_unsigned_or_unnotarized_macos_is_rejected(self):
        item = {"version": "1.0.0", "published": True, "automaticUpdate": False, "artifact": "TEMNO.dmg", "url": "https://github.com/ChekovDanil/temno-vpn-releases/releases/download/macos-v1.0.0/TEMNO.dmg", "size": 1, "sha256": "a" * 64, "signed": False, "notarized": False, "stapled": False}
        self.assertRejected(item, "macos")

    def test_latest_download_alias_is_rejected(self):
        item = copy.deepcopy(self.latest["channels"]["beta"]["windows"])
        item["url"] = "https://github.com/ChekovDanil/temno-vpn-releases/releases/download/latest/" + item["artifact"]
        self.assertRejected(item, "windows")

    def test_unsigned_windows_cannot_enter_stable(self):
        item = copy.deepcopy(self.latest["channels"]["beta"]["windows"])
        with self.assertRaises(catalog.CatalogError):
            catalog.validate_release(item, "windows", "stable", "fixture")

    def test_beta_cannot_enable_automatic_install(self):
        item = copy.deepcopy(self.latest["channels"]["beta"]["windows"])
        item["automaticUpdate"] = True
        self.assertRejected(item, "windows")

    def test_internal_entries_cannot_expose_downloads(self):
        item = copy.deepcopy(self.latest["channels"]["internal"]["macos"])
        item["url"] = "https://github.com/ChekovDanil/temno-vpn-releases/releases/download/android-v0.2.0/debug.apk"
        with self.assertRaises(catalog.CatalogError):
            catalog.validate_release(item, "macos", "internal", "fixture")

    def test_android_candidate_is_manual_and_not_physically_validated(self):
        item = self.latest["channels"]["beta"]["android"]
        self.assertTrue(item["published"])
        self.assertTrue(item["prerelease"])
        self.assertFalse(item["automaticUpdate"])
        self.assertFalse(item["physicalDeviceTested"])
        self.assertEqual({variant["abi"] for variant in item["variants"]}, set(catalog.ANDROID_ABIS))

    def test_android_candidate_cannot_claim_automatic_updates(self):
        item = copy.deepcopy(self.latest["channels"]["beta"]["android"])
        item["automaticUpdate"] = True
        self.assertRejected(item, "android")

    def test_android_candidate_rejects_unsigned_variant(self):
        item = copy.deepcopy(self.latest["channels"]["beta"]["android"])
        item["variants"][1]["signed"] = False
        self.assertRejected(item, "android")

    def test_android_candidate_requires_every_published_abi(self):
        item = copy.deepcopy(self.latest["channels"]["beta"]["android"])
        item["variants"].pop()
        self.assertRejected(item, "android")

    def test_android_variant_cannot_point_to_another_tag(self):
        item = copy.deepcopy(self.latest["channels"]["beta"]["android"])
        item["variants"][0]["url"] = item["variants"][0]["url"].replace("android-v0.2.0-rc", "android-v0.2.1-rc")
        self.assertRejected(item, "android")

    def test_apple_handoff_is_not_an_application_release(self):
        for platform in ("macos", "ios"):
            item = self.latest["channels"]["internal"][platform]
            self.assertFalse(item["published"])
            self.assertFalse(item["automaticUpdate"])
            self.assertFalse(item["vpnReady"])
            self.assertFalse(item["physicalDeviceTested"])
            self.assertEqual(item["handoff"]["type"], "source-handoff")

    def test_apple_handoff_cannot_claim_vpn_readiness(self):
        item = copy.deepcopy(self.latest["channels"]["internal"]["macos"])
        item["vpnReady"] = True
        with self.assertRaises(catalog.CatalogError):
            catalog.validate_release(item, "macos", "internal", "fixture")

    def test_apple_handoff_cannot_disguise_a_dmg_as_source(self):
        item = copy.deepcopy(self.latest["channels"]["internal"]["macos"])
        item["handoff"]["artifact"] = "TEMNO.dmg"
        item["handoff"]["url"] = "https://github.com/ChekovDanil/temno-vpn-releases/releases/download/apple-handoff-v0.4-internal/TEMNO.dmg"
        with self.assertRaises(catalog.CatalogError):
            catalog.validate_release(item, "macos", "internal", "fixture")


if __name__ == "__main__":
    unittest.main()
