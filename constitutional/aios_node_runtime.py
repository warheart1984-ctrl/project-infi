from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Mapping, Sequence


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _hash(value: Any) -> str:
    return hashlib.sha3_256(_canonical_json(value).encode("utf-8")).hexdigest()


def _as_tuple(values: Sequence[Any] | None) -> tuple[str, ...]:
    if not values:
        return ()
    return tuple(str(value) for value in values if str(value))


def _score_band(score: float) -> str:
    if score < 0.0 or score > 1.0:
        raise ValueError(f"trust score must be within 0..1, got {score!r}")
    if score < 0.34:
        return "low"
    if score < 0.67:
        return "medium"
    return "high"


def _receipt_signature(payload_hash: str, previous_hash: str, receipt_id: str) -> str:
    return _hash(
        {
            "payloadHash": payload_hash,
            "previousHash": previous_hash,
            "receiptId": receipt_id,
        }
    )


AIOS_RUNTIME_PLANES: tuple[dict[str, Any], ...] = (
    {
        "name": "Identity Runtime",
        "apis": ("Identity", "Authority", "Relationship"),
        "role": "Manage constitutional identities, authority, delegation, and consent.",
    },
    {
        "name": "Evidence Runtime",
        "apis": ("Evidence", "Provenance", "Traceability"),
        "role": "Ingest, validate, store, and expose evidence artifacts.",
    },
    {
        "name": "Truth Runtime",
        "apis": ("Knowledge", "Conformance"),
        "role": "Interpret evidence in context without overriding ledger neutrality.",
    },
    {
        "name": "Knowledge Runtime",
        "apis": ("Knowledge", "Traceability"),
        "role": "Maintain ontology, knowledge graph, semantic links, and traceability.",
    },
    {
        "name": "Sovereignty Runtime",
        "apis": ("Governance", "Conformance"),
        "role": "Enforce constitutional rules, tiers, authority boundaries, and node governance.",
    },
    {
        "name": "Continuity Runtime",
        "apis": ("Provenance", "Governance", "Conformance"),
        "role": "Preserve lineage, invariants, replayability, and constitutional evolution.",
    },
    {
        "name": "Institutional Memory Runtime",
        "apis": ("Relationship", "Evidence", "Traceability"),
        "role": "Record decisions, receipts, relationships, and institutional workflows.",
    },
    {
        "name": "Reality Runtime",
        "apis": ("Identity", "Evidence", "Knowledge"),
        "role": "Optional v1 integration of external signals into constitutional context.",
    },
)


AIOS_CONSTITUTIONAL_APIS: dict[str, tuple[str, ...]] = {
    "identity": ("register", "delegate", "link"),
    "evidence": ("ingest", "validate", "expose"),
    "truth": ("evaluate",),
    "knowledge": ("link", "trace"),
    "sovereignty": ("govern", "conform"),
    "continuity": ("record", "replay"),
    "memory": ("remember", "audit"),
    "reality": ("ingest", "relate", "project"),
}


@dataclass(frozen=True)
class IdentityRecord:
    identity_id: str
    type: str
    attributes: dict[str, Any]
    created_at: str
    provenance_id: str


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    identity_id: str
    type: str
    content_ref: str
    provenance_id: str
    timestamp: str


@dataclass(frozen=True)
class ProvenanceRecord:
    provenance_id: str
    parent_id: str
    source: str
    lineage_chain: tuple[str, ...]
    timestamp: str


@dataclass(frozen=True)
class RelationshipRecord:
    relationship_id: str
    subject_identity_id: str
    object_identity_id: str
    relationship_type: str
    provenance_id: str
    temporal_bounds: tuple[str, str]
    steward_identity_id: str


@dataclass(frozen=True)
class TrustAssertionRecord:
    trust_id: str
    relationship_id: str
    issuer_identity_id: str
    trust_score: float
    confidence_band: str
    context: dict[str, Any]
    evidence_ids: tuple[str, ...]
    timestamp: str


