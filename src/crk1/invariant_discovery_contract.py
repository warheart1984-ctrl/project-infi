"""Invariant Discovery Contract (IDC) — governed invariant discovery from drift and CF-events."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from src.crk1.kernel_challenge_loop import CFEvent

DiscoverySignal = Literal[
    "unexplained_degradation",
    "persistent_surprise",
    "rdi_collapse",
    "domestication_pattern",
    "ce_drift",
    "se_drift",
    "silent_cf_event",
]
DriftMetric = Literal["CE(S)", "SE(S)"]
IDCChannelStatus = Literal["closed", "open"]


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class DriftObservation(BaseModel):
    """IDC drift trace — sustained CE(S) or SE(S) degradation."""

    id: str
    type: Literal["DriftObservation"] = "DriftObservation"
    created_at: str = Field(default_factory=_now_iso)
    created_by: str
    epoch: int
    payload: dict[str, Any]
    links: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        observation_id: str,
        created_by: str,
        epoch: int,
        metric: DriftMetric,
        value: float,
        baseline: float,
        window: str,
        description: str,
        cf_event_ids: list[str] | None = None,
        receipt_ids: list[str] | None = None,
    ) -> "DriftObservation":
        return cls(
            id=observation_id,
            created_by=created_by,
            epoch=epoch,
            payload={
                "metric": metric,
                "value": value,
                "baseline": baseline,
                "window": window,
                "description": description,
            },
            links={
                "cf_event_ids": list(cf_event_ids or []),
                "receipt_ids": list(receipt_ids or []),
            },
        )

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class InvariantProposal(BaseModel):
    """IDC proposal for a new invariant K_{n+1}."""

    id: str
    type: Literal["InvariantProposal"] = "InvariantProposal"
    created_at: str = Field(default_factory=_now_iso)
    created_by: str
    epoch: int
    payload: dict[str, Any]
    links: dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class InvariantTestSuite(BaseModel):
    """Reproducible stress tests for a proposed invariant."""

    id: str
    type: Literal["InvariantTestSuite"] = "InvariantTestSuite"
    created_at: str = Field(default_factory=_now_iso)
    created_by: str
    epoch: int
    payload: dict[str, Any]
    links: dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class InvariantDiscoveryProposal(BaseModel):
    """Legacy compact proposal — retained for Mission #004 harness compatibility."""

    proposal_id: str
    signal: DiscoverySignal
    summary: str
    supporting_grr_ids: list[str] = Field(default_factory=list)
    enforced_invariants: list[str] = Field(default_factory=list)
    proposed_invariant_id: str = ""
    proposed_statement: str = ""
    timestamp: str = Field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


@dataclass
class DriftTriggerConfig:
    """Thresholds for IDC drift triggers D1–D3."""

    ce_min: float = 0.85
    se_min: float = 0.83
    duration_ce: str = "P7D"
    duration_se: str = "P7D"


