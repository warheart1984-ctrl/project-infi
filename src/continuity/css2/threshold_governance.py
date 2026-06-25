"""Threshold governance — existence, conflicts, provenance (CSS-2 §2.3)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.continuity.css2.spec import (
    THRESHOLD_FAILURE_CONTRADICTORY,
    THRESHOLD_FAILURE_DUPLICATED,
    THRESHOLD_FAILURE_MISSING,
    THRESHOLD_FAILURE_OPAQUE,
    THRESHOLD_FAILURE_ORPHANED,
    ThresholdGovernanceFailureKind,
)
from src.continuity.css2.threshold import Threshold


class ThresholdGovernanceFailure(BaseModel):
    kind: ThresholdGovernanceFailureKind
    message: str
    threshold_ids: list[str] = Field(default_factory=list)
    domain: str | None = None
    metric: str | None = None


class ThresholdGovernanceReport(BaseModel):
    failures: list[ThresholdGovernanceFailure] = Field(default_factory=list)
    ok: bool = True

    def model_post_init(self, __context: object) -> None:
        self.ok = len(self.failures) == 0


def audit_threshold_registry(
    thresholds: list[Threshold],
    *,
    required_metrics: list[tuple[str, str]] | None = None,
) -> ThresholdGovernanceReport:
    """Detect missing, duplicated, contradictory, orphaned, opaque thresholds."""
    failures: list[ThresholdGovernanceFailure] = []

    if required_metrics:
        present = {(t.domain, t.metric) for t in thresholds}
        for domain, metric in required_metrics:
            if (domain, metric) not in present:
                failures.append(
                    ThresholdGovernanceFailure(
                        kind=THRESHOLD_FAILURE_MISSING,
                        message=f"No threshold for domain={domain!r} metric={metric!r}",
                        domain=domain,
                        metric=metric,
                    )
                )

    by_key: dict[tuple[str, str, str], list[Threshold]] = {}
    for th in thresholds:
        key = (th.domain, th.metric, th.name)
        by_key.setdefault(key, []).append(th)

    for (domain, metric, name), group in by_key.items():
        if len(group) > 1:
            ids = [t.id for t in group]
            contradictory = _has_contradiction(group)
            kind = (
                THRESHOLD_FAILURE_CONTRADICTORY
                if contradictory
                else THRESHOLD_FAILURE_DUPLICATED
            )
            msg = (
                f"Contradictory thresholds for {domain}/{metric}/{name}"
                if contradictory
                else f"Duplicated thresholds for {domain}/{metric}/{name}"
            )
            failures.append(
                ThresholdGovernanceFailure(
                    kind=kind,
                    message=msg,
                    threshold_ids=ids,
                    domain=domain,
                    metric=metric,
                )
            )

    for th in thresholds:
        if not th.intent or not th.intent.strip():
            failures.append(
                ThresholdGovernanceFailure(
                    kind=THRESHOLD_FAILURE_OPAQUE,
                    message=f"Threshold {th.id!r} lacks intent (provenance)",
                    threshold_ids=[th.id],
                    domain=th.domain,
                    metric=th.metric,
                )
            )
        if not th.owner and th.created_by == "system":
            failures.append(
                ThresholdGovernanceFailure(
                    kind=THRESHOLD_FAILURE_ORPHANED,
                    message=f"Threshold {th.id!r} has no owner",
                    threshold_ids=[th.id],
                    domain=th.domain,
                    metric=th.metric,
                )
            )

    return ThresholdGovernanceReport(failures=failures, ok=not failures)


def find_relevant_thresholds(
    event: dict,
    thresholds: list[Threshold],
) -> list[Threshold]:
    """Map an event to applicable thresholds (JPSS-2 threshold lookup)."""
    metric = event.get("metric") or event.get("signal")
    domain = event.get("domain")
    if not metric:
        return []
    return [t for t in thresholds if t.applies_to(str(metric), domain)]


def _has_contradiction(group: list[Threshold]) -> bool:
    if len(group) < 2:
        return False
    ref = group[0]
    for other in group[1:]:
        if ref.comparator != other.comparator or ref.value != other.value:
            return True
    return False
