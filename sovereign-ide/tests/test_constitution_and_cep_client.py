from __future__ import annotations

import json
from urllib.request import Request, urlopen

from cep import CEPClient, Invariant
from runtime import SovereignIdeApiServer, SovereignRuntimeOrchestrator
from runtime.agent_loop import build_default_constitution, run_simulation


def test_constitution_apply_promotion_adds_invariant() -> None:
    constitution = build_default_constitution()
    before = constitution.list_ids()
    new_invariant = Invariant("NEW_INV_1", "New invariant", lambda snapshot: True)

    added = constitution.apply_promotion(
        {
            "kind": "AddInvariant",
            "invariant": new_invariant,
        }
    )

    assert added is True
    assert constitution.list_ids() == before + ["NEW_INV_1"]


def test_constitution_apply_promotion_records_capability() -> None:
    constitution = build_default_constitution()

    added = constitution.apply_promotion(
        {
            "kind": "CapabilityPromotion",
            "capability_id": "ROUTING_MODE_V2",
            "reason": "Promote routing mode",
        }
    )

    assert added is True
    assert constitution.capabilities[-1]["capability_id"] == "ROUTING_MODE_V2"


def test_cep_client_reads_decisions_and_audit_streams() -> None:
    env = run_simulation(steps=10, num_agents=1)
    client = CEPClient(env.cep)

    decisions = client.list_decisions()
    audit_events = client.list_audit_events()

    assert decisions
    assert decisions[-1].status == "APPROVED"
    assert audit_events


def test_router_evaluation_endpoint_returns_route_decision() -> None:
    orchestrator = SovereignRuntimeOrchestrator()
    ctx = orchestrator.boot()
    server = SovereignIdeApiServer(ctx, port=0)
    server.start()
    try:
        request = Request(
            f"{server.base_url}/api/router/evaluate",
            data=json.dumps(
                {
                    "requestId": "route-001",
                    "prompt": "Please replay this constitutional event trail.",
                    "routeClass": "replay",
                    "bias": "governance",
                    "evidenceIds": ["evidence-1", "evidence-2"],
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    finally:
        server.close()

    assert payload["requestId"] == "route-001"
    assert payload["selectedModel"] == "codex-reasoning-audit"
    assert payload["blocked"] is False
    assert payload["routeEvaluation"]["trust"] > 0
    assert payload["reason"]
