"""Cross-domain invariant calculations for AAIS.

This module packages the invariant engine from the design doc into a reusable,
deterministic library that stays friendly to runtime traces and JSON payloads.
It covers four domains:

1. Matrix invariants
2. Polynomial invariants
3. Topological invariants
4. Statistical invariants
"""

from __future__ import annotations

def _wrap_ul_payload(payload: dict) -> dict:
    from src.aais_ul.runtime import attach_ul_substrate

    return attach_ul_substrate(dict(payload))
from collections.abc import Iterable
import math
import warnings

import networkx as nx
import numpy as np
from scipy.stats import kurtosis, skew
import sympy as sp

RUNTIME_INVARIANT_STATUS_PASS = "pass"
RUNTIME_INVARIANT_STATUS_FAIL = "fail"
RUNTIME_SAFE_RECOMMENDED_STATES = {"pause", "degrade_safe", "observe"}
MAX_RUNTIME_SUPPORTING_SIGNALS = 4
BRIDGE_ALLOWED_RUNTIME_CONTEXTS = frozenset({"live_runtime", "operator_runtime", "test_harness"})
BRIDGE_INVARIANT_PACKET_TYPES = frozenset({"deliberation_request", "generation_request"})
BRIDGE_SAFE_EXECUTION_INTENTS = frozenset({"observe", "respond", "route"})


def _normalize_scalar(value):
    if isinstance(value, sp.Basic):
        value = complex(value.evalf()) if value.is_complex else float(value)
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, complex):
        if abs(value.imag) <= 1e-12:
            return float(value.real)
        return _wrap_ul_payload({
            "real": round(float(value.real), 12),
            "imag": round(float(value.imag), 12),
        })
    if isinstance(value, (int, float)):
        numeric = float(value)
        if math.isnan(numeric) or math.isinf(numeric):
            raise ValueError("Invariant calculation produced a non-finite numeric result.")
        return numeric
    return value


def _coerce_square_matrix(matrix) -> np.ndarray:
    array = np.asarray(matrix, dtype=float)
    if array.ndim != 2 or array.shape[0] != array.shape[1]:
        raise ValueError("Input must be a square matrix.")
    return array


def _normalize_coefficients(coeffs) -> list[float]:
    if not isinstance(coeffs, Iterable) or isinstance(coeffs, (str, bytes)):
        raise ValueError("Polynomial coefficients must be a non-string iterable.")
    normalized = [float(value) for value in coeffs]
    if not normalized:
        raise ValueError("Polynomial coefficients cannot be empty.")
    while len(normalized) > 1 and abs(normalized[0]) <= 1e-12:
        normalized.pop(0)
    if all(abs(value) <= 1e-12 for value in normalized):
        raise ValueError("Polynomial coefficients cannot all be zero.")
    return normalized


def _build_polynomial(coeffs: list[float]) -> sp.Poly:
    x = sp.symbols("x")
    degree = len(coeffs) - 1
    expression = sum(sp.Float(coeff) * x ** power for coeff, power in zip(coeffs, range(degree, -1, -1)))
    return sp.Poly(expression, x)


def _normalize_edges(edges) -> list[tuple]:
    if edges is None:
        return []
    if not isinstance(edges, Iterable) or isinstance(edges, (str, bytes)):
        raise ValueError("Edges must be an iterable of (u, v) pairs.")
    normalized: list[tuple] = []
    for edge in edges:
        if not isinstance(edge, Iterable) or isinstance(edge, (str, bytes)):
            raise ValueError("Each edge must be an iterable with exactly two nodes.")
        pair = tuple(edge)
        if len(pair) != 2:
            raise ValueError("Each edge must contain exactly two nodes.")
        normalized.append(pair)
    return normalized


def _coerce_numeric_data(data) -> np.ndarray:
    array = np.asarray(list(data), dtype=float)
    if array.ndim != 1 or array.size == 0:
        raise ValueError("Statistical data must be a non-empty one-dimensional sequence.")
    if np.isnan(array).all():
        raise ValueError("Statistical data cannot be entirely NaN.")
    return array


def _safe_distribution_moment(data: np.ndarray, *, mode: str) -> float:
    finite = data[~np.isnan(data)]
    if finite.size == 0:
        raise ValueError("Statistical data cannot be entirely NaN.")
    if finite.size < 2 or np.allclose(finite, finite[0]):
        return 0.0
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        raw = skew(finite, nan_policy="omit") if mode == "skew" else kurtosis(finite, nan_policy="omit")
    numeric = float(raw)
    if math.isnan(numeric) or math.isinf(numeric):
        return 0.0
    return numeric


