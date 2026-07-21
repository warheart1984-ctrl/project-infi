from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from .conformance_runner import enqueue_conformance_jobs, run_conformance_runner
from .evidence_validator import enqueue_evidence_jobs, run_evidence_validator
from .ingress_gateway import handle_promotion_request
from .lineage_validator import enqueue_lineage_jobs, run_lineage_validator
from .models import PromotionDecision, PromotionProposal, PromotionRequest
from .queues import AUDIT_OUT, DECISIONS_OUT, PROMOTIONS_IN, Queue
from .replay_engine import ReplayStore, enqueue_replay_jobs, run_replay_engine


@dataclass
class GovernanceCore:
    constitution: Any
    queue: Queue
    replay_store: ReplayStore
    decisions: list[PromotionDecision] = field(default_factory=list)
    audit_log: list[dict[str, Any]] = field(default_factory=list)

    def ingest_audit_stream(self) -> list[dict[str, Any]]:
        events = self.queue.drain(AUDIT_OUT)
        for event in events:
            self.audit_log.append({"kind": type(event).__name__, "event": event})
        return list(self.audit_log)

    def emit_decision(self, decision: PromotionDecision) -> PromotionDecision:
        self.decisions.append(decision)
        self.queue.publish(DECISIONS_OUT, decision)
        return decision


@dataclass
class ConstitutionalEvolutionProtocol:
    global_constitution: Any
    queue: Queue = field(default_factory=Queue)
    replay_store: ReplayStore = field(default_factory=ReplayStore)
    pending_proposals: list[PromotionProposal] = field(default_factory=list)
    lineage_log: list[Any] = field(default_factory=list)
    decision_log: list[PromotionDecision] = field(default_factory=list)
    governance: GovernanceCore = field(init=False)

    def __post_init__(self) -> None:
        self.governance = GovernanceCore(self.global_constitution, self.queue, self.replay_store)

    def submit_promotion_request(self, agent: Any, payload: dict[str, Any]) -> PromotionRequest:
        evidence_sample = [
            {
                "source": getattr(item, "source", "agent"),
                "payload": dict(getattr(item, "payload", {})),
                "timestamp": getattr(item, "timestamp", 0),
            }
            for item in getattr(agent, "evidence_buffer", [])
        ]
        lineage_sample = [
            {
                "event_type": getattr(event, "event_type", "observation"),
                "payload": dict(getattr(event, "payload", {})),
                "timestamp": getattr(event, "timestamp", 0),
            }
            for event in getattr(agent, "lineage", [])
        ]
        request = handle_promotion_request(
            {
                "agent_id": getattr(agent, "id", "agent"),
                "snapshot": {
                    "drift": getattr(agent, "drift_value", 0.0),
                    "evidence_count": len(getattr(agent, "evidence_buffer", [])),
                    "lineage_depth": len(getattr(agent, "lineage", [])),
                    "evidence": evidence_sample,
                    "lineage": lineage_sample,
                    "drift_profile": {
                        "allowed_delta": getattr(getattr(agent, "drift_profile", None), "allowed_delta", 0.1),
                    },
                },
                "evidence_sample": evidence_sample[-10:],
                "lineage_sample": lineage_sample[-10:],
                "requested_change": dict(payload),
            },
            self.queue,
        )
        self.pending_proposals.append(PromotionProposal(agent=agent, payload=dict(payload), request=request))
        return request

    def process_proposals(self, env: Any) -> list[PromotionDecision]:
        decisions: list[PromotionDecision] = []
        for proposal in list(self.pending_proposals):
            enqueue_evidence_jobs(self.queue, [proposal.request])
            enqueue_lineage_jobs(self.queue, [proposal.request])
            enqueue_replay_jobs(self.queue, [proposal.request])
            enqueue_conformance_jobs(self.queue, [proposal.request])

            replay_id = f"replay-{proposal.request.request_id}"
            replay_frames = [
                dict(frame)
                for frame in getattr(env, "timeline", [])
                if str(frame.get("agent_id", "")) == proposal.request.agent_id
            ]
            temporal_api = getattr(env, "temporal_api", None)
            replay_target = getattr(temporal_api, "replay_store", self.replay_store)
            replay_target.save_replay(replay_id, replay_frames)

            evidence_results = run_evidence_validator(self.queue)
            lineage_results = run_lineage_validator(self.queue)
            replay_results = run_replay_engine(self.queue, replay_target)
            conformance_results = run_conformance_runner(self.queue, self.global_constitution)
            self.governance.ingest_audit_stream()

            passed = all(
                [
                    evidence_results and evidence_results[-1].passed,
                    lineage_results and lineage_results[-1].passed,
                    replay_results and replay_results[-1].passed,
                    conformance_results and conformance_results[-1].passed,
                ]
            )
            decision = self._promote(proposal, passed)
            self.decision_log.append(decision)
            decisions.append(decision)
            self.pending_proposals.remove(proposal)
        return decisions

    def _promote(self, proposal: PromotionProposal, approved: bool) -> PromotionDecision:
        capability_id = str(proposal.payload.get("capability_id", "capability-promotion"))
        change = dict(proposal.payload)
        change.setdefault("kind", proposal.payload.get("kind", "CapabilityPromotion"))
        change.setdefault("capability_id", capability_id)
        decision = PromotionDecision(
            decision_id=f"PROMO-{uuid4()}",
            request_id=proposal.request.request_id,
            agent_id=getattr(proposal.agent, "id", proposal.request.agent_id),
            capability_id=capability_id,
            status="APPROVED" if approved else "REJECTED",
            timestamp=int(getattr(proposal.agent, "step_count", 0)),
            evidence_ref=f"EVID-{proposal.request.request_id}",
            lineage_ref=f"LIN-{proposal.request.request_id}",
            replay_ref=f"REPLAY-{proposal.request.request_id}",
            conformance_ref=f"CONF-{proposal.request.request_id}",
        )
        if approved:
            apply_promotion = getattr(self.global_constitution, "apply_promotion", None)
            if callable(apply_promotion):
                apply_promotion(change)
            self.lineage_log.append(
                {
                    "event_type": "promotion",
                    "payload": change,
                    "timestamp": decision.timestamp,
                    "decision_id": decision.decision_id,
                }
            )
        self.governance.emit_decision(decision)
        return decision
