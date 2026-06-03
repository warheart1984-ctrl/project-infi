"""Operator Health Sentinel for governed AAIS runtime traces.

The Operator Health Sentinel protects the human operator without replacing the
operator. It observes structured runtime signals, estimates operator burden in a
bounded form, and emits advisory-only recommendations through governed trace
surfaces.
"""

# Mythic: Operator Health Sentinel Organ
# Engineering: OperatorHealthSentinelGate
from __future__ import annotations

from typing import Any

from src.module_governance import ModuleGovernanceController, module_governance
from src.phase_gate import (
    ComponentNotRegisteredError,
    GovernedComponent,
    Phase,
    PhaseGateError,
    PhaseViolationError,
    assert_executable,
    get_component,
    register_component,
)


MODULE_ID = "AAIS-OHS-01"
MODULE_VERSION = "0.1"
SENTINEL_COMPONENT_ID = "jarvis.operator_health_sentinel"
SENTINEL_ALLOWED_CONTEXTS = [
    "live_runtime",
    "operator_runtime",
    "test_harness",
]
SNAPSHOT_STATUS_ADVISORY = "advisory_snapshot"
SNAPSHOT_STATUS_BLOCKED = "observer_blocked"
OPERATOR_STATES = {"stable", "watch", "strained", "critical"}
RECOMMENDED_MODES = {
    "normal",
    "simplify",
    "safe_degrade",
    "pause_optional_complexity",
}
RECOMMENDED_ACTIONS = {
    "reduce_active_lanes",
    "pause_optional_modules",
    "prefer_direct_contract",
    "suppress_nonessential_traces",
    "defer_expansion_work",
    "enter_safe_degrade_mode",
    "request_operator_pause",
}
MAX_DOMINANT_FACTORS = 4
MAX_RECOMMENDED_ACTIONS = 4

OVERLOAD_PHRASES = (
    "too much",
    "not now",
    "brain fried",
    "too complex",
    "overloaded",
    "overwhelmed",
    "this is a lot",
    "slow down",
    "need a break",
)
CORRECTION_PHRASES = (
    "fix ",
    "repair ",
    "correct ",
    "redo ",
    "unblock ",
    "clean fix",
    "right move",
    "best next move",
    "guard it",
    "move it out of",
)
DOCTRINE_PHRASES = (
    "doctrine",
    "governance",
    "must not",
    "do not",
    "not allowed",
    "advisory-only",
    "advisory only",
    "bounded",
    "no autonomous",
    "do not bypass",
    "keep the split clean",
)
IDENTITY_PHRASES = (
    "replace the operator",
    "not replace the operator",
    "not a replacement",
    "protect the operator",
    "identity",
    "role",
    "direct answer",
    "one-contract mode",
    "lane correction",
)
CLARIFICATION_PHRASES = (
    "clarify",
    "what do you mean",
    "which one",
    "not clear",
    "be specific",
    "confusing",
)


def _clean_text(value: Any, *, limit: int = 280) -> str:
    normalized = " ".join(str(value or "").split()).strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def _normalize_runtime_context(value: Any) -> str:
    cleaned = _clean_text(value, limit=80).lower().replace("-", "_").replace(" ", "_")
    return cleaned or "live_runtime"


def _normalize_state(value: Any) -> str:
    cleaned = _clean_text(value, limit=48).lower().replace("-", "_").replace(" ", "_")
    return cleaned or "stable"


