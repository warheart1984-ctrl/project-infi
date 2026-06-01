"""Shared ARIS runtime helpers for embedded AAIS enforcement.

ARIS is admitted here as an embedded governed runtime profile inside AAIS,
not as a separate standalone service. These helpers expose the shared ARIS
boundary and the non-copy clause used by ingress and action law.
"""

from __future__ import annotations

from typing import Any, Mapping


ARIS_CONTRACT_VERSION = "aais.aris.v1"
ARIS_RUNTIME_PROFILE = "embedded_governed_repo_intelligence"
ALLOWED_SHARE_MODES = {
    "local_only",
    "signature_only",
    "abstracted",
    "admitted_form_only",
    "comparison_only",
    "reference_only",
}
BLOCKED_SHARE_MODES = {
    "raw",
    "verbatim",
    "full",
    "copy",
    "raw_copy",
}
RAW_COPY_KEYS = (
    "copy_raw_external",
    "share_raw",
    "raw_export",
    "copy_raw",
)
PRIVATE_RUN_KEYS = (
    "copy_private_run",
    "share_private_run",
    "private_export",
)
RAW_CATEGORY_KEYS = (
    "raw_prompts",
    "raw_chat_logs",
    "raw_code",
    "raw_traces",
    "raw_documents",
)


def _clean_text(value: Any, default: str = "") -> str:
    return " ".join(str(value or "").replace("-", "_").split()).strip().lower() or default


def _normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    normalized = _clean_text(value)
    return normalized in {"1", "true", "yes", "on"}


def normalize_non_copy_clause(details: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Return one bounded ARIS non-copy clause state for a request."""

    payload = dict(details or {})
    raw_share_mode = (
        payload.get("pattern_share_mode")
        or payload.get("collective_share_mode")
        or payload.get("export_mode")
        or payload.get("share_mode")
        or payload.get("content_transfer_mode")
    )
    share_mode = _clean_text(raw_share_mode, "local_only")
    aliases = {
        "signature": "signature_only",
        "abstract": "abstracted",
        "admitted": "admitted_form_only",
        "compare": "comparison_only",
        "comparison": "comparison_only",
        "reference": "reference_only",
        "local": "local_only",
        "none": "local_only",
        "verbatim_copy": "verbatim",
        "full_copy": "full",
    }
    share_mode = aliases.get(share_mode, share_mode)

    raw_copy_requested = any(_normalize_bool(payload.get(key)) for key in RAW_COPY_KEYS)
    private_run_requested = any(_normalize_bool(payload.get(key)) for key in PRIVATE_RUN_KEYS)
    raw_categories_requested = [
        key for key in RAW_CATEGORY_KEYS if _normalize_bool(payload.get(key))
    ]

    blocked_mode = share_mode in BLOCKED_SHARE_MODES
    allowed = (
        share_mode in ALLOWED_SHARE_MODES
        and not blocked_mode
        and not raw_copy_requested
        and not private_run_requested
        and not raw_categories_requested
    )
    status = "enforced" if allowed else "blocked"
    summary = (
        "ARIS non-copy clause enforced: raw outside material and private run data stay local; "
        "only admitted, abstracted, or signature-only forms may move forward."
        if allowed
        else "ARIS non-copy clause blocked raw or private material from being copied into "
        "shared truth, implementation authority, or collective flow."
    )
    return {
        "status": status,
        "allowed": allowed,
        "share_mode": share_mode,
        "raw_copy_requested": raw_copy_requested or blocked_mode,
        "private_run_requested": private_run_requested,
        "raw_categories_requested": raw_categories_requested,
        "summary": summary,
    }


def build_aris_enforcement(
    *,
    details: Mapping[str, Any] | None = None,
    runtime_context: str = "live_runtime",
    effectful: bool = False,
    source: str | None = None,
    packet_type: str | None = None,
) -> dict[str, Any]:
    """Build one shared ARIS enforcement envelope for bridge and law surfaces."""

    non_copy_clause = normalize_non_copy_clause(details)
    return {
        "contract_version": ARIS_CONTRACT_VERSION,
        "status": "enforced" if non_copy_clause["allowed"] else "blocked",
        "runtime_profile": ARIS_RUNTIME_PROFILE,
        "authority_model": "embedded_in_aais",
        "execution_boundary": "shared_project_infi_1001",
        "self_apply_changes": False,
        "build_pipeline_role": "artifact_or_world_definition_only",
        "runtime_engine_role": "bounded_live_execution_or_adaptation_only",
        "pattern_learning": {
            "private_run_layer": "local_only",
            "shared_pattern_layer": "signature_only",
            "raw_private_runs_shareable": False,
        },
        "runtime_context": _clean_text(runtime_context, "live_runtime"),
        "effectful": bool(effectful),
        "source": _clean_text(source) or None,
        "packet_type": _clean_text(packet_type) or None,
        "non_copy_clause": non_copy_clause,
    }
