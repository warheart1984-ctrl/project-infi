"""DAR-Z kernel bridge for UGR -> AAIS -> AAES continuity handoff.

The Rust darz-kernel crate owns the typed continuity kernel. This Python bridge
emits the same tagged payload shape so live AAIS/AAES runs can carry a
deterministic DAR-Z handoff receipt before the Rust runtime is available in the
local environment.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
from typing import Any
from uuid import UUID, uuid5


DARZ_BRIDGE_VERSION = "darz.kernel.bridge.v0.1"
DARZ_NAMESPACE = UUID("10011001-0000-4000-8000-000000000100")

DARZ_INVARIANTS = (
    "ugr.identity_continuity",
    "ugr.authority_continuity",
    "ugr.duality.bidirectional_coherence",
    "ugr.duality.symmetric_constraints",
    "ugr.evidence_integrity",
    "ugr.law_surface_binding",
    "ugr.continuity_unifier",
)


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _stable_uuid(*parts: Any) -> str:
    token = "::".join(str(part) for part in parts)
    return str(uuid5(DARZ_NAMESPACE, token))


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _sha256_json(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _tagged_payload(kind: str, data: dict[str, Any]) -> dict[str, Any]:
    return {"kind": kind, "data": data}


def _darz_ul_projection(receipt: dict[str, Any]) -> dict[str, Any]:
    events = list(receipt.get("events") or [])
    substrate_binding = dict(receipt.get("substrate_binding") or {})
    darz_node = dict(receipt.get("darz_node") or {})
    return {
        "bridge_id": "darz.kernel.bridge",
        "bridge_version": receipt.get("bridge_version"),
        "bridge_hash": receipt.get("bridge_hash"),
        "accepted": bool(receipt.get("accepted")),
        "thread_id": (receipt.get("thread") or {}).get("id"),
        "darz_node_id": darz_node.get("node_id"),
        "substrate_role": substrate_binding.get("role"),
        "event_count": len(events),
        "event_types": [event.get("event_type") for event in events],
        "invariant_count": len(list((receipt.get("reasoning_request") or {}).get("invariants") or [])),
        "violations": list(receipt.get("violations") or []),
    }


def attach_darz_ul_substrate(receipt: dict[str, Any]) -> dict[str, Any]:
    """Attach the AAIS universal-language substrate to a DAR-Z bridge receipt."""

    from src.aais_ul.runtime import aais_ul_substrate

    projection = _darz_ul_projection(receipt)
    envelope = aais_ul_substrate.build_envelope(bridge_results=[projection])
    wrapped = dict(receipt)
    wrapped["ul_projection"] = projection
    wrapped["ul_substrate"] = envelope
    wrapped["ul_trace"] = envelope["ul_trace"]
    return wrapped


def _attach_event_bridge_fields(receipt: dict[str, Any]) -> dict[str, Any]:
    substrate_binding = dict(receipt.get("substrate_binding") or {})
    darz_node = dict(receipt.get("darz_node") or {})
    base_fields = {
        "darz_node_id": darz_node.get("node_id"),
        "substrate_role": substrate_binding.get("role"),
        "bridge_hash": receipt.get("bridge_hash"),
        "wave_signature": dict(receipt.get("wave_signature") or {}),
        "continuity_proof": dict(receipt.get("continuity_proof") or {}),
    }
    events: list[dict[str, Any]] = []
    for event in receipt.get("events") or []:
        copied = dict(event)
        copied["bridge_fields"] = {
            **base_fields,
            "lineage_pointers": list(copied.get("lineage") or []),
        }
        events.append(copied)
    wrapped = dict(receipt)
    wrapped["events"] = events
    return wrapped


@dataclass(frozen=True)
class DarzNodeAdvertisement:
    node_id: str
    status: str
    threads: int
    events: int
    reconstruction: str
    proof_status: str
    federation_ready: bool
    genesis_threads: tuple[str, ...]
    proof_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "status": self.status,
            "threads": self.threads,
            "events": self.events,
            "reconstruction": self.reconstruction,
            "proof_status": self.proof_status,
            "federation_ready": self.federation_ready,
            "genesis_threads": list(self.genesis_threads),
            "proof_hash": self.proof_hash,
        }

    def violations(self) -> list[str]:
        violations: list[str] = []
        required_genesis = {"founder.genesis", "identity.genesis", "darz.genesis"}
        if self.status != "ACTIVE":
            violations.append("darz.node.inactive")
        if self.reconstruction != "PASS":
            violations.append("darz.node.reconstruction_failed")
        if self.proof_status != "PROVEN":
            violations.append("darz.node.proof_not_proven")
        if not self.federation_ready:
            violations.append("darz.node.federation_not_ready")
        if set(self.genesis_threads) < required_genesis:
            violations.append("darz.node.genesis_threads_incomplete")
        if self.threads < len(required_genesis):
            violations.append("darz.node.thread_count_below_genesis")
        if self.events < len(required_genesis):
            violations.append("darz.node.event_count_below_genesis")
        if not self.proof_hash:
            violations.append("darz.node.proof_hash_missing")
        return violations


@dataclass(frozen=True)
class DarzBridgeInput:
    ugr_trace_id: str
    ugr_proof_id: str
    ugr_proof_status: str
    ugr_cvr_id: str
    ugr_cvr_score: float
    ugr_trace_hash: str
    ugr_replay_hash: str
    aais_status: str
    aais_trace_stages: list[str]
    tri_core_authority: str
    active_runtimes: list[str]
    darz_node: DarzNodeAdvertisement | None = None
    wave_signature: dict[str, Any] | None = None
    cross_kernel_coherence: dict[str, Any] | None = None
    timestamp: str = ""
    thread_label: str = "UGR -> AAIS -> DAR-Z -> AAES"


def build_darz_bridge_receipt(input_data: DarzBridgeInput) -> dict[str, Any]:
    """Build a Rust-compatible DAR-Z continuity bridge receipt.

    Event payloads intentionally match darz-kernel/src/payload.rs serde tagging:
    {"kind": "Evidence"|"Governance"|"Decision", "data": {...}}.
    """

    timestamp = input_data.timestamp or _now()
    thread_id = _stable_uuid("thread", input_data.ugr_trace_id)
    evidence_id = _stable_uuid("event", "evidence", input_data.ugr_trace_id)
    architecture_id = (
        _stable_uuid("event", "architecture", input_data.ugr_trace_id)
        if input_data.darz_node
        else None
    )
    governance_id = _stable_uuid("event", "governance", input_data.ugr_trace_id)
    decision_id = _stable_uuid("event", "decision", input_data.ugr_trace_id)

    replay_stable = input_data.ugr_trace_hash == input_data.ugr_replay_hash
    proof_proven = input_data.ugr_proof_status == "PROVEN"
    tri_core_bound = input_data.tri_core_authority == "tri_core"
    violations: list[str] = []
    if not proof_proven:
        violations.append("darz.bridge.proof_not_proven")
    if not replay_stable:
        violations.append("darz.bridge.replay_unstable")
    if not tri_core_bound:
        violations.append("darz.bridge.tri_core_authority_missing")
    if input_data.darz_node:
        violations.extend(input_data.darz_node.violations())
    wave_signature = dict(input_data.wave_signature or {})
    cross_kernel_coherence = dict(input_data.cross_kernel_coherence or {})
    if cross_kernel_coherence and not bool(cross_kernel_coherence.get("continuity_ok", False)):
        violations.append("darz.bridge.cross_kernel_coherence_failed")
    continuity_proof = {
        "proof_id": input_data.ugr_proof_id,
        "proof_status": input_data.ugr_proof_status,
        "cvr_id": input_data.ugr_cvr_id,
        "cvr_score": input_data.ugr_cvr_score,
        "trace_hash": input_data.ugr_trace_hash,
        "replay_hash": input_data.ugr_replay_hash,
        "replay_stable": replay_stable,
    }

    thread = {
        "id": thread_id,
        "parent": None,
        "label": input_data.thread_label,
        "created_at": timestamp,
    }
    evidence_event = {
        "id": evidence_id,
        "thread_id": thread_id,
        "event_type": "Evidence",
        "payload": _tagged_payload(
            "Evidence",
            {
                "source": "ugr.continuity",
                "summary": "UGR proof/CVR is carried into AAIS for AAES execution.",
                "details": _canonical_json(
                    {
                        "ugr_trace_id": input_data.ugr_trace_id,
                        "ugr_proof_id": input_data.ugr_proof_id,
                        "ugr_proof_status": input_data.ugr_proof_status,
                        "ugr_cvr_id": input_data.ugr_cvr_id,
                        "ugr_cvr_score": input_data.ugr_cvr_score,
                        "ugr_trace_hash": input_data.ugr_trace_hash,
                        "ugr_replay_hash": input_data.ugr_replay_hash,
                        "ugr_replay_stable": replay_stable,
                        "darz_node_id": input_data.darz_node.node_id if input_data.darz_node else None,
                    }
                ),
            },
        ),
        "timestamp": timestamp,
        "lineage": [],
    }

    architecture_event = None
    if input_data.darz_node and architecture_id:
        architecture_event = {
            "id": architecture_id,
            "thread_id": thread_id,
            "event_type": "Architecture",
            "payload": _tagged_payload(
                "Architecture",
                {
                    "name": "DAR-Z Continuity and Identity Substrate",
                    "version": "darz.node.v0.1",
                    "definition": (
                        "DAR-Z node acts as the typed continuity and identity substrate "
                        "for the UGR -> AAIS -> DAR-Z Continuity Kernel -> AAES bridge."
                    ),
                    "invariants": list(DARZ_INVARIANTS),
                    "components": list(input_data.darz_node.genesis_threads),
                    "evidence_refs": [evidence_id],
                },
            ),
            "timestamp": timestamp,
            "lineage": [evidence_id],
        }

    governance_lineage = [evidence_id]
    if architecture_id:
        governance_lineage.append(architecture_id)
    governance_event = {
        "id": governance_id,
        "thread_id": thread_id,
        "event_type": "Governance",
        "payload": _tagged_payload(
            "Governance",
            {
                "name": "DAR-Z AAIS-to-AAES bridge law surface",
                "authority_scope": "tri_core",
                "invariants": list(DARZ_INVARIANTS),
                "constraints": [
                    "UGR proof must be PROVEN",
                    "UGR trace replay hash must match original trace hash",
                    "AAIS Tri-Core must retain routing authority",
                    "DAR-Z node advertisement must be ACTIVE, PROVEN, reconstructable, and federation-ready",
                    "AAES must record INTENT -> DECISION -> EXECUTION -> RESULT",
                ],
                "evidence_refs": [evidence_id],
            },
        ),
        "timestamp": timestamp,
        "lineage": governance_lineage,
    }

    decision_lineage = [evidence_id, governance_id]
    if architecture_id:
        decision_lineage.insert(1, architecture_id)
    decision_event = {
        "id": decision_id,
        "thread_id": thread_id,
        "event_type": "Decision",
        "payload": _tagged_payload(
            "Decision",
            {
                "title": "Authorize AAES governed execution from AAIS",
                "rationale": (
                    "DAR-Z bridge admits the AAES execution because UGR proof is proven, "
                    "continuity replay is stable, AAIS Tri-Core authority is preserved, "
                    "and the DAR-Z node substrate is verified."
                ),
                "chosen_architecture": architecture_id,
                "alternatives": [],
                "evidence_refs": [evidence_id],
                "governance_refs": [governance_id],
                "outcome_summary": "AAES execution may proceed under DAR-Z continuity handoff.",
            },
        ),
        "timestamp": timestamp,
        "lineage": decision_lineage,
    }

    events = [evidence_event]
    if architecture_event:
        events.append(architecture_event)
    events.extend([governance_event, decision_event])
    reasoning_request = {
        "thread_id": thread_id,
        "problem_statement": "Should AAES execute the AAIS handoff backed by UGR proof?",
        "scope": "ugr-aais-aaes-continuity",
        "time_horizon": "current-turn",
        "invariants": list(DARZ_INVARIANTS),
        "constraints": list(governance_event["payload"]["data"]["constraints"]),
        "evidence_requirements": [input_data.ugr_proof_id, input_data.ugr_trace_hash],
        "context_event_ids": [event["id"] for event in events],
    }
    used_events = [evidence_id, governance_id]
    if architecture_id:
        used_events.insert(1, architecture_id)
    reasoning_response = {
        "proposals": [decision_id] if not violations else [],
        "trace_steps": [
            {
                "description": (
                    "Validated UGR proof/CVR replay stability, AAIS Tri-Core authority, "
                    "and DAR-Z node substrate readiness."
                ),
                "used_events": used_events,
                "produced_events": [decision_id] if not violations else [],
                "invariants_checked": list(DARZ_INVARIANTS),
                "violations": violations,
            }
        ],
        "evidence_refs": [evidence_id],
        "invariants_checked": list(DARZ_INVARIANTS),
        "violations": violations,
    }

    receipt = {
        "bridge_version": DARZ_BRIDGE_VERSION,
        "thread": thread,
        "events": events,
        "reasoning_request": reasoning_request,
        "reasoning_response": reasoning_response,
        "wave_signature": wave_signature,
        "continuity_proof": continuity_proof,
        "cross_kernel_coherence": cross_kernel_coherence,
        "accepted": not violations,
        "violations": violations,
    }
    if input_data.darz_node:
        receipt["darz_node"] = input_data.darz_node.to_dict()
        receipt["substrate_binding"] = {
            "node_id": input_data.darz_node.node_id,
            "role": "continuity_identity_substrate",
            "architecture_event_id": architecture_id,
            "proof_hash": input_data.darz_node.proof_hash,
            "genesis_threads": list(input_data.darz_node.genesis_threads),
        }
    with_hash = {**receipt, "bridge_hash": _sha256_json(receipt)}
    return attach_darz_ul_substrate(_attach_event_bridge_fields(with_hash))


def darz_bridge_summary(receipt: dict[str, Any]) -> dict[str, Any]:
    """Return a compact summary for AAES action args and operator traces."""

    events = list(receipt.get("events") or [])
    substrate_binding = dict(receipt.get("substrate_binding") or {})
    darz_node = dict(receipt.get("darz_node") or {})
    return {
        "bridge_version": receipt.get("bridge_version"),
        "bridge_hash": receipt.get("bridge_hash"),
        "accepted": bool(receipt.get("accepted")),
        "thread_id": (receipt.get("thread") or {}).get("id"),
        "darz_node_id": darz_node.get("node_id"),
        "substrate_role": substrate_binding.get("role"),
        "wave_signature": dict(receipt.get("wave_signature") or {}),
        "continuity_proof": dict(receipt.get("continuity_proof") or {}),
        "cross_kernel_coherence": dict(receipt.get("cross_kernel_coherence") or {}),
        "event_ids": [event.get("id") for event in events],
        "event_types": [event.get("event_type") for event in events],
        "violations": list(receipt.get("violations") or []),
        "ul_substrate_id": (receipt.get("ul_substrate") or {}).get("substrate_id"),
        "ul_trace_count": (receipt.get("ul_trace") or {}).get("count", 0),
        "ul_sections": list((receipt.get("ul_trace") or {}).get("sections") or []),
    }
