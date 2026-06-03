"""Continuity Witness (AAIS-CW-01).

This module observes structured runtime traces over time and emits bounded,
deterministic drift signals. It never mutates routing, output, or execution.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import datetime
from src.datetime_compat import UTC
import json
import math
import os
from pathlib import Path
import threading
from typing import Any


MODULE_ID = "AAIS-CW-01"
MODULE_VERSION = "0.1"
ROLLING_WINDOW_LIMIT = 16
WATCH_THRESHOLD = 0.18
DRIFTING_THRESHOLD = 0.32
CRITICAL_THRESHOLD = 0.52
OBSERVATION_CONFIDENCE_FLOOR = 0.35


def _with_ul_observation(payload: dict[str, Any]) -> dict[str, Any]:
    from src.aais_ul_substrate import wrap_runtime_snapshot

    return wrap_runtime_snapshot(payload)


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1] / ".runtime"


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _normalize_slug(value: Any) -> str:
    return _normalize_text(value).lower().replace(" ", "_")


def _normalize_list(values: list[Any] | None) -> list[str]:
    normalized = [_normalize_slug(value) for value in list(values or [])]
    unique: list[str] = []
    for value in normalized:
        if not value or value in unique:
            continue
        unique.append(value)
    return unique


def _normalize_mapping(mapping: dict[str, Any] | None) -> dict[str, Any]:
    return dict(mapping or {})


def _count_truthy(values: list[bool]) -> int:
    return sum(1 for value in values if value)


def _dominant_tone(governed_pipeline: dict[str, Any]) -> str:
    packets = [
        *list(governed_pipeline.get("forward_packets") or []),
        *list(governed_pipeline.get("service_packets") or []),
        *list(governed_pipeline.get("return_packets") or []),
    ]
    tones = [
        _normalize_slug((packet.get("payload") or {}).get("tone"))
        for packet in packets
        if _normalize_slug((packet.get("payload") or {}).get("tone"))
    ]
    if not tones:
        return "neutral"
    counts = Counter(tones)
    return counts.most_common(1)[0][0]


def _subsystem_for_pipeline(governed_pipeline: dict[str, Any]) -> str:
    tool_type = _normalize_slug(governed_pipeline.get("tool_type"))
    capability = _normalize_mapping(governed_pipeline.get("capability"))
    capability_module = _normalize_slug(capability.get("module"))
    surface_identity = _normalize_slug(governed_pipeline.get("surface_identity"))
    surface_node = _normalize_slug(governed_pipeline.get("surface_node"))
    contract = _normalize_slug(governed_pipeline.get("contract"))

    if tool_type == "otem" or contract == "otem":
        return "OTEM"
    if surface_node == "nov" or "nova" in surface_identity:
        return "NOVA"
    if capability_module:
        return capability_module.upper()
    if tool_type.startswith("forge"):
        return "FORGE"
    if _normalize_slug(governed_pipeline.get("active_lane")) == "service_tools":
        return "SERVICE_BRIDGE"
    return "JARVIS"


def build_continuity_witness_input(governed_pipeline: dict[str, Any] | None) -> dict[str, Any]:
    """Build a structured fingerprint seed from governed pipeline data only."""
    governed_pipeline = dict(governed_pipeline or {})
    validation = _normalize_mapping(governed_pipeline.get("validation"))
    capability = _normalize_mapping(governed_pipeline.get("capability"))
    model_route = _normalize_mapping(governed_pipeline.get("model_route"))
    surface_identity = _normalize_slug(governed_pipeline.get("surface_identity") or "jarvis")
    surface_node = _normalize_slug(governed_pipeline.get("surface_node") or "jar")
    response_mode = _normalize_slug(governed_pipeline.get("response_mode") or "fast")
    contract = _normalize_slug(governed_pipeline.get("contract") or "direct_answer")
    runtime_context = _normalize_slug(governed_pipeline.get("runtime_context") or "live_runtime")
    active_lane = _normalize_slug(governed_pipeline.get("active_lane") or "direct_cognitive")
    traffic_class = _normalize_slug(governed_pipeline.get("traffic_class") or "core_cognition")
    tool_type = _normalize_slug(governed_pipeline.get("tool_type"))
    immune_protocol = _normalize_mapping(governed_pipeline.get("immune_protocol"))
    immune_response = _normalize_slug(immune_protocol.get("response") or "allow")
    coherence_protocol = _normalize_mapping(governed_pipeline.get("coherence_protocol"))
    coherence_response = _normalize_slug(coherence_protocol.get("response") or "allow")
    provider_hint = (
        _normalize_slug(model_route.get("id"))
        or _normalize_slug(capability.get("provider"))
        or "local"
    )

    authority_markers = _normalize_list(
        [
            "god_brain" if validation.get("god_brain_in_path") else None,
            "jarvis_authority" if validation.get("jarvis_authority_preserved") else None,
            "service_lane" if active_lane == "service_tools" else "direct_lane",
            "nova_surface" if surface_node == "nov" else None,
            "immune_boundary" if immune_response != "allow" else None,
            "coherence_boundary" if coherence_response != "allow" else None,
            "tool_traffic" if tool_type else None,
            "capability_bridge" if capability.get("module") else None,
            "operator_runtime" if runtime_context == "operator_runtime" else None,
            "companion_lane" if response_mode in {"tiny", "small"} else None,
        ]
    )
    doctrine_surfaces = _normalize_list(
        [
            "governed_direct_pipeline",
            "realtime_signal_feed",
            "realtime_event_cause_predictor",
            "immune_protocol",
            "coherence_protocol",
            "service_lane_governance" if active_lane == "service_tools" else "direct_lane_governance",
            "capability_service_bridge" if capability.get("module") else None,
            "otem_lane" if tool_type == "otem" else None,
        ]
    )
    identity_signals = _normalize_list(
        [
            f"surface:{surface_identity}",
            f"node:{surface_node}",
            f"mode:{response_mode}",
            f"contract:{contract}",
            f"runtime:{runtime_context}",
            f"traffic:{traffic_class}",
            f"tool:{tool_type}" if tool_type else None,
            f"capability:{_normalize_slug(capability.get('module'))}" if capability.get("module") else None,
        ]
    )
    fingerprint = {
        "authority_markers": authority_markers,
        "tone_band": _dominant_tone(governed_pipeline),
        "doctrine_surfaces": doctrine_surfaces,
        "identity_signals": identity_signals,
        "correction_events": 0,
        "fallback_events": 0,
        "routing_pattern": ":".join(
            value
            for value in (
                runtime_context,
                active_lane,
                surface_node,
                response_mode,
                contract,
                provider_hint,
            )
            if value
        ),
        "lane_type": active_lane,
    }
    return {
        "module_id": MODULE_ID,
        "version": MODULE_VERSION,
        "pipeline_id": _normalize_text(governed_pipeline.get("pipeline_id")),
        "subsystem": _subsystem_for_pipeline(governed_pipeline),
        "fingerprint": fingerprint,
        "observational": True,
        "signals_only": True,
    }


def _trace_doctrine_surfaces(
    response_trace: dict[str, Any] | None,
    provider_notice: dict[str, Any] | None,
) -> list[str]:
    response_trace = dict(response_trace or {})
    provider_notice = dict(provider_notice or {})
    return _normalize_list(
        [
            "prompt_assembly" if isinstance(response_trace.get("prompt_assembly"), dict) else None,
            "output_completion_guard" if isinstance(response_trace.get("output_completion"), dict) else None,
            "visible_scaffold_cleanup"
            if isinstance(response_trace.get("visible_scaffold_cleanup"), dict)
            else None,
            "anti_drift" if isinstance(response_trace.get("drift_state"), dict) else None,
            "capability_service_bridge"
            if isinstance(response_trace.get("capability_bridge"), dict)
            else None,
            "direct_challenge_module"
            if isinstance(response_trace.get("direct_challenge_profile"), dict)
            else None,
            "relational_lane"
            if isinstance(response_trace.get("relational_question_profile"), dict)
            else None,
            "otem_boundary" if isinstance(response_trace.get("otem_boundary"), dict) else None,
            "provider_fallback_notice"
            if _normalize_slug(provider_notice.get("status")) == "fallback"
            else None,
        ]
    )


def _correction_event_count(response_trace: dict[str, Any] | None) -> int:
    response_trace = dict(response_trace or {})
    output_completion = _normalize_mapping(response_trace.get("output_completion"))
    prompt_assembly = _normalize_mapping(response_trace.get("prompt_assembly"))
    visible_scaffold_cleanup = _normalize_mapping(response_trace.get("visible_scaffold_cleanup"))
    drift_state = _normalize_mapping(response_trace.get("drift_state"))
    otem_boundary = _normalize_mapping(response_trace.get("otem_boundary"))
    return _count_truthy(
        [
            bool(output_completion.get("completion_guard_applied")),
            bool(visible_scaffold_cleanup.get("applied")),
            any(
                int(prompt_assembly.get(key) or 0) > 0
                for key in (
                    "duplicates_removed",
                    "malformed_fragments_removed",
                    "budget_dropped",
                    "assistant_echoes_scrubbed",
                )
            ),
            _normalize_slug(drift_state.get("status")) in {"warned", "clamped", "blocked"},
            bool(otem_boundary.get("response_changed_at_egress")),
        ]
    )


def _fallback_event_count(
    response_trace: dict[str, Any] | None,
    provider_notice: dict[str, Any] | None,
) -> int:
    response_trace = dict(response_trace or {})
    provider_notice = dict(provider_notice or {})
    capability_bridge = _normalize_mapping(response_trace.get("capability_bridge"))
    return _count_truthy(
        [
            _normalize_slug(provider_notice.get("status")) == "fallback",
            capability_bridge.get("ok") is False,
        ]
    )


def _merge_fingerprint(
    seed: dict[str, Any],
    *,
    governed_pipeline: dict[str, Any],
    response_trace: dict[str, Any] | None,
    provider_notice: dict[str, Any] | None,
) -> dict[str, Any]:
    fingerprint = deepcopy(dict(seed.get("fingerprint") or {}))
    response_trace = dict(response_trace or {})
    provider_notice = dict(provider_notice or {})
    doctrine_surfaces = _normalize_list(
        list(fingerprint.get("doctrine_surfaces") or [])
        + _trace_doctrine_surfaces(response_trace, provider_notice)
    )
    capability_bridge = _normalize_mapping(response_trace.get("capability_bridge"))
    reasoning_objective = _normalize_slug(response_trace.get("reasoning_objective"))
    identity_signals = _normalize_list(
        list(fingerprint.get("identity_signals") or [])
        + [
            f"objective:{reasoning_objective}" if reasoning_objective else None,
            f"capability:{_normalize_slug(capability_bridge.get('module'))}"
            if capability_bridge.get("module")
            else None,
        ]
    )
    authority_markers = _normalize_list(
        list(fingerprint.get("authority_markers") or [])
        + [
            "direct_challenge_boundary"
            if isinstance(response_trace.get("direct_challenge_profile"), dict)
            else None,
            "relational_boundary"
            if isinstance(response_trace.get("relational_question_profile"), dict)
            else None,
            "anti_drift_containment"
            if _normalize_slug((_normalize_mapping(response_trace.get("drift_state"))).get("status"))
            in {"warned", "clamped", "blocked"}
            else None,
        ]
    )
    fingerprint["authority_markers"] = authority_markers
    fingerprint["doctrine_surfaces"] = doctrine_surfaces
    fingerprint["identity_signals"] = identity_signals
    fingerprint["correction_events"] = int(fingerprint.get("correction_events") or 0) + _correction_event_count(
        response_trace
    )
    fingerprint["fallback_events"] = int(fingerprint.get("fallback_events") or 0) + _fallback_event_count(
        response_trace,
        provider_notice,
    )
    if capability_bridge.get("module"):
        fingerprint["routing_pattern"] = ":".join(
            value
            for value in (
                _normalize_slug(governed_pipeline.get("runtime_context")),
                _normalize_slug(governed_pipeline.get("active_lane")),
                _normalize_slug(governed_pipeline.get("surface_node")),
                _normalize_slug(governed_pipeline.get("response_mode")),
                _normalize_slug(governed_pipeline.get("contract")),
                _normalize_slug(capability_bridge.get("module")),
                _normalize_slug(capability_bridge.get("provider")),
            )
            if value
        )
    return fingerprint


def _binary_frequency_distance(
    current_values: list[str],
    frequency_counts: dict[str, int],
    turn_count: int,
) -> float:
    current = set(_normalize_list(current_values))
    observed = {
        _normalize_slug(key)
        for key, value in dict(frequency_counts or {}).items()
        if _normalize_slug(key) and int(value or 0) > 0
    }
    universe = current | observed
    if not universe or turn_count <= 0:
        return 0.0
    total = 0.0
    for item in universe:
        frequency = int((frequency_counts or {}).get(item) or 0) / max(1, turn_count)
        total += abs((1.0 if item in current else 0.0) - frequency)
    return min(1.0, total / max(1, len(universe)))


def _categorical_distance(current_value: str, counts: dict[str, int], turn_count: int) -> float:
    current = _normalize_slug(current_value)
    normalized_counts = { _normalize_slug(key): int(value or 0) for key, value in dict(counts or {}).items() }
    if not current and not normalized_counts:
        return 0.0
    if turn_count <= 0:
        return 0.0
    return min(1.0, 1.0 - (normalized_counts.get(current, 0) / max(1, turn_count)))


def _numeric_distance(current_value: int, baseline_average: float) -> float:
    baseline = float(baseline_average or 0.0)
    return min(1.0, abs(float(current_value or 0) - baseline) / max(1.0, baseline + 1.0))


def _factor_distances(
    fingerprint: dict[str, Any],
    baseline: dict[str, Any],
    prior_turn_count: int,
) -> dict[str, float]:
    if prior_turn_count <= 0:
        return {
            "authority_markers": 0.0,
            "tone_band": 0.0,
            "doctrine_surfaces": 0.0,
            "identity_signals": 0.0,
            "correction_events": 0.0,
            "fallback_events": 0.0,
            "routing_pattern": 0.0,
            "lane_type": 0.0,
        }
    return {
        "authority_markers": _binary_frequency_distance(
            fingerprint.get("authority_markers") or [],
            baseline.get("authority_markers") or {},
            prior_turn_count,
        ),
        "tone_band": _categorical_distance(
            fingerprint.get("tone_band") or "",
            baseline.get("tone_band") or {},
            prior_turn_count,
        ),
        "doctrine_surfaces": _binary_frequency_distance(
            fingerprint.get("doctrine_surfaces") or [],
            baseline.get("doctrine_surfaces") or {},
            prior_turn_count,
        ),
        "identity_signals": _binary_frequency_distance(
            fingerprint.get("identity_signals") or [],
            baseline.get("identity_signals") or {},
            prior_turn_count,
        ),
        "correction_events": _numeric_distance(
            int(fingerprint.get("correction_events") or 0),
            float(baseline.get("correction_events_avg") or 0.0),
        ),
        "fallback_events": _numeric_distance(
            int(fingerprint.get("fallback_events") or 0),
            float(baseline.get("fallback_events_avg") or 0.0),
        ),
        "routing_pattern": _categorical_distance(
            fingerprint.get("routing_pattern") or "",
            baseline.get("routing_pattern") or {},
            prior_turn_count,
        ),
        "lane_type": _categorical_distance(
            fingerprint.get("lane_type") or "",
            baseline.get("lane_type") or {},
            prior_turn_count,
        ),
    }


def _identity_distance(factor_distances: dict[str, float]) -> tuple[float, list[str]]:
    weights = {
        "authority_markers": 0.12,
        "tone_band": 0.05,
        "doctrine_surfaces": 0.12,
        "identity_signals": 0.08,
        "correction_events": 0.10,
        "fallback_events": 0.14,
        "routing_pattern": 0.08,
        "lane_type": 0.14,
    }
    distance = sum(weights[key] * float(factor_distances.get(key) or 0.0) for key in weights)
    dominant = [
        name
        for name, _value in sorted(
            factor_distances.items(),
            key=lambda item: item[1],
            reverse=True,
        )
        if float(_value or 0.0) >= 0.12
    ][:4]
    return round(min(1.0, distance), 3), dominant


def _trajectory_velocity(recent: list[dict[str, Any]], current_distance: float) -> float:
    if not recent:
        return 0.0
    previous_distance = float(recent[-1].get("identity_distance") or 0.0)
    return round(current_distance - previous_distance, 3)


def _trajectory_direction(velocity: float) -> str:
    if velocity > 0.02:
        return "away_from_center"
    if velocity < -0.02:
        return "toward_center"
    return "steady"


def _trajectory_status(
    *,
    identity_distance: float,
    velocity: float,
    correction_events: int,
    fallback_events: int,
) -> str:
    rapid_shift = (
        identity_distance >= WATCH_THRESHOLD
        and correction_events >= 3
        and fallback_events >= 1
    )
    if identity_distance >= CRITICAL_THRESHOLD or rapid_shift:
        return "CRITICAL"
    if (
        identity_distance >= DRIFTING_THRESHOLD
        or (identity_distance >= WATCH_THRESHOLD and correction_events >= 3)
        or (identity_distance >= WATCH_THRESHOLD and correction_events >= 2 and fallback_events >= 1)
        or (
            identity_distance >= WATCH_THRESHOLD
            and velocity >= 0.18
            and (correction_events >= 2 or fallback_events >= 1)
        )
    ):
        return "DRIFTING"
    if (
        identity_distance >= WATCH_THRESHOLD
        or (identity_distance >= 0.12 and velocity >= 0.06)
        or correction_events >= 1
        or fallback_events >= 1
    ):
        return "WATCH"
    return "STABLE"


def _risk_level(status: str) -> str:
    return {
        "STABLE": "low",
        "WATCH": "moderate",
        "DRIFTING": "high",
        "CRITICAL": "critical",
    }.get(status, "low")


def _projected_crossing_turns(status: str, identity_distance: float, velocity: float) -> int | None:
    if velocity <= 0.0:
        return None
    next_threshold = {
        "STABLE": WATCH_THRESHOLD,
        "WATCH": DRIFTING_THRESHOLD,
        "DRIFTING": CRITICAL_THRESHOLD,
    }.get(status)
    if next_threshold is None or identity_distance >= next_threshold:
        return None
    remaining = max(0.0, next_threshold - identity_distance)
    return max(1, math.ceil(remaining / velocity))


def _confidence(
    *,
    prior_turn_count: int,
    doctrine_surfaces: list[str],
    authority_markers: list[str],
) -> float:
    score = OBSERVATION_CONFIDENCE_FLOOR
    score += min(0.4, prior_turn_count * 0.03)
    score += min(0.12, len(doctrine_surfaces) * 0.015)
    score += min(0.08, len(authority_markers) * 0.01)
    return round(min(0.98, score), 3)


def _new_subsystem_state() -> dict[str, Any]:
    return {
        "turn_count": 0,
        "baseline": {
            "authority_markers": {},
            "tone_band": {},
            "doctrine_surfaces": {},
            "identity_signals": {},
            "routing_pattern": {},
            "lane_type": {},
            "correction_events_avg": 0.0,
            "fallback_events_avg": 0.0,
        },
        "recent": [],
        "last_observation": None,
    }


def _increment_counter(counter: dict[str, int], values: list[str]) -> None:
    for value in _normalize_list(values):
        counter[value] = int(counter.get(value) or 0) + 1


def _increment_category(counter: dict[str, int], value: str) -> None:
    normalized = _normalize_slug(value)
    if not normalized:
        return
    counter[normalized] = int(counter.get(normalized) or 0) + 1


def _update_baseline(subsystem_state: dict[str, Any], fingerprint: dict[str, Any]) -> None:
    baseline = subsystem_state["baseline"]
    turn_count = int(subsystem_state.get("turn_count") or 0)
    _increment_counter(baseline["authority_markers"], fingerprint.get("authority_markers") or [])
    _increment_counter(baseline["doctrine_surfaces"], fingerprint.get("doctrine_surfaces") or [])
    _increment_counter(baseline["identity_signals"], fingerprint.get("identity_signals") or [])
    _increment_category(baseline["tone_band"], fingerprint.get("tone_band") or "")
    _increment_category(baseline["routing_pattern"], fingerprint.get("routing_pattern") or "")
    _increment_category(baseline["lane_type"], fingerprint.get("lane_type") or "")
    correction_events = float(fingerprint.get("correction_events") or 0.0)
    fallback_events = float(fingerprint.get("fallback_events") or 0.0)
    baseline["correction_events_avg"] = round(
        ((float(baseline.get("correction_events_avg") or 0.0) * turn_count) + correction_events)
        / max(1, turn_count + 1),
        4,
    )
    baseline["fallback_events_avg"] = round(
        ((float(baseline.get("fallback_events_avg") or 0.0) * turn_count) + fallback_events)
        / max(1, turn_count + 1),
        4,
    )


class ContinuityWitnessStore:
    """Persist per-subsystem drift observations without storing raw content."""

    def __init__(self, runtime_dir: str | Path | None = None):
        self.runtime_dir = Path(runtime_dir or _default_runtime_dir()) / "continuity_witness"
        self._lock = threading.Lock()
        self._state: dict[str, Any] = {}
        self._observation_cache: dict[str, dict[str, Any]] = {}
        self._load()

    @property
    def _state_path(self) -> Path:
        return self.runtime_dir / "state.json"

    def configure_runtime_dir(self, runtime_dir: str | Path) -> None:
        with self._lock:
            base_dir = Path(runtime_dir)
            self.runtime_dir = (
                base_dir
                if base_dir.name == "continuity_witness"
                else base_dir / "continuity_witness"
            )
            self._state = {}
            self._observation_cache = {}
            self._load()

    def reset(self) -> dict[str, Any]:
        with self._lock:
            self._state = {
                "module_id": MODULE_ID,
                "version": MODULE_VERSION,
                "updated_at": _utc_now_iso(),
                "subsystems": {},
            }
            self._observation_cache = {}
            self._persist_locked()
        return self.snapshot()

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            from src.aais_ul_substrate import wrap_runtime_snapshot

            return wrap_runtime_snapshot(deepcopy(self._state))

    def observe(
        self,
        *,
        governed_pipeline: dict[str, Any] | None,
        response_trace: dict[str, Any] | None = None,
        provider_notice: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        governed_pipeline = dict(governed_pipeline or {})
        if not governed_pipeline:
            return _with_ul_observation(
                {
                    "module_id": MODULE_ID,
                    "version": MODULE_VERSION,
                    "trajectory_status": "STABLE",
                    "risk_level": "low",
                    "dominant_drift_factors": [],
                    "confidence": OBSERVATION_CONFIDENCE_FLOOR,
                    "identity_distance": 0.0,
                    "trajectory_velocity": 0.0,
                    "direction": "steady",
                    "projected_crossing_turns": None,
                    "observation_only": True,
                    "signals_only": True,
                }
            )

        with self._lock:
            seed = governed_pipeline.get("continuity_witness_input")
            if not isinstance(seed, dict) or not seed:
                seed = build_continuity_witness_input(governed_pipeline)
            pipeline_id = _normalize_text(seed.get("pipeline_id") or governed_pipeline.get("pipeline_id"))
            if pipeline_id and pipeline_id in self._observation_cache:
                return _with_ul_observation(deepcopy(self._observation_cache[pipeline_id]))

            subsystem = _normalize_text(seed.get("subsystem") or _subsystem_for_pipeline(governed_pipeline))
            subsystem_key = subsystem or "JARVIS"
            subsystems = self._state.setdefault("subsystems", {})
            subsystem_state = subsystems.setdefault(subsystem_key, _new_subsystem_state())
            prior_turn_count = int(subsystem_state.get("turn_count") or 0)
            fingerprint = _merge_fingerprint(
                seed,
                governed_pipeline=governed_pipeline,
                response_trace=response_trace,
                provider_notice=provider_notice,
            )
            factor_distances = _factor_distances(
                fingerprint,
                subsystem_state.get("baseline") or {},
                prior_turn_count,
            )
            identity_distance, dominant_factors = _identity_distance(factor_distances)
            recent = list(subsystem_state.get("recent") or [])
            velocity = _trajectory_velocity(recent, identity_distance)
            direction = _trajectory_direction(velocity)
            trajectory_status = _trajectory_status(
                identity_distance=identity_distance,
                velocity=velocity,
                correction_events=int(fingerprint.get("correction_events") or 0),
                fallback_events=int(fingerprint.get("fallback_events") or 0),
            )
            projected_crossing_turns = _projected_crossing_turns(
                trajectory_status,
                identity_distance,
                velocity,
            )
            confidence = _confidence(
                prior_turn_count=prior_turn_count,
                doctrine_surfaces=fingerprint.get("doctrine_surfaces") or [],
                authority_markers=fingerprint.get("authority_markers") or [],
            )
            observation = {
                "module_id": MODULE_ID,
                "version": MODULE_VERSION,
                "subsystem": subsystem_key,
                "trajectory_status": trajectory_status,
                "risk_level": _risk_level(trajectory_status),
                "dominant_drift_factors": dominant_factors,
                "confidence": confidence,
                "identity_distance": identity_distance,
                "trajectory_velocity": velocity,
                "direction": direction,
                "projected_crossing_turns": projected_crossing_turns,
                "fingerprint": deepcopy(fingerprint),
                "baseline_turns": prior_turn_count,
                "rolling_window_size": min(ROLLING_WINDOW_LIMIT, len(recent) + 1),
                "persistent_turn_count": prior_turn_count + 1,
                "pipeline_id": pipeline_id or None,
                "observed_at": _utc_now_iso(),
                "observation_only": True,
                "signals_only": True,
                "mutates_routing": False,
                "mutates_output": False,
                "factor_distances": {
                    key: round(float(value or 0.0), 3)
                    for key, value in factor_distances.items()
                },
            }

            _update_baseline(subsystem_state, fingerprint)
            subsystem_state["turn_count"] = prior_turn_count + 1
            subsystem_state["recent"] = (
                recent
                + [
                    {
                        "observed_at": observation["observed_at"],
                        "pipeline_id": pipeline_id or None,
                        "trajectory_status": trajectory_status,
                        "identity_distance": identity_distance,
                        "trajectory_velocity": velocity,
                        "direction": direction,
                    }
                ]
            )[-ROLLING_WINDOW_LIMIT:]
            subsystem_state["last_observation"] = deepcopy(observation)
            self._state["updated_at"] = observation["observed_at"]
            if pipeline_id:
                self._observation_cache[pipeline_id] = deepcopy(observation)
                if len(self._observation_cache) > 128:
                    stale_key = next(iter(self._observation_cache))
                    self._observation_cache.pop(stale_key, None)
            self._persist_locked()
            return _with_ul_observation(deepcopy(observation))

    def _load(self) -> None:
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        if not self._state_path.exists():
            self._state = {
                "module_id": MODULE_ID,
                "version": MODULE_VERSION,
                "updated_at": _utc_now_iso(),
                "subsystems": {},
            }
            return
        try:
            self._state = json.loads(self._state_path.read_text(encoding="utf-8"))
        except Exception:
            self._state = {
                "module_id": MODULE_ID,
                "version": MODULE_VERSION,
                "updated_at": _utc_now_iso(),
                "subsystems": {},
            }

    def _persist_locked(self) -> None:
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self._state_path.write_text(json.dumps(self._state, indent=2), encoding="utf-8")


continuity_witness_store = ContinuityWitnessStore()
