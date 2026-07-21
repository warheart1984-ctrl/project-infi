from __future__ import annotations

from pathlib import Path

from runtime.agent_loop import run_simulation
from cep import PROMOTIONS_IN, Queue, handle_promotion_request


def test_cep_multi_agent_loop_promotes_after_enough_steps() -> None:
    env = run_simulation(steps=10, num_agents=1)

    assert env.time == 10
    assert len(env.agents) == 1
    assert env.agents[0].conformance_status is True
    assert len(env.agents[0].evidence_buffer) >= 10
    assert len(env.agents[0].lineage) >= 10
    assert len(env.audit_stream) == 10
    assert len(env.cep.decision_log) >= 1
    assert env.cep.decision_log[-1].status == "APPROVED"
    assert env.cep.lineage_log


def test_cep_ingress_gateway_publishes_requests() -> None:
    queue = Queue()
    request = handle_promotion_request(
        {
            "agent_id": "agent-123",
            "snapshot": {"drift": 0.03, "evidence_count": 27, "lineage_depth": 42},
            "evidence_sample": [{"source": "sensor-A", "payload": {"x": 1.2}, "timestamp": 1721000001}],
            "lineage_sample": [{"event_type": "observation", "timestamp": 1720999990}],
            "requested_change": {
                "kind": "CapabilityPromotion",
                "capability_id": "ROUTING_MODE_V2",
                "reason": "Improved stability under high drift conditions.",
            },
        },
        queue,
    )

    assert request.agent_id == "agent-123"
    assert queue.count(PROMOTIONS_IN) == 1

