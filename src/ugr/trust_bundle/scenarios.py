"""UGR trust bundle proof scenarios."""

# Mythic: Scenarios
# Engineering: ScenariosEngine
from __future__ import annotations

import json
import os
import shutil
import socket
import sys
import tempfile
import threading
from pathlib import Path
from typing import Any

from werkzeug.serving import make_server

from src.cognitive_bridge import CognitiveBridgeService
from src.immune_system import ImmuneSystemController
from src.jarvis_detachment_guard import JarvisDetachmentGuard
from src.jarvis_provider_registry import ProviderConfig
from src.module_governance import module_governance
from src.phase_gate import reset_registry
from src.provider_registry import ProviderRegistry
from src.ugr.cloud.clients import UGRMeshClients
from src.ugr.cloud.distributed_runtime import DistributedUnifiedGovernedRuntime
from src.ugr.cloud.mesh_config import load_mesh_config
from src.ugr.cloud.services import (
    create_convergence_app,
    create_lane_worker_app,
    create_ledger_app,
    create_orchestrator_app,
    create_policy_app,
)
from src.ugr.lane_manager import LaneSpec
from src.ugr.llm_lane import run_governed_llm_lane
from src.ugr.pattern_ledger import PatternLedgerStore
from src.ugr.trust_bundle.evidence import ScenarioEvidence, sha256_file, sha256_text, stable_json
from src.ugr.unified_runtime import UnifiedGovernedRuntime


REPO_ROOT = Path(__file__).resolve().parents[3]


class _MockProvider:
    async def invoke(self, messages, **kwargs):
        from src.jarvis_protocol import ProviderResponse

        del messages, kwargs
        return ProviderResponse(
            content="Trust bundle governed inference smoke.",
            provider="mock",
            model="mock-model",
            input_tokens=4,
            output_tokens=8,
        )


class _ServiceThread:
    def __init__(self, app, port: int):
        self.server = make_server("127.0.0.1", port, app)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        self.server.shutdown()


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def belief_signature(result: dict[str, Any]) -> list[tuple[Any, ...]]:
    return sorted(
        (
            item.get("subject"),
            item.get("predicate"),
            item.get("object"),
            item.get("status"),
        )
        for item in (result.get("convergence") or {}).get("final_beliefs") or []
    )


def _bootstrap_bridge(runtime_root: Path) -> CognitiveBridgeService:
    return CognitiveBridgeService(
        immune_controller=ImmuneSystemController(runtime_dir=runtime_root),
        detachment_guard=JarvisDetachmentGuard(runtime_dir=runtime_root),
    )


def _deliberation_request() -> dict[str, Any]:
    return {
        "question": "What likely caused the runtime latency spike?",
        "intent": "diagnose_runtime",
        "tenant_id": "default",
        "context": {"component": "orchestrator"},
        "lane_types": ["symbolic", "graph", "llm"],
    }


def scenario_mesh_parity(*, machine_id: str, runtime_root: Path) -> ScenarioEvidence:
    runtime_root.mkdir(parents=True, exist_ok=True)
    original_runtime = os.environ.get("AAIS_RUNTIME_DIR")
    original_mode = os.environ.get("UGR_DEPLOYMENT_MODE")
    original_mesh = os.environ.get("UGR_MESH_CONFIG")
    original_module_dir = module_governance.runtime_dir
    servers: list[_ServiceThread] = []
    try:
        os.environ["AAIS_RUNTIME_DIR"] = str(runtime_root)
        os.environ["UGR_DEPLOYMENT_MODE"] = "distributed"
        module_governance.configure_runtime_dir(runtime_root)
        module_governance.reset()
        reset_registry()
        bridge = _bootstrap_bridge(runtime_root)
        ports = {name: _free_port() for name in ("orchestrator", "policy", "ledger", "lane_worker", "convergence")}
        mesh_path = runtime_root / "mesh.json"
        mesh_path.write_text(
            json.dumps(
                {
                    "mesh_version": "0.1",
                    "cluster_id": f"{machine_id}-cluster",
                    "services": {
                        name: {"host": "127.0.0.1", "port": port, "role": name}
                        for name, port in ports.items()
                    },
                }
            ),
            encoding="utf-8",
        )
        os.environ["UGR_MESH_CONFIG"] = str(mesh_path)
        servers = [
            _ServiceThread(create_policy_app(bridge), ports["policy"]),
            _ServiceThread(create_ledger_app(), ports["ledger"]),
            _ServiceThread(create_lane_worker_app(), ports["lane_worker"]),
            _ServiceThread(create_convergence_app(), ports["convergence"]),
        ]
        distributed = DistributedUnifiedGovernedRuntime(
            clients=UGRMeshClients(mesh=load_mesh_config(mesh_path)),
            runtime_dir=runtime_root,
        )
        servers.append(_ServiceThread(create_orchestrator_app(distributed), ports["orchestrator"]))
        for server in servers:
            server.start()

        request = _deliberation_request()
        monolith = UnifiedGovernedRuntime(bridge=bridge, runtime_dir=runtime_root)
        mono_result = monolith.handle_request(request)
        dist_result = distributed.handle_request(request)
        mono_sig = belief_signature(mono_result)
        dist_sig = belief_signature(dist_result)
        matched = mono_sig == dist_sig and mono_result.get("status") == dist_result.get("status") == "ok"
        payload = {
            "monolith_status": mono_result.get("status"),
            "distributed_status": dist_result.get("status"),
            "belief_signature": mono_sig,
            "matched": matched,
        }
        return ScenarioEvidence(
            scenario_id="mesh_parity",
            machine_id=machine_id,
            status="pass" if matched else "fail",
            summary="monolith vs distributed belief parity",
            payload_sha256=sha256_text(stable_json(payload)),
            details=payload,
        )
    finally:
        for server in reversed(servers):
            server.stop()
        module_governance.configure_runtime_dir(original_module_dir)
        module_governance.reset()
        reset_registry()
        if original_runtime is None:
            os.environ.pop("AAIS_RUNTIME_DIR", None)
        else:
            os.environ["AAIS_RUNTIME_DIR"] = original_runtime
        if original_mode is None:
            os.environ.pop("UGR_DEPLOYMENT_MODE", None)
        else:
            os.environ["UGR_DEPLOYMENT_MODE"] = original_mode
        if original_mesh is None:
            os.environ.pop("UGR_MESH_CONFIG", None)
        else:
            os.environ["UGR_MESH_CONFIG"] = original_mesh


