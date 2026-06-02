"""Imagine Generator capability — emit patterns and Story Forge handoff."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from src.alt3_lineage import record_alt3_lineage
from src.imagine_generator import (
    admit_to_story_forge,
    build_pattern,
    build_pattern_from_fixture,
    load_pattern,
    persist_pattern,
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

CAPABILITY_NAME = "imagine_generator"
IMAGINE_GENERATOR_CAPABILITY_COMPONENT_ID = "jarvis.capability.imagine_generator"

ImagineGeneratorCapability = {
    "name": CAPABILITY_NAME,
    "version": "v1",
    "actions": ["emit", "handoff", "grok_render"],
    "deterministic": True,
}


def ensure_imagine_generator_capability_registered() -> None:
    try:
        get_component(IMAGINE_GENERATOR_CAPABILITY_COMPONENT_ID)
        return
    except ComponentNotRegisteredError:
        pass
    register_component(
        GovernedComponent(
            component_id=IMAGINE_GENERATOR_CAPABILITY_COMPONENT_ID,
            name="Imagine Generator Capability",
            component_type="capability",
            phase=Phase.VALIDATED,
            allowed_contexts=["operator_runtime", "test_harness"],
            notes="Governed imagination pattern emission for Story Forge handoff.",
            validation_metadata=deepcopy(ImagineGeneratorCapability),
        )
    )


def _with_ul_substrate(output: dict[str, Any], request: dict[str, Any] | None) -> dict[str, Any]:
    if isinstance(request, dict) and isinstance(request.get("ul_substrate"), dict):
        output["ul_substrate"] = dict(request["ul_substrate"])
    return output


def _lineage_after(request: dict[str, Any], action: str, payload: dict[str, Any]) -> None:
    record_alt3_lineage(
        subsystem="imagine_generator",
        action=action,
        mission_id=(request or {}).get("mission_id"),
        session_id=(request or {}).get("session_id"),
        payload=payload,
    )


def run_imagine_generator_capability(request: dict[str, Any]) -> dict[str, Any]:
    ensure_imagine_generator_capability_registered()
    runtime_context = str((request or {}).get("runtime_context") or "operator_runtime")
    try:
        assert_executable(IMAGINE_GENERATOR_CAPABILITY_COMPONENT_ID, runtime_context)
    except PhaseViolationError as exc:
        return _with_ul_substrate(
            {
                "ok": False,
                "status": "rejected",
                "error_type": "AuthorityRejected",
                "message": str(exc),
            },
            request,
        )

    action = str((request or {}).get("action") or "emit").strip().lower()
    imagine_root = (request or {}).get("imagine_root")
    story_forge_root = (request or {}).get("story_forge_root")
    root = Path(imagine_root).expanduser() if imagine_root else None
    sf_root = Path(story_forge_root).expanduser() if story_forge_root else None

    try:
        if action == "emit":
            fixture = (request or {}).get("fixture")
            if fixture:
                pattern = build_pattern_from_fixture(str(fixture))
            else:
                pattern = build_pattern(
                    pattern_type=str((request or {}).get("pattern_type") or "scene_seed"),
                    prompt_frame=str((request or {}).get("prompt_frame") or ""),
                    constraints=(request or {}).get("constraints"),
                    mission_id=(request or {}).get("mission_id"),
                    session_id=(request or {}).get("session_id"),
                )
            path = persist_pattern(pattern, root=root)
            out = {
                "ok": True,
                "status": "emitted",
                "pattern": pattern,
                "pattern_path": str(path),
            }
            _lineage_after(request, "emit", {"pattern_id": pattern.get("pattern_id")})
            return _with_ul_substrate(out, request)
        if action == "handoff":
            pattern_id = str((request or {}).get("pattern_id") or "")
            pattern = (request or {}).get("pattern")
            if pattern is None:
                pattern = load_pattern(pattern_id, root=root)
            result = admit_to_story_forge(pattern, story_forge_root=sf_root)
            ok = result.get("status") == "admitted"
            out = {
                "ok": ok,
                "status": result.get("status"),
                "result": result,
            }
            if ok:
                _lineage_after(
                    request,
                    "handoff",
                    {"pattern_id": pattern.get("pattern_id"), "admission_path": result.get("admission_path")},
                )
            return _with_ul_substrate(out, request)
        if action == "grok_render":
            from src.imagine_grok import KeysRequiredError, render_grok_for_pattern

            pattern_id = str((request or {}).get("pattern_id") or "")
            pattern = (request or {}).get("pattern")
            try:
                if pattern is not None:
                    from src.imagine_grok import grok_render_pattern

                    render_result = grok_render_pattern(
                        pattern,
                        transport=(request or {}).get("transport"),
                        imagine_root=root,
                    )
                else:
                    render_result = render_grok_for_pattern(
                        pattern_id,
                        imagine_root=root,
                        transport=(request or {}).get("transport"),
                    )
                out = {
                    "ok": True,
                    "status": "rendered",
                    "result": render_result,
                    "artifact": render_result.get("artifact"),
                }
                _lineage_after(
                    request,
                    "grok_render",
                    {
                        "pattern_id": pattern_id or (pattern or {}).get("pattern_id"),
                        "provider": "xai",
                    },
                )
                return _with_ul_substrate(out, request)
            except KeysRequiredError as exc:
                return _with_ul_substrate(
                    {
                        "ok": False,
                        "status": "rejected",
                        "error_type": "KeysRequired",
                        "message": str(exc),
                    },
                    request,
                )
        return _with_ul_substrate(
            {
                "ok": False,
                "status": "rejected",
                "error_type": "ValidationRejected",
                "message": f"unsupported action: {action}",
            },
            request,
        )
    except Exception as exc:  # noqa: BLE001
        return _with_ul_substrate(
            {
                "ok": False,
                "status": "rejected",
                "error_type": "ExecutionError",
                "message": str(exc),
            },
            request,
        )


__all__ = [
    "IMAGINE_GENERATOR_CAPABILITY_COMPONENT_ID",
    "ensure_imagine_generator_capability_registered",
    "run_imagine_generator_capability",
]
