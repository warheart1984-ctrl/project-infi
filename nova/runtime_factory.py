"""Shared factory for lawful Nova CLI and API runtimes."""

from __future__ import annotations

import os
from typing import Any

from nova.lawful_llm import LawfulLLM, RuntimeSystemLaw
from nova.lsg_loader import ensure_lsg_store, lsg_status
from nova.provider_factory import frontier_provider_status, resolve_frontier_provider

__all__ = ["build_lawful_llm", "collect_runtime_health", "resolve_frontier_provider"]


def build_lawful_llm(
    *,
    operator_session_id: str,
    signing_secret: str,
    tenant_id: str = "local",
) -> LawfulLLM:
    store = ensure_lsg_store(tenant_id=tenant_id)
    law = RuntimeSystemLaw()
    provider = resolve_frontier_provider()
    return LawfulLLM(
        operator_session_id=operator_session_id,
        signing_secret=signing_secret,
        law=law,
        lsg_store=store,
        provider=provider,
    )


def collect_runtime_health() -> dict[str, Any]:
    status = lsg_status()
    return {
        "lsg_loaded": status.get("lsg_loaded", False),
        "bundle_version": status.get("bundle_version"),
        "bundle_id": status.get("bundle_id"),
        "lsg_store_path": status.get("store_path"),
        "lsg_record_count": status.get("record_count", 0),
        "ugr_strict": os.environ.get("NOVA_UGR_STRICT", "").strip().lower() in {"1", "true", "yes"},
        "cvr_store_path": os.environ.get("NOVA_CVR_STORE", "").strip() or None,
        **frontier_provider_status(),
    }
