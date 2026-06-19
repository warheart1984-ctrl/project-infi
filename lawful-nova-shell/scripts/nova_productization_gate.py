"""Productization readiness gate for the local Lawful Nova slice."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from nova.cli import collect_health
from nova.lawful_llm import LawfulLLM


def _python_runtime() -> dict[str, str]:
    return {
        "status": "ok",
        "detail": sys.executable,
    }


def _direct_lawful_llm() -> dict[str, str]:
    try:
        llm = LawfulLLM(operator_session_id="nova-productization-gate", signing_secret="gate-secret")
        turn = llm.ask("observe productization gate", tenant_id="local", capability="observe")
        verified = llm.verify_receipt(turn.receipt)
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"status": "fail", "detail": str(exc)}
    if not verified:
        return {"status": "fail", "detail": "receipt verification failed"}
    return {"status": "ok", "detail": turn.voss_runtime["decision"]}


def _chain_contract() -> dict[str, str]:
    try:
        llm = LawfulLLM(operator_session_id="nova-chain-gate", signing_secret="chain-gate-secret")
        turn = llm.ask("observe chain preservation", tenant_id="local", capability="observe")
        payload = json.loads(str(turn.receipt["payload"]))
        for name in ("identity", "trace", "authority_boundary", "reproducibility"):
            if name not in payload:
                return {"status": "fail", "detail": f"missing {name}"}
        if not payload["identity"].get("instance_id"):
            return {"status": "fail", "detail": "missing identity.instance_id"}
        if not payload["trace"].get("trace_id"):
            return {"status": "fail", "detail": "missing trace.trace_id"}
        if payload["authority_boundary"].get("operator_authority") != "external":
            return {"status": "fail", "detail": "invalid authority boundary"}
        if not payload["reproducibility"].get("prompt_sha256"):
            return {"status": "fail", "detail": "missing reproducibility hash"}
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"status": "fail", "detail": str(exc)}
    return {"status": "ok", "detail": "identity trace authority reproducibility preserved"}


def build_report(repo_root: Path) -> dict[str, Any]:
    health = collect_health()
    checks = {
        "python_runtime": _python_runtime(),
        "direct_lawful_llm": _direct_lawful_llm(),
        "chain_contract": _chain_contract(),
        "local_cli": health["direct_lawful_llm"],
        "lawful_brain_api": health["lawful_brain_api"],
        "operator_kernel_api": health["operator_kernel_api"],
    }
    local_ready = all(
        checks[name]["status"] == "ok"
        for name in ("python_runtime", "direct_lawful_llm", "chain_contract", "local_cli")
    )
    external_stack_ready = all(
        checks[name]["status"] == "ok"
        for name in ("lawful_brain_api", "operator_kernel_api")
    )
    remaining_external_closure: list[str] = []
    if checks["local_cli"]["status"] != "ok":
        remaining_external_closure.append(
            "Point NOVA_CLI at lawful-nova-shell/bin/nova.ps1 or install the vendor Nova CLI."
        )
    if not external_stack_ready:
        remaining_external_closure.append(
            "Start /health-compatible API services for full local stack readiness."
        )
    remaining_external_closure.extend(
        [
            "Install or mount Voss, Cortex, RSL, NVIDIA, and cross-machine Wolf assets where the deployment target requires vendor/hardware assets.",
            "Run cross-machine Wolf reboot and operator rubric proof bundles before making a production-hardware claim.",
        ]
    )
    return {
        "gate": "nova_productization.v1",
        "repo_root": str(repo_root),
        "local_lawful_slice_ready": local_ready,
        "local_services_ready": external_stack_ready,
        "checks": checks,
        "remaining_external_closure": remaining_external_closure,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-out", type=Path, default=Path(".runtime/nova_productization_report.json"))
    args = parser.parse_args(argv)

    repo_root = Path.cwd().resolve()
    report = build_report(repo_root)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["local_lawful_slice_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
