"""CEC-1 AAES continuity execution contract tests."""

from __future__ import annotations

from src.aaes_os import AAESRequest, CognitiveOrchestrator, TraceStore
from src.aaes_os.modules.daniel import ModuleRegistry


def _darz_args(*, continuity_ok: bool) -> dict[str, object]:
    return {
        "darz": {
            "darz_node_id": "darz.node.001",
            "substrate_role": "continuity_identity_substrate",
            "bridge_hash": "bridge.hash.1001",
            "wave_signature": {"A": 0.59, "f": 0.4, "phi": 0.97, "C": 0.9, "R": 0.7},
            "continuity_proof": {"proof_status": "PROVEN", "replay_stable": True},
            "cross_kernel_coherence": {
                "C_comp": 0.92 if continuity_ok else 0.70,
                "C_identity": 0.91 if continuity_ok else 0.66,
                "C_pair": 0.8372 if continuity_ok else 0.46,
                "delta_phi": 0.05 if continuity_ok else 0.30,
                "delta_R": 0.04 if continuity_ok else 0.25,
                "continuity_ok": continuity_ok,
                "violations": [] if continuity_ok else ["ckce.pair_coherence_below_tau"],
            },
        }
    }


def test_cec1_blocks_continuity_typed_execution_when_ckce_fails() -> None:
    store = TraceStore()
    orchestrator = CognitiveOrchestrator(
        trace_store=store,
        module_registry=ModuleRegistry(include_daniel=True),
    )

    result = orchestrator.execute(
        AAESRequest(
            prompt="execute continuity-typed handoff",
            actor_id="aais.composed_turn",
            trace_id="aaes-cec-block",
            metadata={
                "intent": "continuity_typed_execution",
                "module_id": "daniel",
                "operation": "execute",
                "args": _darz_args(continuity_ok=False),
            },
        )
    )

    assert result.blocked is True
    assert result.status == "blocked"
    assert result.block_code == "AAES_CONTINUITY_EXECUTION_BLOCKED"
    assert "ckce.pair_coherence_below_tau" in result.outcome["continuity_execution"]["violations"]
    assert store.get("aaes-cec-block")["blocked"] is True


def test_cec1_propagates_substrate_role_into_downstream_aaes_events() -> None:
    store = TraceStore()
    orchestrator = CognitiveOrchestrator(
        trace_store=store,
        module_registry=ModuleRegistry(include_daniel=True),
    )

    result = orchestrator.execute(
        AAESRequest(
            prompt="execute continuity-typed handoff",
            actor_id="aais.composed_turn",
            trace_id="aaes-cec-allow",
            metadata={
                "intent": "continuity_typed_execution",
                "module_id": "daniel",
                "operation": "execute",
                "args": _darz_args(continuity_ok=True),
            },
        )
    )
    record = store.get("aaes-cec-allow")

    assert result.blocked is False
    assert record is not None
    assert record["outcome"]["args"]["darz"]["darz_node_id"] == "darz.node.001"
    assert record["outcome"]["args"]["darz"]["substrate_role"] == "continuity_identity_substrate"
    for event in record["events"]:
        continuity = event["payload"]["continuity_execution"]
        assert continuity["darz_node_id"] == "darz.node.001"
        assert continuity["substrate_role"] == "continuity_identity_substrate"
        assert continuity["bridge_hash"] == "bridge.hash.1001"
