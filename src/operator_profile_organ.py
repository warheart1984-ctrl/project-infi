"""Operator Profile Organ — normalized operator identity and authority lane."""

# Mythic: Operator Profile Organ
# Engineering: OperatorProfileEngine
from __future__ import annotations

from typing import Any

from src.knowledge_authority import OPERATOR_AUTHORITY_SOURCES, KnowledgeAuthority


def build_operator_profile(
    knowledge_authority: KnowledgeAuthority | None = None,
    *,
    profile_id: str = "operator",
) -> dict[str, Any]:
    _ = knowledge_authority or KnowledgeAuthority()
    sources = list(OPERATOR_AUTHORITY_SOURCES)
    return {
        "operator_profile_organ_version": "operator_profile_organ.v1",
        "profile_id": profile_id or "operator",
        "authority_lane": "operator",
        "capabilities": sources,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "authority_source_count": len(sources),
        "read_only": True,
    }
