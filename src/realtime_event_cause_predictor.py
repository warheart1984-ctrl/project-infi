"""Realtime event-and-cause prediction packets for the governed AAIS fast lane.

The predictor stays advisory and lightweight: it consumes local realtime deltas,
computes compact event and cause forecasts, and emits `rt` channel packets that
still route through God Brain and Jarvis before reaching Nova.
"""

from __future__ import annotations

def _wrap_ul_payload(payload: dict) -> dict:
    from src.aais_ul_substrate import attach_ul_substrate

    return attach_ul_substrate(dict(payload))
from dataclasses import dataclass
from datetime import datetime, timedelta
from src.datetime_compat import UTC
import json
from typing import Any

from src.governed_direct_pipeline import DIRECT_COGNITIVE_LANE, build_pipeline_packet
from src.phase_gate import (
    ComponentNotRegisteredError,
    GovernedComponent,
    Phase,
    PhaseGateError,
    PhaseViolationError,
    assert_executable,
    get_component,
    is_executable,
    register_component,
)


MODULE_ID = "aais.realtime_event_cause_predictor"
MODULE_VERSION = "0.1"
REALTIME_CHANNEL = "rt"
PACKET_SIZE_LIMIT_BYTES = 400
DEFAULT_HORIZON_MS = 180
MIN_HORIZON_MS = 50
MAX_HORIZON_MS = 500
PREDICTOR_COMPONENT_ID = "jarvis.realtime_event_cause_predictor"
PREDICTOR_ALLOWED_CONTEXTS = ("live_runtime", "operator_runtime")
INTERPRETED_STATUS_BOUNDED = "bounded_inference"
INTERPRETED_STATUS_INSUFFICIENT = "insufficient_data"
INTERPRETED_STATUS_PHASE_BLOCKED = "phase_blocked"

CAUSE_CLASSES = {
    "steady_state",
    "operator_service_request",
    "service_lane_request",
    "system_posture_shift",
    "immune_guard_intervention",
    "pipeline_transition",
    "conflicting_signal_state",
    "insufficient_signal",
    "unknown_state",
    "phase_gate_block",
}
RECOMMENDED_STATES = {"proceed", "pause", "degrade_safe", "observe"}
DATA_SUFFICIENCY_STATES = {"sufficient", "partial", "insufficient"}
MAX_SUPPORTING_SIGNALS = 4

EVENT_CODES = {
    "steady_state": 0,
    "focus_shift": 1,
    "intent_commit": 2,
    "intent_drift": 3,
    "escalation_risk": 4,
    "recovery_window": 5,
    "system_transition": 6,
    "session_transition": 7,
}

CAUSE_CODES = {
    "keyboard_acceleration": 1,
    "keyboard_deceleration": 2,
    "rhythm_turbulence": 3,
    "rhythm_pause": 4,
    "bpm_surge": 5,
    "bpm_drop": 6,
    "temperature_rise": 7,
    "user_mode_shift": 8,
    "system_mode_shift": 9,
    "context_switch": 10,
}

SYSTEM_STRAIN_MODES = {"caution", "elevated", "degraded", "blocked", "crisis"}


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _clamp_int(value: Any, *, minimum: int, maximum: int, fallback: int) -> int:
    try:
        numeric = int(round(float(value)))
    except (TypeError, ValueError):
        numeric = fallback
    return max(minimum, min(maximum, numeric))


def _maybe_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_mode(value: Any, default: str) -> str:
    normalized = " ".join(str(value or "").split()).strip().lower()
    return normalized or default


def _normalize_context_ref(value: Any) -> str:
    normalized = " ".join(str(value or "").split()).strip()
    return normalized or "ctx0"


def _normalize_runtime_context(value: Any) -> str:
    normalized = " ".join(str(value or "").split()).strip().lower()
    return normalized or "live_runtime"


def _normalize_observed_at(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, (int, float)):
        stamp = float(value)
        if stamp > 10_000_000_000:
            stamp /= 1000.0
        return datetime.fromtimestamp(stamp, tz=UTC)
    if isinstance(value, str) and value.strip():
        raw = value.strip()
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError:
            return _utc_now()
        return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    return _utc_now()


def _dedupe_codes(values: list[int]) -> list[int]:
    seen: set[int] = set()
    ordered: list[int] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _dedupe_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        normalized = " ".join(str(value or "").split()).strip().lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return ordered


def _round_confidence(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 2)


