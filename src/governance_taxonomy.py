"""Canonical governance vocabulary shared by mask lowering and training projection."""

from __future__ import annotations

from hashlib import sha256
import json
from typing import Any

from src.cisiv import CISIV_STAGE_SEQUENCE
from src.cog_runtime.formal.output_type_governance import ACTION_TYPE_MEMBERS
from src.governance_ir import EXECUTE_VERBS, PROPOSE_VERBS, SAFE_VERBS

TAXONOMY_SCHEMA_ID = "nova.governance_taxonomy.v1"

AUTHORITY_VERBS: frozenset[str] = frozenset(
    sorted(SAFE_VERBS | PROPOSE_VERBS | EXECUTE_VERBS)
)

GOVERNANCE_ACTION_EXTENSIONS: frozenset[str] = frozenset(
    {
        "subagent_spawn",
        "cisiv_stage_transition",
        "external_mutation",
    }
)

ACTION_TYPES: frozenset[str] = frozenset(
    sorted(ACTION_TYPE_MEMBERS | GOVERNANCE_ACTION_EXTENSIONS)
)

RESOURCE_CLASSES: frozenset[str] = frozenset(
    {
        "session",
        "filesystem",
        "network",
        "provider",
        "subagent",
        "odl",
        "repo",
        "federation",
    }
)

ACTION_CLASSES: frozenset[str] = frozenset({"observe", "propose", "execute"})

VERB_TO_ACTION_CLASS: dict[str, str] = {
    "observe": "observe",
    "respond": "observe",
    "route": "observe",
    "propose": "propose",
    "deliberate": "propose",
    "execute": "execute",
    "mutate": "execute",
    "apply": "execute",
}

ACTION_TYPE_TO_RESOURCE_CLASS: dict[str, str] = {
    "tool_call": "provider",
    "shell_command": "filesystem",
    "file_write": "filesystem",
    "file_delete": "filesystem",
    "network_request": "network",
    "provider_generate": "provider",
    "god_brain_execute": "provider",
    "policy_override": "session",
    "subagent_spawn": "subagent",
    "cisiv_stage_transition": "session",
    "external_mutation": "filesystem",
}

CISIV_STAGE_ALLOWED_ACTION_CLASSES: dict[str, frozenset[str]] = {
    "concept": frozenset({"observe"}),
    "identity": frozenset({"observe", "propose"}),
    "structure": frozenset({"observe", "propose"}),
    "implementation": frozenset({"observe", "propose", "execute"}),
    "verification": frozenset({"observe", "propose"}),
}

OTEM_LEVEL_MAX_ACTION_CLASS: dict[str, str] = {
    "none": "execute",
    "detected": "propose",
    "blocked": "observe",
    "approved": "execute",
}

AUTHORITY_BAND_MAX_ACTION_CLASS: dict[str, str] = {
    "autonomous": "execute",
    "governed": "propose",
    "containment": "observe",
    "sovereign": "observe",
}

TRAINING_LABELS: frozenset[str] = frozenset(
    {"COMPLIANT", "VIOLATION", "BORDERLINE", "ESCALATE"}
)

TRAINING_SOURCES: frozenset[str] = frozenset(
    {
        "odl_trace",
        "synthetic_compliant",
        "synthetic_violation",
        "fuzzed_envelope",
    }
)

TRAINING_USAGE_MODES: frozenset[str] = frozenset(
    {"fine_tuning", "reward_model", "eval_harness"}
)

MASKABLE_SITE_IDS: frozenset[str] = frozenset(
    {
        "tool_call_schema",
        "external_mutation_command",
        "subagent_spawn_descriptor",
        "cisiv_stage_transition",
    }
)


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def taxonomy_fingerprint() -> str:
    payload = {
        "schema_id": TAXONOMY_SCHEMA_ID,
        "authority_verbs": sorted(AUTHORITY_VERBS),
        "action_types": sorted(ACTION_TYPES),
        "resource_classes": sorted(RESOURCE_CLASSES),
        "cisiv_stage_allowed_action_classes": {
            stage: sorted(classes)
            for stage, classes in CISIV_STAGE_ALLOWED_ACTION_CLASSES.items()
        },
        "otem_level_max_action_class": OTEM_LEVEL_MAX_ACTION_CLASS,
        "authority_band_max_action_class": AUTHORITY_BAND_MAX_ACTION_CLASS,
        "training_labels": sorted(TRAINING_LABELS),
    }
    return sha256(_stable_json(payload).encode("utf-8")).hexdigest()[:16]