@dataclass(frozen=True)
class ConstitutionalDecisionRecord:
    decision_id: str
    node_id: str
    inputs: dict[str, Any]
    result: dict[str, Any]
    governance_clauses: tuple[str, ...]
    conformance_status: str
    receipt_id: str
    timestamp: str


@dataclass(frozen=True)
class ConstitutionalReceiptRecord:
    receipt_id: str
    decision_id: str
    ledger_entry_id: str
    hash: str
    signature: str
    timestamp: str


@dataclass(frozen=True)
class LedgerEntry:
    entry_id: str
    entry_type: str
    previous_hash: str
    payload: dict[str, Any]
    entry_hash: str
    signature: str
    timestamp: str


@dataclass(frozen=True)
class GovernancePacket:
    allowed: bool
    status: str
    governance_factor: float
    trust_score: float
    trust_band: str
    applied_constraints: tuple[str, ...]
    clause_results: tuple[str, ...]
    conformance_status: str
    decision_id: str
    receipt_id: str


class ConstitutionalAccessError(RuntimeError):
    pass


class AIOSConstitutionalLedger:
    def __init__(self) -> None:
        self.entries: list[LedgerEntry] = []
        self.identities: dict[str, IdentityRecord] = {}
        self.evidence: dict[str, EvidenceRecord] = {}
        self.provenance: dict[str, ProvenanceRecord] = {}
        self.relationships: dict[str, RelationshipRecord] = {}
        self.trust: dict[str, TrustAssertionRecord] = {}
        self.decisions: dict[str, ConstitutionalDecisionRecord] = {}
        self.receipts: dict[str, ConstitutionalReceiptRecord] = {}

    def append(self, entry_type: str, payload: Mapping[str, Any], *, entry_id: str | None = None) -> LedgerEntry:
        previous_hash = self.entries[-1].entry_hash if self.entries else ""
        timestamp = str(payload.get("timestamp", _now()))
        entry_id = entry_id or str(payload.get("id") or payload.get("identity_id") or payload.get("decision_id") or payload.get("receipt_id") or f"{entry_type}-{len(self.entries) + 1:04d}")
        entry_payload = dict(payload)
        entry_payload.setdefault("timestamp", timestamp)
        entry_payload.setdefault("entryType", entry_type)
        entry_payload.setdefault("entryId", entry_id)
        entry_hash = _hash(
            {
                "entryType": entry_type,
                "entryId": entry_id,
                "previousHash": previous_hash,
                "payload": entry_payload,
            }
        )
        signature = _receipt_signature(entry_hash, previous_hash, entry_id)
        entry = LedgerEntry(
            entry_id=entry_id,
            entry_type=entry_type,
            previous_hash=previous_hash,
            payload=entry_payload,
            entry_hash=entry_hash,
            signature=signature,
            timestamp=timestamp,
        )
        self.entries.append(entry)
        return entry

    def verify_chain(self) -> bool:
        previous_hash = ""
        for entry in self.entries:
            expected_hash = _hash(
                {
                    "entryType": entry.entry_type,
                    "entryId": entry.entry_id,
                    "previousHash": previous_hash,
                    "payload": entry.payload,
                }
            )
            expected_signature = _receipt_signature(expected_hash, previous_hash, entry.entry_id)
            if (
                entry.previous_hash != previous_hash
                or entry.entry_hash != expected_hash
                or entry.signature != expected_signature
            ):
                return False
            previous_hash = entry.entry_hash
        return True

    def replay(self) -> list[dict[str, Any]]:
        return [
            {
                "entry_id": entry.entry_id,
                "entry_type": entry.entry_type,
                "previous_hash": entry.previous_hash,
                "payload": dict(entry.payload),
                "entry_hash": entry.entry_hash,
                "signature": entry.signature,
                "timestamp": entry.timestamp,
            }
            for entry in self.entries
        ]

    def snapshot(self) -> dict[str, Any]:
        return {
            "entryCount": len(self.entries),
            "entries": self.replay(),
            "identities": [asdict(record) for record in self.identities.values()],
            "evidence": [asdict(record) for record in self.evidence.values()],
            "provenance": [asdict(record) for record in self.provenance.values()],
            "relationships": [asdict(record) for record in self.relationships.values()],
            "trust": [asdict(record) for record in self.trust.values()],
            "decisions": [asdict(record) for record in self.decisions.values()],
            "receipts": [asdict(record) for record in self.receipts.values()],
            "chainValid": self.verify_chain(),
        }