@dataclass
class InvariantDiscoveryContract:
    """
    IDC — watches drift and silent CF-events; opens governed discovery channel.

    Complements KernelChallengeLoop: IDC adds; KCL revises or deprecates.
    """

    unexplained_failure_threshold: float = 0.5
    config: DriftTriggerConfig = field(default_factory=DriftTriggerConfig)
    channel_status: IDCChannelStatus = "closed"
    proposals: list[InvariantDiscoveryProposal] = field(default_factory=list)
    drift_observations: list[DriftObservation] = field(default_factory=list)
    invariant_proposals: list[InvariantProposal] = field(default_factory=list)
    test_suites: list[InvariantTestSuite] = field(default_factory=list)
    _do_seq: int = 0
    _ip_seq: int = 0
    _its_seq: int = 0

    def _next_do_id(self) -> str:
        self._do_seq += 1
        return f"DO-{self._do_seq:04d}"

    def _next_ip_id(self) -> str:
        self._ip_seq += 1
        return f"IP-{self._ip_seq:04d}"

    def _next_its_id(self) -> str:
        self._its_seq += 1
        return f"ITS-{self._its_seq:04d}"

    def open_channel(self, *, reason: str) -> None:
        self.channel_status = "open"

    def evaluate_ce_drift(
        self,
        *,
        value: float,
        baseline: float,
        window: str,
        created_by: str,
        epoch: int,
        receipt_ids: list[str] | None = None,
        cf_event_ids: list[str] | None = None,
    ) -> DriftObservation | None:
        """Trigger D1 — CE(S) drift below envelope with invariants satisfied."""
        if value >= self.config.ce_min:
            return None
        observation = DriftObservation.create(
            observation_id=self._next_do_id(),
            created_by=created_by,
            epoch=epoch,
            metric="CE(S)",
            value=value,
            baseline=baseline,
            window=window,
            description=f"Sustained CE(S) decline: {value:.2f} < {self.config.ce_min}",
            cf_event_ids=cf_event_ids,
            receipt_ids=receipt_ids,
        )
        self.drift_observations.append(observation)
        self.open_channel(reason="D1 CE(S) drift")
        return observation

    def evaluate_se_drift(
        self,
        *,
        value: float,
        baseline: float,
        window: str,
        created_by: str,
        epoch: int,
        receipt_ids: list[str] | None = None,
        cf_event_ids: list[str] | None = None,
    ) -> DriftObservation | None:
        """Trigger D2 — SE(S) drift below envelope."""
        if value >= self.config.se_min:
            return None
        observation = DriftObservation.create(
            observation_id=self._next_do_id(),
            created_by=created_by,
            epoch=epoch,
            metric="SE(S)",
            value=value,
            baseline=baseline,
            window=window,
            description=f"Sustained SE(S) decline: {value:.2f} < {self.config.se_min}",
            cf_event_ids=cf_event_ids,
            receipt_ids=receipt_ids,
        )
        self.drift_observations.append(observation)
        self.open_channel(reason="D2 SE(S) drift")
        return observation

    def evaluate_silent_cf_event(
        self,
        *,
        cf_event: CFEvent,
        receipt_ids: list[str],
        created_by: str,
        epoch: int,
    ) -> DriftObservation | None:
        """Trigger D3 — compliant governance, no invariant violation, continuity failed."""
        if not cf_event.silent_failure:
            cf_event = cf_event.model_copy(update={"silent_failure": True})
        observation = DriftObservation.create(
            observation_id=self._next_do_id(),
            created_by=created_by,
            epoch=epoch,
            metric="CE(S)",
            value=0.0,
            baseline=1.0,
            window=cf_event.id,
            description=f"Silent CF-event: {cf_event.description}",
            cf_event_ids=[cf_event.id],
            receipt_ids=receipt_ids,
        )
        self.drift_observations.append(observation)
        self.open_channel(reason="D3 silent CF-event")
        return observation

    def propose_invariant(
        self,
        *,
        label: str,
        statement: str,
        motivation_cf_events: list[str],
        gap_in_existing_invariants: list[str],
        created_by: str,
        epoch: int,
        ce_s_min: float | None = None,
        se_s_min: float | None = None,
        drift_observation_ids: list[str] | None = None,
    ) -> InvariantProposal:
        """IDC.4 — expressible, enforceable, testable invariant proposal."""
        proposal = InvariantProposal(
            id=self._next_ip_id(),
            created_by=created_by,
            epoch=epoch,
            payload={
                "label": label,
                "statement": statement,
                "motivation_cf_events": motivation_cf_events,
                "gap_in_existing_invariants": gap_in_existing_invariants,
                "expected_effect_on_ce_se": {
                    "ce_s_min": ce_s_min if ce_s_min is not None else self.config.ce_min,
                    "se_s_min": se_s_min if se_s_min is not None else self.config.se_min,
                },
            },
            links={"drift_observation_ids": list(drift_observation_ids or [])},
        )
        self.invariant_proposals.append(proposal)
        return proposal

    def attach_test_suite(
        self,
        *,
        invariant_proposal_id: str,
        label: str,
        scenarios: list[str],
        passed: bool,
        notes: str,
        created_by: str,
        epoch: int,
    ) -> InvariantTestSuite:
        """IDC.5 — reproducible non-founder test harness output."""
        suite = InvariantTestSuite(
            id=self._next_its_id(),
            created_by=created_by,
            epoch=epoch,
            payload={
                "label": label,
                "scenarios": scenarios,
                "results": {"passed": passed, "notes": notes},
            },
            links={"invariant_proposal_id": invariant_proposal_id},
        )
        self.test_suites.append(suite)
        proposal = next(
            (item for item in self.invariant_proposals if item.id == invariant_proposal_id),
            None,
        )
        if proposal is not None:
            test_ids = list(proposal.links.get("test_suite_ids", []))
            test_ids.append(suite.id)
            proposal.links["test_suite_ids"] = test_ids
        return suite

    def evaluate(
        self,
        *,
        enforced_invariants: list[str],
        continuity_preserved: bool,
        grr_id: str,
        rdi: float | None = None,
        rdi_floor: float = 0.2,
        invariant_violated: bool = False,
        cf_event: CFEvent | None = None,
    ) -> InvariantDiscoveryProposal | None:
        """Legacy entry — maps unexplained failure to IDC channel + compact proposal."""
        if continuity_preserved:
            return None

        if not invariant_violated and cf_event is not None:
            self.evaluate_silent_cf_event(
                cf_event=cf_event,
                receipt_ids=[grr_id],
                created_by="G-ENGINE",
                epoch=1,
            )

        signal: DiscoverySignal = "unexplained_degradation"
        summary = (
            f"Continuity failed while {', '.join(enforced_invariants) or 'no invariants'} "
            "were enforced — unexplained degradation persists."
        )

        if rdi is not None and rdi < rdi_floor:
            signal = "rdi_collapse"
            summary = f"Reality Diversity Index collapsed ({rdi:.4f}) despite invariant enforcement."

        proposal = InvariantDiscoveryProposal(
            proposal_id=self._next_ip_id(),
            signal=signal,
            summary=summary,
            supporting_grr_ids=[grr_id],
            enforced_invariants=list(enforced_invariants),
            proposed_invariant_id=f"K{len(enforced_invariants) + 13}",
            proposed_statement=(
                "New invariant required: close gap between enforced kernel and observed reality."
            ),
        )
        self.proposals.append(proposal)
        self.open_channel(reason=signal)
        return proposal

    def pending(self) -> list[InvariantDiscoveryProposal]:
        return list(self.proposals)
