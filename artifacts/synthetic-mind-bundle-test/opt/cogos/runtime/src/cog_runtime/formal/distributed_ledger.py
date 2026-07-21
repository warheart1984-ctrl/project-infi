"""Distributed ledger sketch — vector-clock merge for cross-machine continuity (debt reducer)."""

from __future__ import annotations

from typing import Any


def vector_clock_tick(clock: dict[str, int], node_id: str) -> dict[str, int]:
    updated = {str(k): int(v) for k, v in (clock or {}).items()}
    updated[str(node_id)] = updated.get(str(node_id), 0) + 1
    return updated


def vector_clock_merge(left: dict[str, int], right: dict[str, int]) -> dict[str, int]:
    keys = set(left or {}) | set(right or {})
    return {key: max(int((left or {}).get(key, 0)), int((right or {}).get(key, 0))) for key in keys}


def compare_vector_clocks(a: dict[str, int], b: dict[str, int]) -> str:
    """Return concurrent|a_before_b|b_before_a|equal."""
    a = {str(k): int(v) for k, v in (a or {}).items()}
    b = {str(k): int(v) for k, v in (b or {}).items()}
    keys = set(a) | set(b)
    a_le_b = all(a.get(k, 0) <= b.get(k, 0) for k in keys)
    b_le_a = all(b.get(k, 0) <= a.get(k, 0) for k in keys)
    if a_le_b and b_le_a:
        return "equal"
    if a_le_b and not b_le_a:
        return "a_before_b"
    if b_le_a and not a_le_b:
        return "b_before_a"
    return "concurrent"


def merge_ledger_entries(
    local: list[dict[str, Any]],
    remote: list[dict[str, Any]],
    *,
    node_id: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Merge two ledger fragments by (vector_clock, trace_id).
    Concurrent entries from different nodes are both retained (append-only union).
    """
    merged: dict[str, dict[str, Any]] = {}
    for entry in list(local or []) + list(remote or []):
        if not isinstance(entry, dict):
            continue
        trace_id = str(entry.get("trace_id") or "")
        runtime_id = str(entry.get("runtime_id") or "")
        key = f"{runtime_id}:{trace_id}" if trace_id else f"{runtime_id}:{len(merged)}"
        existing = merged.get(key)
        if existing is None:
            merged[key] = dict(entry)
            continue
        left_clock = dict(existing.get("vector_clock") or {})
        right_clock = dict(entry.get("vector_clock") or {})
        order = compare_vector_clocks(left_clock, right_clock)
        if order in {"equal", "a_before_b"}:
            merged[key] = dict(entry)
        elif order == "b_before_a":
            merged[key] = dict(existing)
        else:
            alt_key = f"{key}:remote:{len(merged)}"
            merged[alt_key] = dict(entry)

    clock = vector_clock_tick({}, node_id)
    for entry in merged.values():
        entry_clock = dict(entry.get("vector_clock") or {})
        clock = vector_clock_merge(clock, entry_clock)

    ordered = sorted(
        merged.values(),
        key=lambda item: (str(item.get("started_at") or ""), str(item.get("trace_id") or "")),
    )
    report = {
        "merged_count": len(ordered),
        "local_count": len(local or []),
        "remote_count": len(remote or []),
        "vector_clock": clock,
        "policy_id": "nova.distributed_ledger.v1",
    }
    return ordered, report


def validate_ledger_monotonicity(
    local: list[dict[str, Any]],
    remote: list[dict[str, Any]],
    merged: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Invariant: merged ledger is append-only and order-consistent with inputs.
    L' = merge(L1, L2) ⇒ every local/remote trace_id preserved; merged length ≥ max(|L1|, |L2|).
    """
    local_ids = [str(item.get("trace_id") or "") for item in local or [] if isinstance(item, dict)]
    remote_ids = [str(item.get("trace_id") or "") for item in remote or [] if isinstance(item, dict)]
    merged_ids = [str(item.get("trace_id") or "") for item in merged or [] if isinstance(item, dict)]
    issues: list[str] = []

    for trace_id in local_ids:
        if trace_id and trace_id not in merged_ids:
            issues.append(f"missing_local:{trace_id}")
    for trace_id in remote_ids:
        if trace_id and trace_id not in merged_ids:
            issues.append(f"missing_remote:{trace_id}")
    if len(merged) < max(len(local or []), len(remote or [])):
        issues.append("merged_shorter_than_inputs")

    return {
        "valid": not issues,
        "issues": issues,
        "local_count": len(local or []),
        "remote_count": len(remote or []),
        "merged_count": len(merged or []),
        "policy_id": "nova.ledger_monotonic.v1",
    }


def stamp_ledger_entry(entry: dict[str, Any], *, node_id: str) -> dict[str, Any]:
    stamped = dict(entry)
    clock = dict(stamped.get("vector_clock") or {})
    stamped["vector_clock"] = vector_clock_tick(clock, node_id)
    return stamped


def merge_ledger_entries_monotonic(
    local: list[dict[str, Any]],
    remote: list[dict[str, Any]],
    *,
    node_id: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    merged, report = merge_ledger_entries(local, remote, node_id=node_id)
    monotonic = validate_ledger_monotonicity(local, remote, merged)
    report["monotonic"] = monotonic
    if not monotonic.get("valid"):
        report["status"] = "monotonicity_violation"
    else:
        report["status"] = "ok"
    return merged, report
