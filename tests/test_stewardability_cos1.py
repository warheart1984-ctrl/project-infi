"""Tests for stewardability register, drift, emergence, RCM-1, and COS-1."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from src.continuity.stewardability import (
    EmergenceCandidate,
    StewardAbilityRegister,
    StewardContext,
    StewardDemonstration,
    continuity_succeeded,
    detect_stewardability_drift,
    is_stewardability_viable,
    run_steward_emergence_protocol,
)
from src.continuity.stewardability.operating_conditions import bad_conditions, good_conditions
from src.continuity.stewardability.register import record_event
from src.cos1 import ContinuityOS

import pytest

from constitutional.runtime.runtime import ConstitutionalStateRuntime


@pytest.fixture
def csr(tmp_path) -> ConstitutionalStateRuntime:
    from constitutional.core.articles import PURPOSE_CONTINUITY_INVARIANT

    runtime = ConstitutionalStateRuntime(persist_root=tmp_path)
    runtime.register_invariant(PURPOSE_CONTINUITY_INVARIANT, "Article P")
    runtime.register_invariant(
        "CRITICAL_SYSTEMS_MUST_REMAIN_RECONSTRUCTABLE",
        "Article R",
    )
    return runtime


def _strong_demo() -> StewardDemonstration:
    return StewardDemonstration(
        steward_id="candidate-1",
        reconstructions=["purpose", "identity", "judgment", "constitution"],
        critiques=["drift in boundary classification"],
        adaptations=["refined invariant boundary"],
        lineage_impact="STRENGTHENED",
    )


def test_emergence_protocol_recognizes_strong_candidate() -> None:
    register = StewardAbilityRegister()
    result = run_steward_emergence_protocol(
        register,
        EmergenceCandidate(id="c1", name="Steward", background="JPSS"),
        _strong_demo(),
    )
    assert result.recognized_as_steward is True
    assert len(register.emergence_events()) == 1


def test_emergence_protocol_blocks_weak_candidate() -> None:
    register = StewardAbilityRegister()
    weak = StewardDemonstration(
        steward_id="weak",
        reconstructions=["purpose"],
        critiques=[],
        lineage_impact="UNCHANGED",
    )
    result = run_steward_emergence_protocol(
        register,
        EmergenceCandidate(id="w1", name="Weak", background=""),
        weak,
    )
    assert result.recognized_as_steward is False
    assert len(register.blockage_events()) == 1


def test_stewardability_viable_conditions() -> None:
    assert is_stewardability_viable(good_conditions()) is True
    assert is_stewardability_viable(bad_conditions()) is False


def test_imitation_drift_when_only_agreement() -> None:
    register = StewardAbilityRegister()
    ctx = StewardContext(environment_id="env-1", novelty_profile=["novel"])
    record_event(
        register,
        kind="DEMONSTRATION",
        context=ctx,
        demonstration=StewardDemonstration(
            steward_id="s1",
            reconstructions=["purpose", "identity", "judgment"],
            critiques=[],
            lineage_impact="UNCHANGED",
        ),
    )
    signals = detect_stewardability_drift(register, emergence_gap_days=9999)
    kinds = {signal.kind for signal in signals}
    assert "IMITATION_DRIFT" in kinds


def test_rcm_continuity_succeeded_requires_stewards_and_viable_conditions() -> None:
    os = ContinuityOS()
    result = os.step(
        good_conditions(),
        EmergenceCandidate(id="c1", name="S", background=""),
        _strong_demo(),
    )
    assert result.continuity_succeeded is True

    degraded = os.step(bad_conditions())
    assert degraded.continuity_state.stewardability_viable is False
    assert degraded.continuity_succeeded is False


def test_cos1_simulation_phases() -> None:
    os = ContinuityOS()
    phase1 = os.step(
        good_conditions(),
        EmergenceCandidate(id="c1", name="Future Steward", background="JPSS"),
        _strong_demo(),
    )
    assert phase1.emergence_recognized is True
    assert continuity_succeeded(phase1.continuity_state) is True

    phase2 = os.step(bad_conditions())
    assert phase2.continuity_state.stewardability_viable is False


def test_stewardship_capacity_test_three_sections() -> None:
    from src.continuity.stewardability.capacity_test import (
        passing_capacity_test_input,
        run_stewardship_capacity_test,
    )

    result = run_stewardship_capacity_test(passing_capacity_test_input("candidate-1"))
    assert result.passed
    assert len(result.sections) == 3
    assert result.capacity_index >= 0.85


def test_constitutional_memory_bridge(csr: ConstitutionalStateRuntime) -> None:
    from constitutional.legitimacy.seed import seed_stewardship_legitimacy

    seed_stewardship_legitimacy(csr)
    os = ContinuityOS(csr=csr)
    snapshot = os.memory.get_constitutional_snapshot()
    assert snapshot is not None
    assert snapshot.has_eck2_pipeline
    assert snapshot.counts.certified_stewards >= 2
    assert os.memory.artifacts_intact() is True


def test_emergence_drift_on_stale_register() -> None:
    register = StewardAbilityRegister()
    old = datetime.now(UTC) - timedelta(days=400)
    record_event(
        register,
        kind="EMERGENCE",
        context=StewardContext(environment_id="env-old"),
        timestamp=old,
    )
    signals = detect_stewardability_drift(register, emergence_gap_days=365)
    assert any(signal.kind == "EMERGENCE_DRIFT" for signal in signals)


def test_developmental_progression_includes_concept_resonance_first() -> None:
    from src.continuity.stewardability.concept_resonance import DEVELOPMENTAL_PROGRESSION

    assert DEVELOPMENTAL_PROGRESSION[0][0] == "concept_resonance"
    assert DEVELOPMENTAL_PROGRESSION[-1][0] == "stewardability"
    assert len(DEVELOPMENTAL_PROGRESSION) == 8


def test_sue_is_first_crt3_data_point_not_threshold() -> None:
    from src.continuity.stewardability.concept_resonance import (
        ConceptResonanceRegister,
        assess_crt3,
        sue_reference_event,
        validate_concept_resonance_event,
    )

    register = ConceptResonanceRegister()
    sue = sue_reference_event()
    assert validate_concept_resonance_event(sue).valid
    register.append(sue)

    crt3 = assess_crt3(register)
    assert crt3.contributor_count == 1
    assert crt3.contributors_remaining == 2
    assert crt3.threshold_met is False
    assert crt3.propagation_mode == "transmission"


def test_crt3_threshold_met_with_three_independent_contributors() -> None:
    from src.continuity.stewardability.concept_resonance import (
        ConceptExposure,
        ConceptResonanceInsight,
        ConceptResonanceRegister,
        assess_crt3,
        record_concept_resonance,
    )

    register = ConceptResonanceRegister()
    contributors = [
        ("sue", "personal_psychology"),
        ("alex", "organizational_behavior"),
        ("maria", "education"),
    ]
    for contributor_id, domain in contributors:
        record_concept_resonance(
            register,
            contributor_id=contributor_id,
            context_domain=domain,
            exposure=ConceptExposure(
                concept_id="continuity_adjacent",
                description="Encountered isolated continuity-relevant idea.",
            ),
            insight=ConceptResonanceInsight(
                text=f"{contributor_id} independently extended the idea with new explanatory insight.",
                extends_trigger=True,
                adds_explanatory_power=True,
                lineage_compatible=True,
                uses_jpss_vocabulary=False,
            ),
        )

    crt3 = assess_crt3(register)
    assert crt3.threshold_met is True
    assert crt3.propagation_mode == "propagation"
    assert crt3.contributor_count == 3
    assert crt3.context_count == 3


def test_imitation_flag_blocks_crt3_credit() -> None:
    from src.continuity.stewardability.concept_resonance import (
        ConceptExposure,
        ConceptResonanceInsight,
        ConceptResonanceRegister,
        assess_crt3,
        record_concept_resonance,
    )

    register = ConceptResonanceRegister()
    record_concept_resonance(
        register,
        contributor_id="echo",
        context_domain="ethics",
        exposure=ConceptExposure(concept_id="x", description="idea"),
        insight=ConceptResonanceInsight(
            text="paraphrase of founder doc",
            extends_trigger=True,
            adds_explanatory_power=True,
            lineage_compatible=True,
        ),
        imitation_flag=True,
    )
    assert assess_crt3(register).valid_event_count == 0


def test_cos1_step_reports_concept_resonance() -> None:
    from src.continuity.stewardability.concept_resonance import sue_reference_event

    os = ContinuityOS()
    os.memory.get_concept_resonance_register().append(sue_reference_event())
    result = os.step(good_conditions())
    assert result.concept_resonance is not None
    assert result.concept_resonance.contributor_count == 1
