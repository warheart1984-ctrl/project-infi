"""Sovereign runtime profile (v49)."""

from __future__ import annotations

from typing import Any

from platform.store import PlatformStore

PROFILE_VERSION = "platform.sovereign_profile.v1"
DEFAULT_PROFILE = {
    "profile_version": PROFILE_VERSION,
    "mode": "hosted",
    "data_residency": "us",
    "export_bundle_schedule": "",
    "runner_endpoint": "",
}


def get_sovereign_profile(org: dict[str, Any] | None) -> dict[str, Any]:
    if not org:
        return dict(DEFAULT_PROFILE)
    return dict(org.get("sovereign_profile") or DEFAULT_PROFILE)


def set_sovereign_profile(*, store: PlatformStore, org_id: str, profile: dict[str, Any]) -> dict[str, Any]:
    org = store.get_org(org_id) or {"org_id": org_id}
    merged = dict(DEFAULT_PROFILE)
    merged.update(profile)
    merged["profile_version"] = PROFILE_VERSION
    org["sovereign_profile"] = merged
    if merged.get("data_residency"):
        org["data_residency"] = merged["data_residency"]
    store.upsert_org(org)
    return merged


def enforce_residency(*, org: dict[str, Any] | None, region: str) -> tuple[bool, str]:
    profile = get_sovereign_profile(org)
    residency = str(profile.get("data_residency") or (org or {}).get("data_residency") or "us")
    if residency and region and residency != region:
        return False, f"sovereign residency requires {residency}"
    return True, "ok"
