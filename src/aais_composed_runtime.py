"""AAIS Composed Turn Runtime — Spine doctrine, ARIS admission, Nova Cortex."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any

from src.aris_integration import build_aris_enforcement
from src.cog_runtime import nova_cortex_spec, summarize_cognitive_runtime_state
from src.cog_runtime.nova import nova_speaking_adapter
from src.cog_runtime.nova_face import (
    NOVA_FACE_BRIDGE_ID,
    bridge_nova_face_to_cortex_and_jarvis,
)

try:
    from slingshot.launch import resolve_slingshot_turn_config
except ImportError:  # pragma: no cover - optional during partial installs
    def resolve_slingshot_turn_config(_metadata):  # type: ignore[misc]
        return None

AAIS_COMPOSED_RUNTIME_ID = "aais.composed_turn"
AAIS_COMPOSED_RUNTIME_VERSION = "1.0"

SPINE_PRECEDENCE: tuple[str, ...] = (
    "law",
    "blueprint",
    "contract",
    "implementation",
    "pipeline",
    "tool",
)

SPINE_SURFACES: dict[str, str] = {
    "human_guide": "docs/spine/AAIS_HUMAN_GUIDE.md",
    "master_spec": "docs/spine/AAIS_MASTER_SPEC.md",
    "ai_contract": "docs/spine/AAIS_AI_OPERATING_CONTRACT.md",
    "stabilize_and_free": "docs/spine/STABILIZE_AND_FREE.md",
    "runtime_map": "docs/runtime/AAIS_SUBSYSTEM_SPEC.md",
}

COMPOSED_PIPELINE: tuple[str, ...] = (
    "aais_spine",
    "aris_admission",
    "nova_face",
    "nova_cortex",
    "jarvis_core",
    "speaking_optional",
)

COMPOSED_TURN_MODES: tuple[str, ...] = ("instant", "fast", "full")

COMPOSED_TURN_V2_2_INVARIANTS: tuple[dict[str, str], ...] = (
    {
        "id": "super_nova_gate_before_compose",
        "rule": "Super Nova phase and activation gates must pass before composed turn runs.",
    },
    {
        "id": "super_nova_activation_cache",
        "rule": "A valid Super Nova activation token satisfies gate checks until watchdog revokes it.",
    },
    {
        "id": "operator_instant_compose",
        "rule": "Every Jarvis operator turn records Spine doctrine and ARIS admission even when cortex is off.",
    },
    {
        "id": "operator_fast_compose",
        "rule": "Operator cognitive turns default to fast path (reasoning + attention only) unless decision frame or full compose is requested.",
    },
    {
        "id": "aris_before_cortex",
        "rule": "ARIS non-copy admission must pass before Nova Cortex executes.",
    },
    {
        "id": "jarvis_authority",
        "rule": "Jarvis Core retains routing, state, and safety authority on every composed turn.",
    },
)


def _json_safe(value: Any) -> Any:
    if callable(value):
        return getattr(value, "__name__", "callable")
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


@dataclass(slots=True)
class ComposedTurnResult:
    """One governed turn across Spine, ARIS, and Nova Cortex."""

    runtime_id: str = AAIS_COMPOSED_RUNTIME_ID
    runtime_version: str = AAIS_COMPOSED_RUNTIME_VERSION
    status: str = "completed"
    user_message: str = ""
    spine: dict[str, Any] = field(default_factory=dict)
    aris: dict[str, Any] = field(default_factory=dict)
    nova_bridge: dict[str, Any] | None = None
    speaking_reply: str | None = None
    cognitive_summary: dict[str, Any] | None = None
    trace: list[dict[str, Any]] = field(default_factory=list)
    reason_codes: list[str] = field(default_factory=list)
    compose_mode: str = "instant"
    compose_ms: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(
            {
                "runtime_id": self.runtime_id,
                "runtime_version": self.runtime_version,
                "status": self.status,
                "compose_mode": self.compose_mode,
                "user_message": self.user_message,
                "pipeline": list(COMPOSED_PIPELINE),
                "spine": dict(self.spine),
                "aris": dict(self.aris),
                "nova_bridge": dict(self.nova_bridge) if self.nova_bridge else None,
                "speaking_reply": self.speaking_reply,
                "cognitive_summary": dict(self.cognitive_summary) if self.cognitive_summary else None,
                "trace": list(self.trace),
                "reason_codes": list(self.reason_codes),
                "compose_ms": self.compose_ms,
            }
        )


def build_spine_doctrine_envelope() -> dict[str, Any]:
    """Return bounded AAIS Spine doctrine references for turn receipts."""
    return {
        "doctrine": "stabilize_and_free",
        "precedence": list(SPINE_PRECEDENCE),
        "surfaces": dict(SPINE_SURFACES),
        "authority_rule": "Nova may interpret; Jarvis must authorize.",
        "summary": (
            "Stability through defined law and bounded behavior precedes operator freedom "
            "through cognitive load reduction."
        ),
    }


def evaluate_aris_admission(
    *,
    request_payload: dict[str, Any] | None = None,
    session_metadata: dict[str, Any] | None = None,
    companion_turn: bool = False,
) -> dict[str, Any]:
    """Run ARIS non-copy admission on inbound turn material."""
    payload = dict(request_payload or {})
    metadata = dict(session_metadata or {})
    details = dict(payload)
    details.update(metadata.get("pattern_share") or {})
    details.update(metadata.get("external_admission") or {})
    packet_type = str(payload.get("packet_type") or "")
    if not packet_type:
        packet_type = "super_companion_turn" if payload.get("runtime_context") == "super_nova_live" else (
            "companion_turn" if companion_turn else "operator_turn"
        )
    return build_aris_enforcement(
        details=details,
        runtime_context=str(payload.get("runtime_context") or "live_runtime"),
        effectful=bool(payload.get("effectful")),
        source=str(payload.get("source") or "composed_turn"),
        packet_type=packet_type,
    )


def resolve_composed_turn_payload(
    session,
    request_payload: dict[str, Any] | None,
    *,
    companion_turn: bool = False,
    super_nova_turn: bool = False,
    user_message: str = "",
) -> tuple[dict[str, Any], str]:
    """Resolve compose mode and bridge payload for companion or Jarvis operator turns."""
    from src.cog_runtime.deliberation import should_activate_deliberation
    from src.speaking_runtime import infer_frame_kind

    payload = dict(request_payload or {})
    metadata = getattr(session, "metadata", {}) or {}
    slingshot_cfg = resolve_slingshot_turn_config(metadata)
    if slingshot_cfg and not companion_turn and not super_nova_turn:
        payload.update(
            {
                "cognitive_runtime": slingshot_cfg.get("cognitive_runtime", True),
                "runtime_context": slingshot_cfg.get("runtime_context", "jarvis_operator_live"),
                "packet_type": slingshot_cfg.get("packet_type", "operator_turn"),
                "cortex_fast_path": slingshot_cfg.get("cortex_fast_path", True),
            }
        )
        return payload, str(slingshot_cfg.get("compose_mode") or "fast")

    response_mode = str(
        payload.get("response_mode")
        or metadata.get("response_mode")
        or metadata.get("requested_response_mode")
        or "operator"
    )

    if super_nova_turn:
        payload.setdefault("cognitive_runtime", True)
        payload.setdefault("deliberation_llm", True)
        payload["runtime_context"] = "super_nova_live"
        payload["packet_type"] = "super_companion_turn"
        payload.pop("cortex_fast_path", None)
        return payload, "full"

    if companion_turn:
        payload.setdefault("cognitive_runtime", True)
        payload.pop("cortex_fast_path", None)
        return payload, "full"

    explicit = payload.get("cognitive_runtime")
    frame_kind = str(payload.get("frame_kind") or infer_frame_kind(user_message))
    wants_full = bool(payload.get("compose_full")) or should_activate_deliberation(
        user_message,
        frame_kind=frame_kind,
    )

    if explicit is False:
        payload["cognitive_runtime"] = False
        payload.pop("cortex_fast_path", None)
        return payload, "instant"

    if explicit is True or response_mode in {"think", "research", "debug"}:
        payload["cognitive_runtime"] = True
        payload["runtime_context"] = "jarvis_operator_live"
        payload["packet_type"] = "operator_turn"
        if response_mode == "think" or payload.get("operator_speaking_wrap"):
            payload.setdefault("speaking_runtime", True)
        if wants_full or response_mode in {"research", "debug"}:
            payload.pop("cortex_fast_path", None)
            return payload, "full"
        payload["cortex_fast_path"] = True
        return payload, "fast"

    payload.setdefault("cognitive_runtime", False)
    payload["runtime_context"] = "jarvis_operator_live"
    payload["packet_type"] = "operator_turn"
    payload.pop("cortex_fast_path", None)
    return payload, "instant"


def composed_runtime_spec() -> dict[str, Any]:
    """Machine-readable spec for the composed runtime."""
    cortex = nova_cortex_spec()
    return {
        "runtime_id": AAIS_COMPOSED_RUNTIME_ID,
        "version": AAIS_COMPOSED_RUNTIME_VERSION,
        "summary": (
            "Governed turn composition: AAIS Spine doctrine envelope, ARIS admission, "
            "Nova Face → Nova Cortex → Jarvis Core bridge."
        ),
        "pipeline": list(COMPOSED_PIPELINE),
        "spine": build_spine_doctrine_envelope(),
        "nova_cortex_family_id": cortex.get("family_id"),
        "nova_cortex_version": cortex.get("version"),
        "composition_rules": [
            {
                "id": "spine_first",
                "rule": "Every composed turn records spine doctrine and precedence.",
            },
            {
                "id": "aris_before_cortex",
                "rule": "ARIS admission must pass before Nova Cortex executes.",
            },
            {
                "id": "jarvis_authority",
                "rule": "Jarvis Core retains routing, state, and safety authority.",
            },
            {
                "id": "speaking_on_companion",
                "rule": "Companion turns may emit Speaking Runtime output when enabled.",
            },
        ],
        "compose_modes": list(COMPOSED_TURN_MODES),
        "invariants_v2_2": [dict(item) for item in COMPOSED_TURN_V2_2_INVARIANTS],
    }


def _default_speak_body(user_message: str, *, companion_turn: bool) -> str:
    if companion_turn:
        return (
            "This composed turn ran Nova Cortex without a model provider. "
            f"I heard: {user_message.strip()}. "
            "Connect Jarvis or pass a speak body for a full answer."
        )
    return (
        "Composed turn completed under Jarvis authority without a model reply. "
        f"Message: {user_message.strip()}"
    )


def run_composed_turn(
    session,
    user_message: str,
    *,
    request_payload: dict[str, Any] | None = None,
    companion_turn: bool = False,
    surface_profile: dict[str, Any] | None = None,
    speak_body: str | None = None,
    include_speaking_update: bool = False,
    emit_speaking: bool = False,
    compose_mode: str | None = None,
) -> ComposedTurnResult:
    """Execute Spine -> ARIS -> Nova Face/Cortex/Jarvis for one turn."""
    compose_started = time.perf_counter()
    payload = dict(request_payload or {})
    metadata = getattr(session, "metadata", {}) or {}
    if compose_mode is None:
        _, compose_mode = resolve_composed_turn_payload(
            session,
            payload,
            companion_turn=companion_turn,
            super_nova_turn=bool(payload.get("runtime_context") == "super_nova_live"),
            user_message=user_message,
        )
    metadata["composed_turn_mode"] = compose_mode
    metadata["cortex_fast_path"] = bool(payload.get("cortex_fast_path"))
    trace: list[dict[str, Any]] = [{"stage": "compose_mode", "status": compose_mode}]
    reason_codes: list[str] = []

    spine = build_spine_doctrine_envelope()
    trace.append({"stage": "aais_spine", "status": "recorded", "doctrine": spine["doctrine"]})

    aris = evaluate_aris_admission(
        request_payload=payload,
        session_metadata=metadata,
        companion_turn=companion_turn,
    )
    trace.append(
        {
            "stage": "aris_admission",
            "status": aris.get("status"),
            "share_mode": (aris.get("non_copy_clause") or {}).get("share_mode"),
        }
    )
    if aris.get("status") == "blocked":
        compose_ms = round((time.perf_counter() - compose_started) * 1000)
        result = ComposedTurnResult(
            status="blocked",
            user_message=user_message,
            compose_mode=compose_mode,
            spine=spine,
            aris=aris,
            trace=trace,
            reason_codes=["aris_non_copy_clause"],
            compose_ms=compose_ms,
        )
        session.metadata["aais_composed_turn"] = result.to_dict()
        return result

    from src.cog_runtime.formal.turn_agency import AgencyViolation
    from src.cog_runtime.spark_pipeline import (
        append_cortex_ledger_monotonic,
        evaluate_post_cortex_spine,
        evaluate_pre_cortex_spine,
        gate_speaking_output,
        project_coherence_after_cortex,
        run_agency_preservation,
        run_spark_self_tuning,
    )

    spine_eval = evaluate_pre_cortex_spine(
        metadata=metadata,
        aris=aris,
        companion_turn=companion_turn,
    )
    trace.append({"stage": "spine_pipeline", **spine_eval})
    if spine_eval.get("halted"):
        compose_ms = round((time.perf_counter() - compose_started) * 1000)
        result = ComposedTurnResult(
            status="blocked",
            user_message=user_message,
            compose_mode=compose_mode,
            spine=spine,
            aris=aris,
            trace=trace,
            reason_codes=list(spine_eval.get("reason_codes") or [f"spine_halt:{spine_eval.get('halt_stage')}"]),
            compose_ms=compose_ms,
        )
        session.metadata["aais_composed_turn"] = result.to_dict()
        return result

    bridge_result = bridge_nova_face_to_cortex_and_jarvis(
        session,
        payload,
        user_message,
        companion_turn=companion_turn,
        surface_profile=surface_profile,
    )
    nova_bridge = bridge_result.to_dict() if bridge_result is not None else None
    trace.append(
        {
            "stage": "nova_bridge",
            "bridge_id": NOVA_FACE_BRIDGE_ID,
            "face_id": (nova_bridge or {}).get("face", {}).get("face_id"),
            "cortex_active": bool((nova_bridge or {}).get("cortex")),
        }
    )

    projection = project_coherence_after_cortex(session)
    trace.append(
        {
            "stage": "coherence_projection",
            "status": "projected" if projection else "skipped",
            "has_focus": bool((projection or {}).get("focus")),
        }
    )

    try:
        agency_report = run_agency_preservation(session)
        trace.append({"stage": "agency_preservation", "status": "ok", **agency_report})
    except AgencyViolation as exc:
        compose_ms = round((time.perf_counter() - compose_started) * 1000)
        result = ComposedTurnResult(
            status="blocked",
            user_message=user_message,
            compose_mode=compose_mode,
            spine=spine,
            aris=aris,
            nova_bridge=nova_bridge,
            trace=trace,
            reason_codes=["agency_violation"],
            compose_ms=compose_ms,
        )
        session.metadata["aais_composed_turn"] = result.to_dict()
        session.metadata["agency_violation"] = exc.to_dict()
        return result

    slingshot_meta = dict(metadata.get("slingshot") or {})
    if slingshot_meta.get("active"):
        from src.cog_runtime.formal.turn_agency import capture_turn_boundary

        session.metadata["turn_boundary_after"] = capture_turn_boundary(session.metadata)
        from slingshot.midflight import apply_midflight_to_session, evaluate_slingshot_midflight_cortex

        cortex_midflight = evaluate_slingshot_midflight_cortex(
            session,
            packet=dict(slingshot_meta.get("packet") or {}),
            model_calls_this_turn=int(metadata.get("slingshot_model_calls") or 0),
        )
        session.metadata["slingshot_midflight_cortex"] = cortex_midflight
        if cortex_midflight.get("halt_turn"):
            apply_midflight_to_session(session, cortex_midflight)
            compose_ms = round((time.perf_counter() - compose_started) * 1000)
            result = ComposedTurnResult(
                status="blocked",
                user_message=user_message,
                compose_mode=compose_mode,
                spine=spine,
                aris=aris,
                nova_bridge=nova_bridge,
                trace=trace,
                reason_codes=["slingshot_midflight_halt"],
                compose_ms=compose_ms,
            )
            session.metadata["aais_composed_turn"] = result.to_dict()
            return result
        if cortex_midflight.get("escalate"):
            apply_midflight_to_session(session, cortex_midflight)

    ledger_report = append_cortex_ledger_monotonic(session)
    trace.append({"stage": "ledger_append", "status": ledger_report.get("status", "ok")})

    tuning = run_spark_self_tuning(session)
    if tuning:
        trace.append(
            {
                "stage": "self_tuning",
                "performance_score": (tuning.get("performance") or {}).get("score"),
            }
        )

    speaking_reply: str | None = None
    cortex_session = bridge_result.cortex_session if bridge_result is not None else None
    operator_speaking = bool(
        not companion_turn
        and payload.get("operator_speaking_wrap")
        and payload.get("speaking_runtime")
    )
    speaking_enabled = bool(
        operator_speaking
        or (
            emit_speaking
            and (
                speak_body is not None
                or payload.get("speaking_runtime", companion_turn or metadata.get("speaking_runtime_enabled"))
            )
        )
    )
    if cortex_session is not None and speaking_enabled:
        body = speak_body or _default_speak_body(user_message, companion_turn=companion_turn)
        wrapped = nova_speaking_adapter(
            cortex_session,
            body,
            include_update=include_speaking_update or companion_turn or operator_speaking,
        )
        if speak_body is not None:
            speaking_reply, gate_report = gate_speaking_output(session, user_message, wrapped)
            trace.append({"stage": "generation_gate", **gate_report})
            if not gate_report.get("emitted"):
                speaking_reply = None
                reason_codes.append("generation_gate_failed")
        else:
            speaking_reply = wrapped
            trace.append({"stage": "generation_gate", "deferred": True, "authoritative": False})

    post_spine = evaluate_post_cortex_spine(
        metadata=session.metadata,
        companion_turn=companion_turn,
        speaking_validation=session.metadata.get("speaking_validation") or {"valid": True},
    )
    trace.append({"stage": "spine_post_cortex", **post_spine})
    if post_spine.get("halted"):
        compose_ms = round((time.perf_counter() - compose_started) * 1000)
        result = ComposedTurnResult(
            status="blocked",
            user_message=user_message,
            compose_mode=compose_mode,
            spine=spine,
            aris=aris,
            nova_bridge=nova_bridge,
            trace=trace,
            reason_codes=list(post_spine.get("reason_codes") or [f"spine_halt:{post_spine.get('halt_stage')}"]),
            compose_ms=compose_ms,
        )
        session.metadata["aais_composed_turn"] = result.to_dict()
        return result

    if speaking_reply:
        trace.append({"stage": "speaking", "status": "completed", "chars": len(speaking_reply)})

    cognitive_summary = summarize_cognitive_runtime_state(session)
    compose_ms = round((time.perf_counter() - compose_started) * 1000)
    trace.append({"stage": "compose_timing", "status": "recorded", "compose_ms": compose_ms})
    result = ComposedTurnResult(
        status="completed",
        user_message=user_message,
        compose_mode=compose_mode,
        spine=spine,
        aris=aris,
        nova_bridge=nova_bridge,
        speaking_reply=speaking_reply,
        cognitive_summary=cognitive_summary,
        trace=trace,
        reason_codes=reason_codes,
        compose_ms=compose_ms,
    )
    session.metadata["aais_composed_turn"] = result.to_dict()
    return result


def summarize_composed_turn(session) -> dict[str, Any] | None:
    """Project composed turn receipt for API payloads."""
    stored = (getattr(session, "metadata", None) or {}).get("aais_composed_turn")
    if not isinstance(stored, dict):
        return None
    metadata = getattr(session, "metadata", None) or {}
    return {
        "runtime_id": stored.get("runtime_id"),
        "runtime_version": stored.get("runtime_version"),
        "status": stored.get("status"),
        "compose_mode": stored.get("compose_mode"),
        "pipeline": list(stored.get("pipeline") or COMPOSED_PIPELINE),
        "spine_doctrine": (stored.get("spine") or {}).get("doctrine"),
        "aris_status": (stored.get("aris") or {}).get("status"),
        "reason_codes": list(stored.get("reason_codes") or []),
        "nova_face_id": ((stored.get("nova_bridge") or {}).get("face") or {}).get("face_id"),
        "active_cognitive_runtimes": (
            ((stored.get("nova_bridge") or {}).get("jarvis_core") or {}).get("active_cognitive_runtimes")
            or []
        ),
        "compose_ms": stored.get("compose_ms"),
        "coherence_projection": metadata.get("coherence_projection"),
        "generation_gate": metadata.get("generation_gate"),
    }


def _cli_session(**metadata: Any) -> SimpleNamespace:
    return SimpleNamespace(metadata=dict(metadata))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run AAIS Composed Turn Runtime (Spine + ARIS + Nova Cortex).",
    )
    parser.add_argument("message", nargs="?", help="User message for the composed turn.")
    parser.add_argument(
        "--companion",
        action="store_true",
        help="Run as a Nova companion turn (Tiny/Small Nova surface).",
    )
    parser.add_argument(
        "--persona",
        default="tiny_nova",
        help="Companion persona mode when --companion is set (default: tiny_nova).",
    )
    parser.add_argument(
        "--response-mode",
        default="tiny",
        help="Companion response mode when --companion is set (default: tiny).",
    )
    parser.add_argument(
        "--spec",
        action="store_true",
        help="Print composed runtime JSON spec and exit.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print full composed turn receipt as JSON.",
    )
    args = parser.parse_args(argv)

    if args.spec:
        print(json.dumps(composed_runtime_spec(), indent=2, sort_keys=True))
        return 0

    if not args.message:
        parser.error("message is required unless --spec is passed")

    surface_profile = None
    metadata: dict[str, Any] = {}
    if args.companion:
        metadata = {"persona_mode": args.persona, "response_mode": args.response_mode}
        surface_profile = {
            "identity": args.persona,
            "label": args.persona.replace("_", " ").title(),
            "response_mode": args.response_mode,
            "continuity_profile": {
                "scope": args.persona,
                "tone": "companion",
            },
        }

    session = _cli_session(**metadata)
    result = run_composed_turn(
        session,
        args.message,
        request_payload={"cognitive_runtime": True},
        companion_turn=args.companion,
        surface_profile=surface_profile,
        emit_speaking=True,
    )

    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0 if result.status == "completed" else 2

    print(f"status: {result.status}")
    print(f"pipeline: {' -> '.join(COMPOSED_PIPELINE)}")
    if result.speaking_reply:
        print()
        print(result.speaking_reply)
    elif result.nova_bridge:
        runtimes = (
            (result.nova_bridge.get("jarvis_core") or {}).get("active_cognitive_runtimes") or []
        )
        print(f"active runtimes: {', '.join(runtimes) or 'none'}")
    if result.reason_codes:
        print(f"reasons: {', '.join(result.reason_codes)}")
    return 0 if result.status == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
