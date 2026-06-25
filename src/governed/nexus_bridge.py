"""Step 4 — Emit Nexus execution events for ops-console observability."""

from __future__ import annotations

from typing import Any

from src.governed.adapters import get_nexus_record_adapter
from src.governed.config import GovernedRuntimeConfig, get_governed_config


def emit_nexus_event(
    aaes_receipt: dict[str, Any],
    *,
    config: GovernedRuntimeConfig | None = None,
) -> dict[str, Any]:
    """Emit a Nexus execution event from an AAES receipt."""
    cfg = config or get_governed_config()
    adapter = get_nexus_record_adapter(cfg.nexus_record_mode)
    return adapter.record_execution(aaes_receipt)