def _clamp_score(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = 0.0
    return max(0.0, min(1.0, numeric))


def _round_score(value: Any) -> float:
    return round(_clamp_score(value), 2)


def _phrase_count(text: str, phrases: tuple[str, ...]) -> int:
    if not text:
        return 0
    return sum(1 for phrase in phrases if phrase in text)


def _bounded_list(values: list[str], *, limit: int) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        normalized = _clean_text(value, limit=80).lower().replace(" ", "_")
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return ordered[:limit]


def build_operator_health_sentinel_module_spec(
    module_id: str = SENTINEL_COMPONENT_ID,
) -> dict[str, Any]:
    """Return a compliant module-governance spec for the advisory observer."""
    return {
        "module_id": module_id,
        "label": "Operator Health Sentinel",
        "lane": "human_system_governance",
        "declared_scope": [
            "governed_pipeline",
            "realtime_signal_feed",
            "operator_runtime_trace",
            "immune_protocol",
            "phase_gate",
            "module_governance",
            "operator_console",
        ],
        "declared_surfaces": [
            "live_runtime",
            "operator_runtime",
            "diagnostic_trace",
            "operator_console",
        ],
        "capabilities": [
            "operator_load_observation",
            "bounded_advisory_snapshot",
            "safe_degrade_recommendation",
            "phase_gate_visibility",
            "audit_trace",
        ],
        "cisiv": {
            "concept": {
                "status": "passed",
                "summary": "Observe structured operator-load signals without gaining execution authority.",
            },
            "identity": {
                "status": "passed",
                "summary": "Protect the operator through system-load observation rather than profiling, diagnosis, or hidden control.",
            },
            "structure": {
                "status": "passed",
                "summary": "Remain a parallel observer attached to governed trace surfaces and emit advisory-only snapshots.",
            },
            "implementation": {
                "status": "implemented",
                "summary": "The sentinel scores bounded runtime pressures and never mutates routing, memory, or execution behavior directly.",
            },
            "verification": {
                "status": "verified",
                "summary": "Coverage proves stable snapshots, safe degradation recommendations, and advisory-only guarantees.",
                "evidence": [
                    "pytest tests/test_operator_health_sentinel.py -q",
                    "pytest tests/test_governed_direct_pipeline.py -q",
                    "pytest tests/test_api.py -k governed_pipeline -q",
                ],
            },
        },
        "compliance": {
            "stores_persistent_user_metadata": False,
            "creates_user_identity_profiles": False,
            "retains_behavioral_history": False,
            "infers_user_labels": False,
            "builds_personality_models": False,
            "builds_behavior_models": False,
            "stores_live_signals": False,
            "reconstructs_signals": False,
            "requires_identity_history": False,
            "adaptive_logic_scope": "system",
            "alters_nova_tone": False,
            "alters_nova_role": False,
            "alters_nova_constancy": False,
            "bypasses_jarvis_authority": False,
            "bypasses_routing": False,
            "logs_user_identity": False,
            "logs_behavior_patterns": False,
            "logs_biometric_traces": False,
            "hidden_logging": False,
            "exfiltrates_data": False,
        },
    }


class OperatorHealthSentinel:
    """Observation-only evaluator for operator burden during governed turns."""

    def __init__(
        self,
        *,
        component_id: str = SENTINEL_COMPONENT_ID,
        module_governance_controller: ModuleGovernanceController | None = None,
        actor_id: str = "operator_health_sentinel",
    ):
        self.component_id = _clean_text(component_id, limit=120).lower().replace(" ", "_")
        self.module_governance_controller = module_governance_controller or module_governance
        self.actor_id = _clean_text(actor_id, limit=80) or "operator_health_sentinel"

    def observe(
        self,
        governed_pipeline: dict[str, Any] | None,
        *,
        runtime_context: str | None = None,
        operator_text: str | None = None,
        previous_pipeline: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        pipeline = dict(governed_pipeline or {})
        realtime_feed = dict(pipeline.get("realtime_signal_feed") or {})
        predictor = dict(pipeline.get("realtime_event_cause_predictor") or {})
        previous_snapshot = dict((previous_pipeline or {}).get("operator_health_sentinel") or {})
        normalized_runtime_context = _normalize_runtime_context(
            runtime_context or realtime_feed.get("runtime_context") or pipeline.get("runtime_context")
        )
        phase_gate = self._phase_gate_payload("ALLOW", runtime_context=normalized_runtime_context)
        try:
            assert_executable(self.component_id, normalized_runtime_context)
        except PhaseViolationError as exc:
            phase_gate = self._phase_gate_payload(
                "BLOCK",
                runtime_context=normalized_runtime_context,
                reason=str(exc),
            )
        module_governance_payload = self._module_governance_payload()
        if phase_gate["decision"] == "BLOCK" or module_governance_payload["decision"] == "BLOCK":
            return self._blocked_snapshot(
                runtime_context=normalized_runtime_context,
                phase_gate=phase_gate,
                module_governance_payload=module_governance_payload,
            )

        marker_counts = self._marker_counts(operator_text)
        observed_metrics = self._observed_metrics(
            realtime_feed=realtime_feed,
            predictor=predictor,
            previous_snapshot=previous_snapshot,
            marker_counts=marker_counts,
        )
        operator_state = self._operator_state(
            scores=observed_metrics["scores"],
            corroboration_count=observed_metrics["corroboration_count"],
            previous_snapshot=previous_snapshot,
            marker_counts=marker_counts,
        )
        recommended_mode = self._recommended_mode(operator_state)
        dominant_factors = self._dominant_factors(
            scores=observed_metrics["scores"],
            marker_counts=marker_counts,
            previous_snapshot=previous_snapshot,
            realtime_feed=realtime_feed,
        )
        recommended_actions = self._recommended_actions(
            operator_state=operator_state,
            dominant_factors=dominant_factors,
        )
        confidence = self._confidence(
            realtime_feed=realtime_feed,
            predictor=predictor,
            previous_snapshot=previous_snapshot,
            marker_counts=marker_counts,
            corroboration_count=observed_metrics["corroboration_count"],
        )

        scores = observed_metrics["scores"]
        return self._wrap_snapshot(
            {
            "module_id": MODULE_ID,
            "version": MODULE_VERSION,
            "status": SNAPSHOT_STATUS_ADVISORY,
            "operator_state": operator_state,
            "alert_status": operator_state,
            "cognitive_load_score": _round_score(scores["cognitive_load_score"]),
            "manual_arbitration_score": _round_score(scores["manual_arbitration_score"]),
            "drift_pressure_score": _round_score(scores["drift_pressure_score"]),
            "subsystem_tension_score": _round_score(scores["subsystem_tension_score"]),
            "identity_stress_score": _round_score(scores["identity_stress_score"]),
            "recommended_mode": recommended_mode,
            "recommended_actions": recommended_actions,
            "dominant_factors": dominant_factors,
            "confidence": _round_score(confidence),
            "runtime_context": normalized_runtime_context,
            "observed_inputs": {
                "signal_count": len(list(realtime_feed.get("signals") or [])),
                "change_count": int(dict(realtime_feed.get("delta") or {}).get("change_count") or 0),
                "active_lane": _clean_text(realtime_feed.get("active_lane"), limit=40).lower() or "unknown",
                "immune_response": _clean_text(realtime_feed.get("immune_response"), limit=40).upper() or "ALLOW",
                "has_previous_turn": bool(dict(realtime_feed.get("delta") or {}).get("has_previous_turn")),
            },
            "detected_markers": {
                "overload_signal_count": marker_counts["overload"],
                "correction_signal_count": marker_counts["correction"],
                "doctrine_signal_count": marker_counts["doctrine"],
                "identity_signal_count": marker_counts["identity"],
                "clarification_signal_count": marker_counts["clarification"],
            },
            "phase_gate": phase_gate,
            "module_governance": module_governance_payload,
            "advisory_only": True,
            "execution_rights": "none",
            "mutation_rights": "none",
            }
        )

    @staticmethod
    def _wrap_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
        from src.aais_ul_substrate import attach_ul_substrate

        return attach_ul_substrate(dict(snapshot))

    def _ensure_phase_component(self) -> dict[str, Any]:
        try:
            component = get_component(self.component_id)
        except ComponentNotRegisteredError:
            register_component(
                GovernedComponent(
                    component_id=self.component_id,
                    name="Operator Health Sentinel",
                    component_type="operator_governance_observer",
                    phase=Phase.ACTIVE,
                    allowed_contexts=list(SENTINEL_ALLOWED_CONTEXTS),
                    notes="Observation-first human-system governance module with advisory-only output.",
                    validation_metadata={
                        "module_id": MODULE_ID,
                        "advisory_only": True,
                        "execution_rights": "none",
                    },
                )
            )
            component = get_component(self.component_id)
        return {
            "component_id": component.component_id,
            "phase": component.phase.value,
            "allowed_contexts": list(component.allowed_contexts),
        }

    def _ensure_module_record(self) -> dict[str, Any]:
        record = self.module_governance_controller.get_module(self.component_id)
        if record is not None:
            return dict(record)
        admitted = self.module_governance_controller.admit_module(
            build_operator_health_sentinel_module_spec(self.component_id),
            actor_id=self.actor_id,
            actor_role="system",
        )
        return dict(admitted.get("module") or {})

    def _phase_gate_payload(
        self,
        decision: str,
        *,
        runtime_context: Any,
        reason: str | None = None,
    ) -> dict[str, Any]:
        component = self._ensure_phase_component()
        return {
            "decision": "ALLOW" if str(decision).upper() == "ALLOW" else "BLOCK",
            "component": component,
            "runtime_context": _normalize_runtime_context(runtime_context),
            "reason": _clean_text(reason) or None,
        }

    def _module_governance_payload(self) -> dict[str, Any]:
        record = self._ensure_module_record()
        status = _clean_text(record.get("status"), limit=40).lower() or "unknown"
        allowed = status == "admitted"
        return {
            "decision": "ALLOW" if allowed else "BLOCK",
            "module_id": self.component_id,
            "status": status,
            "reason": None if allowed else "Operator Health Sentinel is not admitted for runtime observation.",
        }

    def _blocked_snapshot(
        self,
        *,
        runtime_context: str,
        phase_gate: dict[str, Any],
        module_governance_payload: dict[str, Any],
    ) -> dict[str, Any]:
        return self._wrap_snapshot(
            {
            "module_id": MODULE_ID,
            "version": MODULE_VERSION,
            "status": SNAPSHOT_STATUS_BLOCKED,
            "operator_state": "stable",
            "alert_status": "stable",
            "cognitive_load_score": 0.0,
            "manual_arbitration_score": 0.0,
            "drift_pressure_score": 0.0,
            "subsystem_tension_score": 0.0,
            "identity_stress_score": 0.0,
            "recommended_mode": "normal",
            "recommended_actions": [],
            "dominant_factors": ["observer_blocked"],
            "confidence": 0.0,
            "runtime_context": runtime_context,
            "observed_inputs": {
                "signal_count": 0,
                "change_count": 0,
                "active_lane": "unknown",
                "immune_response": "ALLOW",
                "has_previous_turn": False,
            },
            "detected_markers": {
                "overload_signal_count": 0,
                "correction_signal_count": 0,
                "doctrine_signal_count": 0,
                "identity_signal_count": 0,
                "clarification_signal_count": 0,
            },
            "phase_gate": phase_gate,
            "module_governance": module_governance_payload,
            "advisory_only": True,
            "execution_rights": "none",
            "mutation_rights": "none",
            }
        )

    def _marker_counts(self, operator_text: str | None) -> dict[str, int]:
        normalized_text = _clean_text(operator_text, limit=1200).lower()
        return {
            "overload": _phrase_count(normalized_text, OVERLOAD_PHRASES),
            "correction": _phrase_count(normalized_text, CORRECTION_PHRASES),
            "doctrine": _phrase_count(normalized_text, DOCTRINE_PHRASES),
            "identity": _phrase_count(normalized_text, IDENTITY_PHRASES),
            "clarification": _phrase_count(normalized_text, CLARIFICATION_PHRASES),
        }

    def _observed_metrics(
        self,
        *,
        realtime_feed: dict[str, Any],
        predictor: dict[str, Any],
        previous_snapshot: dict[str, Any],
        marker_counts: dict[str, int],
    ) -> dict[str, Any]:
        signals = list(realtime_feed.get("signals") or [])
        packet_metrics = dict(realtime_feed.get("packet_metrics") or {})
        delta = dict(realtime_feed.get("delta") or {})
        system_state = dict(realtime_feed.get("system_state") or {})
        conflict_flags = list(predictor.get("conflict_flags") or [])
        risk_level = _normalize_state(system_state.get("risk_level") or "low")
        immune_response = _clean_text(realtime_feed.get("immune_response"), limit=40).upper() or "ALLOW"
        active_lane = _clean_text(realtime_feed.get("active_lane"), limit=40).lower() or "direct_cognitive"
        runtime_context = _normalize_runtime_context(realtime_feed.get("runtime_context"))
        change_count = max(0, min(int(delta.get("change_count") or 0), 10))
        total_packets = max(0, min(int(packet_metrics.get("total_packet_count") or len(signals)), 12))
        tool_signal_present = any(
            isinstance(signal, dict) and signal.get("signal_type") == "tool_activity"
            for signal in signals
        )
        predictor_cause = _normalize_state(predictor.get("cause_class") or "steady_state")
        predictor_recommended_state = _normalize_state(
            predictor.get("recommended_state") or "observe"
        )
        predictor_sufficiency = _normalize_state(
            predictor.get("data_sufficiency") or "partial"
        )

        risk_weight = {
            "low": 0.0,
            "caution": 0.15,
            "elevated": 0.22,
            "degraded": 0.3,
            "blocked": 0.42,
        }.get(risk_level, 0.1)
        immune_weight = {
            "ALLOW": 0.0,
            "CLAMP": 0.18,
            "REROUTE": 0.22,
            "REJECT": 0.36,
            "QUARANTINE": 0.45,
        }.get(immune_response, 0.1)
        recommended_state_weight = {
            "proceed": 0.02,
            "observe": 0.05,
            "degrade_safe": 0.22,
            "pause": 0.18,
        }.get(predictor_recommended_state, 0.06)

        cognitive = (
            (0.08 if signals else 0.0)
            + (0.18 if active_lane == "service_tools" else 0.04)
            + min(total_packets * 0.025, 0.18)
            + min(change_count * 0.05, 0.25)
            + risk_weight
            + immune_weight
            + recommended_state_weight
            + min(marker_counts["overload"] * 0.16, 0.32)
        )
        if predictor_sufficiency == "insufficient":
            cognitive -= 0.06

        manual_arbitration = (
            0.06
            + (0.18 if runtime_context == "operator_runtime" else 0.04)
            + (0.22 if active_lane == "service_tools" else 0.0)
            + min(change_count * 0.05, 0.25)
            + (0.12 if tool_signal_present else 0.0)
            + (0.08 if predictor_cause == "operator_service_request" else 0.0)
            + (0.06 if predictor_cause == "service_lane_request" else 0.0)
            + min(marker_counts["correction"] * 0.11, 0.28)
            + min(marker_counts["clarification"] * 0.12, 0.24)
        )

        drift_pressure = (
            min(marker_counts["doctrine"] * 0.14, 0.42)
            + min(marker_counts["correction"] * 0.08, 0.24)
            + (
                0.1
                if any(
                    bool(delta.get(key))
                    for key in (
                        "runtime_context_changed",
                        "response_mode_changed",
                        "contract_changed",
                    )
                )
                else 0.0
            )
            + (
                0.14
                if predictor_cause in {"conflicting_signal_state", "pipeline_transition"}
                else 0.0
            )
        )
        if (
            marker_counts["doctrine"] > 0
            and (
                float(previous_snapshot.get("drift_pressure_score") or 0.0) >= 0.35
                or "repeated_doctrine_correction"
                in list(previous_snapshot.get("dominant_factors") or [])
            )
        ):
            drift_pressure += 0.12

        subsystem_tension = (
            min(len(conflict_flags) * 0.12, 0.36)
            + (0.18 if risk_level in {"elevated", "degraded", "blocked"} else 0.0)
            + (0.16 if immune_response != "ALLOW" else 0.0)
            + (0.12 if active_lane == "service_tools" and change_count >= 3 else 0.0)
            + (
                0.16
                if predictor_cause
                in {"conflicting_signal_state", "immune_guard_intervention", "system_posture_shift"}
                else 0.0
            )
        )

        identity_stress = (
            min(marker_counts["identity"] * 0.14, 0.32)
            + (0.12 if bool(delta.get("surface_node_changed")) else 0.0)
            + (0.08 if bool(delta.get("response_mode_changed")) else 0.0)
            + (0.1 if predictor_cause == "conflicting_signal_state" else 0.0)
            + (0.06 if active_lane == "service_tools" and runtime_context == "operator_runtime" else 0.0)
        )

        scores = {
            "cognitive_load_score": self._blend_with_previous(
                cognitive,
                previous_snapshot.get("cognitive_load_score"),
            ),
            "manual_arbitration_score": self._blend_with_previous(
                manual_arbitration,
                previous_snapshot.get("manual_arbitration_score"),
            ),
            "drift_pressure_score": self._blend_with_previous(
                drift_pressure,
                previous_snapshot.get("drift_pressure_score"),
            ),
            "subsystem_tension_score": self._blend_with_previous(
                subsystem_tension,
                previous_snapshot.get("subsystem_tension_score"),
            ),
            "identity_stress_score": self._blend_with_previous(
                identity_stress,
                previous_snapshot.get("identity_stress_score"),
            ),
        }
        corroboration_count = sum(
            1
            for value in scores.values()
            if float(value) >= 0.45
        )
        if marker_counts["overload"] > 0:
            corroboration_count += 1
        if immune_response != "ALLOW" or risk_level in {"elevated", "degraded", "blocked"}:
            corroboration_count += 1
        return {
            "scores": scores,
            "corroboration_count": min(corroboration_count, 8),
        }

    def _blend_with_previous(self, current: float, previous: Any) -> float:
        current_value = _clamp_score(current)
        if not isinstance(previous, (int, float)):
            return current_value
        return _clamp_score((current_value * 0.72) + (float(previous) * 0.28))

    def _operator_state(
        self,
        *,
        scores: dict[str, float],
        corroboration_count: int,
        previous_snapshot: dict[str, Any],
        marker_counts: dict[str, int],
    ) -> str:
        composite = (
            (scores["cognitive_load_score"] * 0.3)
            + (scores["manual_arbitration_score"] * 0.28)
            + (scores["drift_pressure_score"] * 0.18)
            + (scores["subsystem_tension_score"] * 0.16)
            + (scores["identity_stress_score"] * 0.08)
        )
        previous_state = _normalize_state(previous_snapshot.get("operator_state") or "stable")
        severe_context = (
            marker_counts["overload"] > 0
            and (
                scores["manual_arbitration_score"] >= 0.75
                or scores["subsystem_tension_score"] >= 0.55
            )
        )
        if (
            composite >= 0.86
            and corroboration_count >= 4
            and (previous_state in {"strained", "critical"} or severe_context)
        ):
            return "critical"
        if (
            composite >= 0.62
            or (scores["manual_arbitration_score"] >= 0.75 and corroboration_count >= 2)
            or (
                scores["subsystem_tension_score"] >= 0.4
                and scores["manual_arbitration_score"] >= 0.65
                and corroboration_count >= 3
            )
        ):
            return "strained"
        if (
            composite >= 0.36
            or any(float(value) >= 0.5 for value in scores.values())
            or marker_counts["overload"] > 0
        ):
            return "watch"
        return "stable"

    def _recommended_mode(self, operator_state: str) -> str:
        return {
            "stable": "normal",
            "watch": "simplify",
            "strained": "safe_degrade",
            "critical": "pause_optional_complexity",
        }.get(operator_state, "normal")

    def _dominant_factors(
        self,
        *,
        scores: dict[str, float],
        marker_counts: dict[str, int],
        previous_snapshot: dict[str, Any],
        realtime_feed: dict[str, Any],
    ) -> list[str]:
        delta = dict(realtime_feed.get("delta") or {})
        immune_response = _clean_text(realtime_feed.get("immune_response"), limit=40).upper() or "ALLOW"
        candidates: list[tuple[str, float]] = []
        if scores["manual_arbitration_score"] >= 0.48:
            candidates.append(("high_manual_arbitration", scores["manual_arbitration_score"]))
        if scores["drift_pressure_score"] >= 0.38 and (
            marker_counts["doctrine"] > 0
            or "repeated_doctrine_correction"
            in list(previous_snapshot.get("dominant_factors") or [])
        ):
            candidates.append(("repeated_doctrine_correction", scores["drift_pressure_score"]))
        if scores["subsystem_tension_score"] >= 0.4:
            candidates.append(("subsystem_tension_rise", scores["subsystem_tension_score"]))
        if marker_counts["overload"] > 0:
            candidates.append(("explicit_overload_signal", 0.7))
        if scores["identity_stress_score"] >= 0.34:
            candidates.append(("identity_restoration_pressure", scores["identity_stress_score"]))
        if marker_counts["clarification"] > 0:
            candidates.append(("clarification_loop_pressure", 0.55))
        if (
            _clean_text(realtime_feed.get("active_lane"), limit=40).lower() == "service_tools"
            and int(delta.get("change_count") or 0) >= 2
        ):
            candidates.append(("lane_arbitration_pressure", 0.52))
        if immune_response != "ALLOW":
            candidates.append(("immune_guard_pressure", 0.6))
        ordered = [label for label, _score in sorted(candidates, key=lambda item: item[1], reverse=True)]
        return _bounded_list(ordered, limit=MAX_DOMINANT_FACTORS)

    def _recommended_actions(
        self,
        *,
        operator_state: str,
        dominant_factors: list[str],
    ) -> list[str]:
        actions: list[str] = []
        factors = set(dominant_factors)
        if operator_state == "watch":
            if "high_manual_arbitration" in factors or "lane_arbitration_pressure" in factors:
                actions.append("prefer_direct_contract")
            if "subsystem_tension_rise" in factors or "immune_guard_pressure" in factors:
                actions.append("suppress_nonessential_traces")
        elif operator_state == "strained":
            actions.extend(
                [
                    "reduce_active_lanes",
                    "prefer_direct_contract",
                    "suppress_nonessential_traces",
                ]
            )
            if "repeated_doctrine_correction" in factors:
                actions.append("defer_expansion_work")
            else:
                actions.append("enter_safe_degrade_mode")
        elif operator_state == "critical":
            actions.extend(
                [
                    "enter_safe_degrade_mode",
                    "pause_optional_modules",
                    "request_operator_pause",
                    "reduce_active_lanes",
                ]
            )
        return _bounded_list(actions, limit=MAX_RECOMMENDED_ACTIONS)

    def _confidence(
        self,
        *,
        realtime_feed: dict[str, Any],
        predictor: dict[str, Any],
        previous_snapshot: dict[str, Any],
        marker_counts: dict[str, int],
        corroboration_count: int,
    ) -> float:
        validation = dict(realtime_feed.get("validation") or {})
        predictor_sufficiency = _normalize_state(
            predictor.get("data_sufficiency") or "partial"
        )
        confidence = 0.3
        if list(realtime_feed.get("signals") or []):
            confidence += 0.12
        if validation.get("signal_shape_uniform"):
            confidence += 0.1
        if validation.get("packet_metrics_complete"):
            confidence += 0.08
        if previous_snapshot:
            confidence += 0.08
        if sum(marker_counts.values()) > 0:
            confidence += 0.08
        confidence += min(corroboration_count * 0.06, 0.24)
        if marker_counts["overload"] > 0:
            confidence += 0.08
        if predictor_sufficiency == "insufficient":
            confidence -= 0.12
        elif predictor_sufficiency == "partial":
            confidence -= 0.04
        return _clamp_score(confidence)


def validate_operator_health_snapshot(snapshot: dict[str, Any]) -> dict[str, bool]:
    """Return validation flags for one bounded operator health snapshot."""
    payload = dict(snapshot or {})
    dominant_factors = list(payload.get("dominant_factors") or [])
    recommended_actions = list(payload.get("recommended_actions") or [])
    phase_gate = dict(payload.get("phase_gate") or {})
    module_governance_payload = dict(payload.get("module_governance") or {})
    return {
        "status_known": payload.get("status") in {
            SNAPSHOT_STATUS_ADVISORY,
            SNAPSHOT_STATUS_BLOCKED,
        },
        "operator_state_known": payload.get("operator_state") in OPERATOR_STATES,
        "cognitive_load_bounded": isinstance(payload.get("cognitive_load_score"), (int, float))
        and 0.0 <= float(payload.get("cognitive_load_score")) <= 1.0,
        "manual_arbitration_bounded": isinstance(payload.get("manual_arbitration_score"), (int, float))
        and 0.0 <= float(payload.get("manual_arbitration_score")) <= 1.0,
        "drift_pressure_bounded": isinstance(payload.get("drift_pressure_score"), (int, float))
        and 0.0 <= float(payload.get("drift_pressure_score")) <= 1.0,
        "subsystem_tension_bounded": isinstance(payload.get("subsystem_tension_score"), (int, float))
        and 0.0 <= float(payload.get("subsystem_tension_score")) <= 1.0,
        "identity_stress_bounded": isinstance(payload.get("identity_stress_score"), (int, float))
        and 0.0 <= float(payload.get("identity_stress_score")) <= 1.0,
        "recommended_mode_known": payload.get("recommended_mode") in RECOMMENDED_MODES,
        "recommended_actions_known": len(recommended_actions) <= MAX_RECOMMENDED_ACTIONS
        and all(action in RECOMMENDED_ACTIONS for action in recommended_actions),
        "dominant_factors_bounded": len(dominant_factors) <= MAX_DOMINANT_FACTORS
        and all(isinstance(item, str) and item.strip() for item in dominant_factors),
        "confidence_bounded": isinstance(payload.get("confidence"), (int, float))
        and 0.0 <= float(payload.get("confidence")) <= 1.0,
        "phase_gate_present": phase_gate.get("decision") in {"ALLOW", "BLOCK"},
        "module_governance_present": module_governance_payload.get("decision") in {"ALLOW", "BLOCK"},
        "advisory_only_true": payload.get("advisory_only") is True,
        "execution_rights_none": payload.get("execution_rights") == "none",
        "mutation_rights_none": payload.get("mutation_rights") == "none",
        "runtime_context_explicit": bool(_clean_text(payload.get("runtime_context"), limit=40)),
    }


def assert_valid_operator_health_snapshot(snapshot: dict[str, Any]) -> None:
    """Raise ValueError if one operator health snapshot breaks the contract."""
    validation = validate_operator_health_snapshot(snapshot)
    failed = [name for name, ok in validation.items() if isinstance(ok, bool) and not ok]
    if failed:
        raise ValueError(
            "Operator health snapshot failed validation: " + ", ".join(failed)
        )


operator_health_sentinel = OperatorHealthSentinel()


def observe_operator_health(
    governed_pipeline: dict[str, Any] | None,
    *,
    runtime_context: str | None = None,
    operator_text: str | None = None,
    previous_pipeline: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Observe one governed pipeline turn with the module-level sentinel."""
    return operator_health_sentinel.observe(
        governed_pipeline,
        runtime_context=runtime_context,
        operator_text=operator_text,
        previous_pipeline=previous_pipeline,
    )
