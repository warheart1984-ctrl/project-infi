"""Human Voice Extraction capability."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from src.alt3_lineage import record_alt3_lineage
from src.human_voice_extraction import (
    admit_speakers_constraints,
    apply_signoff,
    extract_from_fixture,
    extract_from_notes,
    load_extraction,
    persist_extraction,
)
from src.phase_gate import (
    ComponentNotRegisteredError,
    GovernedComponent,
    Phase,
    PhaseViolationError,
    assert_executable,
    get_component,
    register_component,
)

HUMAN_VOICE_EXTRACTION_CAPABILITY_COMPONENT_ID = "jarvis.capability.human_voice_extraction"

HumanVoiceExtractionCapability = {
    "name": "human_voice_extraction",
    "version": "v1",
    "actions": ["extract", "signoff", "handoff"],
}


def ensure_human_voice_extraction_capability_registered() -> None:
    try:
        get_component(HUMAN_VOICE_EXTRACTION_CAPABILITY_COMPONENT_ID)
        return
    except ComponentNotRegisteredError:
        pass
    register_component(
        GovernedComponent(
            component_id=HUMAN_VOICE_EXTRACTION_CAPABILITY_COMPONENT_ID,
            name="Human Voice Extraction Capability",
            component_type="capability",
            phase=Phase.VALIDATED,
            allowed_contexts=["operator_runtime", "test_harness"],
            notes="Governed voice profile extraction with retention policy and Speakers handoff.",
            validation_metadata=deepcopy(HumanVoiceExtractionCapability),
        )
    )


def _lineage_after(request: dict[str, Any], action: str, payload: dict[str, Any]) -> None:
    record_alt3_lineage(
        subsystem="human_voice_extraction",
        action=action,
        mission_id=(request or {}).get("mission_id"),
        session_id=(request or {}).get("session_id"),
        payload=payload,
    )


def run_human_voice_extraction_capability(request: dict[str, Any]) -> dict[str, Any]:
    ensure_human_voice_extraction_capability_registered()
    runtime_context = str((request or {}).get("runtime_context") or "operator_runtime")
    try:
        assert_executable(HUMAN_VOICE_EXTRACTION_CAPABILITY_COMPONENT_ID, runtime_context)
    except PhaseViolationError as exc:
        return {
            "ok": False,
            "status": "rejected",
            "error_type": "AuthorityRejected",
            "message": str(exc),
        }

    action = str((request or {}).get("action") or "extract").strip().lower()
    root = Path((request or {}).get("extraction_root")).expanduser() if (request or {}).get("extraction_root") else None
    speakers_root = (
        Path((request or {}).get("speakers_root")).expanduser()
        if (request or {}).get("speakers_root")
        else None
    )

    try:
        if action == "extract":
            if (request or {}).get("fixture"):
                pack = extract_from_fixture(str(request["fixture"]))
            else:
                pack = extract_from_notes(
                    str((request or {}).get("notes_text") or ""),
                    source_kind=str((request or {}).get("source_kind") or "human_notes"),
                    mission_id=(request or {}).get("mission_id"),
                )
            path = persist_extraction(pack, root=root)
            out = {"ok": True, "status": "extracted", "extraction": pack, "path": str(path)}
            _lineage_after(request, "extract", {"extraction_id": pack.get("extraction_id")})
            return out
        if action == "signoff":
            eid = str((request or {}).get("extraction_id") or "")
            pack = (request or {}).get("extraction") or load_extraction(eid, root=root)
            signed = apply_signoff(pack, str((request or {}).get("signoff_by") or "operator"))
            path = persist_extraction(signed, root=root)
            out = {"ok": True, "status": "signed_off", "extraction": signed, "path": str(path)}
            _lineage_after(request, "signoff", {"extraction_id": signed.get("extraction_id")})
            return out
        if action == "handoff":
            eid = str((request or {}).get("extraction_id") or "")
            pack = (request or {}).get("extraction") or load_extraction(eid, root=root)
            result = admit_speakers_constraints(pack, speakers_root=speakers_root)
            ok = result.get("status") == "admitted"
            out = {"ok": ok, "status": result.get("status"), "result": result}
            if ok:
                _lineage_after(
                    request,
                    "handoff",
                    {
                        "extraction_id": pack.get("extraction_id"),
                        "profile_id": (pack.get("voice_profile") or {}).get("profile_id"),
                    },
                )
            return out
        return {
            "ok": False,
            "status": "rejected",
            "error_type": "ValidationRejected",
            "message": f"unsupported action: {action}",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "status": "rejected",
            "error_type": "ExecutionError",
            "message": str(exc),
        }


__all__ = [
    "HUMAN_VOICE_EXTRACTION_CAPABILITY_COMPONENT_ID",
    "ensure_human_voice_extraction_capability_registered",
    "run_human_voice_extraction_capability",
]
