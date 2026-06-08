"""Immune Resilience Organ — defend, heal, and harden posture snapshot."""

# Mythic: Immune Resilience Organ
# Engineering: ImmuneResilienceEngine
from __future__ import annotations

from typing import Any

from src.immune_system import immune_system

MODULE_ID = "AAIS-IR-01"
ORGAN_VERSION = "immune_resilience_organ.v1"


def build_immune_resilience_status() -> dict[str, Any]:
    """Bounded immune resilience snapshot; defensive-only heal and harden cycle."""
    snapshot = immune_system.snapshot(limit_events=4, limit_incidents=2)
    hardening = dict(snapshot.get("hardening") or {})
    eligibility = dict(snapshot.get("heal_eligible") or immune_system.evaluate_heal_eligibility())
    mode = str(snapshot.get("system_mode") or "normal")
    generation = int(snapshot.get("defense_generation") or hardening.get("defense_generation") or 0)
    clean_streak = int(snapshot.get("clean_streak") or 0)
    summary = (
        f"mode={mode};gen={generation};streak={clean_streak};"
        f"heal={bool(eligibility.get('eligible'))};defensive_only=True"
    )[:128]
    return {
        "immune_resilience_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "system_mode": mode,
        "defense_generation": generation,
        "clean_streak": clean_streak,
        "auto_heal_enabled": bool(snapshot.get("auto_heal_enabled", True)),
        "last_heal_at": snapshot.get("last_heal_at"),
        "last_threat_at": snapshot.get("last_threat_at"),
        "heal_eligible": bool(eligibility.get("eligible")),
        "heal_eligibility_reason": str(eligibility.get("reason") or "")[:120] or None,
        "threat_memory_count": int(hardening.get("threat_memory_count") or 0),
        "summary_char_limit": int(hardening.get("summary_char_limit") or 180),
        "defensive_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
