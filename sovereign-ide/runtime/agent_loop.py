from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from cep import ConstitutionalEvolutionProtocol, DriftEnvelope, EvidenceItem, Invariant, InvariantSet, LineageEvent, AuditPacket, MIN_EVIDENCE_ITEMS, MIN_LINEAGE_DEPTH
from .constitution import Constitution


def _default_drift_invariant(agent_state: dict[str, Any]) -> bool:
    drift_profile = agent_state.get("drift_profile")
    drift = float(agent_state.get("drift", 0.0) or 0.0)
    if isinstance(drift_profile, dict):
        allowed = float(drift_profile.get("allowed_delta", 0.1))
    else:
        allowed = float(getattr(drift_profile, "allowed_delta", 0.1))
    return abs(drift) <= allowed


def _default_evidence_invariant(agent_state: dict[str, Any]) -> bool:
    evidence = agent_state.get("evidence", [])
    return len(evidence) >= MIN_EVIDENCE_ITEMS


def _default_lineage_invariant(agent_state: dict[str, Any]) -> bool:
    lineage = agent_state.get("lineage", [])
    if not lineage:
        return False
    timestamps = [
        int(event.get("timestamp", 0) or 0) if isinstance(event, dict) else int(getattr(event, "timestamp", 0) or 0)
        for event in lineage
    ]
    return all(left <= right for left, right in zip(timestamps, timestamps[1:]))


def build_default_constitution() -> Constitution:
    return Constitution(
        [
            Invariant("DRIFT_BOUND_V1", "Agent drift must remain within the allowed envelope.", _default_drift_invariant),
            Invariant("EVIDENCE_SUFFICIENCY_V1", "Agent must retain minimum evidence before promotion.", _default_evidence_invariant),
            Invariant("LINEAGE_CONTINUITY_V1", "Lineage must remain ordered without gaps.", _default_lineage_invariant),
        ]
    )


@dataclass
class ConstitutionalAgent:
    agent_id: str
    constitution: Constitution
    drift_profile: DriftEnvelope
    lineage: list[LineageEvent] = field(default_factory=list)
    evidence_buffer: list[EvidenceItem] = field(default_factory=list)
    conformance_status: bool = True
    audit_log: list[AuditPacket] = field(default_factory=list)
    drift_value: float = 0.0
    state: dict[str, Any] = field(default_factory=dict)
    step_count: int = 0

    @property
    def id(self) -> str:
        return self.agent_id

    def observe(self, env: "SovereignEnvironment") -> dict[str, Any]:
        observation = env.observe(self.id)
        self.state = dict(observation)
        return observation

    def update_evidence(self, observation: dict[str, Any]) -> EvidenceItem:
        item = EvidenceItem(
            source=str(observation.get("source", f"env:{self.id}")),
            payload=dict(observation),
            timestamp=int(observation.get("timestamp", 0)),
        )
        self.evidence_buffer.append(item)
        return item

    def update_lineage(self, event: LineageEvent) -> LineageEvent:
        self.lineage.append(event)
        return event

    def compute_drift(self) -> float:
        total = len(self.evidence_buffer)
        if total <= 0:
            self.drift_value = 1.0
        else:
            self.drift_value = round(1.0 / (total + 1), 6)
        return self.drift_value

    def check_conformance(self, global_constitution: Constitution) -> bool:
        agent_state = {
            "agent_id": self.id,
            "evidence": list(self.evidence_buffer),
            "lineage": list(self.lineage),
            "drift": self.drift_value,
            "drift_profile": self.drift_profile,
            "state": dict(self.state),
        }
        self.conformance_status = global_constitution.validate(agent_state)
        return self.conformance_status

    def maybe_request_promotion(self, cep: ConstitutionalEvolutionProtocol) -> bool:
        if not self.conformance_status:
            return False
        if len(self.evidence_buffer) < MIN_EVIDENCE_ITEMS:
            return False
        if len(self.lineage) < MIN_LINEAGE_DEPTH:
            return False
        payload = {
            "kind": "CapabilityPromotion",
            "capability_id": "ROUTING_MODE_V2",
            "reason": "Improved stability under high drift conditions.",
            "agent_id": self.id,
            "summary_evidence": [item.payload for item in self.evidence_buffer[-MIN_EVIDENCE_ITEMS:]],
            "summary_lineage": [
                {
                    "event_type": event.event_type,
                    "payload": dict(event.payload),
                    "timestamp": event.timestamp,
                }
                for event in self.lineage[-MIN_LINEAGE_DEPTH:]
            ],
        }
        cep.submit_promotion_request(self, payload)
        return True

    def emit_audit_packet(self) -> AuditPacket:
        packet = AuditPacket(
            agent_id=self.id,
            snapshot={
                "evidence_count": len(self.evidence_buffer),
                "lineage_depth": len(self.lineage),
                "drift": self.drift_value,
                "conformance_status": self.conformance_status,
            },
            conformance_status=self.conformance_status,
            timestamp=self.step_count,
        )
        self.audit_log.append(packet)
        return packet