@dataclass(slots=True)
class Observation:
    """Normalized realtime snapshot consumed by the predictor."""

    context_ref: str
    keyboard_rhythm: float | None
    bpm: float | None
    temperature_c: float | None
    user_mode: str
    system_mode: str
    observed_at: datetime
    horizon_ms: int


@dataclass(slots=True)
class PredictorState:
    """Minimal internal state for delta-based prediction."""

    last_observation: Observation | None = None
    tick_count: int = 0


class RealtimeEventCausePredictor:
    """Lightweight heuristic predictor that stays safe for the AAIS fast lane."""

    def __init__(self, *, default_horizon_ms: int = DEFAULT_HORIZON_MS):
        self.default_horizon_ms = _clamp_int(
            default_horizon_ms,
            minimum=MIN_HORIZON_MS,
            maximum=MAX_HORIZON_MS,
            fallback=DEFAULT_HORIZON_MS,
        )
        self.state = PredictorState()

    def predict(self, observation: dict[str, Any]) -> dict[str, Any]:
        current = self._normalize_observation(observation)
        previous = self.state.last_observation
        causes = self._predict_causes(previous, current)
        event_code = self._predict_event(previous, current, causes)
        confidence = self._confidence_for(event_code, causes, current)
        horizon_ms = self._horizon_for(event_code, current)
        self.state.tick_count += 1
        event_ref = f"ev{event_code}_{self.state.tick_count}"
        event_timestamp = current.observed_at + timedelta(milliseconds=horizon_ms)

        prediction = {
            "module_id": MODULE_ID,
            "version": MODULE_VERSION,
            "event_code": event_code,
            "cause_codes": list(causes),
            "confidence": confidence,
            "horizon_ms": horizon_ms,
            "event_ref": event_ref,
            "context_ref": current.context_ref,
            "observed_at": current.observed_at.isoformat(),
            "event_timestamp": int(event_timestamp.timestamp()),
            "user_mode": current.user_mode,
            "system_mode": current.system_mode,
            "advisory_only": True,
        }
        self.state.last_observation = current
        return prediction

    def build_trace(self, observation: dict[str, Any]) -> dict[str, Any]:
        prediction = self.predict(observation)
        packets = build_prediction_packets(prediction)
        validation = validate_prediction_trace(packets)
        return _wrap_ul_payload({
            "module_id": MODULE_ID,
            "version": MODULE_VERSION,
            "summary": "Realtime predictor emitted bounded event/cause packets on the rt channel.",
            "prediction": prediction,
            **packets,
            "validation": validation,
        })

    def interpret_signal_feed(
        self,
        signal_feed: dict[str, Any] | None,
        *,
        runtime_context: str | None = None,
    ) -> dict[str, Any]:
        """Interpret one governed realtime signal feed into a bounded event state."""
        feed = self._normalize_signal_feed(signal_feed)
        normalized_context = _normalize_runtime_context(runtime_context or feed.get("runtime_context"))
        phase_gate = self._evaluate_phase_gate(normalized_context)
        supporting_signals = self._supporting_signals(feed)
        if phase_gate["decision"] == "BLOCK":
            return _wrap_ul_payload({
                "module_id": MODULE_ID,
                "version": MODULE_VERSION,
                "status": INTERPRETED_STATUS_PHASE_BLOCKED,
                "cause_class": "phase_gate_block",
                "confidence": 0.0,
                "supporting_signals": supporting_signals,
                "conflict_flags": [],
                "data_sufficiency": "insufficient",
                "recommended_state": "pause",
                "runtime_context": normalized_context,
                "source_pipeline_id": feed.get("source_pipeline_id"),
                "signal_count": int(feed.get("signal_count") or 0),
                "phase_gate": phase_gate,
                "advisory_only": True,
            })

        conflict_flags = self._detect_conflict_flags(feed)
        data_sufficiency = self._data_sufficiency(feed, conflict_flags)
        interpreted = self._classify_signal_feed(
            feed,
            data_sufficiency=data_sufficiency,
            conflict_flags=conflict_flags,
        )
        interpreted.update(
            {
                "module_id": MODULE_ID,
                "version": MODULE_VERSION,
                "runtime_context": normalized_context,
                "source_pipeline_id": feed.get("source_pipeline_id"),
                "signal_count": int(feed.get("signal_count") or 0),
                "supporting_signals": supporting_signals[:MAX_SUPPORTING_SIGNALS],
                "conflict_flags": conflict_flags,
                "data_sufficiency": data_sufficiency,
                "phase_gate": phase_gate,
                "advisory_only": True,
            }
        )
        return interpreted

    def _ensure_phase_component(self) -> None:
        try:
            get_component(PREDICTOR_COMPONENT_ID)
            return
        except ComponentNotRegisteredError:
            pass

        try:
            register_component(
                GovernedComponent(
                    component_id=PREDICTOR_COMPONENT_ID,
                    name="Realtime Event Cause Predictor",
                    component_type="governed_predictor",
                    phase=Phase.ACTIVE,
                    allowed_contexts=list(PREDICTOR_ALLOWED_CONTEXTS),
                    notes="Bounded interpreter for governed realtime signal feeds.",
                    validation_metadata={
                        "module_id": MODULE_ID,
                        "consumes": "realtime_signal_feed",
                        "advisory_only": True,
                    },
                )
            )
        except PhaseGateError:
            pass

    def _evaluate_phase_gate(self, runtime_context: str) -> dict[str, Any]:
        self._ensure_phase_component()
        normalized_context = _normalize_runtime_context(runtime_context)
        try:
            component = get_component(PREDICTOR_COMPONENT_ID)
        except ComponentNotRegisteredError:
            component = None

        phase_state = {
            "component_id": PREDICTOR_COMPONENT_ID,
            "phase": component.phase.value if component else "unregistered",
            "allowed_contexts": list(component.allowed_contexts) if component else [],
            "runtime_context": normalized_context,
            "executable": is_executable(PREDICTOR_COMPONENT_ID, normalized_context) if component else False,
        }
        try:
            assert_executable(PREDICTOR_COMPONENT_ID, normalized_context)
        except PhaseViolationError as exc:
            return _wrap_ul_payload({
                "decision": "BLOCK",
                "reason": str(exc),
                "runtime_context": normalized_context,
                "component": phase_state,
            })
        return _wrap_ul_payload({
            "decision": "ALLOW",
            "reason": None,
            "runtime_context": normalized_context,
            "component": phase_state,
        })

    def _normalize_signal_feed(self, signal_feed: dict[str, Any] | None) -> dict[str, Any]:
        feed = dict(signal_feed or {})
        signals = []
        for raw_signal in list(feed.get("signals") or []):
            if not isinstance(raw_signal, dict):
                continue
            signals.append(
                {
                    "signal_type": _normalize_mode(raw_signal.get("signal_type"), ""),
                    "signal_class": _normalize_mode(raw_signal.get("signal_class"), ""),
                    "stable_key": _normalize_mode(raw_signal.get("stable_key"), ""),
                    "severity": _normalize_mode(raw_signal.get("severity"), "low"),
                    "status": _normalize_mode(raw_signal.get("status"), "observed"),
                    "data_sufficiency": _normalize_mode(raw_signal.get("data_sufficiency"), "partial"),
                    "attributes": dict(raw_signal.get("attributes") or {}),
                }
            )
        return _wrap_ul_payload({
            "source_pipeline_id": str(feed.get("source_pipeline_id") or "").strip() or None,
            "runtime_context": _normalize_runtime_context(feed.get("runtime_context")),
            "active_lane": _normalize_mode(feed.get("active_lane"), DIRECT_COGNITIVE_LANE),
            "traffic_class": _normalize_mode(feed.get("traffic_class"), "core_cognition"),
            "surface_node": _normalize_mode(feed.get("surface_node"), "jar"),
            "immune_response": str(feed.get("immune_response") or "ALLOW").strip().upper() or "ALLOW",
            "tool_type": _normalize_mode(feed.get("tool_type"), "") or None,
            "signal_count": _clamp_int(feed.get("signal_count"), minimum=0, maximum=32, fallback=len(signals)),
            "signals": signals,
            "packet_metrics": dict(feed.get("packet_metrics") or {}),
            "delta": dict(feed.get("delta") or {}),
            "validation": dict(feed.get("validation") or {}),
            "system_state": dict(feed.get("system_state") or {}),
        })

    def _supporting_signals(self, feed: dict[str, Any]) -> list[str]:
        return [
            signal["stable_key"] or f"{signal['signal_type']}:{signal['signal_class']}"
            for signal in list(feed.get("signals") or [])
            if signal.get("signal_type") and signal.get("signal_class")
        ]

    def _signal_list(self, feed: dict[str, Any], signal_type: str) -> list[dict[str, Any]]:
        normalized_type = _normalize_mode(signal_type, "")
        return [
            signal
            for signal in list(feed.get("signals") or [])
            if signal.get("signal_type") == normalized_type
        ]

    def _first_signal(self, feed: dict[str, Any], signal_type: str) -> dict[str, Any] | None:
        signals = self._signal_list(feed, signal_type)
        return signals[0] if signals else None

    def _detect_conflict_flags(self, feed: dict[str, Any]) -> list[str]:
        conflicts: list[str] = []
        packet_metrics = dict(feed.get("packet_metrics") or {})
        delta = dict(feed.get("delta") or {})
        runtime_signals = self._signal_list(feed, "runtime_boundary")
        lane_signals = self._signal_list(feed, "lane_activity")
        system_signals = self._signal_list(feed, "system_posture")
        tool_signals = self._signal_list(feed, "tool_activity")
        immune_signals = self._signal_list(feed, "immune_boundary")

        if len(runtime_signals) > 1:
            conflicts.append("multiple_runtime_boundaries")
        if len(lane_signals) > 1:
            conflicts.append("multiple_lane_activity_signals")
        if len(system_signals) > 1:
            conflicts.append("multiple_system_posture_signals")
        if feed.get("active_lane") == DIRECT_COGNITIVE_LANE and tool_signals:
            conflicts.append("direct_lane_with_tool_activity")
        if feed.get("active_lane") != DIRECT_COGNITIVE_LANE and not tool_signals:
            conflicts.append("service_lane_without_tool_activity")
        if int(packet_metrics.get("service_packet_count") or 0) > 0 and not tool_signals:
            conflicts.append("service_packets_without_tool_signal")
        if int(packet_metrics.get("service_packet_count") or 0) == 0 and feed.get("active_lane") != DIRECT_COGNITIVE_LANE:
            conflicts.append("service_lane_without_service_packets")
        if delta.get("stable_repeat") and int(delta.get("change_count") or 0) > 0:
            conflicts.append("stable_repeat_with_change_count")
        if feed.get("immune_response") == "ALLOW" and immune_signals:
            conflicts.append("immune_signal_without_immune_response")
        if feed.get("immune_response") != "ALLOW" and not immune_signals:
            conflicts.append("immune_response_without_signal")
        return _dedupe_strings(conflicts)

    def _data_sufficiency(self, feed: dict[str, Any], conflict_flags: list[str]) -> str:
        signals = list(feed.get("signals") or [])
        validation = dict(feed.get("validation") or {})
        packet_metrics = dict(feed.get("packet_metrics") or {})
        if not signals:
            return "insufficient"
        if not validation.get("signal_shape_uniform", False):
            return "insufficient"
        if not validation.get("runtime_context_explicit", False):
            return "insufficient"
        if not validation.get("packet_metrics_complete", False):
            return "partial"
        if not validation.get("delta_shape_complete", False):
            return "partial"
        if conflict_flags:
            return "partial"
        if int(packet_metrics.get("total_packet_count") or 0) <= 0:
            return "insufficient"
        return "sufficient"

    def _classify_signal_feed(
        self,
        feed: dict[str, Any],
        *,
        data_sufficiency: str,
        conflict_flags: list[str],
    ) -> dict[str, Any]:
        immune_signal = self._first_signal(feed, "immune_boundary")
        system_signal = self._first_signal(feed, "system_posture")
        tool_signal = self._first_signal(feed, "tool_activity")
        turn_delta_signal = self._first_signal(feed, "turn_delta")
        runtime_signal = self._first_signal(feed, "runtime_boundary")
        lane_signal = self._first_signal(feed, "lane_activity")
        delta = dict(feed.get("delta") or {})
        system_state = dict(feed.get("system_state") or {})

        if immune_signal:
            immune_response = str(immune_signal.get("attributes", {}).get("response") or feed.get("immune_response") or "ALLOW").strip().upper()
            return _wrap_ul_payload({
                "status": INTERPRETED_STATUS_BOUNDED,
                "cause_class": "immune_guard_intervention",
                "confidence": 0.95 if immune_response in {"REJECT", "QUARANTINE"} else 0.88,
                "recommended_state": "pause" if immune_response in {"REJECT", "QUARANTINE"} else "degrade_safe",
            })

        if data_sufficiency == "insufficient":
            return _wrap_ul_payload({
                "status": INTERPRETED_STATUS_INSUFFICIENT,
                "cause_class": "insufficient_signal",
                "confidence": 0.18,
                "recommended_state": "pause",
            })
        if conflict_flags:
            return _wrap_ul_payload({
                "status": INTERPRETED_STATUS_BOUNDED,
                "cause_class": "conflicting_signal_state",
                "confidence": 0.34,
                "recommended_state": "degrade_safe",
            })

        risk_level = _normalize_mode(system_state.get("risk_level"), "low")
        system_mode = _normalize_mode(system_state.get("system_mode"), "stable")
        if risk_level != "low" or system_mode in SYSTEM_STRAIN_MODES:
            return _wrap_ul_payload({
                "status": INTERPRETED_STATUS_BOUNDED,
                "cause_class": "system_posture_shift",
                "confidence": 0.82,
                "recommended_state": "degrade_safe",
            })

        if (
            runtime_signal
            and lane_signal
            and tool_signal
            and runtime_signal.get("signal_class") == "operator_runtime_active"
            and lane_signal.get("signal_class") == "service_lane_active"
        ):
            return _wrap_ul_payload({
                "status": INTERPRETED_STATUS_BOUNDED,
                "cause_class": "operator_service_request",
                "confidence": 0.91,
                "recommended_state": "proceed",
            })

        if lane_signal and tool_signal and lane_signal.get("signal_class") == "service_lane_active":
            return _wrap_ul_payload({
                "status": INTERPRETED_STATUS_BOUNDED,
                "cause_class": "service_lane_request",
                "confidence": 0.84 if data_sufficiency == "sufficient" else 0.61,
                "recommended_state": "proceed" if data_sufficiency == "sufficient" else "observe",
            })

        if turn_delta_signal and turn_delta_signal.get("signal_class") == "turn_shift_detected":
            change_count = int(delta.get("change_count") or 0)
            return _wrap_ul_payload({
                "status": INTERPRETED_STATUS_BOUNDED,
                "cause_class": "pipeline_transition",
                "confidence": _round_confidence(0.58 + min(change_count, 5) * 0.05),
                "recommended_state": "observe" if change_count <= 3 else "pause",
            })

        if turn_delta_signal and turn_delta_signal.get("signal_class") in {"turn_state_stable", "baseline_only"}:
            return _wrap_ul_payload({
                "status": INTERPRETED_STATUS_BOUNDED,
                "cause_class": "steady_state",
                "confidence": 0.87 if turn_delta_signal.get("signal_class") == "turn_state_stable" else 0.72,
                "recommended_state": "observe" if turn_delta_signal.get("signal_class") == "baseline_only" else "proceed",
            })

        return _wrap_ul_payload({
            "status": INTERPRETED_STATUS_BOUNDED,
            "cause_class": "unknown_state",
            "confidence": 0.31 if data_sufficiency == "partial" else 0.27,
            "recommended_state": "pause",
        })

    def _normalize_observation(self, observation: dict[str, Any] | None) -> Observation:
        source = dict(observation or {})
        return Observation(
            context_ref=_normalize_context_ref(source.get("context_ref") or source.get("ref")),
            keyboard_rhythm=_maybe_float(
                source.get("keyboard_rhythm")
                if "keyboard_rhythm" in source
                else source.get("rhythm")
            ),
            bpm=_maybe_float(source.get("bpm")),
            temperature_c=_maybe_float(
                source.get("temperature_c")
                if "temperature_c" in source
                else source.get("temp")
            ),
            user_mode=_normalize_mode(source.get("user_mode"), "normal"),
            system_mode=_normalize_mode(source.get("system_mode"), "stable"),
            observed_at=_normalize_observed_at(
                source.get("observed_at")
                if "observed_at" in source
                else source.get("ts")
            ),
            horizon_ms=_clamp_int(
                source.get("horiz")
                if "horiz" in source
                else source.get("horizon_ms"),
                minimum=MIN_HORIZON_MS,
                maximum=MAX_HORIZON_MS,
                fallback=self.default_horizon_ms,
            ),
        )

    def _predict_causes(
        self,
        previous: Observation | None,
        current: Observation,
    ) -> list[int]:
        causes: list[int] = []
        if previous is None:
            if current.context_ref != "ctx0":
                causes.append(CAUSE_CODES["context_switch"])
            return causes

        if current.context_ref != previous.context_ref:
            causes.append(CAUSE_CODES["context_switch"])
        if current.user_mode != previous.user_mode:
            causes.append(CAUSE_CODES["user_mode_shift"])
        if current.system_mode != previous.system_mode:
            causes.append(CAUSE_CODES["system_mode_shift"])

        rhythm_delta = None
        if current.keyboard_rhythm is not None and previous.keyboard_rhythm is not None:
            rhythm_delta = current.keyboard_rhythm - previous.keyboard_rhythm
            if rhythm_delta >= 0.25:
                causes.append(CAUSE_CODES["keyboard_acceleration"])
            if rhythm_delta <= -0.25:
                causes.append(CAUSE_CODES["keyboard_deceleration"])
            if abs(rhythm_delta) >= 0.4:
                causes.append(CAUSE_CODES["rhythm_turbulence"])
        if current.keyboard_rhythm is not None and current.keyboard_rhythm <= 0.12:
            causes.append(CAUSE_CODES["rhythm_pause"])

        if current.bpm is not None and previous.bpm is not None:
            bpm_delta = current.bpm - previous.bpm
            if bpm_delta >= 6:
                causes.append(CAUSE_CODES["bpm_surge"])
            if bpm_delta <= -6:
                causes.append(CAUSE_CODES["bpm_drop"])

        if current.temperature_c is not None and previous.temperature_c is not None:
            if current.temperature_c - previous.temperature_c >= 1.0:
                causes.append(CAUSE_CODES["temperature_rise"])

        return _dedupe_codes(causes)

    def _predict_event(
        self,
        previous: Observation | None,
        current: Observation,
        causes: list[int],
    ) -> int:
        cause_set = set(causes)
        if current.system_mode in SYSTEM_STRAIN_MODES or CAUSE_CODES["system_mode_shift"] in cause_set:
            return EVENT_CODES["system_transition"]
        if CAUSE_CODES["context_switch"] in cause_set:
            return EVENT_CODES["session_transition"]
        if CAUSE_CODES["rhythm_turbulence"] in cause_set or CAUSE_CODES["bpm_surge"] in cause_set:
            return EVENT_CODES["escalation_risk"]
        if CAUSE_CODES["keyboard_acceleration"] in cause_set and CAUSE_CODES["user_mode_shift"] in cause_set:
            return EVENT_CODES["intent_commit"]
        if CAUSE_CODES["keyboard_deceleration"] in cause_set or CAUSE_CODES["rhythm_pause"] in cause_set:
            return EVENT_CODES["recovery_window"]
        if CAUSE_CODES["user_mode_shift"] in cause_set:
            return EVENT_CODES["focus_shift"]
        if previous is not None and current.keyboard_rhythm is not None and previous.keyboard_rhythm is not None:
            if current.keyboard_rhythm < previous.keyboard_rhythm:
                return EVENT_CODES["intent_drift"]
        return EVENT_CODES["steady_state"]

    def _confidence_for(self, event_code: int, causes: list[int], current: Observation) -> int:
        score = 54 + (len(causes) * 8)
        if event_code in {
            EVENT_CODES["escalation_risk"],
            EVENT_CODES["system_transition"],
            EVENT_CODES["session_transition"],
        }:
            score += 14
        if current.system_mode in SYSTEM_STRAIN_MODES:
            score += 8
        return _clamp_int(score, minimum=35, maximum=97, fallback=70)

    def _horizon_for(self, event_code: int, current: Observation) -> int:
        if current.horizon_ms != self.default_horizon_ms:
            return current.horizon_ms
        if event_code in {EVENT_CODES["escalation_risk"], EVENT_CODES["system_transition"]}:
            return 90
        if event_code == EVENT_CODES["session_transition"]:
            return 120
        if event_code == EVENT_CODES["intent_commit"]:
            return 140
        if event_code == EVENT_CODES["recovery_window"]:
            return 220
        return self.default_horizon_ms


