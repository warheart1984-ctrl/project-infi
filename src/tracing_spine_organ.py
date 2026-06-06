"""Tracing Spine Organ — read-only governed trace stage visibility."""

# Mythic: Tracing Spine Organ
# Engineering: TracingSpineEngine
from __future__ import annotations

from pathlib import Path
from typing import Any

from src.governed_direct_pipeline import PIPELINE_ID, PIPELINE_VERSION

MODULE_ID = "AAIS-TS-01"
ORGAN_VERSION = "tracing_spine_organ.v1"
TRACING_CONTRACT = "docs/contracts/AAIS_TRACING_PROTOCOL.md"


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def build_tracing_spine_status(*, root: Path | None = None) -> dict[str, Any]:
    """Canonical trace spine posture per AAIS_TRACING_PROTOCOL."""
    root = root or _root()
    contract_present = (root / TRACING_CONTRACT).is_file()
    bridge_present = (root / "src" / "cognitive_bridge.py").is_file()
    pipeline_present = (root / "src" / "governed_direct_pipeline.py").is_file()
    event_chain_present = (root / "src" / "governed_event_chain.py").is_file()
    seam_log_present = (root / "src" / "seam_log.py").is_file()
    stages_ok = all(
        [contract_present, bridge_present, pipeline_present, event_chain_present, seam_log_present]
    )
    fail_closed = stages_ok
    from src.firetiger_otel import firetiger_export_status, is_firetiger_export_configured

    otel_status = firetiger_export_status()
    otel_export_enabled = is_firetiger_export_configured()
    summary = (
        f"contract={contract_present};stages_ok={stages_ok};"
        f"pipeline={PIPELINE_ID};fail_closed={fail_closed};"
        f"otel_export={otel_export_enabled}"
    )[:128]
    return {
        "tracing_spine_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "tracing_contract_present": contract_present,
        "canonical_stages_present": stages_ok,
        "pipeline_id": PIPELINE_ID,
        "pipeline_version": PIPELINE_VERSION,
        "missing_trace_fail_closed": fail_closed,
        "otel_export_enabled": otel_export_enabled,
        "firetiger_export": otel_status,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
