"""Program debt register surfaced in the operator console."""

from __future__ import annotations

from typing import Any


DEBT_REGISTER: list[dict[str, Any]] = [
    {
        "id": "UGR-D1",
        "item": "Cloud output formats remain stubs",
        "severity": "medium",
        "owner": "operator",
        "status": "open",
        "claim_status": "asserted",
    },
    {
        "id": "UGR-D2",
        "item": "External graph DB at scale (SQLite projection active)",
        "severity": "medium",
        "owner": "architect",
        "status": "partial",
        "claim_status": "asserted",
    },
    {
        "id": "UGR-D3",
        "item": "Governed LLM execution commit",
        "severity": "low",
        "owner": "runtime",
        "status": "closed",
        "claim_status": "proven",
    },
    {
        "id": "UGR-D4",
        "item": "Wolf CoG unified write-path",
        "severity": "high",
        "owner": "runtime",
        "status": "partial",
        "claim_status": "asserted",
    },
    {
        "id": "UGR-D5",
        "item": "Cross-OS trust bundle matrix evidence",
        "severity": "medium",
        "owner": "operator",
        "status": "open",
        "claim_status": "asserted",
    },
    {
        "id": "CF-D5",
        "item": "Cross-machine Cloud Forge latency benchmarks",
        "severity": "medium",
        "owner": "operator",
        "status": "open",
        "claim_status": "asserted",
    },
    {
        "id": "PLAT-D1",
        "item": "Unified service boundary — platform membrane v1 landed; OIDC deferred",
        "severity": "medium",
        "owner": "platform",
        "status": "partial",
        "claim_status": "asserted",
    },
    {
        "id": "PLAT-D2",
        "item": "SaaS identity — org/RBAC/API keys v1.1 scopes; OIDC scaffold landed",
        "severity": "medium",
        "owner": "platform",
        "status": "partial",
        "claim_status": "asserted",
    },
    {
        "id": "PLAT-D8",
        "item": "OIDC per org — login/callback scaffold; full IdP integration debt",
        "severity": "medium",
        "owner": "platform",
        "status": "partial",
        "claim_status": "asserted",
    },
    {
        "id": "PLAT-D3",
        "item": "Global job orchestrator — registry + adapters; Redis optional",
        "severity": "low",
        "owner": "platform",
        "status": "partial",
        "claim_status": "asserted",
    },
    {
        "id": "PLAT-D4",
        "item": "Artifact federation index — pointer index v1; S3 copy optional",
        "severity": "low",
        "owner": "platform",
        "status": "partial",
        "claim_status": "asserted",
    },
    {
        "id": "PLAT-D5",
        "item": "Unified operator console — /platform UI v1",
        "severity": "low",
        "owner": "platform",
        "status": "partial",
        "claim_status": "asserted",
    },
    {
        "id": "PLAT-D6",
        "item": "Single-product deploy — compose + Helm skeleton; monitoring debt",
        "severity": "medium",
        "owner": "ops",
        "status": "partial",
        "claim_status": "asserted",
    },
    {
        "id": "PLAT-D7",
        "item": "Cross-machine proof activation — replay runner + CI matrix scaffold",
        "severity": "medium",
        "owner": "ops",
        "status": "open",
        "claim_status": "asserted",
    },
    {
        "id": "UGR-D9",
        "item": "UGR Ledger Bridge v1 — Pattern Ledger ↔ Trust Bundle",
        "severity": "medium",
        "owner": "runtime",
        "status": "partial",
        "claim_status": "asserted",
    },
    {
        "id": "PLAT-PILOT-D1",
        "item": "Infinity Pilot K8s multi-tenant production hardening",
        "severity": "high",
        "owner": "ops",
        "status": "open",
        "claim_status": "rejected",
    },
    {
        "id": "PLAT-PILOT-D2",
        "item": "Infinity Pilot full-stack compose path",
        "severity": "medium",
        "owner": "ops",
        "status": "partial",
        "claim_status": "asserted",
    },
]


def debt_summary() -> dict[str, Any]:
    open_items = [item for item in DEBT_REGISTER if item.get("status") == "open"]
    partial_items = [item for item in DEBT_REGISTER if item.get("status") == "partial"]
    proven_items = [item for item in DEBT_REGISTER if item.get("claim_status") == "proven"]
    return {
        "total": len(DEBT_REGISTER),
        "open": len(open_items),
        "partial": len(partial_items),
        "proven_claims": len(proven_items),
        "items": list(DEBT_REGISTER),
    }