def _risk_level(prediction: dict[str, Any]) -> str:
    event_code = int(prediction.get("event_code", 0))
    if event_code in {
        EVENT_CODES["escalation_risk"],
        EVENT_CODES["system_transition"],
    }:
        return "elevated"
    return "low"


def _shared_state(prediction: dict[str, Any]) -> dict[str, str]:
    return _wrap_ul_payload({
        "user_mode": _normalize_mode(prediction.get("user_mode"), "normal"),
        "system_mode": _normalize_mode(prediction.get("system_mode"), "stable"),
        "risk_level": _risk_level(prediction),
    })


def _base_compact_payload(prediction: dict[str, Any]) -> dict[str, Any]:
    return _wrap_ul_payload({
        "ev": int(prediction["event_code"]),
        "ts": int(prediction["event_timestamp"]),
        "conf": int(prediction["confidence"]),
        "horiz": int(prediction["horizon_ms"]),
    })


def _event_payload(prediction: dict[str, Any]) -> dict[str, Any]:
    payload = _base_compact_payload(prediction)
    payload["ca"] = list(prediction["cause_codes"])
    return payload


def _cause_payload(prediction: dict[str, Any]) -> dict[str, Any]:
    payload = _base_compact_payload(prediction)
    payload["ca"] = list(prediction["cause_codes"])
    payload["ev_ref"] = str(prediction["event_ref"])
    return payload


