"""Cross-run temporal replay comparison."""

from __future__ import annotations

from typing import Any

from src.temporal_replay.event import summarize_event
from src.temporal_replay.timeline import build_timeline


def compare_runs(
    left: dict[str, str],
    right: dict[str, str],
    *,
    align_by: str = "sequence",
) -> dict[str, Any]:
    left_type = str(left.get("subject_type") or "")
    left_id = str(left.get("subject_id") or "")
    right_type = str(right.get("subject_type") or "")
    right_id = str(right.get("subject_id") or "")

    left_tl = build_timeline(left_type, left_id)
    right_tl = build_timeline(right_type, right_id)

    left_events = left_tl.get("events") or []
    right_events = right_tl.get("events") or []

    if align_by == "goal_hash":
        pairs = _align_by_goal_hash(left_events, right_events)
    else:
        pairs = _align_by_sequence(left_events, right_events)

    diffs = []
    for index, (le, re) in enumerate(pairs):
        if not le and not re:
            continue
        lsum = summarize_event(le) if le else {}
        rsum = summarize_event(re) if re else {}
        if lsum.get("kind") != rsum.get("kind") or lsum.get("summary") != rsum.get("summary"):
            diffs.append({"index": index, "left": lsum, "right": rsum, "delta": "diverged"})
        else:
            diffs.append({"index": index, "left": lsum, "right": rsum, "delta": "match"})

    diverged = sum(1 for d in diffs if d.get("delta") == "diverged")
    return {
        "left": {"subject_type": left_type, "subject_id": left_id, "event_count": len(left_events)},
        "right": {"subject_type": right_type, "subject_id": right_id, "event_count": len(right_events)},
        "align_by": align_by,
        "pair_count": len(pairs),
        "diverged_count": diverged,
        "pairs": diffs[:100],
        "runtime_effect": "readout_only",
    }


def _align_by_sequence(
    left: list[dict[str, Any]],
    right: list[dict[str, Any]],
) -> list[tuple[dict[str, Any] | None, dict[str, Any] | None]]:
    max_len = max(len(left), len(right), 0)
    pairs: list[tuple[dict[str, Any] | None, dict[str, Any] | None]] = []
    for i in range(max_len):
        pairs.append((left[i] if i < len(left) else None, right[i] if i < len(right) else None))
    return pairs


def _align_by_goal_hash(
    left: list[dict[str, Any]],
    right: list[dict[str, Any]],
) -> list[tuple[dict[str, Any] | None, dict[str, Any] | None]]:
    left_receipts = [e for e in left if e.get("kind") == "mission_receipt"]
    right_receipts = [e for e in right if e.get("kind") == "mission_receipt"]
    if left_receipts or right_receipts:
        return _align_by_sequence(left, right)
    return _align_by_sequence(left, right)
