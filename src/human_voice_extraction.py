"""Human Voice Extraction — governed voice profiles from human notes."""

# Mythic: Human Voice Extraction Organ
# Engineering: HumanVoiceExtractionEngine
from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXTRACTION_VERSION = "human_voice_extraction.v1"
DEFAULT_EXTRACTION_ROOT = Path(".runtime/human_voice_extraction")
DEFAULT_SPEAKERS_ROOT = Path(".runtime/speakers")
FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "tools" / "human_voice" / "fixtures"

TRAIT_PATTERNS: list[tuple[str, str, re.Pattern[str]]] = [
    ("pace", "pace", re.compile(r"pace\s+is\s+(\w+)", re.IGNORECASE)),
    ("register", "register", re.compile(r"(\w+)\s+register", re.IGNORECASE)),
    ("signature_phrase", "signature phrase", re.compile(r"signature phrase:\s*([^.\n]+)", re.IGNORECASE)),
    ("vocabulary", "vocabulary", re.compile(r"vocabulary[:\s]+([^.\n]+)", re.IGNORECASE)),
    ("emotion_range", "emotion range", re.compile(r"emotion range[:\s]+([^.\n]+)", re.IGNORECASE)),
]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def extraction_root(root: Path | None = None) -> Path:
    return (root or DEFAULT_EXTRACTION_ROOT).expanduser().resolve()


def extraction_dir(extraction_id: str, *, root: Path | None = None) -> Path:
    return extraction_root(root) / extraction_id


def extraction_path(extraction_id: str, *, root: Path | None = None) -> Path:
    return extraction_dir(extraction_id, root=root) / "human_voice_extraction.v1.json"


def speakers_constraint_path(profile_id: str, *, speakers_root: Path | None = None) -> Path:
    base = (speakers_root or DEFAULT_SPEAKERS_ROOT).expanduser().resolve()
    return base / "voice_constraints" / f"{profile_id}.json"


def normalize_notes(notes_text: str) -> str:
    return " ".join(str(notes_text or "").split()).strip()


def content_hash_normalized(text: str) -> str:
    return hashlib.sha256(normalize_notes(text).encode("utf-8")).hexdigest()


def extract_traits_from_notes(notes_text: str) -> list[dict[str, Any]]:
    traits: list[dict[str, Any]] = []
    for trait_id_prefix, trait_kind, pattern in TRAIT_PATTERNS:
        match = pattern.search(notes_text)
        if not match:
            continue
        value = match.group(1).strip()
        traits.append(
            {
                "trait_id": f"{trait_id_prefix}-{uuid.uuid4().hex[:8]}",
                "trait_kind": trait_kind,
                "value": value,
                "confidence": 0.85,
            }
        )
    if not traits:
        traits.append(
            {
                "trait_id": f"fallback-{uuid.uuid4().hex[:8]}",
                "trait_kind": "register",
                "value": "neutral",
                "confidence": 0.5,
            }
        )
    return traits


def load_fixture(name: str) -> dict[str, Any]:
    path = FIXTURE_ROOT / f"{name}.json"
    if not path.is_file():
        path = FIXTURE_ROOT / name
    if not path.is_file():
        raise FileNotFoundError(f"human_voice fixture not found: {name}")
    return json.loads(path.read_text(encoding="utf-8"))


def extract_from_notes(
    notes_text: str,
    *,
    source_kind: str = "human_notes",
    mission_id: str | None = None,
    session_id: str | None = None,
    redaction_applied: bool = True,
) -> dict[str, Any]:
    normalized = normalize_notes(notes_text)
    traits = extract_traits_from_notes(normalized)
    extraction_id = f"extract-{uuid.uuid4().hex[:12]}"
    profile_id = f"profile-{uuid.uuid4().hex[:10]}"
    now = _utc_now_iso()
    pack = {
        "human_voice_extraction_version": EXTRACTION_VERSION,
        "extraction_id": extraction_id,
        "source_kind": source_kind,
        "content_hash": content_hash_normalized(normalized),
        "voice_profile": {
            "profile_id": profile_id,
            "traits": traits,
            "prosody_notes": "Extracted from normalized notes (raw source not stored).",
            "claim_label": "asserted",
        },
        "retention_policy": {
            "store_raw_source": False,
            "ttl_hours": 168,
            "redaction_applied": redaction_applied,
        },
        "speakers_handoff": {
            "handoff_ready": False,
            "target_lane": "speakers",
        },
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "created_at_utc": now,
    }
    if mission_id:
        pack["mission_id"] = mission_id
    if session_id:
        pack["session_id"] = session_id
    validate_extraction(pack)
    return pack


