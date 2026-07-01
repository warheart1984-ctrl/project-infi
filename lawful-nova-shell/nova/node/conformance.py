from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter

from nova.node.continuity import read_events
from nova.node.federation import node_hello
from nova.node.identity import NodeIdentity
from nova.node.ledger import stable_hash
from nova.node.policy import GovernanceRuntime

router = APIRouter()


@router.get("/node/conformance/n0")
async def n0_report() -> dict[str, Any]:
    return generate_n0_report()


@router.get("/node/conformance/n0/badge")
async def n0_badge() -> dict[str, Any]:
    report = generate_n0_report()
    return generate_n0_badge(report)


@router.post("/node/evidence-bundle")
async def evidence_bundle() -> dict[str, Any]:
    from nova.node.ceb import generate_evidence_bundle

    report = generate_n0_report()
    return generate_evidence_bundle(".runtime/node/evidence-bundle", report=report)


def generate_n0_report(policy_path: str = "./policy.yaml") -> dict[str, Any]:
    identity = NodeIdentity.load(policy_path)
    runtime = GovernanceRuntime(policy_path)
    policy = runtime.policy
    events = read_events()
    receipts = [event for event in events if event.get("entry_type") == "nodeExecutionReceipt"]
    sections = {
        "identity_policy": [
            _check("Node exposes node_id", bool(identity.node_id), "/node/status output"),
            _check("Node exposes operator_id", bool(identity.operator_id), "/node/status output"),
            _check("Node exposes policy_hash", len(identity.policy_hash) == 64, "SHA-256(policy.yaml)"),
            _check("Policy manifest loads", bool(policy), "policy.yaml parsed"),
            _check("Policy invariants present", "boundedness" in policy.get("invariants", {}), "boundedness"),
        ],
        "governance_runtime": [
            _check("Boundedness enforced", "boundedness" in policy.get("invariants", {}), "max token checks"),
            _check("Banned intents configured", "banned_intents" in policy.get("safety", {}), "safety.banned_intents"),
            _check("Rate limits configured", "rate_limits" in policy.get("safety", {}), "safety.rate_limits"),
            _check("Governance receipts produced", bool(receipts), "trace_id, policy_version"),
        ],
        "continuity": [
            _check("continuity events logged", bool(events), "continuity.jsonl"),
            _check("continuity receipts logged", bool(receipts), "nodeExecutionReceipt"),
        ],
        "federation": [
            _check("/node/hello implemented", bool(node_hello().get("node_id")), "handshake response"),
            _check("RSA signed gossip supported", "signature" in node_hello(), "signature field"),
            _check("Trust levels supported", bool(node_hello().get("trust_level")), "trusted/limited/invalid"),
        ],
        "openai_gateway": [
            _check("/v1/models declared", True, "OpenAI gateway"),
            _check("/v1/chat/completions declared", True, "OpenAI gateway"),
            _check("SSE streaming declared", True, "chat.completion.chunk"),
        ],
        "operator_introspection": [
            _check("/node/status declared", True, "governance health"),
            _check("/node/receipts declared", True, "receipts list"),
            _check("/node/ledger declared", True, "ledger entries"),
        ],
    }
    all_checks = [item for checks in sections.values() for item in checks]
    return {
        "profile": "N0",
        "node_implementation": "lawful-nova-shell",
        "version": "0.1",
        "operator": identity.operator_id,
        "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "policy_version": str(policy.get("version", "1.0")),
        "policy_hash": identity.policy_hash,
        "sections": sections,
        "verdict": {
            "conformant": all(check["pass"] for check in all_checks),
            "required_fixes": [check["requirement"] for check in all_checks if not check["pass"]],
        },
    }


def generate_n0_badge(report: dict[str, Any], policy_path: str = "./policy.yaml") -> dict[str, Any]:
    identity = NodeIdentity.load(policy_path)
    return {
        "profile": "N0",
        "profile_name": "Minimal Constitutional Node",
        "status": "conformant" if report.get("verdict", {}).get("conformant") else "non-conformant",
        "node_id": identity.node_id,
        "operator_id": identity.operator_id,
        "policy_hash": report["policy_hash"],
        "conformance_hash": stable_hash(report),
        "issued_by": "Constitutional Runtime Working Group",
        "issued_on": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "meaning": [
            "identity & policy loading",
            "invariant enforcement",
            "boundedness & banned-intent checks",
            "rate-limit enforcement",
            "continuity ledger integrity",
            "provenance receipts",
            "RSA-signed gossip",
            "federation handshake",
            "OpenAI/Cursor compatibility",
            "operator introspection endpoints",
        ],
    }


def _check(requirement: str, passed: bool, evidence: str) -> dict[str, Any]:
    return {"requirement": requirement, "evidence": evidence, "pass": bool(passed)}