def scenario_causal_rebuild(*, machine_id: str, runtime_root: Path) -> ScenarioEvidence:
    runtime_root.mkdir(parents=True, exist_ok=True)
    original_runtime = os.environ.get("AAIS_RUNTIME_DIR")
    original_causal = os.environ.get("UGR_CAUSAL_GRAPH_ENABLED")
    try:
        os.environ["AAIS_RUNTIME_DIR"] = str(runtime_root)
        os.environ["UGR_CAUSAL_GRAPH_ENABLED"] = "1"
        ledger = PatternLedgerStore(runtime_dir=runtime_root)
        ledger.append_claim(
            {
                "claim_id": "claim-trust-bundle-a",
                "subject": "deploy pipeline",
                "predicate": "triggered",
                "object": "orchestrator restart",
                "tenant_scope": "global",
                "confidence": 0.8,
                "source_lane": "trust_bundle",
                "evidence_refs": ["evidence-trust-1"],
                "status": "accepted",
            }
        )
        ledger.append_claim(
            {
                "claim_id": "claim-trust-bundle-b",
                "subject": "orchestrator restart",
                "predicate": "caused",
                "object": "latency spike",
                "tenant_scope": "global",
                "confidence": 0.75,
                "source_lane": "trust_bundle",
                "status": "accepted",
            }
        )
        stats = ledger.rebuild_graph_index() or {}
        store = ledger._graph
        assert store is not None
        causal = store.query_causal("claim-trust-bundle-a", depth=2)
        edges_path = Path(getattr(store, "edges_path", runtime_root / "edges.jsonl"))
        edge_ids = sorted(str(edge.get("edge_id") or "") for edge in causal.get("edges") or [])
        payload = {
            "edge_count": stats.get("edge_count"),
            "causal_edges": len(edge_ids),
            "edge_ids": edge_ids,
        }
        edge_hash = sha256_file(edges_path) if edges_path.exists() else ""
        return ScenarioEvidence(
            scenario_id="causal_rebuild",
            machine_id=machine_id,
            status="pass" if edge_ids else "fail",
            summary="causal graph rebuild and walk",
            payload_sha256=sha256_text(stable_json(payload)),
            artifacts={"edges.jsonl": edge_hash} if edge_hash else {},
            details={**payload, "edges_sha256": edge_hash},
        )
    finally:
        if original_runtime is None:
            os.environ.pop("AAIS_RUNTIME_DIR", None)
        else:
            os.environ["AAIS_RUNTIME_DIR"] = original_runtime
        if original_causal is None:
            os.environ.pop("UGR_CAUSAL_GRAPH_ENABLED", None)
        else:
            os.environ["UGR_CAUSAL_GRAPH_ENABLED"] = original_causal