def extract_from_fixture(fixture_name: str) -> dict[str, Any]:
    spec = load_fixture(fixture_name)
    return extract_from_notes(
        str(spec.get("notes_text") or ""),
        source_kind=str(spec.get("source_kind") or "human_notes"),
        mission_id=spec.get("mission_id"),
    )


def validate_extraction(pack: dict[str, Any]) -> None:
    if pack.get("human_voice_extraction_version") != EXTRACTION_VERSION:
        raise ValueError(f"human_voice_extraction_version must be {EXTRACTION_VERSION}")
    retention = pack.get("retention_policy") or {}
    if retention.get("store_raw_source") is not False:
        raise ValueError("retention_policy.store_raw_source must be false")
    if "notes_text" in pack or "raw_source" in pack:
        raise ValueError("raw notes must not be persisted in extraction pack")
    traits = (pack.get("voice_profile") or {}).get("traits") or []
    if not traits:
        raise ValueError("voice_profile.traits required")


def persist_extraction(pack: dict[str, Any], *, root: Path | None = None) -> Path:
    validate_extraction(pack)
    eid = str(pack["extraction_id"])
    path = extraction_path(eid, root=root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(pack)
    payload["updated_at_utc"] = _utc_now_iso()
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def load_extraction(extraction_id: str, *, root: Path | None = None) -> dict[str, Any]:
    path = extraction_path(extraction_id, root=root)
    if not path.is_file():
        raise FileNotFoundError(f"extraction not found: {extraction_id}")
    pack = json.loads(path.read_text(encoding="utf-8"))
    validate_extraction(pack)
    return pack


def apply_signoff(pack: dict[str, Any], signoff_by: str) -> dict[str, Any]:
    updated = dict(pack)
    handoff = dict(updated.get("speakers_handoff") or {})
    handoff["handoff_ready"] = True
    handoff["signoff_by"] = str(signoff_by or "").strip() or "operator"
    handoff["signoff_at_utc"] = _utc_now_iso()
    updated["speakers_handoff"] = handoff
    if updated.get("retention_policy", {}).get("redaction_applied"):
        updated["claim_label"] = "proven"
        profile = dict(updated.get("voice_profile") or {})
        profile["claim_label"] = "proven"
        updated["voice_profile"] = profile
    validate_extraction(updated)
    return updated


def admit_speakers_constraints(
    pack: dict[str, Any],
    *,
    speakers_root: Path | None = None,
) -> dict[str, Any]:
    handoff = pack.get("speakers_handoff") or {}
    if not handoff.get("handoff_ready"):
        return {"status": "rejected", "reason": "signoff_required"}
    profile = pack.get("voice_profile") or {}
    profile_id = str(profile.get("profile_id") or "")
    if not profile_id:
        return {"status": "rejected", "reason": "missing_profile_id"}

    constraints = {
        "profile_id": profile_id,
        "extraction_id": pack.get("extraction_id"),
        "human_voice_extraction_version": EXTRACTION_VERSION,
        "traits": profile.get("traits") or [],
        "claim_label": pack.get("claim_label", "asserted"),
        "admitted_at_utc": _utc_now_iso(),
        "target_lane": "speakers_render",
    }
    path = speakers_constraint_path(profile_id, speakers_root=speakers_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(constraints, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"status": "admitted", "constraints_path": str(path), "constraints": constraints}


__all__ = [
    "EXTRACTION_VERSION",
    "admit_speakers_constraints",
    "apply_signoff",
    "extract_from_fixture",
    "extract_from_notes",
    "load_extraction",
    "persist_extraction",
    "speakers_constraint_path",
    "validate_extraction",
]