def build_prediction_packets(prediction: dict[str, Any]) -> dict[str, Any]:
    """Build governed realtime packets for one prediction cycle."""

    ref = _normalize_context_ref(prediction.get("context_ref"))
    event_ref = str(prediction.get("event_ref") or "ev0")
    state = _shared_state(prediction)
    common_constraints = ["no_tools", "no_external", "bounded_reply"]
    event_payload = _event_payload(prediction)
    cause_payload = _cause_payload(prediction)
    govern_payload = {
        **cause_payload,
        "meaning": "prediction_delta",
        "constraints": common_constraints,
        "tone": "neutral",
    }

    forward_packets = [
        build_pipeline_packet(
            source="pred",
            target="gb",
            lane=DIRECT_COGNITIVE_LANE,
            compact_channel=REALTIME_CHANNEL,
            priority="high",
            intent="predict_event",
            state=state,
            payload={
                **event_payload,
                "meaning": "prediction_event",
                "constraints": common_constraints,
                "tone": "neutral",
            },
            compact_payload=event_payload,
            route=["pred", "gb"],
            ref=ref,
        ),
        build_pipeline_packet(
            source="pred",
            target="gb",
            lane=DIRECT_COGNITIVE_LANE,
            compact_channel=REALTIME_CHANNEL,
            priority="high",
            intent="predict_cause",
            state=state,
            payload={
                **cause_payload,
                "meaning": "prediction_cause",
                "constraints": common_constraints,
                "tone": "neutral",
            },
            compact_payload=cause_payload,
            route=["pred", "gb"],
            ref=event_ref,
        ),
        build_pipeline_packet(
            source="gb",
            target="jar",
            lane=DIRECT_COGNITIVE_LANE,
            compact_channel=REALTIME_CHANNEL,
            priority="high",
            intent="route",
            state=state,
            payload=govern_payload,
            compact_payload=cause_payload,
            route=["pred", "gb", "jar"],
            ref=event_ref,
        ),
        build_pipeline_packet(
            source="jar",
            target="nov",
            lane=DIRECT_COGNITIVE_LANE,
            compact_channel=REALTIME_CHANNEL,
            priority="high",
            intent="approve",
            state=state,
            payload={
                **govern_payload,
                "meaning": "approved_prediction_delta",
            },
            compact_payload=cause_payload,
            route=["pred", "gb", "jar", "nov"],
            ref=event_ref,
        ),
    ]
    return_packets = [
        build_pipeline_packet(
            source="nov",
            target="jar",
            lane=DIRECT_COGNITIVE_LANE,
            compact_channel=REALTIME_CHANNEL,
            priority="high",
            intent="ack",
            state=state,
            payload={
                "ev_ref": event_ref,
                "conf": int(prediction["confidence"]),
                "horiz": int(prediction["horizon_ms"]),
                "meaning": "prediction_ack",
                "constraints": ["bounded_reply"],
                "tone": "neutral",
            },
            compact_payload={
                "ev_ref": event_ref,
                "conf": int(prediction["confidence"]),
                "horiz": int(prediction["horizon_ms"]),
            },
            route=["nov", "jar"],
            ref=event_ref,
        ),
        build_pipeline_packet(
            source="jar",
            target="gb",
            lane=DIRECT_COGNITIVE_LANE,
            compact_channel=REALTIME_CHANNEL,
            priority="high",
            intent="ack",
            state=state,
            payload={
                "ev_ref": event_ref,
                "meaning": "prediction_ack",
                "constraints": ["bounded_reply"],
                "tone": "neutral",
            },
            compact_payload={"ev_ref": event_ref},
            route=["nov", "jar", "gb"],
            ref=event_ref,
        ),
        build_pipeline_packet(
            source="gb",
            target="pred",
            lane=DIRECT_COGNITIVE_LANE,
            compact_channel=REALTIME_CHANNEL,
            priority="high",
            intent="ack",
            state=state,
            payload={
                "ev_ref": event_ref,
                "meaning": "prediction_ack",
                "constraints": ["bounded_reply"],
                "tone": "neutral",
            },
            compact_payload={"ev_ref": event_ref},
            route=["nov", "jar", "gb", "pred"],
            ref=event_ref,
        ),
    ]
    return _wrap_ul_payload({
        "active_lane": DIRECT_COGNITIVE_LANE,
        "channel": REALTIME_CHANNEL,
        "forward_packets": forward_packets,
        "return_packets": return_packets,
    })


