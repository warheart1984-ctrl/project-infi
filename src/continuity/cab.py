"""Continuity Architecture Blueprint (CAB) — reconstructable governance lineage."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable


class CABObjectType(str, Enum):
    INTENT = "IntentRecord"
    DECISION = "DecisionRecord"
    ASSUMPTION = "AssumptionRecord"
    EVIDENCE_CHAIN = "EvidenceChain"
    CONTINUITY_RECEIPT = "ContinuityReceipt"
    FOUNDER_KNOWLEDGE = "FounderKnowledgeSnapshot"
    SUCCESSION = "SuccessionProtocol"
    RECONSTRUCTION = "ReconstructionPlan"


@dataclass(frozen=True)
class IntentRecord:
    intent_id: str
    authors: list[str]
    articulated_at: str
    scope: dict[str, Any]
    problem_statement: str
    desired_outcomes: list[str]
    created_at: str
    constraints: list[str] = field(default_factory=list)
    prior_intent_refs: list[str] = field(default_factory=list)
    decision_refs: list[str] = field(default_factory=list)
    superseded_by: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "intent_id": self.intent_id,
            "authors": list(self.authors),
            "articulated_at": self.articulated_at,
            "scope": dict(self.scope),
            "problem_statement": self.problem_statement,
            "desired_outcomes": list(self.desired_outcomes),
            "constraints": list(self.constraints),
            "prior_intent_refs": list(self.prior_intent_refs),
            "decision_refs": list(self.decision_refs),
            "created_at": self.created_at,
        }
        if self.superseded_by:
            payload["superseded_by"] = self.superseded_by
        return payload


@dataclass(frozen=True)
class DecisionRecord:
    decision_id: str
    decision_makers: list[str]
    chosen_option: str
    rationale: str
    intent_refs: list[str]
    created_at: str
    options_considered: list[dict[str, Any]] = field(default_factory=list)
    govern_policy_refs: list[str] = field(default_factory=list)
    evidence_chain_refs: list[str] = field(default_factory=list)
    assumption_refs: list[str] = field(default_factory=list)
    continuity_receipt_refs: list[str] = field(default_factory=list)
    review_conditions: str = ""
    superseded_by: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "decision_id": self.decision_id,
            "decision_makers": list(self.decision_makers),
            "intent_refs": list(self.intent_refs),
            "options_considered": [dict(item) for item in self.options_considered],
            "chosen_option": self.chosen_option,
            "rationale": self.rationale,
            "govern_policy_refs": list(self.govern_policy_refs),
            "evidence_chain_refs": list(self.evidence_chain_refs),
            "assumption_refs": list(self.assumption_refs),
            "continuity_receipt_refs": list(self.continuity_receipt_refs),
            "review_conditions": self.review_conditions,
            "created_at": self.created_at,
        }
        if self.superseded_by:
            payload["superseded_by"] = self.superseded_by
        return payload


@dataclass(frozen=True)
class AssumptionRecord:
    assumption_id: str
    statement: str
    assumption_type: str
    confidence: float
    created_at: str
    justification: str = ""
    evidence_chain_refs: list[str] = field(default_factory=list)
    fragility_markers: list[str] = field(default_factory=list)
    review_cadence: str = ""
    decision_refs: list[str] = field(default_factory=list)
    superseded_by: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "assumption_id": self.assumption_id,
            "statement": self.statement,
            "assumption_type": self.assumption_type,
            "confidence": self.confidence,
            "justification": self.justification,
            "evidence_chain_refs": list(self.evidence_chain_refs),
            "fragility_markers": list(self.fragility_markers),
            "review_cadence": self.review_cadence,
            "decision_refs": list(self.decision_refs),
            "created_at": self.created_at,
        }
        if self.superseded_by:
            payload["superseded_by"] = self.superseded_by
        return payload


@dataclass(frozen=True)
class EvidenceChain:
    chain_id: str
    sources: list[str]
    methods: list[str]
    created_at: str
    neomundi_measurement_refs: list[str] = field(default_factory=list)
    integrity_assessment: str = ""
    assumption_refs: list[str] = field(default_factory=list)
    decision_refs: list[str] = field(default_factory=list)
    continuity_receipt_refs: list[str] = field(default_factory=list)
    superseded_by: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "chain_id": self.chain_id,
            "neomundi_measurement_refs": list(self.neomundi_measurement_refs),
            "sources": list(self.sources),
            "methods": list(self.methods),
            "integrity_assessment": self.integrity_assessment,
            "assumption_refs": list(self.assumption_refs),
            "decision_refs": list(self.decision_refs),
            "continuity_receipt_refs": list(self.continuity_receipt_refs),
            "created_at": self.created_at,
        }
        if self.superseded_by:
            payload["superseded_by"] = self.superseded_by
        return payload


@dataclass(frozen=True)
class ContinuityReceipt:
    receipt_id: str
    identity_context: dict[str, Any]
    authority_surface: list[str]
    event_description: str
    trace_id: str
    created_at: str
    evaluation_outcome: str = ""
    trace_hash: str = ""
    proof_id: str = ""
    cvr_id: str = ""
    cvr_snapshot: dict[str, Any] = field(default_factory=dict)
    decision_refs: list[str] = field(default_factory=list)
    govern_policy_refs: list[str] = field(default_factory=list)
    continuity_governance: dict[str, Any] = field(default_factory=dict)
    superseded_by: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "receipt_id": self.receipt_id,
            "identity_context": dict(self.identity_context),
            "authority_surface": list(self.authority_surface),
            "event_description": self.event_description,
            "evaluation_outcome": self.evaluation_outcome,
            "trace_id": self.trace_id,
            "trace_hash": self.trace_hash,
            "proof_id": self.proof_id,
            "cvr_id": self.cvr_id,
            "cvr_snapshot": dict(self.cvr_snapshot),
            "decision_refs": list(self.decision_refs),
            "govern_policy_refs": list(self.govern_policy_refs),
            "continuity_governance": dict(self.continuity_governance),
            "created_at": self.created_at,
        }
        if self.superseded_by:
            payload["superseded_by"] = self.superseded_by
        return payload


@dataclass(frozen=True)
class FounderKnowledgeSnapshot:
    snapshot_id: str
    knowledge_holder: dict[str, str]
    narrative: str
    created_at: str
    mental_models: list[str] = field(default_factory=list)
    failure_scars: list[str] = field(default_factory=list)
    artifact_pointers: list[str] = field(default_factory=list)
    intent_refs: list[str] = field(default_factory=list)
    decision_refs: list[str] = field(default_factory=list)
    succession_notes: str = ""
    superseded_by: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "snapshot_id": self.snapshot_id,
            "knowledge_holder": dict(self.knowledge_holder),
            "narrative": self.narrative,
            "mental_models": list(self.mental_models),
            "failure_scars": list(self.failure_scars),
            "artifact_pointers": list(self.artifact_pointers),
            "intent_refs": list(self.intent_refs),
            "decision_refs": list(self.decision_refs),
            "succession_notes": self.succession_notes,
            "created_at": self.created_at,
        }
        if self.superseded_by:
            payload["superseded_by"] = self.superseded_by
        return payload


@dataclass(frozen=True)
class SuccessionProtocol:
    protocol_id: str
    roles: list[dict[str, Any]]
    onboarding_steps: list[str]
    offboarding_steps: list[str]
    created_at: str
    review_triggers: list[str] = field(default_factory=list)
    reconstruction_plan_refs: list[str] = field(default_factory=list)
    superseded_by: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "protocol_id": self.protocol_id,
            "roles": [dict(role) for role in self.roles],
            "onboarding_steps": list(self.onboarding_steps),
            "offboarding_steps": list(self.offboarding_steps),
            "review_triggers": list(self.review_triggers),
            "reconstruction_plan_refs": list(self.reconstruction_plan_refs),
            "created_at": self.created_at,
        }
        if self.superseded_by:
            payload["superseded_by"] = self.superseded_by
        return payload


@dataclass(frozen=True)
class ReconstructionPlan:
    plan_id: str
    minimal_object_refs: list[str]
    reconstruction_order: list[str]
    runtime_component_map: dict[str, Any]
    created_at: str
    known_gaps: list[str] = field(default_factory=list)
    steward_recommendations: list[str] = field(default_factory=list)
    superseded_by: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "plan_id": self.plan_id,
            "minimal_object_refs": list(self.minimal_object_refs),
            "reconstruction_order": list(self.reconstruction_order),
            "runtime_component_map": dict(self.runtime_component_map),
            "known_gaps": list(self.known_gaps),
            "steward_recommendations": list(self.steward_recommendations),
            "created_at": self.created_at,
        }
        if self.superseded_by:
            payload["superseded_by"] = self.superseded_by
        return payload


CABObject = (
    IntentRecord
    | DecisionRecord
    | AssumptionRecord
    | EvidenceChain
    | ContinuityReceipt
    | FounderKnowledgeSnapshot
    | SuccessionProtocol
    | ReconstructionPlan
)


def cab_object_type(obj: CABObject) -> CABObjectType:
    if isinstance(obj, IntentRecord):
        return CABObjectType.INTENT
    if isinstance(obj, DecisionRecord):
        return CABObjectType.DECISION
    if isinstance(obj, AssumptionRecord):
        return CABObjectType.ASSUMPTION
    if isinstance(obj, EvidenceChain):
        return CABObjectType.EVIDENCE_CHAIN
    if isinstance(obj, ContinuityReceipt):
        return CABObjectType.CONTINUITY_RECEIPT
    if isinstance(obj, FounderKnowledgeSnapshot):
        return CABObjectType.FOUNDER_KNOWLEDGE
    if isinstance(obj, SuccessionProtocol):
        return CABObjectType.SUCCESSION
    if isinstance(obj, ReconstructionPlan):
        return CABObjectType.RECONSTRUCTION
    raise TypeError(f"unsupported CAB object: {type(obj)!r}")


def cab_object_id(obj: CABObject) -> str:
    mapping = {
        IntentRecord: "intent_id",
        DecisionRecord: "decision_id",
        AssumptionRecord: "assumption_id",
        EvidenceChain: "chain_id",
        ContinuityReceipt: "receipt_id",
        FounderKnowledgeSnapshot: "snapshot_id",
        SuccessionProtocol: "protocol_id",
        ReconstructionPlan: "plan_id",
    }
    field_name = mapping[type(obj)]
    return str(getattr(obj, field_name))


@dataclass
class CABLedgerEntry:
    sequence: int
    object_type: CABObjectType
    object_id: str
    payload: dict[str, Any]
    created_at: str
    superseded: bool = False


@dataclass
class CABLedger:
    """Append-only continuity ledger for CAB objects."""

    entries: list[CABLedgerEntry] = field(default_factory=list)
    store_path: Path | None = None

    @classmethod
    def open(cls, path: Path | None = None) -> CABLedger:
        resolved = path or default_cab_store_path()
        ledger = cls(store_path=resolved)
        if resolved.exists():
            ledger._load(resolved)
        return ledger

    def append(self, obj: CABObject) -> CABLedgerEntry:
        object_id = cab_object_id(obj)
        if self.get_latest(object_id) is not None:
            raise ValueError(f"CAB object already exists (use supersede): {object_id}")
        entry = CABLedgerEntry(
            sequence=len(self.entries) + 1,
            object_type=cab_object_type(obj),
            object_id=object_id,
            payload=obj.to_dict(),
            created_at=str(getattr(obj, "created_at")),
        )
        self.entries.append(entry)
        self._persist_entry(entry)
        return entry

    def supersede(self, old_object_id: str, new_obj: CABObject) -> CABLedgerEntry:
        latest = self.get_latest(old_object_id)
        if latest is None:
            raise ValueError(f"unknown CAB object: {old_object_id}")
        marked = dict(latest.payload)
        marked["superseded_by"] = cab_object_id(new_obj)
        self.entries[latest.sequence - 1] = CABLedgerEntry(
            sequence=latest.sequence,
            object_type=latest.object_type,
            object_id=latest.object_id,
            payload=marked,
            created_at=latest.created_at,
            superseded=True,
        )
        return self.append(new_obj)

    def get_latest(self, object_id: str) -> CABLedgerEntry | None:
        matches = [entry for entry in self.entries if entry.object_id == object_id]
        if not matches:
            return None
        return matches[-1]

    def list_by_type(self, object_type: CABObjectType) -> list[CABLedgerEntry]:
        return [entry for entry in self.entries if entry.object_type == object_type and not entry.superseded]

    def active_payloads(self) -> dict[str, dict[str, Any]]:
        latest: dict[str, CABLedgerEntry] = {}
        for entry in self.entries:
            latest[entry.object_id] = entry
        return {
            object_id: entry.payload
            for object_id, entry in latest.items()
            if not entry.superseded and not entry.payload.get("superseded_by")
        }

    def _persist_entry(self, entry: CABLedgerEntry) -> None:
        if self.store_path is None:
            return
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "sequence": entry.sequence,
            "object_type": entry.object_type.value,
            "object_id": entry.object_id,
            "payload": entry.payload,
            "created_at": entry.created_at,
            "superseded": entry.superseded,
        }
        with self.store_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")

    def _load(self, path: Path) -> None:
        for line in path.read_text(encoding="utf-8").splitlines():
            cleaned = line.strip()
            if not cleaned:
                continue
            record = json.loads(cleaned)
            self.entries.append(
                CABLedgerEntry(
                    sequence=int(record["sequence"]),
                    object_type=CABObjectType(str(record["object_type"])),
                    object_id=str(record["object_id"]),
                    payload=dict(record["payload"]),
                    created_at=str(record["created_at"]),
                    superseded=bool(record.get("superseded")),
                )
            )


def default_cab_store_path() -> Path:
    override = os.environ.get("CAB_STORE", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    home = Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or ".").expanduser()
    return home / ".cab" / "ledger.jsonl"


def ingest_nova_continuity_governance(
    *,
    trace_id: str,
    identity_context: dict[str, Any],
    continuity_governance: dict[str, Any],
    event_description: str,
    created_at: str,
    decision_refs: Iterable[str] = (),
    govern_policy_refs: Iterable[str] = (),
    ledger: CABLedger | None = None,
) -> ContinuityReceipt:
    """Map Nova lawful-turn continuity_governance into a CAB ContinuityReceipt."""
    proof = dict(continuity_governance.get("proof") or {})
    cvr = dict(continuity_governance.get("cvr") or {})
    trace = dict(continuity_governance.get("continuity_trace") or {})
    receipt = ContinuityReceipt(
        receipt_id=f"cab.receipt.{trace_id}",
        identity_context=dict(identity_context),
        authority_surface=list(proof.get("law_surfaces") or cvr.get("law_surfaces") or []),
        event_description=event_description,
        evaluation_outcome=str(proof.get("status") or ""),
        trace_id=str(trace.get("trace_id") or trace_id),
        trace_hash=str(trace.get("trace_hash") or proof.get("replay_fingerprint") or ""),
        proof_id=str(proof.get("proof_id") or ""),
        cvr_id=str(cvr.get("cvr_id") or ""),
        cvr_snapshot=cvr,
        decision_refs=list(decision_refs),
        govern_policy_refs=list(govern_policy_refs),
        continuity_governance=dict(continuity_governance),
        created_at=created_at,
    )
    active = ledger or CABLedger()
    active.append(receipt)
    return receipt


def ingest_ciems_transformation_event(
    event: dict[str, Any],
    *,
    intent_refs: Iterable[str],
    decision_makers: Iterable[str],
    govern_policy_refs: Iterable[str] = (),
    continuity_receipt_refs: Iterable[str] = (),
    ledger: CABLedger | None = None,
) -> DecisionRecord:
    """Convert a governed CIEMS transformation event into CAB evidence + decision records."""
    active = ledger or CABLedger()
    suffix = _stable_suffix(
        {
            "timestamp": event.get("timestamp"),
            "thread_id": event.get("thread_id"),
            "event_type": event.get("event_type"),
            "context_hash_before": event.get("context_hash_before"),
            "context_hash_after": event.get("context_hash_after"),
            "output_hash": event.get("output_hash"),
            "state_change": event.get("state_change"),
            "file_target": event.get("file_target"),
        }
    )
    evidence_chain = ingest_neomundi_measurement(
        {
            "measurement_id": f"ciems.event.{suffix}",
            "source": str(event.get("backend") or "ciems"),
            "method": str(event.get("event_type") or "governed_transform"),
            "integrity": str(event.get("output_hash") or ""),
            "measured_at": str(event.get("timestamp") or ""),
            "context_hash_before": str(event.get("context_hash_before") or ""),
            "context_hash_after": str(event.get("context_hash_after") or ""),
            "file_target": str(event.get("file_target") or ""),
        },
        decision_refs=[f"cab.decision.ciems.{suffix}"],
        continuity_receipt_refs=continuity_receipt_refs,
        ledger=active,
        chain_prefix="cab.evidence_chain.ciems",
    )
    decision = DecisionRecord(
        decision_id=f"cab.decision.ciems.{suffix}",
        decision_makers=list(decision_makers),
        chosen_option=str(event.get("state_change") or event.get("event_type") or "governed_transform"),
        rationale=(
            "CIEMS governed transformation event preserved as CAB decision lineage "
            f"for thread {event.get('thread_id', '')}."
        ),
        intent_refs=list(intent_refs),
        options_considered=[
            {
                "event_type": event.get("event_type"),
                "input": event.get("input"),
                "conflict_flag": bool(event.get("conflict_flag")),
                "failure_code": event.get("failure_code") or "",
            }
        ],
        govern_policy_refs=list(govern_policy_refs),
        evidence_chain_refs=[evidence_chain.chain_id],
        continuity_receipt_refs=list(continuity_receipt_refs),
        review_conditions=str(event.get("failure_code") or ""),
        created_at=str(event.get("timestamp") or ""),
    )
    existing = active.get_latest(decision.decision_id)
    if existing is None:
        active.append(decision)
    return decision


def ingest_neomundi_measurement(
    measurement: dict[str, Any],
    *,
    decision_refs: Iterable[str] = (),
    assumption_refs: Iterable[str] = (),
    continuity_receipt_refs: Iterable[str] = (),
    ledger: CABLedger | None = None,
    chain_prefix: str = "cab.evidence_chain.neomundi",
) -> EvidenceChain:
    """Map a NeoMundi measurement into a stable, deduplicated CAB EvidenceChain."""
    active = ledger or CABLedger()
    measurement_ref = str(
        measurement.get("measurement_id")
        or measurement.get("id")
        or measurement.get("ref")
        or _stable_suffix(measurement)
    )
    chain_id = f"{chain_prefix}.{_safe_id(measurement_ref)}"
    existing = active.get_latest(chain_id)
    if existing is not None:
        return _evidence_chain_from_payload(existing.payload)
    integrity = str(
        measurement.get("integrity")
        or measurement.get("hash")
        or measurement.get("measurement_hash")
        or ""
    )
    source = str(measurement.get("source") or measurement.get("origin") or "neomundi")
    method = str(measurement.get("method") or measurement.get("measurement_method") or "measurement")
    chain = EvidenceChain(
        chain_id=chain_id,
        neomundi_measurement_refs=[measurement_ref],
        sources=[source],
        methods=[method],
        integrity_assessment=integrity,
        assumption_refs=list(assumption_refs),
        decision_refs=list(decision_refs),
        continuity_receipt_refs=list(continuity_receipt_refs),
        created_at=str(measurement.get("measured_at") or measurement.get("created_at") or ""),
    )
    active.append(chain)
    return chain


def _stable_suffix(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def _safe_id(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in ".:-_" else "-" for ch in value.strip().lower())
    return cleaned.strip(".:-_") or _stable_suffix({"value": value})


def _evidence_chain_from_payload(payload: dict[str, Any]) -> EvidenceChain:
    return EvidenceChain(
        chain_id=str(payload["chain_id"]),
        sources=list(payload.get("sources") or []),
        methods=list(payload.get("methods") or []),
        created_at=str(payload.get("created_at") or ""),
        neomundi_measurement_refs=list(payload.get("neomundi_measurement_refs") or []),
        integrity_assessment=str(payload.get("integrity_assessment") or ""),
        assumption_refs=list(payload.get("assumption_refs") or []),
        decision_refs=list(payload.get("decision_refs") or []),
        continuity_receipt_refs=list(payload.get("continuity_receipt_refs") or []),
        superseded_by=str(payload.get("superseded_by") or ""),
    )


def load_cab_scenario(path: Path) -> dict[str, Any]:
    import yaml

    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        return yaml.safe_load(text)
    return json.loads(text)


def populate_ledger_from_scenario(scenario: dict[str, Any]) -> CABLedger:
    ledger = CABLedger()
    for raw in scenario.get("intents") or []:
        ledger.append(IntentRecord(**raw))
    for raw in scenario.get("assumptions") or []:
        ledger.append(AssumptionRecord(**raw))
    for raw in scenario.get("evidence_chains") or []:
        ledger.append(EvidenceChain(**raw))
    for raw in scenario.get("decisions") or []:
        ledger.append(DecisionRecord(**raw))
    for raw in scenario.get("continuity_receipts") or []:
        ledger.append(ContinuityReceipt(**raw))
    for raw in scenario.get("founder_knowledge") or []:
        ledger.append(FounderKnowledgeSnapshot(**raw))
    for raw in scenario.get("succession_protocols") or []:
        ledger.append(SuccessionProtocol(**raw))
    for raw in scenario.get("reconstruction_plans") or []:
        ledger.append(ReconstructionPlan(**raw))
    return ledger
