"""Tests for CFT-F3 transmission monitor (TransmissionMonitorRecord)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.crk1.schema_validator import CRK1SchemaValidator
from src.crk1.transmission_monitor import (
    ConsequenceSummary,
    MacroEvidence,
    TransmissionMonitor,
    TransmissionThresholds,
    correlation_proxy,
    evaluate_transmission,
)

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "crk1"


def _collapsed_case() -> tuple[int, ConsequenceSummary, MacroEvidence, TransmissionThresholds]:
    payload = json.loads((FIXTURES / "sample_transmission_monitor_input.json").read_text(encoding="utf-8"))
    return (
        payload["generation"],
        ConsequenceSummary.model_validate(payload["k_g"]),
        MacroEvidence.model_validate(payload["E_next"]),
        TransmissionThresholds.model_validate(payload["thresholds"]),
    )


def test_correlation_proxy_collapsed_transmission() -> None:
    k = [0.9, 0.1, 0.0]
    e = [0.05, 0.05, 0.05]
    assert correlation_proxy(k, e) == pytest.approx(0.0)


def test_canonical_collapsed_case() -> None:
    generation, k_g, e_next, thresholds = _collapsed_case()
    record = evaluate_transmission(generation, k_g, e_next, thresholds)

    assert record.generation == 12
    assert record.transmissionIntegrity == pytest.approx(0.0)
    assert record.band == "critical"
    assert record.runtimeFlags.allowArchitectureChange is False
    assert record.runtimeFlags.externalReview is True
    assert record.runtimeFlags.constitutionalFreeze is False


def test_record_validates_against_schema() -> None:
    generation, k_g, e_next, thresholds = _collapsed_case()
    record = evaluate_transmission(generation, k_g, e_next, thresholds)
    CRK1SchemaValidator().validate("TransmissionMonitorRecord", record.model_dump())


def test_healthy_band_flags() -> None:
    k_g = ConsequenceSummary(vector=[0.8, 0.2, 0.1], categories=["harm", "benefit", "drift"])
    e_next = MacroEvidence(vector=[0.75, 0.25, 0.15], sourceChannels=["harm", "benefit"])
    thresholds = TransmissionThresholds(ok=0.4, critical=0.1, consecutiveCriticalLimit=3)

    record = evaluate_transmission(1, k_g, e_next, thresholds)

    assert record.band == "healthy"
    assert record.runtimeFlags.allowArchitectureChange is True
    assert record.runtimeFlags.requireChannelExpansion is False
    assert record.runtimeFlags.externalReview is False


def test_consecutive_critical_triggers_constitutional_freeze() -> None:
    monitor = TransmissionMonitor()
    generation, k_g, e_next, thresholds = _collapsed_case()

    for gen in range(1, thresholds.consecutiveCriticalLimit):
        record = monitor.evaluate_transmission(gen, k_g, e_next, thresholds)
        assert record.band == "critical"
        assert record.runtimeFlags.constitutionalFreeze is False

    record = monitor.evaluate_transmission(thresholds.consecutiveCriticalLimit, k_g, e_next, thresholds)
    assert record.runtimeFlags.constitutionalFreeze is True


def test_recovery_resets_critical_counter() -> None:
    monitor = TransmissionMonitor()
    generation, k_g, e_next, thresholds = _collapsed_case()

    monitor.evaluate_transmission(generation, k_g, e_next, thresholds)
    assert monitor.critical_counter == 1

    healthy_k = ConsequenceSummary(vector=[0.8, 0.2, 0.1])
    healthy_e = MacroEvidence(vector=[0.75, 0.25, 0.15])
    record = monitor.evaluate_transmission(generation + 1, healthy_k, healthy_e, thresholds)

    assert record.band == "healthy"
    assert monitor.critical_counter == 0
