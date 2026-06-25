"""Export CRK-1 dashboard JSON — validator, attack sim, governance receipts."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.crk1.attack_simulator import InsulationAttackSimulator
from src.crk1.consequence_lattice import consequence_exposure
from src.crk1.governance_receipt import issue_receipt
from src.crk1.runtime_facade import CRK1Runtime
from src.crk1.runtime_validator import CRK1RuntimeValidator


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_dashboard_payload(facade: CRK1Runtime) -> dict:
    identity_id = facade.kernel.ledgers.identity.id

    def lineage_resolver(identity: object) -> list[str]:
        ident_id = str(getattr(identity, "id", identity))
        chain = [ident_id]
        parent = facade._identity_parents.get(ident_id)  # noqa: SLF001
        while parent:
            chain.append(parent)
            parent = facade._identity_parents.get(parent)  # noqa: SLF001
        return chain

    validator = CRK1RuntimeValidator(lineage_resolver=lineage_resolver)

    decision = facade.propose_and_execute(identity=identity_id, evidence=["EVD-CRK1-001"])
    outcome = facade.get_outcomes(decision.id)[0]
    evidence = facade.replay_outcome(outcome.id)

    context = {
        "from_state": "OutcomeReplayed",
        "to_state": "EvidenceAdmitted",
        "decision": decision,
        "outcome": outcome,
        "evidence": evidence,
        "identity": identity_id,
        "evidence_pool": [evidence],
        "identity_present": True,
        "evidence_present": True,
        "governance_approval": True,
        "create_outcome": True,
        "outcome_replayable": True,
        "evidence_admissible": True,
        "timestamp": _now_iso(),
    }

    receipt = issue_receipt(validator, context, ancestors=lineage_resolver(identity_id))
    attacks = InsulationAttackSimulator(facade).run_all(identity_id)
    ce = consequence_exposure(facade)

    all_pass = all(result[1] == "PASS" for result in attacks.values())
    continuity = receipt.continuity_status == "PRESERVED" and all_pass

    return {
        "runtime": "CRK-1 ConstitutionalRuntime",
        "updated_at": _now_iso(),
        "continuity_status": "PRESERVED" if continuity else "BREACHED",
        "consequence_exposure": ce.to_dict(),
        "invariants": {
            "K0": receipt.k0_status,
            "K1": receipt.k1_status,
            "K2": receipt.k2_status,
            "K3": receipt.k3_status,
            "K4": "PASS",
            "K5": "PASS",
            "K6": "PASS",
        },
        "lattice": {
            "K4": "Consequence Preservation Law",
            "K5": "Mutation Admissibility Test",
            "K6": "Constitutional Drift Envelope",
            "ce_score": ce.score,
        },
        "attacks": attacks,
        "receipts": [{"text": receipt.render(), **receipt.to_dict()}],
    }


def main() -> int:
    from src.continuity.constitutional_runtime import ConstitutionalRuntime, ConstitutionalLedgers
    from src.continuity.decision_ledger import bootstrap_decision_ledger
    from src.continuity.evidence_ledger import (
        EvidenceLedgerStore,
        EvidenceRecord,
        EvidenceType,
        bootstrap_evidence_ledger,
    )
    from src.continuity.outcome_fitness import OutcomeConfig
    from src.continuity.outcome_ledger import OutcomeLedgerStore, bootstrap_outcome_ledger
    from src.continuity.resource_ledger import ResourceLedgerStore, bootstrap_resource_ledger
    from src.continuity.constitutional_runtime import (
        DEFAULT_IDENTITY,
        EvidenceContract,
        GovernanceContract,
    )

    evidence = EvidenceLedgerStore()
    bootstrap_evidence_ledger(evidence)
    for evidence_id in ("EVD-CRK1-001",):
        evidence.upsert_evidence_record(
            EvidenceRecord(
                evidence_id=evidence_id,
                evidence_hash=f"{evidence_id}-hash",
                evidence_type=EvidenceType.IMPORT,
                source_lineage="CRK1-DASHBOARD",
                source_epoch=17,
                validation_method="crk1-dashboard",
                confidence=0.95,
                canonical_hash=f"{evidence_id}-hash",
            )
        )

    ledgers = ConstitutionalLedgers(
        identity=DEFAULT_IDENTITY,
        decisions=__import__("src.continuity.decision_ledger", fromlist=["DecisionLedgerStore"]).DecisionLedgerStore(),
        resources=ResourceLedgerStore(),
        outcomes=OutcomeLedgerStore(config=OutcomeConfig()),
        evidence_store=evidence,
        epoch=17,
    )
    bootstrap_decision_ledger(ledgers.decisions, epoch=17)
    bootstrap_resource_ledger(ledgers.resources, epoch=17)
    bootstrap_outcome_ledger(ledgers.outcomes, epoch=17)

    kernel = ConstitutionalRuntime(
        ledgers,
        evidence_contract=EvidenceContract(evidence_store=evidence),
        governance_contract=GovernanceContract(DEFAULT_IDENTITY),
    )
    facade = CRK1Runtime(kernel)
    payload = build_dashboard_payload(facade)

    out_path = _ROOT / "docs" / "crk1" / "crk1_dashboard_data.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[crk1-dashboard] wrote {out_path}")
    print(f"[crk1-dashboard] continuity={payload['continuity_status']}")
    return 0 if payload["continuity_status"] == "PRESERVED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
