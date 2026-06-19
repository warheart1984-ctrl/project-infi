"""CVR recompute bridge — lawful Nova turns into Proof → CVR pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
from typing import Any

from nova.identity import NovaIdentity
from src.continuity.ccs import (
    CCSStore,
    ContinuityTrace,
    Evaluation,
    Event,
    Evidence,
    Identity,
)
from src.continuity.proof import Proof, ProofStatus, create_proof, valid_proof
from src.continuity.reputation import (
    ContinuityValidatedReputation,
    compute_cvr,
)
from src.continuity.trace_v1 import ContinuityMetrics, ContinuityTraceV1, project_trace_v1
from src.continuity.ugr_trace import (
    evaluate_trace_ugr_invariants,
    trace_authority_chain_strength,
    trace_continuity_score,
    trace_evidence_integrity_score,
)
from src.continuity.cab import CABLedger, ingest_nova_continuity_governance

SYSTEM_LAW_ENGINE_ID = "id:system:aais-law-engine"
NOVA_LAW_SURFACE = {
    "aais_laws": ["aais.law.runtime.system", "aais.proof"],
    "csleis_laws": [],
    "other_laws": ["ugr.continuity"],
}


def _default_cvr_store_path() -> Path:
    override = os.environ.get("NOVA_CVR_STORE", "").strip()
    if override:
        return Path(override)
    repo_root = os.environ.get("LAWFUL_NOVA_REPO_ROOT", "").strip()
    if repo_root:
        return Path(repo_root) / "data" / "nova_cvr_store.jsonl"
    return Path.home() / ".nova" / "cvr_store.jsonl"


def _ensure_system_identity(store: CCSStore) -> None:
    if SYSTEM_LAW_ENGINE_ID in store.identities:
        return
    store.add_identity(
        Identity(
            id=SYSTEM_LAW_ENGINE_ID,
            kind="system",
            display_name="AAIS Law Engine",
            lineage={
                "parent_ids": [],
                "clan_or_family": None,
                "org_or_body": "AAIS Runtime",
                "jurisdiction": "global-technical",
            },
            authority_surface={
                "roles": ["technical_evaluator"],
                "scopes": ["rsl_compliance_review"],
                "constraints": ["advisory_only"],
            },
            cultural_surface={
                "community_id": None,
                "land_relation": None,
                "sovereignty_context": None,
            },
            technical_surface={
                "aais_id": "aais:system:law-engine",
                "provider_id": None,
                "runtime": "nova.lawful_llm",
            },
        )
    )


def _ensure_nova_identity(store: CCSStore, identity: NovaIdentity) -> str:
    nova_id = f"id:nova:{identity.instance_id}"
    if nova_id in store.identities:
        return nova_id
    store.add_identity(
        Identity(
            id=nova_id,
            kind="system",
            display_name=f"Nova Instance {identity.instance_id[:8]}",
            lineage={
                "parent_ids": [],
                "clan_or_family": None,
                "org_or_body": "Lawful Nova",
                "jurisdiction": "runtime",
            },
            authority_surface={
                "roles": ["lawful_actor"],
                "scopes": ["observe", "reason", "summarize"],
                "constraints": ["rsl_gated"],
            },
            cultural_surface={
                "community_id": None,
                "land_relation": None,
                "sovereignty_context": None,
            },
            technical_surface={
                "aais_id": f"aais:nova:{identity.instance_id}",
                "provider_id": None,
                "tier": identity.tier,
            },
        )
    )
    return nova_id


@dataclass
class TurnCVRResult:
    """Continuity governance snapshot for one lawful Nova turn."""

    proof: Proof | None
    cvr: ContinuityValidatedReputation
    trace_v1: ContinuityTraceV1 | None = None
    metrics: ContinuityMetrics | None = None

    def to_receipt_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"cvr": self.cvr.to_dict()}
        if self.proof is not None:
            payload["proof"] = self.proof.to_dict()
        if self.trace_v1 is not None:
            payload["continuity_trace"] = self.trace_v1.to_dict()
        if self.metrics is not None:
            payload["continuity_metrics"] = self.metrics.to_dict()
        return payload


@dataclass
class CVRRegistry:
    """Per-subject proof accumulation and CVR recomputation across lawful turns."""

    store: CCSStore = field(default_factory=CCSStore)
    proofs_by_subject: dict[str, list[Proof]] = field(default_factory=dict)
    store_path: Path | None = None

    def __post_init__(self) -> None:
        _ensure_system_identity(self.store)

    @classmethod
    def open(cls, path: Path | None = None) -> CVRRegistry:
        resolved = path or _default_cvr_store_path()
        registry = cls(store_path=resolved)
        if resolved.exists():
            registry._load(resolved)
        return registry

    def _load(self, path: Path) -> None:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            subject_id = str(record["subject_id"])
            proof = _proof_from_dict(record["proof"])
            self._ingest_turn_ccs(record.get("ccs") or {})
            if proof.proof_id not in {p.proof_id for p in self.proofs_by_subject.get(subject_id, [])}:
                self.proofs_by_subject.setdefault(subject_id, []).append(proof)

    def _persist(self, *, subject_id: str, proof: Proof, ccs_snapshot: dict[str, Any]) -> None:
        if self.store_path is None:
            return
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(
            {
                "subject_id": subject_id,
                "proof": proof.to_dict(),
                "ccs": ccs_snapshot,
            },
            sort_keys=True,
        )
        with self.store_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    def _ingest_turn_ccs(self, snapshot: dict[str, Any]) -> None:
        for identity in snapshot.get("identities", []):
            if identity["id"] not in self.store.identities:
                self.store.add_identity(_identity_from_snapshot(identity))
        for event in snapshot.get("events", []):
            if event["id"] not in self.store.events:
                self.store.add_event(_event_from_snapshot(event))
        for evaluation in snapshot.get("evaluations", []):
            if evaluation["id"] not in self.store.evaluations:
                self.store.add_evaluation(_evaluation_from_snapshot(evaluation))
        for evidence in snapshot.get("evidence", []):
            if evidence["id"] not in self.store.evidence:
                self.store.add_evidence(_evidence_from_snapshot(evidence))
        for trace in snapshot.get("traces", []):
            if trace["id"] not in self.store.traces:
                self.store.add_trace(_trace_from_snapshot(trace))

    def record_lawful_turn(
        self,
        *,
        identity: NovaIdentity,
        trace_id: str,
        tenant_id: str,
        capability: str,
        prompt_sha256: str,
        output_sha256: str,
        memory_facts_sha256: str,
        timestamp: str,
        nova_ugr_report: dict[str, dict[str, str]],
    ) -> TurnCVRResult:
        """Discovery → Evidence → Evaluation → CT → Proof → CVR for one lawful turn."""
        subject_id = f"nova:{identity.instance_id}"
        subject_ref = f"disc.nova.turn.{trace_id}"
        ct_id = f"ct.nova.{trace_id}"
        event_id = f"event.nova.{trace_id}"
        eval_id = f"eval.nova.{trace_id}"
        evidence_prompt_id = f"evidence.nova.prompt.{trace_id}"
        evidence_output_id = f"evidence.nova.output.{trace_id}"
        evidence_facts_id = f"evidence.nova.lsg.{trace_id}"
        proof_id = f"proof.nova.{trace_id}"

        subject_proofs = self.proofs_by_subject.setdefault(subject_id, [])
        existing = next((proof for proof in subject_proofs if proof.proof_id == proof_id), None)
        if existing is not None:
            trace = self.store.traces[f"ct.nova.{trace_id}"]
            cvr = compute_cvr(
                store=self.store,
                subject_id=subject_id,
                proofs=subject_proofs,
                scope={"domains": ["nova", tenant_id, capability]},
                cvr_id=f"cvr.{subject_id}",
            )
            report = evaluate_trace_ugr_invariants(self.store, trace)
            metrics = ContinuityMetrics(
                metrics_id=f"metrics.ct.nova.{trace_id}",
                continuity_score=trace_continuity_score(report),
                lineage_strength=0.9,
                authority_chain_strength=trace_authority_chain_strength(self.store, trace),
                evidence_integrity_score=trace_evidence_integrity_score(self.store, trace),
                drift_risk=0.1,
                preservation_risk=0.1,
            )
            trace_v1 = project_trace_v1(
                trace,
                subject_ref=f"disc.nova.turn.{trace_id}",
                metrics_ref=metrics.metrics_id,
                created_at=timestamp,
            )
            return TurnCVRResult(proof=existing, cvr=cvr, trace_v1=trace_v1, metrics=metrics)

        nova_identity_id = _ensure_nova_identity(self.store, identity)
        timeline_evidence = sorted([evidence_prompt_id, evidence_output_id, evidence_facts_id])

        event = Event(
            id=event_id,
            kind="nova.lawful_turn",
            actors=[nova_identity_id, SYSTEM_LAW_ENGINE_ID],
            targets=[subject_ref],
            time={"start": timestamp, "end": timestamp, "timezone": "UTC"},
            context={
                "tenant_id": tenant_id,
                "capability": capability,
                "trace_id": trace_id,
            },
            law_surface=dict(NOVA_LAW_SURFACE),
            description=f"Lawful Nova turn {trace_id}",
            linked_evaluations=[eval_id],
            linked_evidence=[evidence_prompt_id, evidence_output_id, evidence_facts_id],
        )
        evaluation = Evaluation(
            id=eval_id,
            kind="technical",
            evaluator_id=SYSTEM_LAW_ENGINE_ID,
            evaluated_event_ids=[event_id],
            law_surface={
                "aais_laws": ["aais.law.runtime.system"],
                "csleis_laws": [],
                "other_laws": ["ugr.continuity"],
            },
            finding="compliant" if _nova_ugr_passed(nova_ugr_report) else "pending",
            reasoning="RSL-satisfied lawful turn with continuity invariants evaluated.",
            uncertainty=5,
            risks=[],
            recommended_actions=[],
            linked_evidence_ids=[evidence_prompt_id, evidence_output_id, evidence_facts_id],
        )
        evidence_items = [
            Evidence(
                id=evidence_prompt_id,
                type="prompt_digest",
                source="nova.lawful_llm",
                integrity={"algorithm": "SHA-256", "hash": prompt_sha256},
                linked_identity_ids=[nova_identity_id],
                linked_event_ids=[event_id],
                law_surface={"aais_laws": ["aais.law.runtime.system"], "csleis_laws": [], "other_laws": []},
                payload_ref=f"sha256:{prompt_sha256}",
            ),
            Evidence(
                id=evidence_output_id,
                type="output_digest",
                source="nova.lawful_llm",
                integrity={"algorithm": "SHA-256", "hash": output_sha256},
                linked_identity_ids=[nova_identity_id],
                linked_event_ids=[event_id],
                law_surface={"aais_laws": ["aais.law.runtime.system"], "csleis_laws": [], "other_laws": []},
                payload_ref=f"sha256:{output_sha256}",
            ),
            Evidence(
                id=evidence_facts_id,
                type="lsg_grounding_digest",
                source="nova.lsg",
                integrity={"algorithm": "SHA-256", "hash": memory_facts_sha256},
                linked_identity_ids=[nova_identity_id],
                linked_event_ids=[event_id],
                law_surface={"aais_laws": ["aais.law.runtime.system"], "csleis_laws": [], "other_laws": []},
                payload_ref=f"sha256:{memory_facts_sha256}",
            ),
        ]

        trace = ContinuityTrace(
            id=ct_id,
            scope={
                "identity_ids": [nova_identity_id, SYSTEM_LAW_ENGINE_ID],
                "event_ids": [event_id],
                "time_window": {"start": timestamp, "end": timestamp},
            },
            timeline=[
                {
                    "event_id": event_id,
                    "evaluations": [eval_id],
                    "evidence": timeline_evidence,
                }
            ],
            law_surfaces=dict(NOVA_LAW_SURFACE),
            continuity_summary={
                "subject_ref": subject_ref,
                "tenant_id": tenant_id,
                "capability": capability,
                "nova_ugr_passed": str(_nova_ugr_passed(nova_ugr_report)),
            },
            reproducibility_metadata={
                "prompt_sha256": prompt_sha256,
                "output_sha256": output_sha256,
                "memory_facts_sha256": memory_facts_sha256,
                "trace_id": trace_id,
            },
        )

        self.store.add_event(event)
        self.store.add_evaluation(evaluation)
        for item in evidence_items:
            self.store.add_evidence(item)
        self.store.add_trace(trace)

        proof = create_proof(
            store=self.store,
            subject_ref=subject_ref,
            trace=trace,
            proof_id=proof_id,
        )
        is_valid, _detail = valid_proof(self.store, proof)
        if is_valid:
            proof.status = ProofStatus.PROVEN
        else:
            proof.status = ProofStatus.PENDING

        subject_proofs = self.proofs_by_subject.setdefault(subject_id, [])
        if proof not in subject_proofs:
            subject_proofs.append(proof)

        cvr = compute_cvr(
            store=self.store,
            subject_id=subject_id,
            proofs=subject_proofs,
            scope={"domains": ["nova", tenant_id, capability]},
            cvr_id=f"cvr.{subject_id}",
        )

        report = evaluate_trace_ugr_invariants(self.store, trace)
        metrics = ContinuityMetrics(
            metrics_id=f"metrics.{ct_id}",
            continuity_score=trace_continuity_score(report),
            lineage_strength=0.9,
            authority_chain_strength=trace_authority_chain_strength(self.store, trace),
            evidence_integrity_score=trace_evidence_integrity_score(self.store, trace),
            drift_risk=0.1,
            preservation_risk=0.1,
        )
        trace_v1 = project_trace_v1(
            trace,
            subject_ref=subject_ref,
            metrics_ref=metrics.metrics_id,
            created_at=timestamp,
        )

        ccs_snapshot = _ccs_snapshot(self.store, trace, event, evaluation, evidence_items, nova_identity_id)
        self._persist(subject_id=subject_id, proof=proof, ccs_snapshot=ccs_snapshot)

        return TurnCVRResult(proof=proof, cvr=cvr, trace_v1=trace_v1, metrics=metrics)


_registry: CVRRegistry | None = None


def get_cvr_registry() -> CVRRegistry:
    global _registry
    if _registry is None:
        _registry = CVRRegistry.open()
    return _registry


def reset_cvr_registry_for_tests() -> None:
    global _registry
    _registry = CVRRegistry()


def recompute_cvr_for_lawful_turn(
    *,
    identity: NovaIdentity,
    trace_id: str,
    tenant_id: str,
    capability: str,
    prompt_sha256: str,
    output_sha256: str,
    memory_facts_sha256: str,
    timestamp: str,
    nova_ugr_report: dict[str, dict[str, str]],
    registry: CVRRegistry | None = None,
) -> TurnCVRResult:
    active = registry or get_cvr_registry()
    result = active.record_lawful_turn(
        identity=identity,
        trace_id=trace_id,
        tenant_id=tenant_id,
        capability=capability,
        prompt_sha256=prompt_sha256,
        output_sha256=output_sha256,
        memory_facts_sha256=memory_facts_sha256,
        timestamp=timestamp,
        nova_ugr_report=nova_ugr_report,
    )
    _maybe_ingest_cab_receipt(
        result=result,
        identity=identity,
        trace_id=trace_id,
        tenant_id=tenant_id,
        capability=capability,
        timestamp=timestamp,
    )
    return result


def _cab_auto_ingest_enabled() -> bool:
    return os.environ.get("CAB_AUTO_INGEST", "").strip().lower() in {"1", "true", "yes"}


def _maybe_ingest_cab_receipt(
    *,
    result: TurnCVRResult,
    identity: NovaIdentity,
    trace_id: str,
    tenant_id: str,
    capability: str,
    timestamp: str,
) -> None:
    if not _cab_auto_ingest_enabled():
        return
    ledger = CABLedger.open()
    receipt_id = f"cab.receipt.{trace_id}"
    if ledger.get_latest(receipt_id) is not None:
        return
    ingest_nova_continuity_governance(
        trace_id=trace_id,
        identity_context={
            "instance_id": identity.instance_id,
            "tier": identity.tier,
            "operator_session_id": identity.operator_session_id,
            "tenant_id": tenant_id,
            "capability": capability,
        },
        continuity_governance=result.to_receipt_dict(),
        event_description=f"Lawful Nova turn {trace_id}",
        created_at=timestamp,
        decision_refs=["cab.decision.nova-lawful-turn"],
        govern_policy_refs=["aais.law.runtime.system", "ugr.continuity"],
        ledger=ledger,
    )


def _nova_ugr_passed(report: dict[str, dict[str, str]]) -> bool:
    return all(entry.get("status") == "pass" for entry in report.values())


def _proof_from_dict(data: dict[str, Any]) -> Proof:
    return Proof(
        proof_id=str(data["proof_id"]),
        subject_ref=str(data["subject_ref"]),
        continuity_trace_ref=str(data["continuity_trace_ref"]),
        law_surfaces=list(data.get("law_surfaces") or []),
        status=ProofStatus(str(data.get("status", "PENDING"))),
        created_at=str(data.get("created_at", "")),
        updated_at=str(data.get("updated_at", "")),
        continuity_invariants=dict(data.get("continuity_invariants") or {}),
        replay_fingerprint=str(data.get("replay_fingerprint") or ""),
    )


def _identity_from_snapshot(data: dict[str, Any]) -> Identity:
    return Identity(
        id=data["id"],
        kind=data["kind"],
        display_name=data["display_name"],
        lineage=data["lineage"],
        authority_surface=data["authority_surface"],
        cultural_surface=data["cultural_surface"],
        technical_surface=data["technical_surface"],
    )


def _event_from_snapshot(data: dict[str, Any]) -> Event:
    return Event(
        id=data["id"],
        kind=data["kind"],
        actors=list(data["actors"]),
        targets=list(data["targets"]),
        time=data["time"],
        context=data["context"],
        law_surface=data["law_surface"],
        description=data["description"],
        linked_evaluations=list(data.get("linked_evaluations") or []),
        linked_evidence=list(data.get("linked_evidence") or []),
    )


def _evaluation_from_snapshot(data: dict[str, Any]) -> Evaluation:
    return Evaluation(
        id=data["id"],
        kind=data["kind"],
        evaluator_id=data["evaluator_id"],
        evaluated_event_ids=list(data["evaluated_event_ids"]),
        law_surface=data["law_surface"],
        finding=data["finding"],
        reasoning=data["reasoning"],
        uncertainty=int(data["uncertainty"]),
        risks=list(data["risks"]),
        recommended_actions=list(data["recommended_actions"]),
        linked_evidence_ids=list(data["linked_evidence_ids"]),
    )


def _evidence_from_snapshot(data: dict[str, Any]) -> Evidence:
    return Evidence(
        id=data["id"],
        type=data["type"],
        source=data["source"],
        integrity=data["integrity"],
        linked_identity_ids=list(data["linked_identity_ids"]),
        linked_event_ids=list(data["linked_event_ids"]),
        law_surface=data["law_surface"],
        payload_ref=data["payload_ref"],
    )


def _trace_from_snapshot(data: dict[str, Any]) -> ContinuityTrace:
    return ContinuityTrace(
        id=data["id"],
        scope=data["scope"],
        timeline=data["timeline"],
        law_surfaces=data["law_surfaces"],
        continuity_summary=data["continuity_summary"],
        reproducibility_metadata=data["reproducibility_metadata"],
    )


def _ccs_snapshot(
    store: CCSStore,
    trace: ContinuityTrace,
    event: Event,
    evaluation: Evaluation,
    evidence_items: list[Evidence],
    nova_identity_id: str,
) -> dict[str, Any]:
    return {
        "identities": [
            {
                "id": store.identities[SYSTEM_LAW_ENGINE_ID].id,
                "kind": store.identities[SYSTEM_LAW_ENGINE_ID].kind,
                "display_name": store.identities[SYSTEM_LAW_ENGINE_ID].display_name,
                "lineage": store.identities[SYSTEM_LAW_ENGINE_ID].lineage,
                "authority_surface": store.identities[SYSTEM_LAW_ENGINE_ID].authority_surface,
                "cultural_surface": store.identities[SYSTEM_LAW_ENGINE_ID].cultural_surface,
                "technical_surface": store.identities[SYSTEM_LAW_ENGINE_ID].technical_surface,
            },
            {
                "id": store.identities[nova_identity_id].id,
                "kind": store.identities[nova_identity_id].kind,
                "display_name": store.identities[nova_identity_id].display_name,
                "lineage": store.identities[nova_identity_id].lineage,
                "authority_surface": store.identities[nova_identity_id].authority_surface,
                "cultural_surface": store.identities[nova_identity_id].cultural_surface,
                "technical_surface": store.identities[nova_identity_id].technical_surface,
            },
        ],
        "events": [_event_to_snapshot(event)],
        "evaluations": [_evaluation_to_snapshot(evaluation)],
        "evidence": [_evidence_to_snapshot(item) for item in evidence_items],
        "traces": [_trace_to_snapshot(trace)],
    }


def _event_to_snapshot(event: Event) -> dict[str, Any]:
    return {
        "id": event.id,
        "kind": event.kind,
        "actors": event.actors,
        "targets": event.targets,
        "time": event.time,
        "context": event.context,
        "law_surface": event.law_surface,
        "description": event.description,
        "linked_evaluations": event.linked_evaluations,
        "linked_evidence": event.linked_evidence,
    }


def _evaluation_to_snapshot(evaluation: Evaluation) -> dict[str, Any]:
    return {
        "id": evaluation.id,
        "kind": evaluation.kind,
        "evaluator_id": evaluation.evaluator_id,
        "evaluated_event_ids": evaluation.evaluated_event_ids,
        "law_surface": evaluation.law_surface,
        "finding": evaluation.finding,
        "reasoning": evaluation.reasoning,
        "uncertainty": evaluation.uncertainty,
        "risks": evaluation.risks,
        "recommended_actions": evaluation.recommended_actions,
        "linked_evidence_ids": evaluation.linked_evidence_ids,
    }


def _evidence_to_snapshot(evidence: Evidence) -> dict[str, Any]:
    return {
        "id": evidence.id,
        "type": evidence.type,
        "source": evidence.source,
        "integrity": evidence.integrity,
        "linked_identity_ids": evidence.linked_identity_ids,
        "linked_event_ids": evidence.linked_event_ids,
        "law_surface": evidence.law_surface,
        "payload_ref": evidence.payload_ref,
    }


def _trace_to_snapshot(trace: ContinuityTrace) -> dict[str, Any]:
    return {
        "id": trace.id,
        "scope": trace.scope,
        "timeline": trace.timeline,
        "law_surfaces": trace.law_surfaces,
        "continuity_summary": trace.continuity_summary,
        "reproducibility_metadata": trace.reproducibility_metadata,
    }