def action_class_for_verb(verb: str) -> str:
    normalized = str(verb or "").strip().lower()
    return VERB_TO_ACTION_CLASS.get(normalized, "execute")


def allowed_actions_for_stage(stage: str) -> frozenset[str]:
    normalized = str(stage or "implementation").strip().lower()
    if normalized not in CISIV_STAGE_SEQUENCE:
        normalized = "implementation"
    return CISIV_STAGE_ALLOWED_ACTION_CLASSES.get(normalized, frozenset({"observe"}))


def resource_class_for_action(action_type: str) -> str:
    normalized = str(action_type or "").strip().lower()
    return ACTION_TYPE_TO_RESOURCE_CLASS.get(normalized, "session")


def max_action_class_for_otem(otem_level: str) -> str:
    normalized = str(otem_level or "none").strip().lower()
    return OTEM_LEVEL_MAX_ACTION_CLASS.get(normalized, "observe")


def max_action_class_for_authority_band(band: str, *, ceiling_active: bool = False) -> str:
    if ceiling_active:
        return "observe"
    normalized = str(band or "autonomous").strip().lower()
    return AUTHORITY_BAND_MAX_ACTION_CLASS.get(normalized, "observe")


def effective_max_action_class(
    *,
    otem_level: str = "none",
    authority_band: str | None = None,
    ceiling_active: bool = False,
    containment_mode: bool = False,
) -> str:
    """Lowest (most restrictive) max action class from OTEM level and authority band."""
    otem_cap = max_action_class_for_otem(otem_level)
    band = str(authority_band or "autonomous").strip().lower()
    if containment_mode and band not in {"containment", "sovereign"}:
        band = "containment"
    band_cap = max_action_class_for_authority_band(band, ceiling_active=ceiling_active or containment_mode)
    rank = {"observe": 0, "propose": 1, "execute": 2}
    if rank.get(otem_cap, 0) <= rank.get(band_cap, 0):
        return otem_cap
    return band_cap


def normalize_resource_classes(resources: list[str] | tuple[str, ...] | None) -> tuple[str, ...]:
    normalized: list[str] = []
    seen: set[str] = set()
    for item in resources or ():
        value = str(item or "").strip().lower()
        if not value:
            continue
        if value.startswith("session:"):
            value = "session"
        elif value.startswith("federation:"):
            value = "federation"
        elif value.startswith("repo:") or value == "repo":
            value = "repo"
        if value not in RESOURCE_CLASSES:
            value = "session"
        if value in seen:
            continue
        seen.add(value)
        normalized.append(value)
    if not normalized:
        normalized.append("session")
    return tuple(normalized)


def taxonomy_spec() -> dict[str, Any]:
    return {
        "schema_id": TAXONOMY_SCHEMA_ID,
        "taxonomy_fingerprint": taxonomy_fingerprint(),
        "authority_verbs": sorted(AUTHORITY_VERBS),
        "action_types": sorted(ACTION_TYPES),
        "resource_classes": sorted(RESOURCE_CLASSES),
        "action_classes": sorted(ACTION_CLASSES),
        "cisiv_stage_allowed_action_classes": {
            stage: sorted(classes)
            for stage, classes in CISIV_STAGE_ALLOWED_ACTION_CLASSES.items()
        },
        "otem_level_max_action_class": dict(OTEM_LEVEL_MAX_ACTION_CLASS),
        "authority_band_max_action_class": dict(AUTHORITY_BAND_MAX_ACTION_CLASS),
        "training_labels": sorted(TRAINING_LABELS),
        "training_sources": sorted(TRAINING_SOURCES),
        "training_usage_modes": sorted(TRAINING_USAGE_MODES),
        "maskable_site_ids": sorted(MASKABLE_SITE_IDS),
    }