def _compact_packet_size(packet: dict[str, Any]) -> int:
    return len(json.dumps(packet.get("compact") or {}, separators=(",", ":"), sort_keys=True))


def validate_prediction_trace(trace: dict[str, Any]) -> dict[str, Any]:
    """Return deterministic validation results for a prediction trace."""

    forward_packets = list(trace.get("forward_packets") or [])
    return_packets = list(trace.get("return_packets") or [])
    all_packets = [*forward_packets, *return_packets]
    prediction_packets = [
        packet for packet in forward_packets if packet.get("intent") in {"predict_event", "predict_cause"}
    ]
    packet_sizes = {packet["packet_id"]: _compact_packet_size(packet) for packet in all_packets}

    return _wrap_ul_payload({
        "god_brain_in_path": any(
            packet.get("source") == "gb" or packet.get("target") == "gb" for packet in all_packets
        ),
        "jarvis_authority_preserved": any(packet.get("source") == "jar" for packet in forward_packets),
        "nova_edge_present": any(packet.get("target") == "nov" for packet in forward_packets),
        "rt_channel_only": all((packet.get("compact") or {}).get("ch") == REALTIME_CHANNEL for packet in all_packets),
        "no_service_tool_intents": all(
            packet.get("intent") not in {"tool_call", "tool_result"} for packet in all_packets
        ),
        "explicit_confidence": all((packet.get("compact") or {}).get("pl", {}).get("conf") is not None for packet in prediction_packets),
        "explicit_horizon": all((packet.get("compact") or {}).get("pl", {}).get("horiz") is not None for packet in prediction_packets),
        "packet_size_under_limit": all(size < PACKET_SIZE_LIMIT_BYTES for size in packet_sizes.values()),
        "packet_sizes": packet_sizes,
    })


