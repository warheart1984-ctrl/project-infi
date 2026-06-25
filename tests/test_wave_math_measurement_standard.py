"""WMMS-1 substrate-to-wave measurement tests."""

from __future__ import annotations

import pytest

from src.continuity.ccs import CCSStore, ContinuityTrace, Event
from src.continuity.substrate import ContinuitySubstrate
from src.continuity.wave_math import (
    WaveSignature,
    derive_wave_signature_from_substrate,
    measure_wave_signature,
)


def _store_with_wave_events() -> tuple[CCSStore, ContinuitySubstrate, ContinuityTrace]:
    store = CCSStore()
    law_surface = {"aais_laws": ["AAIS"], "csleis_laws": [], "other_laws": ["UGR"]}
    for event in (
        Event(
            id="event.identity.1",
            kind="identity_update",
            actors=["identity:jon"],
            targets=["identity:nova", "system:aais"],
            time={"timestamp": "2026-06-20T12:00:00Z"},
            context={
                "affected_identities": ["identity:jon", "identity:nova"],
                "affected_systems": ["aais", "aaes"],
                "lineage_depth": 4,
                "governance_severity": 0.5,
                "architectural_scope": "subsystem",
                "declared_intent_vector": [1.0, 0.0],
                "observed_behavior_vector": [0.8, 0.2],
                "lineage_direction_vector": [1.0, 0.0],
                "pattern_key": "identity:jon",
                "pattern_persistence": 0.7,
                "natural_frequency": 0.4,
                "governance_reinforcement_cycles": 2,
            },
            law_surface=law_surface,
            description="identity lineage update",
            linked_evidence=["evidence.1"],
        ),
        Event(
            id="event.identity.2",
            kind="identity_update",
            actors=["identity:jon"],
            targets=["system:aais"],
            time={"timestamp": "2026-06-20T12:01:00Z"},
            context={
                "affected_identities": ["identity:jon"],
                "affected_systems": ["aais"],
                "lineage_depth": 2,
                "governance_severity": 0.2,
                "architectural_scope": "local",
                "pattern_key": "identity:jon",
            },
            law_surface=law_surface,
            description="identity recurrence",
            linked_evidence=["evidence.2"],
        ),
    ):
        store.add_event(event)

    trace = ContinuityTrace(
        id="ct.wave.1001",
        scope={"identity_ids": ["identity:jon", "identity:nova"], "event_ids": ["event.identity.1", "event.identity.2"]},
        timeline=[
            {"event_id": "event.identity.1", "evaluations": [], "evidence": ["evidence.1"]},
            {"event_id": "event.identity.2", "evaluations": [], "evidence": ["evidence.2"]},
        ],
        law_surfaces=law_surface,
        continuity_summary={
            "replay_divergence": 0.10,
            "cross_kernel_disagreement": 0.20,
            "cross_layer_mismatch": 0.10,
            "lineage_pointer_mismatch": 0.00,
            "invariant_violation_rate": 0.10,
        },
        reproducibility_metadata={"window_seconds": 300},
    )
    store.add_trace(trace)

    substrate = ContinuitySubstrate(
        substrate_id="substrate.wave.1001",
        ccs_layer={"identities": [], "events": ["event.identity.1", "event.identity.2"], "evaluations": [], "evidence": []},
        trace_layer={"traces": ["ct.wave.1001"]},
    )
    return store, substrate, trace


def test_wmms1_derives_wave_signature_from_observable_substrate_fields() -> None:
    store, substrate, trace = _store_with_wave_events()

    signature = derive_wave_signature_from_substrate(
        store,
        substrate,
        trace_id=trace.id,
        pattern_key="identity:jon",
    )

    assert isinstance(signature, WaveSignature)
    assert signature.amplitude == pytest.approx(0.59)
    assert signature.frequency == pytest.approx(0.4)
    assert signature.phase == pytest.approx(0.9701425)
    assert signature.coherence == pytest.approx(0.9)
    assert signature.resonance == pytest.approx(0.7)
    assert signature.sources["substrate_id"] == "substrate.wave.1001"
    assert signature.sources["event_ids"] == ["event.identity.1", "event.identity.2"]
    assert signature.to_dict()["standard"] == "WMMS-1"


def test_wmms1_measurement_fails_when_required_observables_are_missing() -> None:
    with pytest.raises(ValueError, match="missing required observables"):
        measure_wave_signature({})
