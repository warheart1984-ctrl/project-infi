"""Optional L0 bridge for app/tools.py when tenant+law env is set."""

from __future__ import annotations

import os
from typing import Any

from src.cloud_forge.cache import get_default_cache_store
from src.cloud_forge.types import LawEnvelope


def l0_context_from_env() -> dict[str, str] | None:
    tenant_id = os.environ.get("CLOUD_FORGE_TENANT_ID", "").strip()
    law_id = os.environ.get("CLOUD_FORGE_LAW_ID", "").strip()
    law_version = os.environ.get("CLOUD_FORGE_LAW_VERSION", "").strip()
    if not (tenant_id and law_id and law_version):
        return None
    return {
        "tenant_id": tenant_id,
        "law_id": law_id,
        "law_version": law_version,
    }


def bridge_l0_get(tool_name: str, tool_input: str) -> str | None:
    ctx = l0_context_from_env()
    if not ctx:
        return None
    law = LawEnvelope(law_id=ctx["law_id"], law_version=ctx["law_version"])
    return get_default_cache_store().l0_get(ctx["tenant_id"], law, tool_name, tool_input)


def bridge_l0_set(tool_name: str, tool_input: str, result: str) -> dict[str, Any] | None:
    ctx = l0_context_from_env()
    if not ctx:
        return None
    law = LawEnvelope(law_id=ctx["law_id"], law_version=ctx["law_version"])
    return get_default_cache_store().l0_set(ctx["tenant_id"], law, tool_name, tool_input, result)
