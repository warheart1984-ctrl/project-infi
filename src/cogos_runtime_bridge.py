"""CoG OS ↔ AAIS cognitive runtime bridge."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.cog_runtime import cognitive_runtime_family_spec, export_family_json, nova_cortex_spec
from src.cog_runtime.capability_governance import validate_nova_cortex_capability_governance
from src.cog_runtime.intent_store import (
    load_intent_store,
    rehydrate_nova_intent,
    resolve_intent_store_root,
)
from src.cog_runtime.narrative_store import (
    load_narrative_store,
    rehydrate_nova_narrative,
    resolve_narrative_store_root,
)
from src.cog_runtime.nova import nova_cognitive_router, run_nova_cognitive_turn
from src.speaking_runtime import infer_frame_kind

DEFAULT_FAMILY_PATH = Path("/opt/cogos/config/cognitive_runtime_family.json")


def load_family_config(path: str | Path | None = None) -> dict[str, Any]:
    target = Path(path) if path is not None else DEFAULT_FAMILY_PATH
    if target.is_file():
        return json.loads(target.read_text(encoding="utf-8-sig"))
    return nova_cortex_spec()


def resolve_active_runtimes(turn_context: dict[str, Any]) -> list[str]:
    return nova_cognitive_router(turn_context)


def build_turn_envelope(
    user_message: str,
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ctx = dict(context or {})
    if "frame_kind" not in ctx:
        ctx["frame_kind"] = infer_frame_kind(user_message)
    active = resolve_active_runtimes(
        {
            "user_message": user_message,
            **ctx,
        }
    )
    session = run_nova_cognitive_turn(user_message, context=ctx)
    return {
        "family_id": cognitive_runtime_family_spec()["family_id"],
        "active_runtimes": active,
        "frame_kind": session.frame_kind,
        "artifacts": dict(session.artifacts),
        "ledger": list(session.ledger),
        "session": session.to_dict(),
    }


def family_spec() -> dict[str, Any]:
    return nova_cortex_spec()


def validate_family_config(config: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    if not config.get("family_id"):
        issues.append("missing_family_id")
    elif config.get("family_id") not in {"nova.cortex", "nova.cognitive.family"}:
        issues.append("unexpected_family_id")
    runtimes = config.get("runtimes")
    if not isinstance(runtimes, list) or not runtimes:
        issues.append("missing_runtimes")
    else:
        for runtime in runtimes:
            if not isinstance(runtime, dict):
                issues.append("invalid_runtime_entry")
                break
            if not runtime.get("id"):
                issues.append("runtime_missing_id")
                break
    capability = validate_nova_cortex_capability_governance(config)
    if not capability["valid"]:
        issues.extend(capability["issues"])
    return {"valid": not issues, "issues": issues, "capability_governance": capability}


def rehydrate_nova_narrative_boot(
    narrative_id: str,
    *,
    store_root: str | Path | None = None,
) -> dict[str, Any]:
    """Wolf boot hook: load identity-bound narrative for session seeding."""
    root = resolve_narrative_store_root(store_root)
    record = load_narrative_store(narrative_id, store_root=root)
    if not record:
        return {"rehydrated": False, "narrative_id": narrative_id, "store_root": str(root)}
    narrative = dict(record.get("narrative") or {})
    return {
        "rehydrated": True,
        "narrative_id": narrative_id,
        "store_root": str(root),
        "active_story": narrative.get("active_story"),
        "current_chapter": narrative.get("current_chapter"),
        "continuity_answers": narrative.get("continuity_answers"),
        "turn_count": record.get("turn_count"),
        "updated_at": record.get("updated_at"),
        "narrative": narrative,
    }


def seed_session_nova_narrative(
    session_metadata: dict[str, Any],
    narrative_id: str,
    *,
    store_root: str | Path | None = None,
) -> dict[str, Any]:
    """Apply boot rehydration payload to a Jarvis session metadata dict."""
    session = type("SessionSeed", (), {"metadata": dict(session_metadata or {})})()
    session.metadata["nova_narrative_id"] = narrative_id
    rehydrate_nova_narrative(
        session,
        store_root=resolve_narrative_store_root(store_root),
        nova_face=session.metadata.get("nova_face"),
    )
    return dict(session.metadata)


def rehydrate_nova_intent_boot(
    intent_id: str,
    *,
    store_root: str | Path | None = None,
) -> dict[str, Any]:
    """Wolf boot hook: load identity-bound intent for session seeding."""
    root = resolve_intent_store_root(store_root)
    record = load_intent_store(intent_id, store_root=root)
    if not record:
        return {"rehydrated": False, "intent_id": intent_id, "store_root": str(root)}
    intent = dict(record.get("intent") or {})
    return {
        "rehydrated": True,
        "intent_id": intent_id,
        "store_root": str(root),
        "agency_note": intent.get("agency_note"),
        "active_commitments": intent.get("active_commitments"),
        "current_tensions": intent.get("current_tensions"),
        "turn_count": record.get("turn_count"),
        "updated_at": record.get("updated_at"),
        "intent": intent,
    }


def seed_session_nova_intent(
    session_metadata: dict[str, Any],
    intent_id: str,
    *,
    store_root: str | Path | None = None,
) -> dict[str, Any]:
    """Apply boot rehydration payload to a Jarvis session metadata dict."""
    session = type("SessionSeed", (), {"metadata": dict(session_metadata or {})})()
    session.metadata["nova_intent_id"] = intent_id
    rehydrate_nova_intent(
        session,
        store_root=resolve_intent_store_root(store_root),
        nova_face=session.metadata.get("nova_face"),
    )
    return dict(session.metadata)


def rehydrate_boot_combined(
    identity_id: str,
    *,
    narrative_store_root: str | Path | None = None,
    intent_store_root: str | Path | None = None,
) -> dict[str, Any]:
    """Combined Wolf boot rehydration for narrative + intent."""
    narrative = rehydrate_nova_narrative_boot(
        identity_id,
        store_root=narrative_store_root,
    )
    intent = rehydrate_nova_intent_boot(
        identity_id,
        store_root=intent_store_root,
    )
    return {
        "identity_id": identity_id,
        "narrative": narrative,
        "intent": intent,
        "rehydrated": bool(narrative.get("rehydrated") and intent.get("rehydrated")),
    }


def build_ceiling_safe_mode_status(*, scope_id: str | None = None) -> dict[str, Any]:
    """Advisory safe-mode reanchor status for OTEM Level 20 recovery."""
    scope = str(scope_id or "global").strip() or "global"
    family = load_family_config()
    return {
        "status": "safe_mode",
        "scope_id": scope,
        "family_id": family.get("family_id"),
        "active_runtimes": ["nova_cortex"],
        "reanchor": {
            "narrative_store": str(resolve_narrative_store_root()),
            "intent_store": str(resolve_intent_store_root()),
            "frame_kind": "governance_recovery",
        },
        "runtime_effect": "advisory_only",
        "summary": "CoG OS safe-mode reanchor projection — operator must confirm before apply.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CoG OS cognitive runtime bridge")
    parser.add_argument("--spec", action="store_true", help="Print family spec JSON")
    parser.add_argument("--export", type=str, help="Export family JSON to path")
    parser.add_argument("--validate-config", type=str, help="Validate family JSON file")
    parser.add_argument("--rehydrate-narrative", metavar="ID", help="Boot rehydrate narrative store")
    parser.add_argument("--rehydrate-intent", metavar="ID", help="Boot rehydrate intent store")
    parser.add_argument("--rehydrate-boot", metavar="ID", help="Boot rehydrate narrative + intent")
    parser.add_argument("--narrative-store", default="", help="Override narrative store root")
    parser.add_argument("--intent-store", default="", help="Override intent store root")
    parser.add_argument(
        "--verify-rehydration",
        metavar="STORE_ROOT",
        help="Run INV-1 reboot round-trip harness against store root",
    )
    args = parser.parse_args(argv)

    narrative_root = args.narrative_store or None
    intent_root = args.intent_store or None

    if args.spec:
        print(json.dumps(family_spec(), indent=2, sort_keys=True))
        return 0
    if args.export:
        path = export_family_json(args.export)
        print(path)
        return 0
    if args.validate_config:
        config = load_family_config(args.validate_config)
        result = validate_family_config(config)
        print(json.dumps(result, indent=2))
        return 0 if result["valid"] else 1
    if args.rehydrate_narrative:
        payload = rehydrate_nova_narrative_boot(
            args.rehydrate_narrative,
            store_root=narrative_root,
        )
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if payload.get("rehydrated") else 1
    if args.rehydrate_intent:
        payload = rehydrate_nova_intent_boot(
            args.rehydrate_intent,
            store_root=intent_root,
        )
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if payload.get("rehydrated") else 1
    if args.rehydrate_boot:
        payload = rehydrate_boot_combined(
            args.rehydrate_boot,
            narrative_store_root=narrative_root,
            intent_store_root=intent_root,
        )
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if payload.get("rehydrated") else 1
    if args.verify_rehydration:
        from src.cog_runtime.wolf_rehydration_harness import run_reboot_round_trip

        payload = run_reboot_round_trip(store_root=args.verify_rehydration)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if payload.get("post_reboot", {}).get("valid") else 1
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
