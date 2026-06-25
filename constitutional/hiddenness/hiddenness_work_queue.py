"""Hiddenness work queue — canonical backlog of implicit / undocumented knowledge."""

from __future__ import annotations

import hashlib
import sys
from datetime import UTC, datetime
from typing import IO, Literal

from pydantic import BaseModel, Field

from constitutional.core.models import StateObject
from constitutional.hiddenness.hiddenness_runtime import HiddennessState
from constitutional.runtime.runtime import ConstitutionalStateRuntime

HIDDENNESS_WORK_QUEUE_STATE_ID = "hiddenness_work_queue"

WorkItemKind = Literal[
    "assumption",
    "invariant",
    "invariant_drift",
    "purpose_fragment",
    "authority",
    "context",
    "constraint",
    "semantic_mismatch",
    "lineage_gap",
    "founder_knowledge",
]
WorkItemSeverity = Literal["low", "medium", "high", "critical"]
WorkItemStatus = Literal["open", "in_progress", "resolved"]
WorkItemSource = Literal[
    "HiddennessRuntimeV2",
    "HiddennessRuntime",
    "ColdStart",
    "MissionFidelity",
    "Fitness",
]

SEVERITY_BY_KIND: dict[WorkItemKind, WorkItemSeverity] = {
    "assumption": "high",
    "invariant": "critical",
    "invariant_drift": "high",
    "purpose_fragment": "high",
    "authority": "critical",
    "context": "medium",
    "constraint": "medium",
    "semantic_mismatch": "high",
    "lineage_gap": "high",
    "founder_knowledge": "critical",
}


class HiddennessWorkItem(BaseModel):
    """Atomic unit of hiddenness — one implicit or undocumented piece of knowledge."""

    item_id: str
    kind: WorkItemKind
    description: str
    source: WorkItemSource
    severity: WorkItemSeverity
    related_invariants: list[str] = Field(default_factory=list)
    related_purpose: list[str] = Field(default_factory=list)
    related_states: list[str] = Field(default_factory=list)
    related_receipts: list[str] = Field(default_factory=list)
    created_at: datetime
    last_seen_at: datetime
    status: WorkItemStatus = "open"
    resolution_receipt: str | None = None


class HiddennessWorkQueue(BaseModel):
    """Backlog of hiddenness work items — lives in the constitutional state registry."""

    queue_id: str = HIDDENNESS_WORK_QUEUE_STATE_ID
    state_id: str = HIDDENNESS_WORK_QUEUE_STATE_ID
    state_type: str = "hiddenness_work_queue"
    items: dict[str, HiddennessWorkItem] = Field(default_factory=dict)

    def add(self, item: HiddennessWorkItem) -> HiddennessWorkItem:
        self.items[item.item_id] = item
        return item

    def upsert(self, item: HiddennessWorkItem) -> HiddennessWorkItem:
        """Add or refresh last_seen for an open item with the same stable id."""
        existing = self.items.get(item.item_id)
        if existing is None:
            return self.add(item)
        if existing.status == "resolved":
            return existing
        existing.last_seen_at = item.last_seen_at
        existing.source = item.source
        existing.severity = item.severity
        existing.related_invariants = list(
            dict.fromkeys(existing.related_invariants + item.related_invariants)
        )
        existing.related_purpose = list(dict.fromkeys(existing.related_purpose + item.related_purpose))
        existing.related_states = list(dict.fromkeys(existing.related_states + item.related_states))
        existing.related_receipts = list(dict.fromkeys(existing.related_receipts + item.related_receipts))
        if existing.status == "open" and item.status == "in_progress":
            existing.status = "in_progress"
        return existing

    def update_last_seen(self, item_id: str, now: datetime) -> None:
        item = self.items[item_id]
        item.last_seen_at = now

    def mark_in_progress(self, item_id: str, *, now: datetime | None = None) -> None:
        item = self.items[item_id]
        item.status = "in_progress"
        item.last_seen_at = now or datetime.now(UTC).replace(microsecond=0)

    def resolve(self, item_id: str, receipt_id: str) -> HiddennessWorkItem:
        item = self.items[item_id]
        item.status = "resolved"
        item.resolution_receipt = receipt_id
        return item

    def unresolved(self) -> list[HiddennessWorkItem]:
        return [item for item in self.items.values() if item.status != "resolved"]

    def unresolved_count(self) -> int:
        return len(self.unresolved())


def stable_work_item_id(kind: WorkItemKind, description: str) -> str:
    digest = hashlib.sha256(f"{kind}:{description}".encode()).hexdigest()[:16]
    return f"{kind}-{digest}"


def load_hiddenness_work_queue(csr: ConstitutionalStateRuntime) -> HiddennessWorkQueue:
    try:
        doc = csr.get_domain_doc(HIDDENNESS_WORK_QUEUE_STATE_ID, HiddennessWorkQueue)
        assert isinstance(doc, HiddennessWorkQueue)
        return doc
    except KeyError:
        return HiddennessWorkQueue()


def save_hiddenness_work_queue(csr: ConstitutionalStateRuntime, queue: HiddennessWorkQueue) -> None:
    csr.register_or_replace_state(
        StateObject(
            state_id=HIDDENNESS_WORK_QUEUE_STATE_ID,
            state_type="hiddenness_work_queue",
            current_state="Observed",
        )
    )
    csr.put_domain_doc(HIDDENNESS_WORK_QUEUE_STATE_ID, "hiddenness_work_queue", queue)


