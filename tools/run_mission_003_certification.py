#!/usr/bin/env python3
"""Run Mission #003 external reproduction + red-team certification."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

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
from src.crk1.crk1_redteam_suite import CRK1RedTeamSuite
from src.crk1.d3_reproduction_certificate import issue_d3_certificate
from src.crk1.external_reproduction_harness import ExternalReproductionHarness
from src.crk1.reproduction_certifier import Mission003Certifier
from src.crk1.runtime_facade import CRK1Runtime


def _bootstrap_runtime(online_dir: Path) -> CRK1Runtime:
    online_dir.mkdir(parents=True, exist_ok=True)
    evidence = EvidenceLedgerStore()
    bootstrap_evidence_ledger(evidence)
    for evidence_id in ("EVD-CRK1-001",):
        evidence.upsert_evidence_record(
            EvidenceRecord(
                evidence_id=evidence_id,
                evidence_hash=f"{evidence_id}-hash",
                evidence_type=EvidenceType.IMPORT,
                source_lineage="CRK1-MISSION-003",
                source_epoch=17,
                validation_method="mission-003",
                confidence=0.95,
                canonical_hash=f"{evidence_id}-hash",
            )
        )
    ledgers = ConstitutionalLedgers(
        identity=DEFAULT_IDENTITY,
        decisions=DecisionLedgerStore(),
        resources=ResourceLedgerStore(),
        outcomes=OutcomeLedgerStore(config=OutcomeConfig()),
        evidence_store=evidence,
        epoch=17,
    )
    bootstrap_decision_ledger(ledgers.decisions, epoch=ledgers.epoch)
    bootstrap_resource_ledger(ledgers.resources, epoch=ledgers.epoch)
    bootstrap_outcome_ledger(ledgers.outcomes, epoch=ledgers.epoch)
    kernel = ConstitutionalRuntime(
        ledgers,
        evidence_contract=EvidenceContract(evidence_store=ledgers.evidence_store),
        governance_contract=GovernanceContract(ledgers.identity),
        runtime_contract=RuntimeContract(),
    )
    return CRK1Runtime(kernel)


def main() -> int:
    parser = argparse.ArgumentParser(description="Mission #003 CRK-1 certification")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit certification JSON only",
    )
    parser.add_argument(
        "--workdir",
        type=Path,
        default=_ROOT / ".mission-003",
        help="Ephemeral runtime directory",
    )
    parser.add_argument(
        "--d3-seal",
        action="store_true",
        help="Emit D-3 Reproduction Certificate (markdown)",
    )
    args = parser.parse_args()

    runtime = _bootstrap_runtime(args.workdir)
    certifier = Mission003Certifier(runtime)
    report = certifier.certify()

    if args.d3_seal:
        d3 = issue_d3_certificate(runtime)
        print(d3.to_markdown())
        return 0 if d3.certified else 1

    if args.json:
        print(report.to_json())
        return 0 if report.certified else 1

    repro = ExternalReproductionHarness(runtime).run_all()
    red_team = CRK1RedTeamSuite(runtime).run_full()

    print(repro.summary())
    print()
    print(red_team.summary())
    print()
    print(report.to_json())

    return 0 if report.certified else 1


if __name__ == "__main__":
    raise SystemExit(main())
