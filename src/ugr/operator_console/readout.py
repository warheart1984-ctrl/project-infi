"""Operator readout builder — advisory-only UGR / Cloud Forge surface."""

from __future__ import annotations

from typing import Any


def build_operator_readout(snapshot: dict[str, Any]) -> dict[str, Any]:
    ugr = dict(snapshot.get("ugr") or {})
    forge = dict(snapshot.get("cloud_forge") or {})
    trust = dict(snapshot.get("trust_bundle") or {})
    debt = dict(snapshot.get("debt_register") or {})
    mesh = dict(snapshot.get("mesh_health") or {})
    traces = dict(snapshot.get("deliberation_traces") or {})
    platform = dict(snapshot.get("forge_platform") or {})
    summary_parts = [
        f"UGR deployment={ugr.get('deployment_mode') or 'unknown'}",
        f"embryo={((ugr.get('embryo') or {}).get('status') or 'unknown')}",
        f"forge_rail={forge.get('rail') or 'unknown'}",
        f"trust_bundle={trust.get('overall_status') or 'missing'}",
        f"debt_open={debt.get('open', 0)}",
        f"mesh={mesh.get('poll_status') or 'unknown'}",
        f"traces={traces.get('trace_count', 0)}",
        f"forge_platform={platform.get('status') or 'unknown'}",
    ]
    return {
        "contract_version": "1.0",
        "summary": "; ".join(summary_parts),
        "claim_status": str(snapshot.get("claim_status") or "asserted"),
        "runtime_effect": "readout_only",
        "influences_runtime": False,
        "ugr": ugr,
        "cloud_forge": forge,
        "trust_bundle": trust,
        "debt_register": debt,
    }
