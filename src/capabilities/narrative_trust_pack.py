"""Narrative Trust Pack — governed export for Story Forge → Beatbox → Speakers."""

# Mythic: Narrative Trust Pack Organ
# Engineering: NarrativeTrustPackEngine
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mechanic.common import derive_claim_status, sha256_file
from src.alt3_lineage import record_alt3_lineage

PACK_VERSION = "narrative_trust_pack.v1"
DEFAULT_NARRATIVE_ROOT = Path(".runtime/narrative")
SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "narrative_trust_pack.v1.json"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def pack_dir(pack_id: str, *, root: Path | None = None) -> Path:
    base = (root or DEFAULT_NARRATIVE_ROOT).expanduser().resolve()
    return base / pack_id


def pack_path(pack_id: str, *, root: Path | None = None) -> Path:
    return pack_dir(pack_id, root=root) / "narrative_trust_pack.v1.json"


def build_stage_envelope(
    *,
    stage_name: str,
    artifact_path: str | Path,
    author: str,
    ul_substrate: dict[str, Any] | None = None,
    claim_label: str = "asserted",
) -> dict[str, Any]:
    path = Path(artifact_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"stage artifact not found: {path}")
    envelope = {
        "stage_id": f"stage-{uuid.uuid4().hex[:12]}",
        "stage_name": stage_name,
        "artifact_hash": sha256_file(path),
        "artifact_path": str(path),
        "claim_label": claim_label,
        "author": author,
        "created_at_utc": _utc_now_iso(),
    }
    if ul_substrate:
        envelope["ul_substrate"] = ul_substrate
    return envelope


