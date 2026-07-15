"""Wolf metal reboot rehydration harness — single-machine simulation + verification."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.cog_runtime.intent_store import (
    flush_nova_intent_store,
    load_intent_store,
    resolve_intent_store_root,
)
from src.cog_runtime.intent_core import CONSTITUTIONAL_PROTECTED_VALUES
from src.cog_runtime.narrative import NOVA_CORE_IDENTITY
from src.cog_runtime.narrative_store import (
    flush_nova_narrative_store,
    load_narrative_store,
    resolve_narrative_store_root,
)
from src.cogos_runtime_bridge import (
    rehydrate_nova_intent_boot,
    rehydrate_nova_narrative_boot,
    seed_session_nova_intent,
    seed_session_nova_narrative,
)


def _sample_narrative(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "version": "1.0",
        "core_identity": NOVA_CORE_IDENTITY,
        "active_story": "Continuing Wolf metal proof",
        "current_chapter": "INV-1 rehydration",
        "becoming": "proving cross-session continuity",
        "working_on": "metal reboot harness",
        "open_threads": ["metal reboot", "memory membrane"],
        "promises": [],
        "last_growth": "harness wired",
        "continuity_answers": {
            "doing": "metal reboot harness",
            "done": "harness wired",
            "toward": "Continuing Wolf metal proof",
        },
        "turn_delta": {},
        "stages_completed": ["orient", "persist"],
    }
    payload.update(overrides)
    return payload


def _sample_intent(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "version": "0.1",
        "active_commitments": [
            {
                "commitment_id": "inv1-metal-proof",
                "commitment": "Prove narrative and intent survive reboot",
                "status": "active",
                "source": "harness",
                "claim_posture": "asserted",
            }
        ],
        "protected_values": list(CONSTITUTIONAL_PROTECTED_VALUES),
        "long_horizon_goals": ["Persistent continuity"],
        "current_tensions": [],
        "agency_note": "Operator commitments survive reboot (harness fixture).",
        "stages_completed": ["orient", "persist"],
    }
    payload.update(overrides)
    return payload


def simulate_pre_reboot_persist(
    *,
    identity_id: str = "operator",
    store_root: str | Path,
    narrative: dict[str, Any] | None = None,
    intent: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Write narrative + intent as if a companion turn flushed before reboot."""
    root = Path(store_root)
    root.mkdir(parents=True, exist_ok=True)
    narrative_root = root / "nova_narrative"
    intent_root = root / "nova_intent"
    narrative_root.mkdir(parents=True, exist_ok=True)
    intent_root.mkdir(parents=True, exist_ok=True)

    session = type("Session", (), {"metadata": {"nova_face": {"scope": identity_id}, "session_id": "pre-reboot"}})()
    narrative_payload = narrative or _sample_narrative()
    intent_payload = intent or _sample_intent()

    narrative_path = flush_nova_narrative_store(
        session,
        narrative_payload,
        store_root=narrative_root,
    )
    intent_path = flush_nova_intent_store(
        session,
        intent_payload,
        store_root=intent_root,
    )
    return {
        "identity_id": identity_id,
        "narrative_path": str(narrative_path) if narrative_path else "",
        "intent_path": str(intent_path) if intent_path else "",
        "narrative_active_story": narrative_payload.get("active_story"),
        "intent_commitment_count": len(intent_payload.get("active_commitments") or []),
    }


def verify_post_reboot_rehydration(
    *,
    identity_id: str = "operator",
    store_root: str | Path,
    expected_active_story: str | None = None,
    expected_commitment_id: str | None = "inv1-metal-proof",
) -> dict[str, Any]:
    """Simulate post-reboot boot hooks and assert durable stores round-trip."""
    root = Path(store_root)
    narrative_root = root / "nova_narrative"
    intent_root = root / "nova_intent"

    narrative_boot = rehydrate_nova_narrative_boot(identity_id, store_root=narrative_root)
    intent_boot = rehydrate_nova_intent_boot(identity_id, store_root=intent_root)

    issues: list[str] = []
    if not narrative_boot.get("rehydrated"):
        issues.append("narrative_not_rehydrated")
    if not intent_boot.get("rehydrated"):
        issues.append("intent_not_rehydrated")

    active_story = narrative_boot.get("active_story")
    if expected_active_story and active_story != expected_active_story:
        issues.append("active_story_mismatch")

    commitments = list(intent_boot.get("active_commitments") or [])
    if expected_commitment_id:
        ids = set()
        for item in commitments:
            if not isinstance(item, dict):
                continue
            ids.add(str(item.get("commitment_id") or ""))
            ids.add(str(item.get("commitment") or ""))
        if expected_commitment_id not in ids:
            issues.append("commitment_missing")

    seeded = seed_session_nova_narrative(
        {"nova_face": {"scope": identity_id}},
        identity_id,
        store_root=narrative_root,
    )
    seeded_intent = seed_session_nova_intent(
        seeded,
        identity_id,
        store_root=intent_root,
    )
    if not seeded.get("nova_narrative"):
        issues.append("session_narrative_seed_failed")
    if not seeded_intent.get("nova_intent"):
        issues.append("session_intent_seed_failed")

    return {
        "valid": not issues,
        "issues": issues,
        "identity_id": identity_id,
        "narrative_boot": narrative_boot,
        "intent_boot": intent_boot,
        "store_roots": {
            "narrative": str(resolve_narrative_store_root(narrative_root)),
            "intent": str(resolve_intent_store_root(intent_root)),
        },
        "loaded_records": {
            "narrative": load_narrative_store(identity_id, store_root=narrative_root) is not None,
            "intent": load_intent_store(identity_id, store_root=intent_root) is not None,
        },
    }


def run_reboot_round_trip(
    *,
    store_root: str | Path,
    identity_id: str = "operator",
) -> dict[str, Any]:
    """Full pre-reboot persist → post-reboot verify cycle."""
    pre = simulate_pre_reboot_persist(identity_id=identity_id, store_root=store_root)
    post = verify_post_reboot_rehydration(
        identity_id=identity_id,
        store_root=store_root,
        expected_active_story=pre.get("narrative_active_story"),
    )
    return {
        "claim_label": "asserted" if post["valid"] else "rejected",
        "pre_reboot": pre,
        "post_reboot": post,
    }


def export_rehydration_snapshot(path: str | Path, payload: dict[str, Any]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target
