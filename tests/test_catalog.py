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
        item = copy.deepcopy(self.latest["channels"]["internal"]["android"])
        item["url"] = "https://github.com/ChekovDanil/temno-vpn-releases/releases/download/android-v0.2.0/debug.apk"
        with self.assertRaises(catalog.CatalogError):
            catalog.validate_release(item, "android", "internal", "fixture")


if __name__ == "__main__":
    unittest.main()
