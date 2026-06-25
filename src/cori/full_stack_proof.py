"""Production-grade full-stack proof: Nova → UGR → AAIS → AAES → Nexus → CORI."""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from urllib import error, request

from nova.bridges import law_ledger_bridge, panel_store
from nova.bridges.panel_store import PanelStore

from src.aaes_os.nexus_execution_ledger import NexusExecutionLedger, reset_nexus_execution_ledger
from src.continuity.continuity_store import ContinuityStore, reset_continuity_store
from src.continuity.law_ledger import LawLedgerStore, bootstrap_law_ledger
from src.cori.asset_registry import reset_asset_registry
from src.cori.evidence_factory import EvidenceFactory, reset_evidence_factory
from src.cori.governance_invariants import GovernanceInvariantChecker
from src.governed.config import GovernedRuntimeConfig, reset_governed_config
from src.governed.make_governed_mission import make_governed_mission
from tests.governed_stubs import StubMissionRuntime


ProofMode = Literal["in_process", "http", "hybrid"]
ProofStatus = Literal["pass", "fail"]


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class LayerCheck:
    layer: str
    passed: bool
    detail: str
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "layer": self.layer,
            "passed": self.passed,
            "detail": self.detail,
            "evidence": self.evidence,
        }


@dataclass
class FullStackProofReport:
    status: ProofStatus
    mode: ProofMode
    started_at: str
    completed_at: str
    layers: list[LayerCheck] = field(default_factory=list)
    governed_trace: dict[str, Any] | None = None
    invariants: list[dict[str, Any]] = field(default_factory=list)
    alpha_proof: dict[str, Any] | None = None
    vault_cp001: dict[str, Any] | None = None
    failures: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "mode": self.mode,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "layers": [layer.to_dict() for layer in self.layers],
            "governed_trace": self.governed_trace,
            "invariants": self.invariants,
            "alpha_proof": self.alpha_proof,
            "vault_cp001": self.vault_cp001,
            "failures": self.failures,
            "summary": self._summary(),
        }

    def _summary(self) -> str:
        passed = sum(1 for layer in self.layers if layer.passed)
        total = len(self.layers)
        if self.status == "pass":
            return f"Full stack proof PASSED ({passed}/{total} layers verified)"
        return f"Full stack proof FAILED ({passed}/{total} layers passed, {len(self.failures)} failures)"

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)


def _http_get_json(url: str, timeout: float = 10.0) -> dict[str, Any] | list[Any]:
    req = request.Request(url, method="GET")
    with request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body)


def _http_post_json(url: str, payload: dict[str, Any], timeout: float = 120.0) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
        parsed = json.loads(body)
        if not isinstance(parsed, dict):
            raise RuntimeError(f"expected JSON object from {url}, got {type(parsed).__name__}")
        return parsed


def _service_urls() -> dict[str, str]:
    return {
        "nova": os.environ.get("LAWFUL_NOVA_BASE_URL", "http://127.0.0.1:8080").rstrip("/"),
        "aais": os.environ.get("AAIS_BASE_URL", "http://127.0.0.1:8000").rstrip("/"),
        "aaes": os.environ.get("AAES_BASE_URL", "http://127.0.0.1:8101").rstrip("/"),
        "nexus": os.environ.get("NEXUS_OPS_CONSOLE_URL", "http://127.0.0.1:4000").rstrip("/"),
        "dashboard": os.environ.get("DASHBOARD_URL", "http://127.0.0.1:8100").rstrip("/"),
    }


