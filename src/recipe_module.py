"""Recipe Module — governed workflow recipe packs for Mission Board admission."""

# Mythic: Recipe Module Organ
# Engineering: RecipeModuleEngine
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.cisiv import CISIV_STAGE_SEQUENCE, normalize_cisiv_stage

RECIPE_VERSION = "recipe_module.v1"
DEFAULT_RECIPE_ROOT = Path(".runtime/recipe_module")
FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "tools" / "recipe" / "fixtures"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "recipe_module.v1.json"

REQUIRED_TOP = frozenset(
    {
        "recipe_module_version",
        "recipe_id",
        "recipe_name",
        "steps",
        "gates",
        "cisiv_stage",
        "claim_label",
        "created_at_utc",
    }
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def recipe_root(root: Path | None = None) -> Path:
    return (root or DEFAULT_RECIPE_ROOT).expanduser().resolve()


def recipe_dir(recipe_id: str, *, root: Path | None = None) -> Path:
    return recipe_root(root) / recipe_id


def pack_path(recipe_id: str, *, root: Path | None = None) -> Path:
    return recipe_dir(recipe_id, root=root) / "recipe_module.v1.json"


def ledger_path(recipe_id: str, *, root: Path | None = None) -> Path:
    return recipe_dir(recipe_id, root=root) / "execution_ledger.jsonl"


def resolve_fixture_path(recipe_id: str) -> Path | None:
    candidate = FIXTURE_ROOT / f"{recipe_id}.json"
    return candidate if candidate.is_file() else None


def load_recipe_pack(path: str | Path) -> dict[str, Any]:
    resolved = Path(path).expanduser().resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"recipe pack not found: {resolved}")
    pack = json.loads(resolved.read_text(encoding="utf-8"))
    validate_pack(pack)
    return pack


def load_recipe_by_id(recipe_id: str, *, root: Path | None = None) -> dict[str, Any]:
    rid = str(recipe_id or "").strip()
    if not rid:
        raise ValueError("recipe_id is required")
    fixture = resolve_fixture_path(rid)
    if fixture is not None:
        return load_recipe_pack(fixture)
    runtime_pack = pack_path(rid, root=root)
    if runtime_pack.is_file():
        return load_recipe_pack(runtime_pack)
    raise FileNotFoundError(f"recipe pack not found for id: {rid}")


def validate_pack(pack: dict[str, Any]) -> None:
    if not isinstance(pack, dict):
        raise ValueError("recipe pack must be an object")
    missing = sorted(REQUIRED_TOP - set(pack.keys()))
    if missing:
        raise ValueError(f"recipe pack missing required fields: {', '.join(missing)}")
    if pack.get("recipe_module_version") != RECIPE_VERSION:
        raise ValueError(f"recipe_module_version must be {RECIPE_VERSION}")
    if not str(pack.get("recipe_id") or "").strip():
        raise ValueError("recipe_id is required")
    steps = pack.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError("steps must be a non-empty array")
    for step in steps:
        if not isinstance(step, dict):
            raise ValueError("each step must be an object")
        for key in ("step_id", "step_order", "action", "claim_label"):
            if key not in step:
                raise ValueError(f"step missing {key}")
    gates = pack.get("gates")
    if not isinstance(gates, list):
        raise ValueError("gates must be an array")
    for gate in gates:
        if not isinstance(gate, dict):
            raise ValueError("each gate must be an object")
        if "gate_id" not in gate or "gate_type" not in gate:
            raise ValueError("gate missing gate_id or gate_type")
    if pack.get("claim_label") not in {"asserted", "proven", "rejected"}:
        raise ValueError("invalid claim_label")


def evaluate_gates(
    pack: dict[str, Any],
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return gate evaluation summary; passed=False blocks mission admission."""
    ctx = dict(context or {})
    signoff_ack = bool(ctx.get("signoff_ack"))
    results: list[dict[str, Any]] = []
    passed = True
    for gate in pack.get("gates") or []:
        gate_id = str(gate.get("gate_id") or "")
        gate_type = str(gate.get("gate_type") or "")
        gate_passed = True
        reason = "ok"
        if gate_type == "human_signoff":
            if pack.get("signoff_required", True) and not signoff_ack:
                gate_passed = False
                reason = "human_signoff_required"
        elif gate_type == "schema_valid":
            schema_name = (gate.get("parameters") or {}).get("schema")
            if schema_name and not SCHEMA_PATH.name == schema_name:
                if not (Path(__file__).resolve().parents[1] / "schemas" / schema_name).is_file():
                    gate_passed = False
                    reason = f"schema_not_found:{schema_name}"
        elif gate_type == "make_target":
            if ctx.get("skip_make_target"):
                gate_passed = True
            elif not ctx.get("make_target_ok", True):
                gate_passed = False
                reason = "make_target_failed"
        elif gate_type == "cisiv_stage_min":
            minimum = (gate.get("parameters") or {}).get("minimum", "concept")
            current = normalize_cisiv_stage(pack.get("cisiv_stage"), default="concept")
            try:
                gate_passed = CISIV_STAGE_SEQUENCE.index(current) >= CISIV_STAGE_SEQUENCE.index(
                    normalize_cisiv_stage(minimum, default="concept")
                )
            except ValueError:
                gate_passed = False
            if not gate_passed:
                reason = f"cisiv_stage_below:{minimum}"
        results.append(
            {
                "gate_id": gate_id,
                "gate_type": gate_type,
                "passed": gate_passed,
                "reason": reason,
            }
        )
        if not gate_passed:
            passed = False
    return {"passed": passed, "gates": results}


def draft_mission_fields(pack: dict[str, Any]) -> dict[str, Any]:
    first_step = sorted(pack.get("steps") or [], key=lambda s: int(s.get("step_order", 0)))[0]
    last_step = sorted(pack.get("steps") or [], key=lambda s: int(s.get("step_order", 0)))[-1]
    description = str(pack.get("description") or pack.get("recipe_name") or "").strip()
    return {
        "title": str(pack.get("recipe_name") or pack.get("recipe_id")),
        "objective": description or str(first_step.get("action") or "Recipe mission"),
        "next_step": str(last_step.get("action") or first_step.get("action") or ""),
        "tags": ["recipe_module", str(pack.get("recipe_id"))],
        "cisiv_stage": pack.get("cisiv_stage"),
    }


def persist_pack(pack: dict[str, Any], *, root: Path | None = None) -> Path:
    validate_pack(pack)
    recipe_id = str(pack["recipe_id"])
    path = pack_path(recipe_id, root=root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(pack)
    payload["updated_at_utc"] = _utc_now_iso()
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def append_ledger(recipe_id: str, event: dict[str, Any], *, root: Path | None = None) -> Path:
    path = ledger_path(recipe_id, root=root)
    path.parent.mkdir(parents=True, exist_ok=True)
    record = dict(event)
    record.setdefault("recorded_at_utc", _utc_now_iso())
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    return path


def content_hash(pack: dict[str, Any]) -> str:
    raw = json.dumps(pack, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def seed_fixture_to_runtime(recipe_id: str, *, root: Path | None = None) -> Path:
    pack = load_recipe_by_id(recipe_id)
    return persist_pack(pack, root=root)


__all__ = [
    "RECIPE_VERSION",
    "FIXTURE_ROOT",
    "append_ledger",
    "content_hash",
    "draft_mission_fields",
    "evaluate_gates",
    "load_recipe_by_id",
    "load_recipe_pack",
    "persist_pack",
    "resolve_fixture_path",
    "seed_fixture_to_runtime",
    "validate_pack",
]
