"""Semantic registries for Hiddenness Runtime v2 — claimed vs encoded knowledge."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field

from constitutional.core.articles import (
    HIDDENNESS_AMENDMENT_TEMPLATE_ID,
    HIDDENNESS_INDEX_THRESHOLD,
    PURPOSE_CONTINUITY_INVARIANT,
    SURVIVABILITY_BLOCK_THRESHOLD,
)
from constitutional.runtime.mission_fidelity_runtime import (
    MISSION_STATEMENT_STATE_ID,
    load_mission_statement,
)
from constitutional.runtime.mission_fidelity_interactive import load_mission_fidelity_interactive
from constitutional.runtime.receipts_v2 import BaseReceiptV2
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.runtime.runtime_charter import RUNTIME_CHARTER


class InvariantRecord(BaseModel):
    name: str
    description: str
    source: str = "invariant_registry"


class InvariantRegistryView(BaseModel):
    invariants: list[InvariantRecord] = Field(default_factory=list)

    def names(self) -> set[str]:
        return {record.name for record in self.invariants}


class PurposeFragment(BaseModel):
    fragment_id: str
    text: str
    source: str


class PurposeRegistryView(BaseModel):
    fragments: list[PurposeFragment] = Field(default_factory=list)

    def combined_text(self) -> str:
        return " ".join(fragment.text for fragment in self.fragments).lower()


class PolicyNode(BaseModel):
    node_id: str
    kind: str
    declared_purpose: str | None = None
    declared_constraints: list[str] = Field(default_factory=list)
    observed_behavior: list[str] = Field(default_factory=list)


class PolicyGraphView(BaseModel):
    nodes: list[PolicyNode] = Field(default_factory=list)

    def constraint_text(self) -> str:
        parts: list[str] = []
        for node in self.nodes:
            parts.extend(node.declared_constraints)
            if node.declared_purpose:
                parts.append(node.declared_purpose)
            parts.extend(node.observed_behavior)
        return " ".join(parts).lower()


def get_invariant_registry(csr: ConstitutionalStateRuntime) -> InvariantRegistryView:
    records = [
        InvariantRecord(name=name, description=description, source="invariant_registry")
        for name, description in csr.invariant_registry.items()
    ]
    for receipt in _all_receipts(csr):
        inv = getattr(receipt, "invariant", None)
        if inv is None:
            continue
        name = getattr(inv, "name", None)
        description = getattr(inv, "description", None)
        if not name:
            continue
        records.append(
            InvariantRecord(
                name=str(name),
                description=str(description or ""),
                source=f"receipt:{receipt.receipt_id}",
            )
        )
    return InvariantRegistryView(invariants=_dedupe_invariants(records))


def get_purpose_registry(csr: ConstitutionalStateRuntime) -> PurposeRegistryView:
    fragments: list[PurposeFragment] = []
    mission = load_mission_statement(csr)
    if mission is not None:
        fragments.append(
            PurposeFragment(
                fragment_id=MISSION_STATEMENT_STATE_ID,
                text=mission.text,
                source="mission_statement",
            )
        )
        if mission.invariant_rationale.strip():
            fragments.append(
                PurposeFragment(
                    fragment_id=f"{MISSION_STATEMENT_STATE_ID}:rationale",
                    text=mission.invariant_rationale,
                    source="mission_invariant_rationale",
                )
            )
        if mission.founding_context.strip():
            fragments.append(
                PurposeFragment(
                    fragment_id=f"{MISSION_STATEMENT_STATE_ID}:context",
                    text=mission.founding_context,
                    source="mission_founding_context",
                )
            )

    interactive = load_mission_fidelity_interactive(csr)
    if interactive is not None:
        for question_id, answer in interactive.answers.items():
            if len(answer.answer.strip()) >= 15:
                fragments.append(
                    PurposeFragment(
                        fragment_id=question_id,
                        text=answer.answer,
                        source="mission_fidelity_interactive",
                    )
                )

    for receipt in _all_receipts(csr):
        action = getattr(receipt, "action_type", "")
        if action not in {"purpose_continuity", "mission_fidelity_test"}:
            continue
        payload = getattr(receipt, "purpose_continuity", None) or getattr(
            receipt, "mission_fidelity", None
        )
        if payload is None:
            continue
        summary = getattr(payload, "mission_summary", None) or getattr(payload, "notes", None)
        if summary:
            fragments.append(
                PurposeFragment(
                    fragment_id=receipt.receipt_id,
                    text=str(summary),
                    source=f"receipt:{action}",
                )
            )
    return PurposeRegistryView(fragments=fragments)


def get_policy_graph(csr: ConstitutionalStateRuntime) -> PolicyGraphView:
    nodes: list[PolicyNode] = [
        PolicyNode(
            node_id="governance:survivability_block",
            kind="governance_threshold",
            declared_purpose="Block when system survivability falls below constitutional minimum",
            declared_constraints=[f"system_survivability_score >= {SURVIVABILITY_BLOCK_THRESHOLD}"],
        ),
        PolicyNode(
            node_id="governance:hiddenness_block",
            kind="governance_threshold",
            declared_purpose="Block when hiddenness exceeds Article H tolerance",
            declared_constraints=[f"hiddenness_index >= {HIDDENNESS_INDEX_THRESHOLD}"],
        ),
        PolicyNode(
            node_id=f"amendment:{HIDDENNESS_AMENDMENT_TEMPLATE_ID}",
            kind="amendment_template",
            declared_purpose="Remediate implicit or undocumented critical knowledge",
            declared_constraints=["externalize assumptions", "document invariants"],
        ),
    ]

    for runtime_name, resisted in RUNTIME_CHARTER.items():
        nodes.append(
            PolicyNode(
                node_id=f"runtime_charter:{runtime_name}",
                kind="runtime_charter",
                declared_purpose=f"Runtime {runtime_name} resists reconstructability failures",
                declared_constraints=[failure.value for failure in resisted[:5]],
                observed_behavior=[f"emits receipts as {runtime_name}"],
            )
        )

    for receipt in _all_receipts(csr):
        boundary = receipt.impact_boundary
        nodes.append(
            PolicyNode(
                node_id=f"receipt_policy:{receipt.receipt_id}",
                kind="receipt_policy",
                declared_constraints=[
                    f"scope_in={','.join(boundary.scope_in)}",
                    f"scope_out={','.join(boundary.scope_out)}",
                ],
                observed_behavior=[f"action_type={getattr(receipt, 'action_type', 'unknown')}"],
            )
        )

    return PolicyGraphView(nodes=nodes)


def _all_receipts(csr: ConstitutionalStateRuntime) -> list[BaseReceiptV2]:
    return csr.get_all_receipts()


def _dedupe_invariants(records: list[InvariantRecord]) -> list[InvariantRecord]:
    by_name: dict[str, InvariantRecord] = {}
    for record in records:
        existing = by_name.get(record.name)
        if existing is None:
            by_name[record.name] = record
            continue
        if record.source.startswith("receipt:") and not existing.source.startswith("receipt:"):
            by_name[record.name] = record
    return list(by_name.values())


def normalize_invariant_text(text: str) -> str:
    collapsed = re.sub(r"\s+", " ", text.strip().lower())
    return re.sub(r"[^\w\s]", "", collapsed)


def purpose_protection_tokens() -> set[str]:
    return {
        "protect",
        "minority",
        "steward",
        "continuity",
        "legitimacy",
        "meaning",
        "independent",
        "reconstruct",
    }


def throughput_optimization_tokens() -> set[str]:
    return {
        "throughput",
        "optimize",
        "speed",
        "latency",
        "maximize",
        "efficiency",
        "batch",
    }
