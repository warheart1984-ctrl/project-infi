"""Prior judgment, environment gate, failure bridge, and epistemic amendment tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from constitutional.amendment.epistemic_orchestrator import generate_epistemic_remediation_amendment
from constitutional.environment.governance import succession_decision_environment_ready
from constitutional.failure.bridge import record_epistemic_failures
from constitutional.eck1.registers import load_failure_register
from constitutional.priors.drift_detector import PriorDriftDetector, PriorDriftFailure, StewardPriorMap
from constitutional.priors.ledger import PriorEntry, load_prior_ledger, save_prior_ledger
from constitutional.salience.continuity_runtime import append_salience_entry
from constitutional.salience.ledger import SalienceEntry
from constitutional.priors.judgment_runtime import PriorJudgmentTest, StewardPriorAnswer, seed_passing_prior_judgment
from constitutional.priors.reference_maps import get_reference_prior_maps
from constitutional.runtime.domain_receipts_store import clear_domain_memory_index
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.salience.continuity_runtime import SalienceContinuityRuntime, SalienceFailure, StewardKnowledgeIndex
from constitutional.salience.perceptual_drift import PerceptualDriftDetector, PerceptualDriftFailure


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    clear_domain_memory_index()


@pytest.fixture
def csr(tmp_path) -> ConstitutionalStateRuntime:
    return ConstitutionalStateRuntime(persist_root=tmp_path)


def test_prior_judgment_reference_maps() -> None:
    ref = get_reference_prior_maps()
    answers = {
        scenario_id: StewardPriorAnswer(
            scenario_id=scenario_id,
            expected_signals=list(ref_map.expected_signals),
            expected_risks=list(ref_map.expected_risks),
            assumed_stabilities=list(ref_map.assumed_stabilities),
            assumed_volatilities=list(ref_map.assumed_volatilities),
            feared_failures=list(ref_map.feared_failures),
            ignored_possibilities=list(ref_map.ignored_possibilities),
        )
        for scenario_id, ref_map in ref.items()
    }
    result = PriorJudgmentTest().evaluate(answers)
    assert result.passed is True


def test_decision_environment_ready_empty_csr(csr: ConstitutionalStateRuntime) -> None:
    ok, reasons = succession_decision_environment_ready(csr)
    assert ok is True
    assert reasons == []


def test_failure_register_records_drift(csr: ConstitutionalStateRuntime) -> None:
    prior = PriorDriftDetector(
        csr,
        steward_priors=StewardPriorMap(),
    ).run()
    perceptual = PerceptualDriftDetector(csr).run()
    salience = SalienceContinuityRuntime(csr).run()

    register = record_epistemic_failures(
        csr,
        prior_drift_state=prior,
        perceptual_drift_state=perceptual,
        salience_continuity_state=salience,
    )
    assert register.entries
    layers = {entry.layer for entry in register.entries}
    assert "prior" in layers or "salience" in layers


def test_epistemic_amendment_requires_co_occurring_failures(csr: ConstitutionalStateRuntime) -> None:
    assert generate_epistemic_remediation_amendment(csr, record_failures=False) is None

    now = datetime.now(UTC).replace(microsecond=0)
    prior_ledger = load_prior_ledger(csr)
    prior_ledger.append(
        PriorEntry(
            timestamp=now,
            decision_id="prior-1",
            expected_signals=["latent authority concentration"],
            expected_risks=["constitutional capture"],
            steward_id="seed",
        )
    )
    save_prior_ledger(csr, prior_ledger)
    append_salience_entry(
        csr,
        SalienceEntry(
            timestamp=now,
            decision_id="decision-1",
            artifact_id="artifact_a",
            primary_signals=["latent authority concentration"],
            steward_id="seed",
        ),
    )

    prior = PriorDriftDetector(csr, steward_priors=StewardPriorMap()).run()
    perceptual = PerceptualDriftDetector(csr).run()
    salience = SalienceContinuityRuntime(
        csr,
        steward_knowledge_index=StewardKnowledgeIndex(set()),
    ).run()
    assert PriorDriftFailure.PRIOR_BLINDNESS in prior.failed_surfaces
    assert PerceptualDriftFailure.SALIENCE_BLINDNESS in perceptual.failed_surfaces
    assert SalienceFailure.SALIENCE_BLINDNESS in salience.failed_surfaces

    amendment = generate_epistemic_remediation_amendment(csr, record_failures=True)
    assert amendment is not None
    assert amendment["amendment_type"] == "EPISTEMIC STACK REMEDIATION"
    assert load_failure_register(csr).entries


def test_seed_passing_prior_judgment(csr: ConstitutionalStateRuntime) -> None:
    state = seed_passing_prior_judgment(csr)
    assert state.passed is True
