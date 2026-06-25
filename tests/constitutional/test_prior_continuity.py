"""Stewardship prior ledger, drift detector, and succession gate tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from constitutional.priors.drift_detector import PriorDriftDetector, PriorDriftFailure, StewardPriorMap
from constitutional.priors.governance import prior_aware_succession_gate, succession_prior_continuity_ready
from constitutional.priors.judgment_runtime import seed_passing_prior_judgment
from constitutional.priors.ledger import PriorEntry, load_prior_ledger, save_prior_ledger
from constitutional.priors.panel import format_prior_continuity_panel
from constitutional.runtime.domain_receipts_store import clear_domain_memory_index
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.salience.judgment_runtime import seed_passing_salience_judgment
from constitutional.salience.continuity_runtime import (
    SalienceContinuityRuntime,
    StewardKnowledgeIndex,
    append_salience_entry,
)
from constitutional.salience.ledger import SalienceEntry
from constitutional.salience.perceptual_drift import PerceptualDriftDetector, StewardSalienceMap


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    clear_domain_memory_index()


@pytest.fixture
def csr(tmp_path) -> ConstitutionalStateRuntime:
    runtime = ConstitutionalStateRuntime(persist_root=tmp_path)
    runtime.register_invariant("CRITICAL_SYSTEMS_MUST_PRESERVE_STEWARDSHIP_PRIORS", "Article Q-7")
    return runtime


def _seed_prior_ledger(csr: ConstitutionalStateRuntime) -> None:
    ledger = load_prior_ledger(csr)
    ledger.append(
        PriorEntry(
            timestamp=datetime.now(UTC).replace(microsecond=0),
            decision_id="prior-artifact-a-1",
            artifact_id="artifact_a",
            expected_signals=["latent authority concentration"],
            expected_risks=["constitutional capture"],
            assumed_stabilities=["tier 0 invariants"],
            assumed_volatilities=["emergency bypass scope"],
            predictive_models=["if bypass unchecked then capture risk rises"],
            feared_failures=["hidden authority"],
            ignored_possibilities=["cosmetic ritual change"],
            steward_id="steward-seed",
        )
    )
    save_prior_ledger(csr, ledger)


def _seed_salience_stack(csr: ConstitutionalStateRuntime) -> None:
    now = datetime.now(UTC).replace(microsecond=0)
    append_salience_entry(
        csr,
        SalienceEntry(
            timestamp=now,
            decision_id="decision-artifact-a-1",
            artifact_id="artifact_a",
            primary_signals=["latent authority concentration", "anti-corruption invariant"],
            secondary_signals=["operational urgency"],
            ignored_signals=["convenience"],
            risk_salience=["constitutional capture"],
            deprioritized_risks=["cosmetic outage"],
            attention_triggers=["emergency bypass proposal"],
            attention_suppressors=["founder preference"],
            steward_id="steward-seed",
        ),
    )
    SalienceContinuityRuntime(
        csr,
        steward_knowledge_index=StewardKnowledgeIndex({"artifact_a"}),
    ).run()
    PerceptualDriftDetector(
        csr,
        steward_salience_map=StewardSalienceMap(
            primary_signals=["latent authority concentration", "anti-corruption invariant"],
        ),
    ).run()
    seed_passing_salience_judgment(csr)


def test_prior_drift_blindness_without_matching_priors(csr: ConstitutionalStateRuntime) -> None:
    _seed_prior_ledger(csr)
    state = PriorDriftDetector(csr, steward_priors=StewardPriorMap()).run()
    assert PriorDriftFailure.PRIOR_BLINDNESS in state.failed_surfaces


def test_prior_drift_passes_with_aligned_priors(csr: ConstitutionalStateRuntime) -> None:
    _seed_prior_ledger(csr)
    state = PriorDriftDetector(
        csr,
        steward_priors=StewardPriorMap(
            expected_signals=["latent authority concentration"],
            expected_risks=["constitutional capture"],
            assumed_stabilities=["tier 0 invariants"],
            assumed_volatilities=["emergency bypass scope"],
        ),
    ).run()
    assert state.drift_index >= 0.8


def test_prior_aware_succession_gate(csr: ConstitutionalStateRuntime) -> None:
    _seed_prior_ledger(csr)
    _seed_salience_stack(csr)

    ok, _ = succession_prior_continuity_ready(csr)
    assert ok is False

    PriorDriftDetector(
        csr,
        steward_priors=StewardPriorMap(
            expected_signals=["latent authority concentration"],
            expected_risks=["constitutional capture"],
            assumed_stabilities=["tier 0 invariants"],
            assumed_volatilities=["emergency bypass scope"],
            feared_failures=["hidden authority"],
        ),
    ).run()
    seed_passing_prior_judgment(csr)

    ok, message = prior_aware_succession_gate(csr)
    assert ok is True
    assert "prior-aware" in message.lower()


def test_prior_continuity_panel(csr: ConstitutionalStateRuntime) -> None:
    _seed_prior_ledger(csr)
    drift = PriorDriftDetector(csr).run()
    ledger = load_prior_ledger(csr)
    panel = format_prior_continuity_panel(ledger, drift, StewardPriorMap())
    assert "PRIOR CONTINUITY PANEL" in panel
    assert "latent authority concentration" in panel
