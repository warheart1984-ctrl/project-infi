"""Shared fixtures for CRK-1 conformance tests."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.continuity.constitutional_runtime import (
    ConstitutionalLedgers,
    ConstitutionalRuntime,
    DEFAULT_IDENTITY,
    EvidenceContract,
    GovernanceContract,
    RuntimeContract,
)
from src.continuity.decision_ledger import DecisionLedgerStore, bootstrap_decision_ledger
from src.continuity.evidence_ledger import (
    EvidenceLedgerStore,
    EvidenceRecord,
    EvidenceType,
    bootstrap_evidence_ledger,
)
from src.continuity.outcome_fitness import OutcomeConfig
from src.continuity.outcome_ledger import OutcomeLedgerStore, bootstrap_outcome_ledger
from src.continuity.resource_ledger import ResourceLedgerStore, bootstrap_resource_ledger
from src.crk1.runtime_facade import CRK1Runtime
from src.crk1.schema_validator import CRK1SchemaValidator
from src.crk1.semantic_exposure_monitor import SemanticExposureMonitor


def uuid4_str() -> str:
    return str(uuid.uuid4())


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@pytest.fixture
def crk1_ledgers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ConstitutionalLedgers:
    online = tmp_path / "crk1"
    online.mkdir()
    monkeypatch.setenv("AAIS_ONLINE_RUNTIME_DIR", str(online))
    monkeypatch.setenv("DECISION_LEDGER_PATH", str(online / "decision.sqlite3"))
    monkeypatch.setenv("RESOURCE_LEDGER_PATH", str(online / "resource.sqlite3"))
    monkeypatch.setenv("OUTCOME_LEDGER_PATH", str(online / "outcome.sqlite3"))
    monkeypatch.setenv("EVIDENCE_LEDGER_PATH", str(online / "evidence.sqlite3"))
    evidence = EvidenceLedgerStore()
    bootstrap_evidence_ledger(evidence)
    for evidence_id in ("EV-PIT-1-E17", "EVD-CRK1-001", "E1", "E2"):
        evidence.upsert_evidence_record(
            EvidenceRecord(
                evidence_id=evidence_id,
                evidence_hash=f"{evidence_id}-hash",
                evidence_type=EvidenceType.IMPORT,
                source_lineage="CRK1-TEST",
                source_epoch=17,
                validation_method="crk1-test",
                confidence=0.95,
                canonical_hash=f"{evidence_id}-hash",
            )
        )
    return ConstitutionalLedgers(
        identity=DEFAULT_IDENTITY,
        decisions=DecisionLedgerStore(),
        resources=ResourceLedgerStore(),
        outcomes=OutcomeLedgerStore(config=OutcomeConfig()),
        evidence_store=evidence,
        epoch=17,
    )


@pytest.fixture
def crk1_runtime(crk1_ledgers: ConstitutionalLedgers) -> ConstitutionalRuntime:
    bootstrap_decision_ledger(crk1_ledgers.decisions, epoch=crk1_ledgers.epoch)
    bootstrap_resource_ledger(crk1_ledgers.resources, epoch=crk1_ledgers.epoch)
    bootstrap_outcome_ledger(crk1_ledgers.outcomes, epoch=crk1_ledgers.epoch)
    return ConstitutionalRuntime(
        crk1_ledgers,
        evidence_contract=EvidenceContract(evidence_store=crk1_ledgers.evidence_store),
        governance_contract=GovernanceContract(crk1_ledgers.identity),
        runtime_contract=RuntimeContract(),
    )


@pytest.fixture
def runtime(crk1_runtime: ConstitutionalRuntime) -> CRK1Runtime:
    """CRK-1 facade with K0–K3 constitutional guards."""
    return CRK1Runtime(crk1_runtime)


@pytest.fixture
def semantic_monitor(runtime: CRK1Runtime) -> SemanticExposureMonitor:
    """K11–K12 semantic exposure tracker over the runtime interpretive layer."""
    runtime.create_evidence()
    return SemanticExposureMonitor(runtime)


@pytest.fixture
def schema_validator() -> CRK1SchemaValidator:
    return CRK1SchemaValidator()