def resolve_hiddenness_work_item(
    csr: ConstitutionalStateRuntime,
    item_id: str,
    receipt_id: str,
) -> HiddennessWorkItem:
    """Mark a work item resolved after externalization and receipting."""
    queue = load_hiddenness_work_queue(csr)
    item = queue.resolve(item_id, receipt_id)
    save_hiddenness_work_queue(csr, queue)
    return item


def _build_work_item(
    *,
    kind: WorkItemKind,
    description: str,
    source: WorkItemSource,
    now: datetime,
    related_invariants: list[str] | None = None,
    related_purpose: list[str] | None = None,
    related_states: list[str] | None = None,
    related_receipts: list[str] | None = None,
    severity: WorkItemSeverity | None = None,
) -> HiddennessWorkItem:
    return HiddennessWorkItem(
        item_id=stable_work_item_id(kind, description),
        kind=kind,
        description=description,
        source=source,
        severity=severity or SEVERITY_BY_KIND[kind],
        related_invariants=list(related_invariants or []),
        related_purpose=list(related_purpose or []),
        related_states=list(related_states or []),
        related_receipts=list(related_receipts or []),
        created_at=now,
        last_seen_at=now,
    )


def _lineage_context(state: HiddennessState) -> tuple[list[str], list[str]]:
    links = getattr(state, "lineage_links", None)
    if links is None:
        return [], []
    return list(links.related_states), list(links.related_receipts)


def sync_hiddenness_state_to_work_queue(
    csr: ConstitutionalStateRuntime,
    hiddenness: HiddennessState,
    *,
    source: WorkItemSource = "HiddennessRuntimeV2",
    now: datetime | None = None,
) -> HiddennessWorkQueue:
    """Enumerate hiddenness findings as stable work items."""
    clock = now or hiddenness.snapshot_at
    if clock.tzinfo is None:
        clock = clock.replace(tzinfo=UTC)

    related_states, related_receipts = _lineage_context(hiddenness)
    queue = load_hiddenness_work_queue(csr)

    def _emit(
        kind: WorkItemKind,
        descriptions: list[str],
        *,
        related_invariants: list[str] | None = None,
        related_purpose: list[str] | None = None,
    ) -> None:
        for description in descriptions:
            if not description.strip():
                continue
            item = _build_work_item(
                kind=kind,
                description=description,
                source=source,
                now=clock,
                related_invariants=related_invariants,
                related_purpose=related_purpose,
                related_states=related_states,
                related_receipts=related_receipts,
            )
            queue.upsert(item)

    _emit("assumption", list(hiddenness.implicit_assumptions))
    _emit("invariant", list(hiddenness.undocumented_invariants), related_invariants=list(hiddenness.undocumented_invariants))
    _emit(
        "invariant_drift",
        list(getattr(hiddenness, "invariant_drift_candidates", []) or []),
        related_invariants=list(getattr(hiddenness, "invariant_drift_candidates", []) or []),
    )
    _emit(
        "purpose_fragment",
        list(hiddenness.undocumented_purpose_fragments),
        related_purpose=list(hiddenness.undocumented_purpose_fragments),
    )
    _emit("authority", list(hiddenness.undocumented_authority))
    _emit("context", list(hiddenness.undocumented_context))
    _emit("constraint", list(hiddenness.undocumented_constraints))
    _emit(
        "semantic_mismatch",
        list(getattr(hiddenness, "semantic_mismatches", []) or []),
        related_purpose=list(getattr(hiddenness, "semantic_mismatches", []) or []),
    )
    _emit("lineage_gap", list(getattr(hiddenness, "lineage_gaps", []) or []))
    _emit("founder_knowledge", list(hiddenness.founder_only_knowledge))

    save_hiddenness_work_queue(csr, queue)
    return queue


def format_hiddenness_work_queue_panel(queue: HiddennessWorkQueue) -> str:
    """Render the hiddenness burn-down list as text."""
    lines: list[str] = [
        "",
        "=== HIDDENNESS WORK QUEUE ===",
        f"Unresolved items: {queue.unresolved_count()}",
        "--------------------------------",
    ]
    unresolved = sorted(queue.unresolved(), key=lambda item: item.last_seen_at, reverse=True)
    if not unresolved:
        lines.append("(no unresolved hiddenness work items)")
    else:
        for item in unresolved:
            lines.append(f"[{item.kind}] {item.description}")
            lines.append(f"  severity: {item.severity}")
            lines.append(f"  status: {item.status}")
            lines.append(f"  last_seen: {item.last_seen_at.isoformat()}")
            lines.append(f"  source: {item.source}")
            lines.append(f"  item_id: {item.item_id}")
            lines.append("")
    lines.append("================================")
    lines.append("")
    return "\n".join(lines)


def hiddenness_work_queue_panel(
    queue: HiddennessWorkQueue,
    *,
    stream: IO[str] | None = None,
) -> str:
    """Print (or write) the hiddenness work queue panel."""
    text = format_hiddenness_work_queue_panel(queue)
    out = stream if stream is not None else sys.stdout
    out.write(text)
    if stream is None:
        out.flush()
    return text
