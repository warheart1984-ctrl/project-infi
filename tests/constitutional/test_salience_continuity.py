"""Salience continuity, judgment, drift, and succession gate tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from constitutional.runtime.domain_receipts_store import clear_domain_memory_index
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.salience.continuity_runtime import (
    SalienceContinuityRuntime,
    SalienceFailure,
    StewardKnowledgeIndex,
    append_salience_entry,
)
from constitutional.salience.governance import (
    salience_aware_succession_gate,
    succession_salience_continuity_ready,
    succession_salience_judgment_ready,
)
from constitutional.salience.judgment_runtime import (
    SalienceJudgmentTest,
    StewardSalienceAnswer,
    seed_passing_salience_judgment,
)
from constitutional.salience.ledger import SalienceEntry
from constitutional.salience.perceptual_drift import PerceptualDriftDetector, StewardSalienceMap
from constitutional.salience.reference_maps import get_reference_salience_maps
from constitutional.salience.amendment import generate_salience_amendment
from constitutional.salience.panel import format_salience_panel
from constitutional.salience.ledger import load_salience_ledger


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    clear_domain_memory_index()


@pytest.fixture
def csr(tmp_path) -> ConstitutionalStateRuntime:
    runtime = ConstitutionalStateRuntime(persist_root=tmp_path)
    runtime.register_invariant("CRITICAL_SYSTEMS_MUST_PRESERVE_SALIENCE_CONTINUITY", "Article Q-6")
    return runtime


def _seed_artifact_a_salience(csr: ConstitutionalStateRuntime) -> None:
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


def test_salience_continuity_detects_loss(csr: ConstitutionalStateRuntime) -> None:
    state = SalienceContinuityRuntime(csr).run()
    assert SalienceFailure.SALIENCE_LOSS in state.failed_surfaces
    assert "artifact_a" in state.missing_salience_entries


def test_salience_continuity_passes_with_seed(csr: ConstitutionalStateRuntime) -> None:
    _seed_artifact_a_salience(csr)
    state = SalienceContinuityRuntime(
        csr,
        steward_knowledge_index=StewardKnowledgeIndex({"artifact_a"}),
    ).run()
    assert state.salience_index >= 0.8
    assert SalienceFailure.SALIENCE_LOSS not in state.failed_surfaces


def test_salience_judgment_reference_maps() -> None:
    ref = get_reference_salience_maps()
    answers = {
        scenario_id: StewardSalienceAnswer(
            scenario_id=scenario_id,
            primary_signals=list(ref_map.primary_signals),
            secondary_signals=list(ref_map.secondary_signals),
            ignored_signals=list(ref_map.ignored_signals),
            risk_order=list(ref_map.risk_order),
        )
        for scenario_id, ref_map in ref.items()
    }
    result = SalienceJudgmentTest().evaluate(answers)
    assert result.passed is True


def test_salience_succession_gate_requires_judgment(csr: ConstitutionalStateRuntime) -> None:
    _seed_artifact_a_salience(csr)
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

    ok, message = salience_aware_succession_gate(csr)
    assert ok is False
    assert "Salience Judgment" in message

    seed_passing_salience_judgment(csr)
    ok, message = salience_aware_succession_gate(csr)
    assert ok is True
    assert "satisfied" in message.lower()


def test_salience_panel_and_amendment(csr: ConstitutionalStateRuntime) -> None:
    _seed_artifact_a_salience(csr)
    cont = SalienceContinuityRuntime(
        csr,
        steward_knowledge_index=StewardKnowledgeIndex({"artifact_a"}),
    ).run()
    drift = PerceptualDriftDetector(csr).run()
    ledger = load_salience_ledger(csr)

    panel = format_salience_panel(ledger, cont, drift)
    assert "SALIENCE PANEL" in panel
    assert "artifact_a" in panel

    amendment = generate_salience_amendment(cont, drift)
    assert amendment["amendment_type"] == "SALIENCE CONTINUITY REMEDIATION"
    assert "Article Q-6" in amendment["constitutional_linkage"][0]
