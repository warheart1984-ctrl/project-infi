"""End-to-end UGR -> AAIS -> DAR-Z -> AAES bridge trace."""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from types import SimpleNamespace

from nova.governance.cvr_recompute import CVRRegistry
from nova.identity import NovaIdentity
from src.aaes_os import AAESRequest, CognitiveOrchestrator, TraceStore, reconstruct_span
from src.aaes_os.modules.daniel import ModuleRegistry
from src.aais_composed_runtime import run_composed_turn
from src.continuity.ccs import continuity_trace_fingerprint, replay_trace_from_store
from src.continuity.proof import valid_proof
from src.darz_kernel_bridge import (
    DarzBridgeInput,
    DarzNodeAdvertisement,
    build_darz_bridge_receipt,
    darz_bridge_summary,
)


def _digest(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def _stage_names(trace: list[dict[str, object]]) -> list[str]:
    return [str(step.get("stage") or "?") for step in trace]


def _passing_ugr_report() -> dict[str, dict[str, str]]:
    return {
        "ugr.identity_continuity": {"status": "pass", "detail": "identity stable"},
        "ugr.authority_continuity": {"status": "pass", "detail": "authority stable"},
        "ugr.duality.bidirectional_coherence": {"status": "pass", "detail": "replay stable"},
        "ugr.duality.symmetric_constraints": {"status": "pass", "detail": "law surfaces symmetric"},
        "ugr.evidence_integrity": {"status": "pass", "detail": "hashes present"},
        "ugr.law_surface_binding": {"status": "pass", "detail": "law bound"},
        "ugr.continuity_unifier": {"status": "pass", "detail": "all pass"},
    }


def test_ugr_aais_darz_aaes_bridge_replays() -> None:
    timestamp = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    registry = CVRRegistry()
    identity = NovaIdentity(
        tier="nova",
        operator_session_id="ugr-aais-darz-aaes-test",
        instance_id="ugr-aais-darz-aaes-1001",
    )
    ugr_result = registry.record_lawful_turn(
        identity=identity,
        trace_id="ugr-aais-darz-aaes-test",
        tenant_id="local",
        capability="darz_bridge_trace",
        prompt_sha256=_digest("UGR starts the DAR-Z bridge."),
        output_sha256=_digest("AAIS carries the DAR-Z bridge to AAES."),
        memory_facts_sha256=_digest("UGR -> AAIS -> DAR-Z -> AAES"),
        timestamp=timestamp,
        nova_ugr_report=_passing_ugr_report(),
    )
    ugr_trace = registry.store.traces[ugr_result.proof.continuity_trace_ref]
    ugr_replay = replay_trace_from_store(registry.store, ugr_trace)
    trace_hash = continuity_trace_fingerprint(ugr_trace)
    replay_hash = continuity_trace_fingerprint(ugr_replay)
    proof_valid, proof_detail = valid_proof(registry.store, ugr_result.proof)

    assert proof_valid, proof_detail
    assert trace_hash == replay_hash

    surface_profile = {
        "identity": "tiny_nova",
        "label": "Tiny Nova",
        "response_mode": "tiny",
        "continuity_profile": {"scope": "tiny_nova", "tone": "companion"},
    }
    session = SimpleNamespace(metadata={"persona_mode": "tiny_nova", "response_mode": "tiny"})
    aais = run_composed_turn(
        session,
        "Carry UGR proof through DAR-Z into AAES.",
        request_payload={
            "cognitive_runtime": True,
            "ugr_trace_id": ugr_trace.id,
            "ugr_proof_id": ugr_result.proof.proof_id,
            "ugr_cvr_id": ugr_result.cvr.cvr_id,
            "ugr_replay_fingerprint": replay_hash,
        },
        companion_turn=True,
        surface_profile=surface_profile,
        emit_speaking=True,
    )
    tri_core = ((aais.nova_bridge or {}).get("tri_core") or {})

    darz = build_darz_bridge_receipt(
        DarzBridgeInput(
            ugr_trace_id=ugr_trace.id,
            ugr_proof_id=ugr_result.proof.proof_id,
            ugr_proof_status=ugr_result.proof.status.value,
            ugr_cvr_id=ugr_result.cvr.cvr_id,
            ugr_cvr_score=ugr_result.cvr.derived_score,
            ugr_trace_hash=trace_hash,
            ugr_replay_hash=replay_hash,
            aais_status=aais.status,
            aais_trace_stages=_stage_names(aais.trace),
            tri_core_authority=str(tri_core.get("routing_authority") or ""),
            active_runtimes=list(tri_core.get("active_cognitive_runtimes") or []),
            darz_node=DarzNodeAdvertisement(
                node_id="darz.node.001",
                status="ACTIVE",
                threads=3,
                events=3,
                reconstruction="PASS",
                proof_status="PROVEN",
                federation_ready=True,
                genesis_threads=("founder.genesis", "identity.genesis", "darz.genesis"),
                proof_hash="darz.node.001.proof.hash",
            ),
            wave_signature={"A": 0.59, "f": 0.4, "phi": 0.97, "C": 0.9, "R": 0.7},
            cross_kernel_coherence={
                "C_comp": 0.92,
                "C_identity": 0.91,
                "C_pair": 0.8372,
                "delta_phi": 0.05,
                "delta_R": 0.04,
                "continuity_ok": True,
                "violations": [],
            },
            timestamp=timestamp,
        )
    )
    darz_summary = darz_bridge_summary(darz)

    assert darz["accepted"] is True
    assert darz["events"][0]["payload"]["kind"] == "Evidence"
    assert darz["events"][1]["payload"]["kind"] == "Architecture"
    assert darz["events"][2]["payload"]["kind"] == "Governance"
    assert darz["events"][3]["payload"]["kind"] == "Decision"
    assert darz["events"][3]["lineage"] == [darz["events"][0]["id"], darz["events"][1]["id"], darz["events"][2]["id"]]
    assert darz["substrate_binding"]["node_id"] == "darz.node.001"
    assert darz["substrate_binding"]["role"] == "continuity_identity_substrate"
    assert darz["events"][3]["bridge_fields"]["wave_signature"]["C"] == 0.9
    assert darz["events"][3]["bridge_fields"]["continuity_proof"]["proof_status"] == "PROVEN"
    assert darz["ul_projection"]["bridge_id"] == "darz.kernel.bridge"
    assert darz["ul_substrate"]["substrate_id"] == "aais.ul_substrate"
    assert darz["ul_trace"]["count"] == 1
    assert darz["ul_trace"]["sections"] == ["protocol_trace"]
    assert darz["ul_trace"]["payloads"][0]["kind"] == "darz_kernel_bridge"
    assert darz_summary["darz_node_id"] == "darz.node.001"
    assert darz_summary["substrate_role"] == "continuity_identity_substrate"
    assert darz_summary["ul_substrate_id"] == "aais.ul_substrate"
    assert darz_summary["ul_trace_count"] == 1

    store = TraceStore()
    aaes = CognitiveOrchestrator(
        trace_store=store,
        module_registry=ModuleRegistry(include_daniel=True),
    )
    aaes_result = aaes.execute(
        AAESRequest(
            prompt=aais.speaking_reply or aais.user_message,
            actor_id="aais.composed_turn",
            session_id=str(tri_core.get("nova_cortex_session_id") or ""),
            trace_id=f"aaes-from-{ugr_trace.id}",
            metadata={
                "intent": "ugr_to_aais_to_darz_to_aaes_trace_replay",
                "module_id": "daniel",
                "operation": "execute",
                "args": {
                    "ugr_trace_id": ugr_trace.id,
                    "ugr_proof_id": ugr_result.proof.proof_id,
                    "aais_status": aais.status,
                    "darz": darz_summary,
                },
            },
        )
    )
    rebuilt = reconstruct_span(aaes.bus, aaes_result.span_id)
    stored = store.get(aaes_result.trace_id)

    assert aaes_result.status == "ok"
    assert aaes_result.blocked is False
    assert [event.event_type.value for event in rebuilt.events] == ["INTENT", "DECISION", "EXECUTION", "RESULT"]
    assert stored is not None
    assert stored["outcome"]["args"]["darz"]["bridge_hash"] == darz["bridge_hash"]
    assert stored["outcome"]["args"]["darz"]["darz_node_id"] == "darz.node.001"
    assert stored["outcome"]["args"]["darz"]["substrate_role"] == "continuity_identity_substrate"
    assert stored["outcome"]["args"]["darz"]["wave_signature"]["C"] == 0.9
    assert stored["outcome"]["args"]["darz"]["cross_kernel_coherence"]["continuity_ok"] is True
    assert stored["outcome"]["args"]["darz"]["ul_trace_count"] == 1
