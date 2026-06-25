"""Resource Contract — RC-1 through RC-4 (CRK-1)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.continuity.decision_ledger import DecisionLedgerStore, DecisionRecord, DecisionStatus
from src.continuity.resource_ledger import (
    ResourceAllocation,
    ResourceLedgerStore,
    ResourceObject,
    ResourceStatus,
    recompute_resource_status,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class ResourceContract:
    """Govern resource allocation, release, and execution readiness."""

    def __init__(
        self,
        resource_ledger: ResourceLedgerStore,
        *,
        decision_ledger: DecisionLedgerStore | None = None,
    ) -> None:
        self.resources = resource_ledger
        self.decisions = decision_ledger

    def _get_resource(self, resource_id: str) -> ResourceObject:
        record = self.resources.get(resource_id)
        if record is None:
            raise ValueError(f"Resource not found: {resource_id}")
        return record

    def _get_decision(self, decision_id: str) -> DecisionRecord:
        if self.decisions is None:
            raise ValueError("Resource contract: decision ledger required for allocation linkage")
        decision = self.decisions.get(decision_id)
        if decision is None:
            raise ValueError(f"Decision not found: {decision_id}")
        return decision

    def _validate_decision_for_allocation(self, decision: DecisionRecord) -> None:
        if decision.status not in {DecisionStatus.PROPOSED, DecisionStatus.APPROVED}:
            raise ValueError(
                f"Resource contract: decision {decision.id} must be proposed or approved to allocate"
            )

    def allocate(self, resource_id: str, decision_id: str, amount: float, epoch: int) -> ResourceObject:
        if amount <= 0:
            raise ValueError("Resource contract: allocation amount must be positive")
        decision = self._get_decision(decision_id)
        self._validate_decision_for_allocation(decision)
        resource = self._get_resource(resource_id)
        if resource.status in {ResourceStatus.FROZEN, ResourceStatus.RETIRED}:
            raise ValueError(f"Resource not allocatable in status {resource.status.value}")
        if resource.quantity_allocated + amount > resource.quantity_total:
            raise ValueError("Allocation would exceed total quantity")
        resource.allocations.append(
            ResourceAllocation(
                decision_id=decision_id,
                amount=amount,
                unit=resource.quantity_unit,
                epoch=epoch,
            )
        )
        resource.quantity_allocated += amount
        resource.status = recompute_resource_status(resource)
        resource.updated_at = _now_iso()
        return self.resources.upsert(resource)

    def release(self, resource_id: str, decision_id: str, amount: float) -> ResourceObject:
        if amount <= 0:
            raise ValueError("Resource contract: release amount must be positive")
        resource = self._get_resource(resource_id)
        if resource.status == ResourceStatus.RETIRED:
            raise ValueError("Resource contract: cannot release from retired resource")
        remaining = amount
        new_allocations: list[ResourceAllocation] = []
        for allocation in resource.allocations:
            if allocation.decision_id == decision_id and remaining > 0:
                if allocation.amount <= remaining:
                    remaining -= allocation.amount
                    continue
                allocation.amount -= remaining
                remaining = 0.0
            new_allocations.append(allocation)
        if remaining > 0:
            raise ValueError("Not enough allocation to release")
        resource.allocations = new_allocations
        resource.quantity_allocated -= amount
        resource.status = recompute_resource_status(resource)
        resource.updated_at = _now_iso()
        return self.resources.upsert(resource)

    def update(self, resource_id: str, patch: dict[str, Any]) -> ResourceObject:
        resource = self._get_resource(resource_id)
        if resource.status == ResourceStatus.RETIRED:
            raise ValueError("Resource contract: cannot update retired resource")
        if "label" in patch:
            resource.label = str(patch["label"])
        if "constraints" in patch:
            resource.constraints = [dict(item) for item in patch["constraints"] or []]
        if "quantity_total" in patch:
            resource.quantity_total = float(patch["quantity_total"])
        if resource.quantity_allocated > resource.quantity_total:
            raise ValueError("Resource contract: patch would violate non-negative availability")
        resource.status = recompute_resource_status(resource)
        resource.updated_at = _now_iso()
        return self.resources.upsert(resource)

    def verify_decision_allocations(self, decision: DecisionRecord) -> None:
        """Ensure planned allocations exist and fit within resource totals."""
        plan_items = self._plan_items(decision)
        if not plan_items:
            return
        for item in plan_items:
            resource_id = str(item["resource_id"])
            amount = float(item["amount"])
            resource = self._get_resource(resource_id)
            allocated_for_decision = sum(
                alloc.amount
                for alloc in resource.allocations
                if alloc.decision_id == decision.id
            )
            if allocated_for_decision >= amount:
                continue
            needed = amount - allocated_for_decision
            available = resource.quantity_total - resource.quantity_allocated
            if needed > available:
                raise ValueError(
                    f"Resource contract: insufficient {resource_id} for decision {decision.id}"
                )
            if resource.status in {ResourceStatus.FROZEN, ResourceStatus.RETIRED}:
                raise ValueError(
                    f"Resource contract: resource {resource_id} not allocatable in status "
                    f"{resource.status.value}"
                )

    def allocate_for_decision(self, decision: DecisionRecord) -> None:
        plan_items = self._plan_items(decision)
        for item in plan_items:
            resource_id = str(item["resource_id"])
            amount = float(item["amount"])
            resource = self._get_resource(resource_id)
            allocated_for_decision = sum(
                alloc.amount
                for alloc in resource.allocations
                if alloc.decision_id == decision.id
            )
            if allocated_for_decision < amount:
                self.allocate(
                    resource_id,
                    decision.id,
                    amount - allocated_for_decision,
                    decision.epoch,
                )

    @staticmethod
    def _plan_items(decision: DecisionRecord) -> list[dict[str, Any]]:
        plan = decision.resource_plan or {}
        items = plan.get("allocations")
        if isinstance(items, list) and items:
            return items
        refs = plan.get("resource_refs") or []
        estimated = dict(plan.get("estimated_cost") or {})
        if not refs:
            return []
        if len(refs) == 1 and estimated.get("time_hours") is not None:
            return [{"resource_id": str(refs[0]), "amount": float(estimated["time_hours"])}]
        return []