def build_pack_from_capability_output(
    output: dict[str, Any],
    *,
    pack_id: str,
    author: str,
    story_forge_artifact_path: str | Path | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    """Build NTP from story_forge_audio capability result dict."""
    stages: list[dict[str, Any]] = []
    ul_substrate = output.get("ul_substrate") if isinstance(output.get("ul_substrate"), dict) else None

    sf_path = story_forge_artifact_path
    if sf_path is None:
        for candidate_key in ("metadata_path", "artifact_path"):
            if output.get(candidate_key):
                sf_path = output[candidate_key]
                break
    if sf_path:
        stages.append(
            build_stage_envelope(
                stage_name="story_forge",
                artifact_path=sf_path,
                author=author,
                ul_substrate=ul_substrate,
            )
        )

    music_path = output.get("music_stem_path") or output.get("beatbox_path")
    if music_path:
        stages.append(
            build_stage_envelope(
                stage_name="beatbox",
                artifact_path=music_path,
                author=author,
            )
        )

    final_audio = output.get("final_audio_path")
    if final_audio:
        stages.append(
            build_stage_envelope(
                stage_name="speakers",
                artifact_path=final_audio,
                author=author,
            )
        )

    if not stages:
        raise ValueError("capability output missing stage artifact paths")

    now = _utc_now_iso()
    pack = {
        "pack_version": PACK_VERSION,
        "pack_id": pack_id,
        "session_id": output.get("session_id") or "",
        "stages": stages,
        "claim_label": derive_claim_status([stage["claim_label"] for stage in stages]),
        "export_ready": False,
        "created_at_utc": now,
        "updated_at_utc": now,
    }
    persist_pack(pack, root=root)
    return pack


def persist_pack(pack: dict[str, Any], *, root: Path | None = None) -> Path:
    pack_id = str(pack["pack_id"])
    out_dir = pack_dir(pack_id, root=root)
    out_dir.mkdir(parents=True, exist_ok=True)
    for stage in pack.get("stages") or []:
        stage_dir = out_dir / "stages" / str(stage.get("stage_name") or "unknown")
        stage_dir.mkdir(parents=True, exist_ok=True)
    path = pack_path(pack_id, root=root)
    pack["updated_at_utc"] = _utc_now_iso()
    path.write_text(json.dumps(pack, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def load_pack(pack_id: str, *, root: Path | None = None) -> dict[str, Any]:
    path = pack_path(pack_id, root=root)
    if not path.is_file():
        raise FileNotFoundError(f"pack not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def verify_pack_integrity(pack: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    for stage in pack.get("stages") or []:
        path = Path(str(stage.get("artifact_path") or ""))
        expected = str(stage.get("artifact_hash") or "")
        if not path.is_file():
            failures.append(f"missing artifact: {path}")
            continue
        actual = sha256_file(path)
        if expected and actual != expected:
            failures.append(f"hash mismatch: {stage.get('stage_name')} ({path.name})")

    if failures:
        return {"ok": False, "claim_label": "rejected", "failures": failures}
    return {"ok": True, "claim_label": "asserted", "failures": []}


def apply_signoff(
    pack: dict[str, Any],
    *,
    signoff_by: str,
    notes: str = "",
    override_command: str = "none",
) -> dict[str, Any]:
    verify = verify_pack_integrity(pack)
    if not verify.get("ok"):
        pack["claim_label"] = "rejected"
        pack["export_ready"] = False
        pack["signoff_error"] = verify.get("failures")
        return pack

    pack["signoff"] = {
        "signoff_by": signoff_by,
        "signoff_at_utc": _utc_now_iso(),
        "override_command": override_command,
        "notes": notes[:500],
    }
    pack["claim_label"] = "proven"
    pack["export_ready"] = True
    pack.pop("signoff_error", None)
    return pack


def run_narrative_trust_pack_capability(request: dict[str, Any]) -> dict[str, Any]:
    """Dispatch pack / verify / signoff for bridge and API routes."""
    from copy import deepcopy

    from src.phase_gate import (
        ComponentNotRegisteredError,
        GovernedComponent,
        Phase,
        PhaseViolationError,
        assert_executable,
        get_component,
        register_component,
    )

    component_id = "jarvis.capability.narrative_trust_pack"
    capability_meta = {
        "name": "narrative_trust_pack",
        "version": "v1",
        "actions": ["pack", "verify", "signoff"],
    }

    try:
        get_component(component_id)
    except ComponentNotRegisteredError:
        register_component(
            GovernedComponent(
                component_id=component_id,
                name="Narrative Trust Pack Capability",
                component_type="capability",
                phase=Phase.VALIDATED,
                allowed_contexts=["operator_runtime", "test_harness"],
                notes="Governed Story Forge → Beatbox → Speakers export wrapper.",
                validation_metadata=deepcopy(capability_meta),
            )
        )

    runtime_context = str((request or {}).get("runtime_context") or "operator_runtime")
    try:
        assert_executable(component_id, runtime_context)
    except PhaseViolationError as exc:
        return {
            "ok": False,
            "status": "rejected",
            "error_type": "AuthorityRejected",
            "message": str(exc),
        }

    action = str((request or {}).get("action") or "pack").strip().lower()
    root = Path((request or {}).get("narrative_root")).expanduser() if (request or {}).get("narrative_root") else None

    try:
        if action == "pack":
            output = request.get("capability_output")
            if output is None and request.get("from_capability_result"):
                result_path = Path(str(request["from_capability_result"])).expanduser().resolve()
                output = json.loads(result_path.read_text(encoding="utf-8"))
            if not isinstance(output, dict):
                return {
                    "ok": False,
                    "status": "rejected",
                    "error_type": "ValidationError",
                    "message": "capability_output or from_capability_result is required",
                }
            pack_id = str((request or {}).get("pack_id") or "").strip()
            if not pack_id:
                return {
                    "ok": False,
                    "status": "rejected",
                    "error_type": "ValidationError",
                    "message": "pack_id is required",
                }
            pack = build_pack_from_capability_output(
                output,
                pack_id=pack_id,
                author=str((request or {}).get("author") or "operator"),
                story_forge_artifact_path=(request or {}).get("story_forge_artifact"),
                root=root,
            )
            record_alt3_lineage(
                subsystem="narrative_trust_pack",
                action="pack",
                mission_id=(request or {}).get("mission_id"),
                session_id=(request or {}).get("session_id") or pack.get("session_id"),
                payload={"pack_id": pack_id},
            )
            return {"ok": True, "status": "completed", "pack": pack}

        if action == "verify":
            pack_id = str((request or {}).get("pack_id") or "").strip()
            if not pack_id:
                return {
                    "ok": False,
                    "status": "rejected",
                    "error_type": "ValidationError",
                    "message": "pack_id is required",
                }
            pack = load_pack(pack_id, root=root)
            verify = verify_pack_integrity(pack)
            return {
                "ok": bool(verify.get("ok")),
                "status": "completed" if verify.get("ok") else "failed",
                "pack_id": pack_id,
                **verify,
            }

        if action == "signoff":
            pack_id = str((request or {}).get("pack_id") or "").strip()
            signoff_by = str((request or {}).get("signoff_by") or "").strip()
            if not pack_id or not signoff_by:
                return {
                    "ok": False,
                    "status": "rejected",
                    "error_type": "ValidationError",
                    "message": "pack_id and signoff_by are required",
                }
            pack = load_pack(pack_id, root=root)
            pack = apply_signoff(
                pack,
                signoff_by=signoff_by,
                notes=str((request or {}).get("notes") or ""),
            )
            persist_pack(pack, root=root)
            if pack.get("claim_label") == "proven":
                record_alt3_lineage(
                    subsystem="narrative_trust_pack",
                    action="signoff",
                    mission_id=(request or {}).get("mission_id"),
                    session_id=(request or {}).get("session_id") or pack.get("session_id"),
                    payload={"pack_id": pack_id, "claim_label": "proven"},
                )
            return {
                "ok": pack.get("claim_label") == "proven",
                "status": "completed" if pack.get("claim_label") == "proven" else "failed",
                "pack": pack,
            }

        return {
            "ok": False,
            "status": "rejected",
            "error_type": "UnsupportedAction",
            "message": f"unsupported action: {action}",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "status": "failed",
            "error_type": type(exc).__name__,
            "message": str(exc),
        }