@dataclass
class SovereignEnvironment:
    agents: list[ConstitutionalAgent]
    global_constitution: Constitution
    cep: ConstitutionalEvolutionProtocol
    time: int = 0
    audit_stream: list[AuditPacket] = field(default_factory=list)
    timeline: list[dict[str, Any]] = field(default_factory=list)
    replay_store: Any = None

    def __post_init__(self) -> None:
        if self.replay_store is None:
            self.replay_store = self.cep.replay_store

    def observe(self, agent_id: str) -> dict[str, Any]:
        return {
            "agent_id": agent_id,
            "source": f"env:{agent_id}",
            "timestamp": self.time,
            "time": self.time,
            "peers": len(self.agents),
        }

    def submit_promotion_request(self, agent: ConstitutionalAgent) -> bool:
        return agent.maybe_request_promotion(self.cep)

    def broadcast_audit(self, packet: AuditPacket) -> None:
        self.audit_stream.append(packet)

    def record_replay_frame(self, agent: ConstitutionalAgent) -> None:
        replay_id = f"replay-{agent.id}"
        self.replay_store.append(
            replay_id,
            {
                "time": self.time,
                "agent_id": agent.id,
                "evidence_count": len(agent.evidence_buffer),
                "lineage_depth": len(agent.lineage),
                "drift": agent.drift_value,
                "conformance_status": agent.conformance_status,
            },
        )

    def step(self) -> list[Any]:
        emitted: list[Any] = []
        for agent in self.agents:
            agent.step_count = self.time
            observation = agent.observe(self)
            agent.update_evidence(observation)
            lineage_event = LineageEvent(
                event_type="observation",
                payload=dict(observation),
                timestamp=self.time,
            )
            agent.update_lineage(lineage_event)
            agent.compute_drift()
            agent.check_conformance(self.global_constitution)
            self.submit_promotion_request(agent)
            audit_packet = agent.emit_audit_packet()
            self.broadcast_audit(audit_packet)
            self.record_replay_frame(agent)
            self.timeline.append(
                {
                    "time": self.time,
                    "agent_id": agent.id,
                    "drift": agent.drift_value,
                    "conformance_status": agent.conformance_status,
                    "evidence_count": len(agent.evidence_buffer),
                    "lineage_depth": len(agent.lineage),
                }
            )
            emitted.append(audit_packet)
        self.cep.process_proposals(self)
        self.time += 1
        return emitted


def build_sovereign_environment(agent_count: int = 3) -> SovereignEnvironment:
    constitution = build_default_constitution()
    cep = ConstitutionalEvolutionProtocol(constitution)
    agents = [
        ConstitutionalAgent(
            agent_id=f"agent-{index + 1}",
            constitution=constitution,
            drift_profile=DriftEnvelope(allowed_delta=0.1),
        )
        for index in range(agent_count)
    ]
    return SovereignEnvironment(agents=agents, global_constitution=constitution, cep=cep)


def run_simulation(steps: int, num_agents: int, global_constitution: Constitution | None = None) -> SovereignEnvironment:
    constitution = global_constitution or build_default_constitution()
    cep = ConstitutionalEvolutionProtocol(constitution)
    agents = [
        ConstitutionalAgent(
            agent_id=f"agent-{index + 1}",
            constitution=constitution,
            drift_profile=DriftEnvelope(allowed_delta=0.1),
        )
        for index in range(num_agents)
    ]
    env = SovereignEnvironment(agents=agents, global_constitution=constitution, cep=cep)
    for _ in range(steps):
        env.step()
    return env