class AIOSConstitutionalNodeRuntime:
    def __init__(self, node_id: str = "aios-node-v1") -> None:
        self.node_id = node_id
        self.ledger = AIOSConstitutionalLedger()
        self.api_catalog = dict(AIOS_CONSTITUTIONAL_APIS)

    def list_runtime_planes(self) -> tuple[dict[str, Any], ...]:
        return tuple(dict(plane) for plane in AIOS_RUNTIME_PLANES)

    def list_constitutional_apis(self) -> dict[str, tuple[str, ...]]:
        return dict(self.api_catalog)

    def invoke(self, runtime_name: str, api_name: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        normalized_runtime = str(runtime_name).strip().lower()
        runtime_key = self._runtime_name(normalized_runtime)
        allowed_apis = self.api_catalog.get(runtime_key)
        if allowed_apis is None:
            raise ConstitutionalAccessError(f"Unknown runtime: {runtime_name!r}")
        if api_name not in allowed_apis:
            raise ConstitutionalAccessError(f"API {api_name!r} is not available on runtime {runtime_name!r}")
        handler = getattr(self, f"_{runtime_key}_{api_name.lower()}", None)
        if handler is None:
            raise ConstitutionalAccessError(f"No handler registered for {runtime_name!r}.{api_name!r}")
        result = handler(dict(payload))
        return result if isinstance(result, dict) else {"result": result}

    def _runtime_name(self, normalized_runtime: str) -> str:
        mapping = {
            "identity runtime": "identity",
            "evidence runtime": "evidence",
            "truth runtime": "truth",
            "knowledge runtime": "knowledge",
            "sovereignty runtime": "sovereignty",
            "continuity runtime": "continuity",
            "institutional memory runtime": "memory",
            "reality runtime": "reality",
        }
        return mapping.get(normalized_runtime, normalized_runtime)

    def _identity_register(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        record = self.register_identity(
            str(payload.get("identity_id", payload.get("id", ""))),
            str(payload.get("type", "system")),
            payload.get("attributes", {}),
            provenance_id=str(payload.get("provenance_id", "")),
            created_at=payload.get("created_at"),
        )
        return asdict(record)

    def _evidence_ingest(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        record = self.ingest_evidence(
            str(payload.get("evidence_id", payload.get("id", ""))),
            str(payload.get("identity_id", "")),
            str(payload.get("type", "evidence")),
            str(payload.get("content_ref", "")),
            provenance_id=str(payload.get("provenance_id", "")),
            timestamp=payload.get("timestamp"),
        )
        return asdict(record)

    def _truth_evaluate(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        evidence_ids = payload.get("evidence_ids", payload.get("evidenceIds", []))
        context = payload.get("context", {})
        return self.evaluate_truth(tuple(evidence_ids or ()), context)

    def _knowledge_link(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        return self.link_knowledge(
            str(payload.get("subject", "")),
            str(payload.get("predicate", "")),
            str(payload.get("object", "")),
            provenance_id=str(payload.get("provenance_id", "")),
        )

    def _sovereignty_govern(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        packet = self.evaluate_governance(
            node_id=str(payload.get("node_id", self.node_id)),
            inputs=dict(payload.get("inputs", {})),
            evidence_ids=tuple(payload.get("evidence_ids", ())),
            relationship_ids=tuple(payload.get("relationship_ids", ())),
            trust_ids=tuple(payload.get("trust_ids", ())),
            governance_clauses=tuple(payload.get("governance_clauses", ())),
        )
        return asdict(packet)

    def _continuity_record(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        record = self.record_memory(
            str(payload.get("relationship_id", "")),
            tuple(payload.get("evidence_ids", ())),
            dict(payload.get("workflow", {})),
        )
        return record

    def _memory_remember(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        return self.record_memory(
            str(payload.get("relationship_id", "")),
            tuple(payload.get("evidence_ids", ())),
            dict(payload.get("workflow", {})),
        )

    def _memory_audit(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "entries": self.ledger.replay(),
            "query": dict(payload),
            "chainValid": self.ledger.verify_chain(),
        }

    def _reality_ingest(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        return self.ingest_reality(str(payload.get("identity_id", "")), payload.get("signal", {}))

    def _reality_relate(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        return self.record_relationship(
            str(payload.get("relationship_id", f"rel::{len(self.ledger.relationships) + 1:04d}")),
            str(payload.get("subject_identity_id", "")),
            str(payload.get("object_identity_id", "")),
            str(payload.get("relationship_type", "dependency")),
            str(payload.get("provenance_id", "")),
            temporal_bounds=tuple(payload.get("temporal_bounds", ("", "")))[:2] if payload.get("temporal_bounds") else ("", ""),
            steward_identity_id=str(payload.get("steward_identity_id", "")),
        ).__dict__

    def _reality_project(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        return self.ingest_reality(str(payload.get("identity_id", "")), payload.get("signal", {}))

    def register_identity(
        self,
        identity_id: str,
        type: str,
        attributes: Mapping[str, Any] | None = None,
        *,
        provenance_id: str = "",
        created_at: str | None = None,
    ) -> IdentityRecord:
        record = IdentityRecord(
            identity_id=identity_id,
            type=type,
            attributes=dict(attributes or {}),
            created_at=created_at or _now(),
            provenance_id=provenance_id,
        )
        self.ledger.identities[identity_id] = record
        self.ledger.append("Identity", asdict(record), entry_id=identity_id)
        return record

    def ingest_evidence(
        self,
        evidence_id: str,
        identity_id: str,
        type: str,
        content_ref: str,
        *,
        provenance_id: str = "",
        timestamp: str | None = None,
    ) -> EvidenceRecord:
        record = EvidenceRecord(
            evidence_id=evidence_id,
            identity_id=identity_id,
            type=type,
            content_ref=content_ref,
            provenance_id=provenance_id,
            timestamp=timestamp or _now(),
        )
        self.ledger.evidence[evidence_id] = record
        self.ledger.append("Evidence", asdict(record), entry_id=evidence_id)
        return record

    def record_provenance(
        self,
        provenance_id: str,
        parent_id: str,
        source: str,
        lineage_chain: Sequence[str] | None = None,
        *,
        timestamp: str | None = None,
    ) -> ProvenanceRecord:
        record = ProvenanceRecord(
            provenance_id=provenance_id,
            parent_id=parent_id,
            source=source,
            lineage_chain=_as_tuple(lineage_chain),
            timestamp=timestamp or _now(),
        )
        self.ledger.provenance[provenance_id] = record
        self.ledger.append("Provenance", asdict(record), entry_id=provenance_id)
        return record

    def record_relationship(
        self,
        relationship_id: str,
        subject_identity_id: str,
        object_identity_id: str,
        relationship_type: str,
        provenance_id: str,
        *,
        temporal_bounds: tuple[str, str] = ("", ""),
        steward_identity_id: str = "",
    ) -> RelationshipRecord:
        record = RelationshipRecord(
            relationship_id=relationship_id,
            subject_identity_id=subject_identity_id,
            object_identity_id=object_identity_id,
            relationship_type=relationship_type,
            provenance_id=provenance_id,
            temporal_bounds=tuple(temporal_bounds),
            steward_identity_id=steward_identity_id,
        )
        self.ledger.relationships[relationship_id] = record
        self.ledger.append("Relationship", asdict(record), entry_id=relationship_id)
        return record

    def assert_trust(
        self,
        trust_id: str,
        relationship_id: str,
        issuer_identity_id: str,
        trust_score: float,
        context: Mapping[str, Any],
        evidence_ids: Sequence[str],
        *,
        timestamp: str | None = None,
    ) -> TrustAssertionRecord:
        band = _score_band(trust_score)
        record = TrustAssertionRecord(
            trust_id=trust_id,
            relationship_id=relationship_id,
            issuer_identity_id=issuer_identity_id,
            trust_score=trust_score,
            confidence_band=band,
            context=dict(context),
            evidence_ids=_as_tuple(evidence_ids),
            timestamp=timestamp or _now(),
        )
        self.ledger.trust[trust_id] = record
        self.ledger.append("TrustAssertion", asdict(record), entry_id=trust_id)
        return record

    def evaluate_truth(self, evidence_ids: Sequence[str], context: Mapping[str, Any] | None = None) -> dict[str, Any]:
        referenced = [self.ledger.evidence[evidence_id] for evidence_id in evidence_ids if evidence_id in self.ledger.evidence]
        score = min(1.0, 0.25 + 0.2 * len(referenced))
        band = _score_band(score)
        return {
            "result": "interpretive",
            "score": score,
            "band": band,
            "evidenceIds": [record.evidence_id for record in referenced],
            "context": dict(context or {}),
        }

    def link_knowledge(self, subject: str, predicate: str, object_: str, *, provenance_id: str = "") -> dict[str, Any]:
        payload = {
            "subject": subject,
            "predicate": predicate,
            "object": object_,
            "provenance_id": provenance_id,
            "timestamp": _now(),
        }
        self.ledger.append("Knowledge", payload, entry_id=f"knowledge::{len(self.ledger.entries) + 1:04d}")
        return payload

    def evaluate_governance(
        self,
        *,
        node_id: str,
        inputs: Mapping[str, Any],
        evidence_ids: Sequence[str] = (),
        relationship_ids: Sequence[str] = (),
        trust_ids: Sequence[str] = (),
        governance_clauses: Sequence[str] = (),
    ) -> GovernancePacket:
        referenced_evidence = [self.ledger.evidence[evidence_id] for evidence_id in evidence_ids if evidence_id in self.ledger.evidence]
        referenced_trust = [self.ledger.trust[trust_id] for trust_id in trust_ids if trust_id in self.ledger.trust]
        trust_score = max((item.trust_score for item in referenced_trust), default=0.0)
        trust_band = _score_band(trust_score if trust_score else 0.0)
        evidence_factor = min(1.0, len(referenced_evidence) / 2.0)
        authority_factor = 1.0 if relationship_ids else 0.5
        governance_factor = round((0.45 * evidence_factor) + (0.35 * trust_score) + (0.20 * authority_factor), 3)

        clause_results: list[str] = []
        applied_constraints: list[str] = []
        allowed = True
        status = "allowed"

        if not referenced_evidence:
            clause_results.append("evidence before assertion: blocked")
            applied_constraints.append("missing evidence")
            allowed = False
            status = "blocked"
        else:
            clause_results.append("evidence before assertion: satisfied")

        if trust_band == "low" and len(referenced_evidence) < 2:
            clause_results.append("authority before action: blocked")
            applied_constraints.append("low trust requires stronger evidence")
            allowed = False
            status = "blocked"
        else:
            clause_results.append("authority before action: satisfied")

        if bool(inputs.get("execution")) and not bool(inputs.get("simulation")):
            clause_results.append("simulation before execution: warning")
            if allowed:
                status = "warning"
        else:
            clause_results.append("simulation before execution: satisfied")

        if bool(inputs.get("commitment")) and not bool(inputs.get("recovery_plan")):
            clause_results.append("recovery before commitment: warning")
            if allowed and status == "allowed":
                status = "warning"
        else:
            clause_results.append("recovery before commitment: satisfied")

        if bool(inputs.get("boundary")):
            clause_results.append("human judgment at boundaries: escalated")
            applied_constraints.append("boundary review required")
            if status == "allowed":
                status = "warning"
        else:
            clause_results.append("human judgment at boundaries: not required")

        receipt_id = f"receipt::{node_id}::{len(self.ledger.receipts) + 1:04d}"
        decision_id = f"decision::{node_id}::{len(self.ledger.decisions) + 1:04d}"
        result = {
            "node_id": node_id,
            "inputs": dict(inputs),
            "allowed": allowed,
            "status": status,
            "governance_factor": governance_factor,
            "trust_score": trust_score,
            "trust_band": trust_band,
            "applied_constraints": applied_constraints,
            "clause_results": clause_results,
            "evidence_ids": list(evidence_ids),
            "relationship_ids": list(relationship_ids),
            "trust_ids": list(trust_ids),
        }
        decision = ConstitutionalDecisionRecord(
            decision_id=decision_id,
            node_id=node_id,
            inputs=dict(inputs),
            result=result,
            governance_clauses=tuple(governance_clauses),
            conformance_status="pass" if allowed else "fail",
            receipt_id=receipt_id,
            timestamp=_now(),
        )
        self.ledger.decisions[decision_id] = decision
        decision_entry = self.ledger.append("ConstitutionalDecision", asdict(decision), entry_id=decision_id)
        payload_hash = _hash(asdict(decision))
        receipt = ConstitutionalReceiptRecord(
            receipt_id=receipt_id,
            decision_id=decision_id,
            ledger_entry_id=decision_entry.entry_id,
            hash=payload_hash,
            signature=_receipt_signature(payload_hash, decision_entry.entry_hash, receipt_id),
            timestamp=_now(),
        )
        self.ledger.receipts[receipt_id] = receipt
        self.ledger.append("ConstitutionalReceipt", asdict(receipt), entry_id=receipt_id)
        return GovernancePacket(
            allowed=allowed,
            status=status,
            governance_factor=governance_factor,
            trust_score=trust_score,
            trust_band=trust_band,
            applied_constraints=tuple(applied_constraints),
            clause_results=tuple(clause_results),
            conformance_status=decision.conformance_status,
            decision_id=decision_id,
            receipt_id=receipt_id,
        )

    def record_memory(self, relationship_id: str, evidence_ids: Sequence[str], workflow: Mapping[str, Any]) -> dict[str, Any]:
        payload = {
            "relationship_id": relationship_id,
            "evidence_ids": list(evidence_ids),
            "workflow": dict(workflow),
            "timestamp": _now(),
        }
        self.ledger.append("InstitutionalMemory", payload, entry_id=f"memory::{len(self.ledger.entries) + 1:04d}")
        return payload

    def ingest_reality(self, identity_id: str, signal: Mapping[str, Any]) -> dict[str, Any]:
        payload = {
            "identity_id": identity_id,
            "signal": dict(signal),
            "timestamp": _now(),
        }
        self.ledger.append("Reality", payload, entry_id=f"reality::{len(self.ledger.entries) + 1:04d}")
        return payload

    def replay(self) -> list[dict[str, Any]]:
        return self.ledger.replay()

    def snapshot(self) -> dict[str, Any]:
        return {
            "nodeId": self.node_id,
            "runtimes": self.list_runtime_planes(),
            "apis": self.list_constitutional_apis(),
            "ledger": self.ledger.snapshot(),
        }


def build_aios_node_runtime(node_id: str = "aios-node-v1") -> AIOSConstitutionalNodeRuntime:
    return AIOSConstitutionalNodeRuntime(node_id=node_id)


__all__ = [
    "AIOSConstitutionalLedger",
    "AIOSConstitutionalNodeRuntime",
    "AIOS_CONSTITUTIONAL_APIS",
    "AIOS_RUNTIME_PLANES",
    "ConstitutionalAccessError",
    "ConstitutionalDecisionRecord",
    "ConstitutionalReceiptRecord",
    "EvidenceRecord",
    "GovernancePacket",
    "IdentityRecord",
    "LedgerEntry",
    "ProvenanceRecord",
    "RelationshipRecord",
    "TrustAssertionRecord",
    "build_aios_node_runtime",
]
