"""Formal ledger entry schema, compression, and retention policy."""

from __future__ import annotations

from typing import Any

LEDGER_ENTRY_SCHEMA_V1: dict[str, Any] = {
    "schema_id": "nova.ledger.entry.v1",
    "required_fields": (
        "runtime_id",
        "stage",
        "trace_id",
        "started_at",
        "ended_at",
        "payload",
        "result",
    ),
    "field_types": {
        "runtime_id": "string",
        "stage": "string",
        "trace_id": "string",
        "started_at": "iso8601_utc",
        "ended_at": "iso8601_utc|null",
        "payload": "object",
        "result": "object",
    },
    "payload_rules": {
        "max_keys": 32,
        "forbidden_keys": ("raw_provider_response", "full_system_prompt"),
        "summary_fields": ("user_message_hash", "frame_kind", "focus_primary"),
    },
    "result_rules": {
        "max_keys": 48,
        "artifact_pointer_fields": ("artifact_key", "artifact_version"),
    },
    "rationale": (
        "Each stage record e_i = (stage, timestamp, input, output, rationale) maps to "
        "StageRecord with payload≈input, result≈output, trace_id+timestamps≈audit metadata."
    ),
}

LEDGER_COMPRESSION_POLICY: dict[str, Any] = {
    "policy_id": "nova.ledger.compression.v1",
    "full_store": ("decision_object", "intent_artifact", "narrative_artifact"),
    "summarize": (
        "user_message",
        "speak_body",
        "provider_messages",
    ),
    "summary_max_chars": 512,
    "hash_instead_of_body": ("user_message",),
    "drop_from_ledger": ("raw_embeddings", "intermediate_scores"),
}

LEDGER_RETENTION_POLICY: dict[str, Any] = {
    "policy_id": "nova.ledger.retention.v1",
    "per_turn_max_entries": 128,
    "session_metadata_max_turns": 64,
    "persistent_store": ("intent", "narrative", "arc"),
    "ephemeral_ttl_turns": 8,
    "compaction_trigger_entries": 256,
}


def validate_ledger_entry(entry: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    for field in LEDGER_ENTRY_SCHEMA_V1["required_fields"]:
        if field not in entry:
            issues.append(f"missing:{field}")
    payload = entry.get("payload")
    if payload is not None and not isinstance(payload, dict):
        issues.append("payload_not_object")
    result = entry.get("result")
    if result is not None and not isinstance(result, dict):
        issues.append("result_not_object")
    if isinstance(payload, dict):
        rules = LEDGER_ENTRY_SCHEMA_V1["payload_rules"]
        if len(payload) > int(rules["max_keys"]):
            issues.append("payload_too_large")
        for key in rules["forbidden_keys"]:
            if key in payload:
                issues.append(f"forbidden_payload:{key}")
    return {"valid": not issues, "issues": issues, "schema_id": LEDGER_ENTRY_SCHEMA_V1["schema_id"]}


def compress_ledger_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Apply compression policy to one ledger entry (non-destructive copy)."""
    compressed = dict(entry)
    payload = dict(compressed.get("payload") or {})
    result = dict(compressed.get("result") or {})
    max_chars = int(LEDGER_COMPRESSION_POLICY["summary_max_chars"])

    for key in LEDGER_COMPRESSION_POLICY["summarize"]:
        if key in payload and isinstance(payload[key], str) and len(payload[key]) > max_chars:
            payload[key] = payload[key][: max_chars - 1] + "…"
        if key in result and isinstance(result[key], str) and len(result[key]) > max_chars:
            result[key] = result[key][: max_chars - 1] + "…"

    for key in LEDGER_COMPRESSION_POLICY["drop_from_ledger"]:
        payload.pop(key, None)
        result.pop(key, None)

    compressed["payload"] = payload
    compressed["result"] = result
    compressed["compression_policy"] = LEDGER_COMPRESSION_POLICY["policy_id"]
    return compressed