def scenario_llm_execution_smoke(*, machine_id: str, runtime_root: Path) -> ScenarioEvidence:
    runtime_root.mkdir(parents=True, exist_ok=True)
    original_runtime = os.environ.get("AAIS_RUNTIME_DIR")
    try:
        os.environ["AAIS_RUNTIME_DIR"] = str(runtime_root)
        module_governance.configure_runtime_dir(runtime_root)
        module_governance.reset()
        reset_registry()
        registry = ProviderRegistry()
        registry._providers = {}
        registry._adapters = {}
        registry.register(
            ProviderConfig(name="local", display_name="Mock Local", enabled=True, is_default=True),
            adapter=_MockProvider(),
        )
        result = run_governed_llm_lane(
            LaneSpec(lane_id="lane-trust", lane_type="llm"),
            {
                "trace_id": "trace-trust-bundle-organ",
                "question": "Explain orchestrator latency spike causes",
                "intent": "diagnose_runtime",
                "context": {},
            },
            provider_registry_instance=registry,
            force_execute=True,
        )
        execution = result.payload.get("governed_llm_execution") or {}
        passed = execution.get("status") == "EXECUTED" and result.metrics.get("tokens_used", 0) > 0
        payload = {
            "execution_status": execution.get("status"),
            "tokens_used": result.metrics.get("tokens_used"),
            "provider": execution.get("provider"),
        }
        return ScenarioEvidence(
            scenario_id="llm_execution_smoke",
            machine_id=machine_id,
            status="pass" if passed else "fail",
            summary="governed LLM execution commit smoke",
            payload_sha256=sha256_text(stable_json(payload)),
            details=payload,
        )
    finally:
        if original_runtime is None:
            os.environ.pop("AAIS_RUNTIME_DIR", None)
        else:
            os.environ["AAIS_RUNTIME_DIR"] = original_runtime


def scenario_gate_manifest(*, machine_id: str, runtime_root: Path | None = None) -> ScenarioEvidence:
    del runtime_root
    command = [
        sys.executable,
        str(REPO_ROOT / "wolf-cog-os" / "scripts" / "validate-ugr-trust-bundle-manifest.py"),
        "--repo-root",
        str(REPO_ROOT),
        "--mode",
        "fail",
    ]
    from src.ugr.trust_bundle.evidence import run_command

    exit_code, output = run_command(command, cwd=REPO_ROOT)
    return ScenarioEvidence(
        scenario_id="gate_manifest",
        machine_id=machine_id,
        status="pass" if exit_code == 0 else "fail",
        summary="trust bundle manifest validator",
        command=" ".join(command),
        exit_code=exit_code,
        stdout_sha256=sha256_text(output),
        details={"output_tail": output.strip()[-400:]},
    )


def scenario_federation_dual_ledger(
    *,
    machine_id: str,
    runtime_root: Path | None = None,
) -> ScenarioEvidence:
    """v1.9 — bilateral grant, federated step, dual ledger hash witness."""
    root = Path(runtime_root or Path(tempfile.mkdtemp(prefix="ugr-fed-scenario-")))
    root.mkdir(parents=True, exist_ok=True)
    original_runtime = os.environ.get("AAIS_RUNTIME_DIR")
    os.environ["AAIS_RUNTIME_DIR"] = str(root)
    os.environ.setdefault("URG_OPERATOR_RECEIPT_KEY", "trust-bundle-fed-op")
    os.environ.setdefault("URG_RECEIPT_SIGNING_KEY", "trust-bundle-fed-urg")
    try:
        from src.ugr.mission.federation_grants import (
            CAP_ROUTE_STEP,
            FederationGrantStore,
            compute_federation_digest,
        )
        from src.ugr.mission.mission_ledger import MissionLedger
        from src.ugr.mission.mission_runtime import UGRMissionRuntime

        demo_path = REPO_ROOT / "deploy" / "ugr" / "mission-demo-federation-v17.json"
        mission = json.loads(demo_path.read_text(encoding="utf-8"))["mission"]
        store = FederationGrantStore(root)
        grant = store.issue(
            issuer_tenant="tenant:acme",
            grantee_tenant="tenant:contoso",
            capabilities=[CAP_ROUTE_STEP],
            operator_id="trust-bundle",
        )
        store.accept(
            grant.grant_id,
            accepting_tenant="tenant:contoso",
            operator_id="trust-bundle",
        )
        for step in mission["steps"]:
            if step.get("federation_grant_id") == "__GRANT_ID__":
                step["federation_grant_id"] = grant.grant_id
        result = UGRMissionRuntime(runtime_dir=root).run_mission(mission)
        mission_id = str(result.get("mission_id") or "")
        home_ledger = MissionLedger(runtime_dir=root, tenant_id="tenant:acme")
        peer_ledger = MissionLedger(runtime_dir=root, tenant_id="tenant:contoso")
        digest = compute_federation_digest(
            home_rows=home_ledger.list_for_mission(mission_id),
            peer_rows=peer_ledger.list_for_mission(mission_id),
            grant_id=grant.grant_id,
        )
        ok = result.get("status") == "ok" and bool(digest)
        payload = {
            "grant_id": grant.grant_id,
            "mission_id": mission_id,
            "federation_digest": digest,
            "status": result.get("status"),
        }
        return ScenarioEvidence(
            scenario_id="federation_dual_ledger",
            machine_id=machine_id,
            status="pass" if ok else "fail",
            summary="bilateral federated step dual ledger",
            command="federation_dual_ledger",
            exit_code=0 if ok else 1,
            payload_sha256=sha256_text(stable_json(payload)),
            details=payload,
        )
    finally:
        if original_runtime is None:
            os.environ.pop("AAIS_RUNTIME_DIR", None)
        else:
            os.environ["AAIS_RUNTIME_DIR"] = original_runtime