class MathInvariants:
    """Deterministic invariant calculations across multiple mathematical domains."""

    @staticmethod
    def matrix_invariants(matrix) -> dict:
        """Return trace, determinant, eigenvalues, rank, and Frobenius norm."""
        array = _coerce_square_matrix(matrix)
        eigenvalues = [_normalize_scalar(value) for value in np.linalg.eigvals(array)]
        return _wrap_ul_payload({
            "trace": _normalize_scalar(np.trace(array)),
            "determinant": _normalize_scalar(np.linalg.det(array)),
            "eigenvalues": eigenvalues,
            "rank": int(np.linalg.matrix_rank(array)),
            "frobenius_norm": _normalize_scalar(np.linalg.norm(array, "fro")),
        })

    @staticmethod
    def polynomial_invariants(coeffs) -> dict:
        """Return degree, discriminant, and leading coefficient for numeric coefficients."""
        normalized = _normalize_coefficients(coeffs)
        poly = _build_polynomial(normalized)
        return _wrap_ul_payload({
            "degree": int(poly.degree()),
            "discriminant": _normalize_scalar(poly.discriminant()),
            "leading_coefficient": _normalize_scalar(poly.LC()),
        })

    @staticmethod
    def topological_invariants(edges) -> dict:
        """Return graph invariants for an undirected edge list."""
        graph = nx.Graph()
        graph.add_edges_from(_normalize_edges(edges))
        vertices = graph.number_of_nodes()
        edge_count = graph.number_of_edges()
        connected_components = nx.number_connected_components(graph) if vertices else 0
        return _wrap_ul_payload({
            "vertices": vertices,
            "edges": edge_count,
            "connected_components": connected_components,
            "euler_characteristic": vertices - edge_count + connected_components,
            "number_of_cycles": len(nx.cycle_basis(graph)),
        })

    @staticmethod
    def statistical_invariants(data) -> dict:
        """Return mean, variance, standard deviation, skewness, and kurtosis."""
        array = _coerce_numeric_data(data)
        return _wrap_ul_payload({
            "mean": _normalize_scalar(np.nanmean(array)),
            "variance": _normalize_scalar(np.nanvar(array)),
            "standard_deviation": _normalize_scalar(np.nanstd(array)),
            "skewness": _normalize_scalar(_safe_distribution_moment(array, mode="skew")),
            "kurtosis": _normalize_scalar(_safe_distribution_moment(array, mode="kurtosis")),
        })

    @staticmethod
    def cross_domain_report(
        *,
        matrix=None,
        polynomial_coeffs=None,
        edges=None,
        data=None,
    ) -> dict:
        """Return a compact multi-domain report for whichever inputs are provided."""
        domains: dict[str, dict] = {}
        if matrix is not None:
            domains["matrix"] = MathInvariants.matrix_invariants(matrix)
        if polynomial_coeffs is not None:
            domains["polynomial"] = MathInvariants.polynomial_invariants(polynomial_coeffs)
        if edges is not None:
            domains["topology"] = MathInvariants.topological_invariants(edges)
        if data is not None:
            domains["statistics"] = MathInvariants.statistical_invariants(data)
        if not domains:
            raise ValueError("At least one domain input is required.")
        return _wrap_ul_payload({
            "module": "invariant_engine",
            "domains": domains,
            "domain_count": len(domains),
            "available_domains": list(domains.keys()),
        })