def assert_valid_prediction_trace(trace: dict[str, Any]) -> None:
    """Raise a ValueError if a prediction trace violates the realtime contract."""

    validation = validate_prediction_trace(trace)
    failed = [name for name, ok in validation.items() if isinstance(ok, bool) and not ok]
    if failed:
        raise ValueError(f"Realtime prediction trace failed validation: {', '.join(failed)}")


def validate_interpreted_event_state(state: dict[str, Any]) -> dict[str, bool]:
    """Return validation flags for one bounded interpreted realtime state."""
    payload = dict(state or {})
    supporting_signals = list(payload.get("supporting_signals") or [])
    conflict_flags = list(payload.get("conflict_flags") or [])
    phase_gate = dict(payload.get("phase_gate") or {})
    return _wrap_ul_payload({
        "status_known": payload.get("status") in {
            INTERPRETED_STATUS_BOUNDED,
            INTERPRETED_STATUS_INSUFFICIENT,
            INTERPRETED_STATUS_PHASE_BLOCKED,
        },
        "cause_class_known": payload.get("cause_class") in CAUSE_CLASSES,
        "confidence_bounded": isinstance(payload.get("confidence"), (int, float)) and 0.0 <= float(payload.get("confidence")) <= 1.0,
        "recommended_state_known": payload.get("recommended_state") in RECOMMENDED_STATES,
        "data_sufficiency_known": payload.get("data_sufficiency") in DATA_SUFFICIENCY_STATES,
        "supporting_signals_bounded": len(supporting_signals) <= MAX_SUPPORTING_SIGNALS,
        "supporting_signals_shape": all(isinstance(signal, str) and signal.strip() for signal in supporting_signals),
        "conflict_flags_shape": all(isinstance(flag, str) and flag.strip() for flag in conflict_flags),
        "phase_gate_present": phase_gate.get("decision") in {"ALLOW", "BLOCK"},
        "advisory_only_true": payload.get("advisory_only") is True,
        "runtime_context_explicit": bool(str(payload.get("runtime_context") or "").strip()),
    })


def assert_valid_interpreted_event_state(state: dict[str, Any]) -> None:
    """Raise a ValueError if one interpreted realtime state violates the bounded contract."""
    validation = validate_interpreted_event_state(state)
    failed = [name for name, ok in validation.items() if isinstance(ok, bool) and not ok]
    if failed:
        raise ValueError(
            "Realtime interpreted event state failed validation: " + ", ".join(failed)
        )


realtime_event_cause_predictor = RealtimeEventCausePredictor()


def interpret_realtime_signal_feed(
    signal_feed: dict[str, Any] | None,
    *,
    runtime_context: str | None = None,
) -> dict[str, Any]:
    """Interpret one governed realtime signal feed with the module-level predictor."""
    return realtime_event_cause_predictor.interpret_signal_feed(
        signal_feed,
        runtime_context=runtime_context,
    )