def scenario_forge_federation_boundary(
    *,
    machine_id: str,
    runtime_root: Path | None = None,
) -> ScenarioEvidence:
    """v3.0 — federated peer rail with boundary extend and forge digest witness."""
    root = Path(runtime_root or Path(tempfile.mkdtemp(prefix="ugr-forge-fed-scenario-")))
    root.mkdir(parents=True, exist_ok=True)
    original_runtime = os.environ.get("AAIS_RUNTIME_DIR")
    os.environ["AAIS_RUNTIME_DIR"] = str(root)
    os.environ.setdefault("URG_OPERATOR_RECEIPT_KEY", "trust-bundle-forge-op")
    os.environ.setdefault("URG_RECEIPT_SIGNING_KEY", "trust-bundle-forge-urg")
    try:
        from src.ugr.mission.federation_grants import (
            CAP_FORGE_PEER_RAIL,
            CAP_ROUTE_STEP,
            FederationGrantStore,
            compute_federation_forge_digest,
        )
        from src.ugr.mission.mission_ledger import MissionLedger
        from src.ugr.mission.mission_runtime import UGRMissionRuntime

        demo_path = REPO_ROOT / "deploy" / "ugr" / "mission-demo-federation-v17.json"
        mission = json.loads(demo_path.read_text(encoding="utf-8"))["mission"]
        mission["context"] = {"forbid_express": False}
        store = FederationGrantStore(root)
        grant = store.issue(
            issuer_tenant="tenant:acme",
            grantee_tenant="tenant:contoso",
            capabilities=[CAP_ROUTE_STEP, CAP_FORGE_PEER_RAIL],
            operator_id="trust-bundle",
        )
        store.accept(
            grant.grant_id,
            accepting_tenant="tenant:contoso",
            operator_id="trust-bundle",
        )
        for step in mission["steps"]:
            if step.get("federation_grant_id") == "__GRANT_ID__":
                step["federation_grant_id"] = grant.grant_id
        result = UGRMissionRuntime(runtime_dir=root).run_mission(mission)
        mission_id = str(result.get("mission_id") or "")
        fed_ctx = list((result.get("urg_ingress") or {}).get("federation_context") or [])
        forge_digest = compute_federation_forge_digest(fed_ctx)
        home_ledger = MissionLedger(runtime_dir=root, tenant_id="tenant:acme")
        boundary_rows = [
            r
            for r in home_ledger.list_for_mission(mission_id)
            if r.get("phase") == "federation_boundary_extend"
        ]
        ok = (
            result.get("status") == "ok"
            and bool(forge_digest)
            and (bool(boundary_rows) or fed_ctx[0].get("mission_rail") == fed_ctx[0].get("peer_rail"))
        )
        payload = {
            "grant_id": grant.grant_id,
            "mission_id": mission_id,
            "federation_forge_digest": forge_digest,
            "boundary_extend_rows": len(boundary_rows),
            "status": result.get("status"),
        }
        return ScenarioEvidence(
            scenario_id="forge_federation_boundary",
            machine_id=machine_id,
            status="pass" if ok else "fail",
            summary="federated forge boundary extend witness",
            command="forge_federation_boundary",
            exit_code=0 if ok else 1,
            payload_sha256=sha256_text(stable_json(payload)),
            details=payload,
        )
    finally:
        if original_runtime is None:
            os.environ.pop("AAIS_RUNTIME_DIR", None)
        else:
            os.environ["AAIS_RUNTIME_DIR"] = original_runtime


SCENARIO_RUNNERS = {
    "mesh_parity": scenario_mesh_parity,
    "causal_rebuild": scenario_causal_rebuild,
    "llm_execution_smoke": scenario_llm_execution_smoke,
    "gate_manifest": scenario_gate_manifest,
    "federation_dual_ledger": scenario_federation_dual_ledger,
    "forge_federation_boundary": scenario_forge_federation_boundary,
}
