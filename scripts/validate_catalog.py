#!/usr/bin/env python3
"""Validate TEMNO release metadata without network access or third-party packages."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

PLATFORMS = ("windows", "android", "macos", "ios")
CHANNELS = ("stable", "beta", "internal")
REPOSITORY = "ChekovDanil/temno-vpn-releases"
VERSION = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-(?:alpha|beta|rc)(?:\.(0|[1-9][0-9]*))?)?$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SAFE_TAG = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
ANDROID_ABIS = ("arm64-v8a", "armeabi-v7a", "x86_64")


class CatalogError(ValueError):
    pass


def fail(path: str, message: str) -> None:
    raise CatalogError(f"{path}: {message}")


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise CatalogError(f"{path}: invalid JSON: {error}") from error
    if not isinstance(value, dict):
        raise CatalogError(f"{path}: root must be an object")
    return value


def validate_url(value: object, artifact: str, path: str) -> None:
    if not isinstance(value, str):
        fail(path, "URL must be a string")
    parsed = urlsplit(value)
    if parsed.scheme != "https" or parsed.netloc != "github.com" or parsed.query or parsed.fragment:
        fail(path, "URL must use the canonical GitHub HTTPS host without query or fragment")
    if unquote(parsed.path) != parsed.path or "\\" in parsed.path or "/../" in parsed.path or "/./" in parsed.path:
        fail(path, "encoded or relative path components are forbidden")
    match = re.fullmatch(
        rf"/{re.escape(REPOSITORY)}/releases/download/([A-Za-z0-9][A-Za-z0-9._-]*)/([A-Za-z0-9][A-Za-z0-9._-]*)",
        parsed.path,
    )
    if not match:
        fail(path, "URL must point to an asset under an immutable release tag")
    tag, filename = match.groups()
    if tag.lower() == "latest" or filename != artifact:
        fail(path, "URL tag must be immutable and its filename must equal artifact")


def validate_release_page(value: object, tag: str, path: str) -> None:
    if not isinstance(value, str):
        fail(path, "release page must be a string")
    parsed = urlsplit(value)
    expected = f"/{REPOSITORY}/releases/tag/{tag}"
    if (
        parsed.scheme != "https"
        or parsed.netloc != "github.com"
        or parsed.query
        or parsed.fragment
        or unquote(parsed.path) != parsed.path
        or parsed.path != expected
    ):
        fail(path, "release page must point to the matching immutable GitHub tag")


def validate_artifact(item: object, path: str, *, require_signed: bool = False) -> None:
    if not isinstance(item, dict):
        fail(path, "artifact metadata must be an object")
    required = ("artifact", "url", "size", "sha256", "signed")
    missing = [key for key in required if key not in item]
    if missing:
        fail(path, f"missing fields: {', '.join(missing)}")
    artifact = item["artifact"]
    if not isinstance(artifact, str) or not SAFE_NAME.fullmatch(artifact):
        fail(f"{path}.artifact", "unsafe filename")
    if not isinstance(item["size"], int) or isinstance(item["size"], bool) or item["size"] < 1:
        fail(f"{path}.size", "must be a positive integer")
    if not isinstance(item["sha256"], str) or not SHA256.fullmatch(item["sha256"]):
        fail(f"{path}.sha256", "must be a lowercase SHA-256")
    if not isinstance(item["signed"], bool):
        fail(f"{path}.signed", "must be a boolean")
    if require_signed and not item["signed"]:
        fail(f"{path}.signed", "stable artifacts must be signed")
    validate_url(item["url"], artifact, f"{path}.url")


def validate_android_variants(item: dict, path: str) -> None:
    variants = item.get("variants")
    if not isinstance(variants, list) or not variants:
        fail(f"{path}.variants", "published Android releases need at least one ABI variant")
    seen_abis: set[str] = set()
    seen_artifacts: set[str] = set()
    for index, variant in enumerate(variants):
        variant_path = f"{path}.variants[{index}]"
        validate_artifact(variant, variant_path, require_signed=True)
        abi = variant.get("abi") if isinstance(variant, dict) else None
        if abi not in ANDROID_ABIS:
            fail(f"{variant_path}.abi", "unsupported Android ABI")
        if abi in seen_abis:
            fail(f"{variant_path}.abi", "duplicate Android ABI")
        if variant["artifact"] in seen_artifacts:
            fail(f"{variant_path}.artifact", "duplicate Android artifact")
        if not variant["artifact"].lower().endswith(".apk"):
            fail(f"{variant_path}.artifact", "Android variant must be an APK")
        if f"/releases/download/{item.get('tag')}/" not in variant["url"]:
            fail(f"{variant_path}.url", "Android variant tag must match release tag")
        seen_abis.add(abi)
        seen_artifacts.add(variant["artifact"])
    if seen_abis != set(ANDROID_ABIS):
        fail(f"{path}.variants", "published Android candidate must list every released ABI exactly once")
    if item.get("artifact") not in seen_artifacts:
        fail(f"{path}.artifact", "primary Android artifact must also appear in variants")


def validate_handoff(item: object, path: str) -> None:
    if not isinstance(item, dict):
        fail(path, "handoff metadata must be an object")
    required = ("published", "prerelease", "tag", "releasePage", "artifact", "url", "size", "sha256", "type")
    missing = [key for key in required if key not in item]
    if missing:
        fail(path, f"missing fields: {', '.join(missing)}")
    if item["published"] is not True or item["prerelease"] is not True:
        fail(path, "handoff must describe a published prerelease")
    if item["type"] != "source-handoff":
        fail(f"{path}.type", "only source handoff archives are allowed")
    tag = item["tag"]
    if not isinstance(tag, str) or not SAFE_TAG.fullmatch(tag) or not tag.endswith("-internal"):
        fail(f"{path}.tag", "handoff tag must be an immutable internal tag")
    validate_release_page(item["releasePage"], tag, f"{path}.releasePage")
    artifact = item["artifact"]
    if not isinstance(artifact, str) or not SAFE_NAME.fullmatch(artifact) or not artifact.lower().endswith(".zip"):
        fail(f"{path}.artifact", "handoff artifact must be a safe ZIP archive")
    if not isinstance(item["size"], int) or isinstance(item["size"], bool) or item["size"] < 1:
        fail(f"{path}.size", "must be a positive integer")
    if not isinstance(item["sha256"], str) or not SHA256.fullmatch(item["sha256"]):
        fail(f"{path}.sha256", "must be a lowercase SHA-256")
    validate_url(item["url"], artifact, f"{path}.url")
    if f"/releases/download/{tag}/" not in item["url"]:
        fail(f"{path}.url", "handoff asset tag must match handoff tag")


def validate_release(item: object, platform: str, channel: str, path: str) -> None:
    if item is None:
        return
    if not isinstance(item, dict):
        fail(path, "release must be an object or null")
    for key in ("version", "published", "automaticUpdate"):
        if key not in item:
            fail(path, f"missing {key}")
    if not isinstance(item["version"], str) or not VERSION.fullmatch(item["version"]):
        fail(f"{path}.version", "invalid semantic release version")
    if not isinstance(item["published"], bool) or not isinstance(item["automaticUpdate"], bool):
        fail(path, "published and automaticUpdate must be booleans")

    if channel == "internal":
        if item["published"] or item["automaticUpdate"]:
            fail(path, "internal app entries must be unpublished and non-automatic")
        forbidden = {"artifact", "url", "size", "sha256", "installer", "storeUrl"}.intersection(item)
        if forbidden:
            fail(path, f"internal metadata cannot expose distributable fields: {', '.join(sorted(forbidden))}")
        if item.get("status") == "handoff":
            validate_handoff(item.get("handoff"), f"{path}.handoff")
            if item.get("vpnReady") is not False or item.get("physicalDeviceTested") is not False:
                fail(path, "Apple handoff must explicitly state that VPN and physical-device readiness are false")
        elif "handoff" in item:
            fail(f"{path}.handoff", "handoff metadata requires handoff status")
        elif item.get("localOnly") is not True:
            fail(path, "non-handoff internal entries must be local-only")
        return

    if not item["published"]:
        forbidden = {"artifact", "url", "size", "sha256", "installer"}.intersection(item)
        if forbidden:
            fail(path, "unpublished public entries cannot contain downloadable artifacts")
        if item["automaticUpdate"]:
            fail(path, "unpublished release cannot enable updates")
        return

    if platform == "ios":
        if any(key in item for key in ("artifact", "url", "size", "sha256", "installer")):
            fail(path, "iOS must not publish an IPA or direct binary")
        if item.get("distribution") not in ("app-store", "testflight") or not isinstance(item.get("storeUrl"), str):
            fail(path, "published iOS release needs an App Store or TestFlight URL")
        return

    validate_artifact(item, path, require_signed=(channel == "stable"))
    artifact = item["artifact"].lower()
    if platform == "windows" and not artifact.endswith((".exe", ".zip", ".msix")):
        fail(f"{path}.artifact", "Windows artifact must be EXE, ZIP or MSIX")
    if platform == "android":
        if item.get("buildType") != "release" or not item.get("signed") or not artifact.endswith(".apk"):
            fail(path, "public Android artifact must be a signed release APK")
        if channel == "beta":
            if item.get("prerelease") is not True or item.get("status") != "candidate":
                fail(path, "Android beta must be marked as a release candidate prerelease")
            if item.get("physicalDeviceTested") is not False:
                fail(path, "current Android candidate must truthfully record missing physical-device validation")
        elif item.get("physicalDeviceTested") is not True:
            fail(path, "stable Android releases require physical-device validation")
        tag = item.get("tag")
        if not isinstance(tag, str) or not SAFE_TAG.fullmatch(tag):
            fail(f"{path}.tag", "published Android candidate needs an immutable tag")
        if not isinstance(item.get("certificateSha256"), str) or not SHA256.fullmatch(item["certificateSha256"]):
            fail(f"{path}.certificateSha256", "published Android candidate needs its signing-certificate SHA-256")
        if not isinstance(item.get("minimumSdk"), int) or not isinstance(item.get("targetSdk"), int):
            fail(path, "published Android candidate needs numeric minimumSdk and targetSdk")
        if item["minimumSdk"] < 1 or item["targetSdk"] < item["minimumSdk"]:
            fail(path, "Android SDK bounds are invalid")
        validate_release_page(item.get("releasePage"), tag, f"{path}.releasePage")
        if f"/releases/download/{tag}/" not in item["url"]:
            fail(f"{path}.url", "Android asset tag must match release tag")
        validate_android_variants(item, path)
    if platform == "macos":
        if not artifact.endswith((".dmg", ".pkg")):
            fail(f"{path}.artifact", "macOS artifact must be DMG or PKG")
        if not all(item.get(key) is True for key in ("signed", "notarized", "stapled")):
            fail(path, "macOS artifact must be signed, notarized and stapled")
    if item["automaticUpdate"] and (channel != "stable" or not item.get("signed")):
        fail(path, "automatic updates require a signed stable release")
    if "installer" in item:
        validate_artifact(item["installer"], f"{path}.installer", require_signed=(channel == "stable"))


def checksum_entries(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for checksum_file in sorted((root / "checksums").glob("*.txt")):
        for number, raw in enumerate(checksum_file.read_text(encoding="utf-8").splitlines(), 1):
            if not raw.strip():
                continue
            match = re.fullmatch(r"([0-9a-f]{64})  ([A-Za-z0-9][A-Za-z0-9._-]*)", raw)
            if not match:
                fail(f"{checksum_file}:{number}", "expected '<lowercase sha256><two spaces><safe filename>'")
            digest, artifact = match.groups()
            previous = result.get(artifact)
            if previous is not None and previous != digest:
                fail(str(checksum_file), f"conflicting checksum for {artifact}")
            result[artifact] = digest
    return result


def validate(root: Path) -> None:
    updates = root / "updates"
    latest = load_json(updates / "latest.json")
    if latest.get("schemaVersion") != 1 or latest.get("product") != "TEMNO VPN":
        fail("updates/latest.json", "unexpected schemaVersion or product")
    channels = latest.get("channels")
    if not isinstance(channels, dict) or tuple(channels) != CHANNELS:
        fail("updates/latest.json.channels", "channels must be ordered stable, beta, internal")
    for channel in CHANNELS:
        entries = channels[channel]
        if not isinstance(entries, dict) or tuple(entries) != PLATFORMS:
            fail(f"channels.{channel}", "must contain ordered windows, android, macos, ios entries")
        for platform in PLATFORMS:
            validate_release(entries[platform], platform, channel, f"channels.{channel}.{platform}")

    checksums = checksum_entries(root)
    for channel in ("stable", "beta"):
        for platform in PLATFORMS:
            item = channels[channel][platform]
            if not isinstance(item, dict) or not item.get("published"):
                continue
            for artifact_item in (item, item.get("installer")):
                if not isinstance(artifact_item, dict) or "artifact" not in artifact_item:
                    continue
                artifact = artifact_item["artifact"]
                if checksums.get(artifact) != artifact_item["sha256"]:
                    fail(f"channels.{channel}.{platform}", f"checksum file is missing or differs for {artifact}")
            if platform == "android" and isinstance(item.get("variants"), list):
                for variant in item["variants"]:
                    artifact = variant["artifact"]
                    if checksums.get(artifact) != variant["sha256"]:
                        fail(f"channels.{channel}.{platform}", f"checksum file is missing or differs for {artifact}")

    for platform in ("macos", "ios"):
        item = channels["internal"][platform]
        if isinstance(item, dict) and isinstance(item.get("handoff"), dict):
            handoff = item["handoff"]
            artifact = handoff["artifact"]
            if checksums.get(artifact) != handoff["sha256"]:
                fail(f"channels.internal.{platform}.handoff", f"checksum file is missing or differs for {artifact}")

    for platform in PLATFORMS:
        manifest = load_json(updates / f"{platform}.json")
        if manifest.get("schemaVersion") != 1 or manifest.get("product") != "TEMNO VPN" or manifest.get("platform") != platform:
            fail(f"updates/{platform}.json", "unexpected identity fields")
        if manifest.get("channels") != {channel: channels[channel][platform] for channel in CHANNELS}:
            fail(f"updates/{platform}.json", "platform manifest differs from latest.json")

    load_json(updates / "schema.json")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        validate(args.root.resolve())
    except CatalogError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("PASS: release catalog, platform manifests, immutable URLs and checksums are consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