class InvariantEngine(MathInvariants):
    """Math invariants plus bounded runtime-event validation helpers."""

    @staticmethod
    def validate_realtime_event_prediction(event, prediction) -> dict:
        """Validate one governed realtime event/prediction pair with bounded invariants."""
        from src.realtime_event_cause_predictor import validate_interpreted_event_state

        event_payload = dict(event or {})
        prediction_payload = dict(prediction or {})
        event_validation = {
            key: bool(value)
            for key, value in dict(event_payload.get("validation") or {}).items()
            if isinstance(value, bool)
        }
        prediction_validation = validate_interpreted_event_state(prediction_payload)
        event_signals = list(event_payload.get("signals") or [])
        event_signal_count = int(event_payload.get("signal_count") or len(event_signals))
        prediction_signal_count = int(prediction_payload.get("signal_count") or 0)
        runtime_context = str(event_payload.get("runtime_context") or "").strip().lower()
        prediction_context = str(prediction_payload.get("runtime_context") or "").strip().lower()
        recommended_state = str(prediction_payload.get("recommended_state") or "").strip().lower()
        data_sufficiency = str(prediction_payload.get("data_sufficiency") or "").strip().lower()
        immune_response = str(event_payload.get("immune_response") or "ALLOW").strip().upper()
        phase_gate_decision = str((prediction_payload.get("phase_gate") or {}).get("decision") or "").strip().upper()
        conflict_flags = list(prediction_payload.get("conflict_flags") or [])
        supporting_signals = list(prediction_payload.get("supporting_signals") or [])

        basic_event_shape = bool(runtime_context) and isinstance(event_signals, list) and event_signal_count >= 0
        checks = {
            "event_validation_pass": all(event_validation.values()) if event_validation else basic_event_shape,
            "prediction_validation_pass": all(
                value for value in prediction_validation.values() if isinstance(value, bool)
            ),
            "prediction_phase_allows": phase_gate_decision == "ALLOW",
            "runtime_context_match": runtime_context == prediction_context and bool(runtime_context),
            "signal_count_match": prediction_signal_count == event_signal_count,
            "supporting_signal_bound": len(supporting_signals) <= MAX_RUNTIME_SUPPORTING_SIGNALS
            and (event_signal_count <= 0 or len(supporting_signals) <= event_signal_count),
            "insufficient_data_safe_state": not (
                data_sufficiency == "insufficient" and recommended_state not in RUNTIME_SAFE_RECOMMENDED_STATES
            ),
            "conflict_safe_state": not (
                conflict_flags and recommended_state not in RUNTIME_SAFE_RECOMMENDED_STATES
            ),
            "immune_alignment": not (
                immune_response != "ALLOW"
                and (
                    prediction_payload.get("cause_class") != "immune_guard_intervention"
                    or recommended_state not in {"pause", "degrade_safe"}
                )
            ),
            "phase_gate_alignment": not (
                phase_gate_decision == "BLOCK"
                and (
                    prediction_payload.get("status") != "phase_blocked"
                    or recommended_state != "pause"
                )
            ),
        }
        failed = [name for name, passed in checks.items() if not passed]
        return _wrap_ul_payload({
            "module_id": "aais.invariant_engine.runtime_event_guard",
            "status": RUNTIME_INVARIANT_STATUS_PASS if not failed else RUNTIME_INVARIANT_STATUS_FAIL,
            "allows": not failed,
            "checked_invariants": checks,
            "failed_invariants": failed,
            "reason_codes": list(failed),
            "summary": (
                "Realtime invariant gate accepted the bounded predictor output."
                if not failed
                else "Realtime invariant gate blocked the bounded predictor output: "
                + ", ".join(failed)
            ),
            "advisory_only": True,
        })

    @staticmethod
    def assert_realtime_event_prediction_allowed(event, prediction) -> None:
        """Raise when one governed realtime event/prediction pair violates invariants."""
        result = InvariantEngine.validate_realtime_event_prediction(event, prediction)
        if not result["allows"]:
            raise ValueError(
                "Realtime event invariant validation failed: "
                + ", ".join(result["failed_invariants"])
            )

    @staticmethod
    def validate_bridge_packet(normalized_packet: dict, governance: dict) -> dict:
        """Validate governed bridge packets on the live deliberation/generation path."""
        packet_type = str(
            normalized_packet.get("type") or governance.get("packet_type") or ""
        ).strip().lower()
        payload = dict(normalized_packet.get("payload") or {})
        runtime_context = str(
            governance.get("runtime_context") or payload.get("runtime_context") or ""
        ).strip().lower()
        execution_intent = str(
            governance.get("execution_intent") or payload.get("execution_intent") or ""
        ).strip().lower()
        effectful = bool(governance.get("effectful") or normalized_packet.get("effectful"))
        source = str(governance.get("source") or normalized_packet.get("source") or "").strip().lower()
        attestation = payload.get("bridge_attestation")

        checks = {
            "runtime_context_allowed": runtime_context in BRIDGE_ALLOWED_RUNTIME_CONTEXTS,
            "source_declared": bool(source),
            "packet_type_in_scope": packet_type in BRIDGE_INVARIANT_PACKET_TYPES,
        }

        if packet_type == "deliberation_request":
            checks["deliberation_subject_present"] = bool(
                str(payload.get("question") or payload.get("intent") or "").strip()
            )
            checks["deliberation_observation_only"] = (
                execution_intent in BRIDGE_SAFE_EXECUTION_INTENTS and not effectful
            )
            checks["bridge_attestation_present"] = isinstance(attestation, dict) and bool(attestation)

        if packet_type == "generation_request":
            checks["generation_response_only"] = execution_intent in BRIDGE_SAFE_EXECUTION_INTENTS
            checks["bridge_attestation_present"] = isinstance(attestation, dict) and bool(attestation)

        failed = [name for name, passed in checks.items() if not passed]
        return _wrap_ul_payload({
            "module_id": "aais.invariant_engine.bridge_guard",
            "status": RUNTIME_INVARIANT_STATUS_PASS if not failed else RUNTIME_INVARIANT_STATUS_FAIL,
            "allows": not failed,
            "checked_invariants": checks,
            "failed_invariants": failed,
            "reason_codes": list(failed),
            "summary": (
                "Bridge invariant gate accepted the governed packet."
                if not failed
                else "Bridge invariant gate blocked the governed packet: " + ", ".join(failed)
            ),
            "advisory_only": False,
            "packet_type": packet_type,
        })