def _check_http_health(report: FullStackProofReport) -> None:
    urls = _service_urls()
    for layer, base in urls.items():
        health_path = f"{base}/health"
        try:
            payload = _http_get_json(health_path, timeout=5.0)
            ok = isinstance(payload, dict) and str(payload.get("status", "")).lower() in {"ok", "healthy"}
            report.layers.append(
                LayerCheck(
                    layer=f"{layer}_health",
                    passed=ok,
                    detail=f"GET {health_path}",
                    evidence={"response": payload},
                )
            )
            if not ok:
                report.failures.append(f"{layer} health check returned unexpected payload")
        except (error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            report.layers.append(
                LayerCheck(
                    layer=f"{layer}_health",
                    passed=False,
                    detail=f"GET {health_path} failed: {exc}",
                )
            )
            report.failures.append(f"{layer} unreachable at {health_path}: {exc}")


def _setup_in_process_runtime(base_dir: Path) -> GovernedRuntimeConfig:
    runtime_dir = base_dir / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    panel_path = base_dir / "nova_panel_store.sqlite3"
    law_path = base_dir / "law-ledger.sqlite3"
    continuity_path = base_dir / "continuity.sqlite3"
    nexus_path = base_dir / "nexus_executions.jsonl"
    vault_path = base_dir / "vault.sqlite3"
    alpha_path = base_dir / "alpha_evidence.sqlite3"
    runtime_db = base_dir / "runtime_core.db"

    os.environ["AAIS_RUNTIME_DIR"] = str(runtime_dir)
    os.environ["NOVA_PANEL_STORE_PATH"] = str(panel_path)
    os.environ["LAW_LEDGER_PATH"] = str(law_path)
    os.environ["CONTINUITY_STORE_PATH"] = str(continuity_path)
    os.environ["NEXUS_EXECUTION_LEDGER_PATH"] = str(nexus_path)
    os.environ["VAULT_STORE_PATH"] = str(vault_path)
    os.environ["ALPHA_EVIDENCE_PATH"] = str(alpha_path)
    os.environ["RUNTIME_DATABASE_URL"] = f"sqlite:///{runtime_db.as_posix()}"
    os.environ["GOVERNED_NOVA_IN_PROCESS"] = "1"
    os.environ["GOVERNED_URG_IN_PROCESS"] = "1"
    os.environ["GOVERNED_AAES_IN_PROCESS"] = "1"
    os.environ.pop("CORI_CI_STUB_URG", None)

    continuity = ContinuityStore(path=continuity_path)
    law_store = LawLedgerStore(path=law_path)
    bootstrap_law_ledger(law_store)
    law_ledger_bridge.reset_law_ledger_store(law_store)
    panel_store.reset_panel_store(PanelStore(path=panel_path))
    reset_continuity_store(continuity)
    reset_asset_registry()
    reset_evidence_factory(EvidenceFactory(continuity=continuity))
    reset_nexus_execution_ledger(NexusExecutionLedger(path=nexus_path))

    from src.runtime import api as runtime_api
    from src.runtime.database import reset_runtime_engine

    reset_runtime_engine(f"sqlite:///{runtime_db.as_posix()}", create_tables=True)
    runtime_api._runtime_db_ready = False

    cfg = GovernedRuntimeConfig(
        use_http_nova=False,
        use_http_urg=False,
        use_http_aaes=False,
        mission_tenant_id="tenant:acme",
        aais_instance_id="aais-local-1",
        mission_runtime=StubMissionRuntime(),
    )
    reset_governed_config(cfg)
    return cfg


def _teardown_in_process_runtime(base_dir: Path) -> None:
    reset_governed_config(None)
    law_ledger_bridge.reset_law_ledger_store(None)
    panel_store.reset_panel_store(None)
    reset_continuity_store(None)
    reset_asset_registry(None)
    reset_evidence_factory(None)
    reset_nexus_execution_ledger(None)
    shutil.rmtree(base_dir / "runtime", ignore_errors=True)


def _run_governed_spine(cfg: GovernedRuntimeConfig, report: FullStackProofReport) -> dict[str, Any]:
    trace = make_governed_mission(
        "Full stack production proof — constitutional spine.",
        {"operator_id": "full-stack-proof", "steward_id": "vault"},
        config=cfg,
    )
    report.governed_trace = trace

    law_ok = trace.get("law_eval", {}).get("status") == "ok"
    urg_ok = bool(trace.get("urg_receipt", {}).get("mission_id"))
    aaes_ok = trace.get("aaes_receipt", {}).get("status") == "executed"
    nexus_ok = trace.get("nexus_event", {}).get("event_type") == "execution"
    spine_ok = law_ok and urg_ok and aaes_ok and nexus_ok

    report.layers.extend(
        [
            LayerCheck("nova", law_ok, "Lawful Nova LAW_EVAL", {"law_eval_id": trace.get("law_eval", {}).get("id")}),
            LayerCheck(
                "ugr",
                urg_ok,
                "URG mission receipt",
                {"mission_id": trace.get("urg_receipt", {}).get("mission_id")},
            ),
            LayerCheck(
                "aais",
                trace.get("status") in {"ok", "partial"},
                "AAIS governed orchestration",
                {"trace_status": trace.get("status")},
            ),
            LayerCheck(
                "aaes",
                aaes_ok,
                "AAES execution receipt",
                {"execution_id": trace.get("aaes_receipt", {}).get("execution_id")},
            ),
            LayerCheck(
                "nexus",
                nexus_ok,
                "Nexus execution ledger event",
                {"event_id": trace.get("nexus_event", {}).get("event_id")},
            ),
        ]
    )
    if not spine_ok:
        report.failures.append("constitutional spine incomplete")
    return trace


def _run_invariants(report: FullStackProofReport) -> None:
    checker = GovernanceInvariantChecker()
    results = checker.run_all()
    checker.persist_status(results)
    report.invariants = [result.to_dict() for result in results]
    failed = [result for result in results if not result.passed]
    report.layers.append(
        LayerCheck(
            "cori_invariants",
            not failed,
            f"{len(results) - len(failed)}/{len(results)} invariants passed",
            {"failed": [result.invariant_id for result in failed]},
        )
    )
    for result in failed:
        report.failures.append(f"invariant {result.invariant_id}: {result.violations}")


def _run_alpha_proof(report: FullStackProofReport) -> None:
    from fastapi.testclient import TestClient

    import app.main as app_main
    from src.cori.pel.bootstrap_claims import create_alpha_t1_claim
    from src.cori.pel.pel_register import audit_to_pel, fetch_audit_record
    from src.cori.pel.pel_verify import verify_pel_record
    from src.cori.pel.storage import ClaimStorage, PelStorage, VerificationStorage

    payload = {
        "email": "full-stack-proof@example.org",
        "display_name": "Full Stack Proof",
        "asset": {
            "type": "document",
            "name": "Full Stack Proof Asset",
            "metadata": {"category": "full-stack-proof"},
        },
        "evidence": {
            "kind": "upload",
            "uri": "s3://full-stack-proof/artifact",
            "hash": "full-stack-proof-hash",
        },
    }

    with TestClient(app_main.app) as client:
        response = client.post("/v1/runtime/core-loop", json=payload)
        response.raise_for_status()
        audit_id = str(response.json()["audit_id"])
        audit = fetch_audit_record(audit_id, client=client)
        pel = audit_to_pel(audit)
        claim = create_alpha_t1_claim()
        verification = verify_pel_record(pel, claim)
        PelStorage().save_pel_record(pel)
        ClaimStorage().save_claim(claim)
        VerificationStorage().save_verification(verification)

    ok = verification.status == "verified"
    report.alpha_proof = {
        "audit_id": audit_id,
        "pel_id": pel.id,
        "claim_id": claim.id,
        "verification_status": verification.status,
        "primary_hash": pel.primary_hash,
    }
    report.layers.append(
        LayerCheck(
            "cori_alpha_pel",
            ok,
            "Runtime core-loop → PEL → Claim → Verification",
            report.alpha_proof,
        )
    )
    if not ok:
        report.failures.append(f"alpha proof verification: {verification.status}")


def _run_vault_cp001(report: FullStackProofReport) -> None:
    from src.cori.vault.avcp import run_avcp_ceremony
    from src.cori.vault.store import VaultStorage

    result = run_avcp_ceremony(observer="FullStackProof-01")
    VaultStorage().persist_ceremony(
        result.package,
        result.vault_entry,
        result.seal_record,
        result.lineage_registration,
    )
    ok = result.vault_entry.status == "sealed" and result.reproduction_log[0].result == "verified"
    report.vault_cp001 = {
        "vault_entry_id": result.vault_entry.id,
        "seal_record_id": result.seal_record.id,
        "canonical_hash": result.package.canonical_hash,
        "verified_fact": result.package.artifacts.derived_claim.summary,
        "status": result.vault_entry.status,
    }
    report.layers.append(
        LayerCheck(
            "cori_vault_cp001",
            ok,
            "AVCP-1.0 ceremony + D-3 seal",
            report.vault_cp001,
        )
    )
    if not ok:
        report.failures.append("vault CP-001 ceremony did not seal")


def _run_http_governed_mission(report: FullStackProofReport) -> None:
    urls = _service_urls()
    trace = _http_post_json(
        f"{urls['aais']}/governed/mission",
        {"text": "HTTP full stack proof", "operator_id": "full-stack-http"},
    )
    report.governed_trace = trace

    aais_exec = _http_get_json(f"{urls['aais']}/api/nexus/executions")
    nexus_exec = _http_get_json(f"{urls['nexus']}/api/nexus/executions")

    aais_list = aais_exec.get("executions", aais_exec) if isinstance(aais_exec, dict) else aais_exec
    nexus_list = nexus_exec.get("executions", nexus_exec) if isinstance(nexus_exec, dict) else nexus_exec

    mission_id = trace.get("urg_receipt", {}).get("mission_id")
    law_ok = trace.get("law_eval", {}).get("status") == "ok"
    urg_ok = bool(mission_id)
    aaes_ok = trace.get("aaes_receipt", {}).get("status") == "executed"
    nexus_ok = trace.get("nexus_event", {}).get("event_type") == "execution"

    aais_has_mission = any(row.get("mission_id") == mission_id for row in aais_list if isinstance(row, dict))
    nexus_has_mission = any(row.get("mission_id") == mission_id for row in nexus_list if isinstance(row, dict))
    ledger_shared = aais_has_mission and nexus_has_mission

    report.layers.extend(
        [
            LayerCheck(
                "nova_http",
                law_ok,
                "Lawful Nova via HTTP (container :8080)",
                {"law_eval_id": trace.get("law_eval", {}).get("id")},
            ),
            LayerCheck(
                "ugr_http",
                urg_ok,
                "URG mission via HTTP (/legacy_api/api/ugr/mission/run)",
                {"mission_id": mission_id},
            ),
            LayerCheck(
                "aaes_http",
                aaes_ok,
                "AAES execution via HTTP (/aaes/execute on AAIS)",
                {"execution_id": trace.get("aaes_receipt", {}).get("execution_id")},
            ),
            LayerCheck(
                "aais_http_mission",
                trace.get("status") in {"ok", "partial"} and law_ok and urg_ok and aaes_ok,
                "POST /governed/mission via HTTP",
                {"mission_id": mission_id, "trace_status": trace.get("status"), "nexus_event": nexus_ok},
            ),
            LayerCheck(
                "nexus_cross_port",
                ledger_shared,
                "Nexus execution visible on AAIS and ops console (shared ledger)",
                {"aais_count": len(aais_list), "nexus_count": len(nexus_list)},
            ),
        ]
    )
    if not (law_ok and urg_ok and aaes_ok and nexus_ok):
        report.failures.append("HTTP constitutional spine incomplete")
    if not ledger_shared:
        report.failures.append("governed mission not found on both Nexus endpoints (check NEXUS_EXECUTION_LEDGER_PATH)")


def resolve_proof_mode() -> ProofMode:
    explicit = os.environ.get("FULL_STACK_PROOF_MODE", "").strip().lower()
    if explicit in {"in_process", "http", "hybrid"}:
        return explicit  # type: ignore[return-value]
    if _truthy(os.environ.get("FULL_STACK_HTTP")):
        return "http"
    return "in_process"


def run_full_stack_proof(
    *,
    mode: ProofMode | None = None,
    work_dir: Path | None = None,
) -> FullStackProofReport:
    """
    Run production-grade proof across Nova → UGR → AAIS → AAES → Nexus → CORI.

    Modes:
    - in_process: full spine + invariants + alpha + vault (no external services)
    - http: health checks + HTTP governed mission against live stack
    - hybrid: http health + in_process constitutional proof
    """
    started = _now()
    selected = mode or resolve_proof_mode()
    report = FullStackProofReport(
        status="fail",
        mode=selected,
        started_at=started,
        completed_at=started,
    )

    base_dir = work_dir
    owns_dir = base_dir is None
    if base_dir is None:
        import tempfile

        base_dir = Path(tempfile.mkdtemp(prefix="cori-full-stack-"))

    cfg: GovernedRuntimeConfig | None = None
    try:
        if selected in {"http", "hybrid"}:
            _check_http_health(report)

        if selected == "http":
            if not any(layer.layer.endswith("_health") and layer.passed for layer in report.layers):
                report.failures.append("no HTTP services healthy — cannot run http-only proof")
            else:
                _run_http_governed_mission(report)
        else:
            cfg = _setup_in_process_runtime(base_dir)
            _run_governed_spine(cfg, report)
            _run_invariants(report)
            _run_alpha_proof(report)
            _run_vault_cp001(report)
            if selected == "hybrid":
                healthy = [layer for layer in report.layers if layer.layer.endswith("_health") and layer.passed]
                if healthy:
                    _run_http_governed_mission(report)

        report.completed_at = _now()
        report.status = "pass" if not report.failures and all(layer.passed for layer in report.layers) else "fail"
        return report
    finally:
        if cfg is not None and owns_dir and base_dir is not None:
            _teardown_in_process_runtime(base_dir)
        if owns_dir and base_dir is not None:
            shutil.rmtree(base_dir, ignore_errors=True)
