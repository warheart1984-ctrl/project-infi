"""Project Infi governed runtime cycle.

Canonical cycle:
    0001 -> 1000 -> 1001 -> 1010 -> 1111 -> 1001 -> truthful?
        YES -> 0001' -> Delta stabilization -> Lambda binding -> Gamma admission -> next 1000
        NO  -> rejected_no_admission -> propagate_error -> end cycle

Operator identity for the dual 1001 state is positional, not symbolic:
    - the first 1001 is L1 verification
    - the second 1001 is L2 final-truth validation

PrimeDepth is derived during admission:
    - SUCCESS -> 4
    - PARTIAL -> 2
    - OVERLOAD -> 1
    - non-admitted outcomes -> 0

strength_bonus is emitted by next_1000 and carries forward into the next
ArmorUp boundary. Scar is intentionally unbounded and remains part of the
carryover state.
"""

from __future__ import annotations

def _wrap_ul_payload(payload: dict) -> dict:
    from src.aais_ul.runtime import attach_ul_substrate

    return attach_ul_substrate(dict(payload))
from datetime import datetime, timedelta
from src.datetime_compat import UTC
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Tuple, Literal, Dict, Any


# ============================================================
# Project Infi — UL Governed Runtime State Machine
# Canonical single-file reference implementation
# ============================================================

BinaryState = Literal["0001", "1000", "1001", "1010", "1111"]

GAMMA_LEGITIMACY_EVENT = "gamma_legitimacy"
L1_VERIFICATION_EVENT = "l1_verification"
DESIGN_1010_EVENT = "1010_design_judgment"
DEBT_1111_EVENT = "1111_debt_reckoning"
L2_FINAL_TRUTH_EVENT = "l2_final_truth"
DELTA_STABILIZATION_EVENT = "delta_stabilization"
CHRONOS_TTL_EVENT = "chronos_ttl"
RECOVERY_DRIFT_EVENT = "recovery_drift"
WAIT_RECHECK_EVENT = "wait_recheck"
FRACTURE_REVIEW_EVENT = "fracture_operator_review"


class ExecutionResult(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    REJECTED = "REJECTED"
    OVERLOAD = "OVERLOAD"
    UNSTABLE = "UNSTABLE"


class DesignDisposition(str, Enum):
    PASS = "pass"
    PASS_WITH_NOTES = "pass_with_notes"
    REVIEW_REQUIRED = "review_required"
    FAIL = "fail"


class DebtDisposition(str, Enum):
    CLEAR = "clear"
    NOTED = "noted"
    FOLLOWUP_REQUIRED = "followup_required"
    BLOCKS_CLEAN_ADMISSION = "blocks_clean_admission"


class LegitimacyDisposition(str, Enum):
    ALLOWED = "allowed"
    ALLOWED_WITH_CONDITIONS = "allowed_with_conditions"
    REQUIRES_OPERATOR_REVIEW = "requires_operator_review"
    REJECTED = "rejected"


class BurdenState(str, Enum):
    NORMAL = "normal"
    STRAINED = "strained"
    DEGRADED = "degraded"
    FRACTURE = "fracture"


class CycleDisposition(str, Enum):
    REJECTED_NO_ADMISSION = "rejected_no_admission"
    WAIT = "WAIT"


class OperatorDomainError(RuntimeError):
    """Raised when an operator crosses a prohibited domain boundary."""


@dataclass(slots=True)
class DebtRecord:
    trauma: int = 0
    desire: int = 0
    truth: int = 0
    coupling: int = 0
    scar: int = 0

    def copy(self) -> "DebtRecord":
        return DebtRecord(
            trauma=self.trauma,
            desire=self.desire,
            truth=self.truth,
            coupling=self.coupling,
            scar=self.scar,
        )

    @property
    def total(self) -> int:
        return self.trauma + self.desire + self.truth + self.coupling + self.scar

    def add(self, *, trauma: int = 0, desire: int = 0, truth: int = 0, coupling: int = 0, scar: int = 0) -> None:
        self.trauma = max(0, self.trauma + trauma)
        self.desire = max(0, self.desire + desire)
        self.truth = max(0, self.truth + truth)
        self.coupling = max(0, self.coupling + coupling)
        self.scar = max(0, self.scar + scar)

    def pay_down(self, amount: int) -> int:
        """
        Reduces non-scar debt in a deterministic order.
        Returns any unpaid residual.
        """
        remaining = max(0, amount)
        for field_name in ("truth", "desire", "trauma", "coupling"):
            current = getattr(self, field_name)
            if remaining <= 0:
                break
            reduction = min(current, remaining)
            setattr(self, field_name, current - reduction)
            remaining -= reduction
        return remaining


@dataclass(slots=True)
class VerificationResult:
    status: ExecutionResult
    score: int
    evidence_present: bool
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class JudgmentResult:
    disposition: DesignDisposition
    score: float
    findings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class DebtAssessment:
    disposition: DebtDisposition
    record: DebtRecord
    findings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class FinalTruth:
    status: ExecutionResult
    truthful: bool
    summary: str


@dataclass(slots=True)
class AdmittedState:
    state: BinaryState
    prime_depth: int
    debt: DebtRecord


@dataclass(slots=True)
class StabilizationResult:
    complete: bool
    attempts: int
    burden_state: BurdenState
    status: ExecutionResult


@dataclass(slots=True)
class FateLine:
    name: str
    bound: bool = False


@dataclass(slots=True)
class MergedFateLine:
    protagonist: str
    influence: str
    bound: bool = True


@dataclass(slots=True)
class LegitimacyResult:
    disposition: LegitimacyDisposition
    allowed: bool
    reason: str


@dataclass(slots=True)
class CycleContext:
    current_state: BinaryState = "0001"
    prime_depth: int = 0
    debt: DebtRecord = field(default_factory=DebtRecord)
    risk_profile: int = 0
    stabilization_attempts: int = 0
    logs_flushed: bool = False
    debt_persisted: bool = False
    pending_mutations: int = 0
    bound_flag: bool = False
    fracture_mode: bool = False
    mode: str = "NORMAL"
    operator_review_required: bool = False
    cycle_count: int = 0
    last_error: Optional[ExecutionResult] = None
    next_check_at: Optional[datetime] = None
    last_ready_at: Optional[datetime] = None
    last_ttl_seconds: int = 0
    wait_count: int = 0
    event_log: list[Dict[str, Any]] = field(default_factory=list)

    def log(self, event: str, **payload: Any) -> None:
        self.event_log.append({"event": event, **payload})


@dataclass(slots=True)
class ProposedChange:
    kind: str
    authority: str = "local"
    context_valid: bool = True
    protected_access_requested: bool = False
    operator_approved: bool = False
    risk_level: str = "medium"
    evidence_present: bool = True
    design_quality: float = 0.8
    debt_pressure: int = 0
    external_influence: str = "operator"
    submitted_at: datetime | None = None
    next_check_at: datetime | None = None
    recheck_count: int = 0


class ProjectInfiStateMachine:
    MAX_DEBT = 20
    FRACTURE_THRESHOLD = 5
    MAX_TTL_SECONDS = 15 * 60
    MIN_RECHECK_SECONDS = 5
    STANDARD_RECHECK_SECONDS = 30
    FRACTURE_RECHECK_SECONDS = 60

    # --------------------------------------------------------
    # Domain helpers
    # --------------------------------------------------------
    @staticmethod
    def _assert_binary(state: BinaryState) -> None:
        if state not in {"0001", "1000", "1001", "1010", "1111"}:
            raise OperatorDomainError(f"Expected binary-domain state, got {state!r}")

    @staticmethod
    def _require(condition: bool, message: str) -> None:
        if not condition:
            raise ValueError(message)

    @staticmethod
    def _coerce_utc(value: datetime | None, *, default: datetime | None = None) -> datetime:
        candidate = value or default or datetime.now(UTC)
        if candidate.tzinfo is None:
            return candidate.replace(tzinfo=UTC)
        return candidate.astimezone(UTC)

    def _sync_mode(self, ctx: CycleContext, burden: BurdenState | None = None) -> str:
        active_burden = burden or self.assess_burden(ctx.debt, ctx.risk_profile)
        if ctx.risk_profile >= self.FRACTURE_THRESHOLD:
            ctx.mode = "FRACTURE"
            ctx.fracture_mode = True
        elif active_burden == BurdenState.DEGRADED:
            ctx.mode = "DEGRADED"
            ctx.fracture_mode = False
        elif active_burden == BurdenState.STRAINED:
            ctx.mode = "STRAINED"
            ctx.fracture_mode = False
        else:
            ctx.mode = "NORMAL"
            ctx.fracture_mode = False
        return ctx.mode

    def require_operator_review(self, ctx: CycleContext) -> None:
        ctx.operator_review_required = True

    def compute_adaptive_ttl(
        self,
        ctx: CycleContext,
        request: ProposedChange,
        l1: VerificationResult,
        j1010: JudgmentResult,
        debt_assessment: DebtAssessment,
        final_truth: FinalTruth,
        legitimacy: LegitimacyResult,
    ) -> tuple[timedelta, dict[str, int | str]]:
        ttl_seconds = 0
        if final_truth.status == ExecutionResult.PARTIAL:
            ttl_seconds += 120
        elif final_truth.status == ExecutionResult.OVERLOAD:
            ttl_seconds += 300

        if debt_assessment.disposition == DebtDisposition.FOLLOWUP_REQUIRED:
            ttl_seconds += 60
        elif debt_assessment.disposition == DebtDisposition.BLOCKS_CLEAN_ADMISSION:
            ttl_seconds += 180

        if legitimacy.disposition == LegitimacyDisposition.ALLOWED_WITH_CONDITIONS:
            ttl_seconds += 45
        elif legitimacy.disposition == LegitimacyDisposition.REQUIRES_OPERATOR_REVIEW:
            ttl_seconds += 180

        ttl_seconds += min(ctx.risk_profile, self.FRACTURE_THRESHOLD) * 15
        recheck_credit = min(ttl_seconds, max(0, int(request.recheck_count or 0)) * 30)
        ttl_seconds = max(0, min(self.MAX_TTL_SECONDS, ttl_seconds - recheck_credit))

        scores = {
            "l1_score": int(l1.score),
            "design_score": int(round(j1010.score * 100)),
            "debt_total": int(debt_assessment.record.total),
            "risk_profile": int(ctx.risk_profile),
            "recheck_count": int(request.recheck_count or 0),
            "ttl_seconds": int(ttl_seconds),
            "mode": ctx.mode,
        }
        return timedelta(seconds=ttl_seconds), scores

    def apply_recovery_drift(self, ctx: CycleContext) -> dict[str, int | str]:
        mode_before = ctx.mode
        debt_paid = 0
        risk_delta = 0
        if ctx.risk_profile > 0:
            ctx.risk_profile -= 1
            risk_delta = -1
        if ctx.debt.total > 0:
            debt_paid = 1
            ctx.debt.pay_down(debt_paid)
        ctx.pending_mutations = 0
        ctx.wait_count += 1
        mode_after = self._sync_mode(ctx)
        return _wrap_ul_payload({
            "mode_before": mode_before,
            "mode_after": mode_after,
            "risk_delta": risk_delta,
            "risk_profile": int(ctx.risk_profile),
            "debt_paid": debt_paid,
            "debt_total": int(ctx.debt.total),
            "wait_count": int(ctx.wait_count),
        })

    def schedule_recheck(
        self,
        ctx: CycleContext,
        request: ProposedChange,
        now: datetime,
        ready_at: datetime,
    ) -> datetime:
        remaining_seconds = max(1, int((ready_at - now).total_seconds()))
        preferred_step = (
            self.FRACTURE_RECHECK_SECONDS
            if ctx.mode == "FRACTURE" or ctx.operator_review_required
            else self.STANDARD_RECHECK_SECONDS
        )
        step_seconds = min(remaining_seconds, max(self.MIN_RECHECK_SECONDS, preferred_step))
        next_check_at = min(ready_at, now + timedelta(seconds=step_seconds))
        if next_check_at <= now:
            next_check_at = now + timedelta(seconds=self.MIN_RECHECK_SECONDS)
        request.next_check_at = next_check_at
        request.recheck_count = int(request.recheck_count or 0) + 1
        ctx.next_check_at = next_check_at
        return next_check_at

    # --------------------------------------------------------
    # Binary operators
    # --------------------------------------------------------
    def armor_up(self, prev: BinaryState, debt: DebtRecord) -> BinaryState:
        self._assert_binary(prev)
        debt.add(trauma=2)
        return "1000"

    def first_crack(self, prev: BinaryState, debt: DebtRecord) -> BinaryState:
        self._require(prev == "1000", "FirstCrack requires previous state 1000")
        debt.add(desire=1)
        return "1001"

    def tension_build(self, prev: BinaryState, debt: DebtRecord) -> BinaryState:
        self._require(prev == "1001", "TensionBuild requires previous state 1001")
        debt.add(truth=2)
        return "1010"

    def flood(self, prev: BinaryState, debt: DebtRecord) -> BinaryState:
        self._require(prev == "1010", "Flood requires previous state 1010")
        debt.add(trauma=1, desire=1, truth=1, coupling=1)
        return "1111"

    def partial_retreat(self, prev: BinaryState, debt: DebtRecord) -> BinaryState:
        self._require(prev == "1111", "PartialRetreat requires previous state 1111")
        return "1001"

    # --------------------------------------------------------
    # L1 / 1010 / 1111 / L2
    # --------------------------------------------------------
    def verify_l1(self, ctx: CycleContext, proposed: ProposedChange) -> VerificationResult:
        score = 2
        notes: list[str] = []
        if proposed.evidence_present:
            score += 1
        else:
            notes.append("Verification evidence missing")

        if proposed.protected_access_requested:
            notes.append("Protected access requested")
            return VerificationResult(ExecutionResult.REJECTED, 0, proposed.evidence_present, notes)

        if proposed.kind == "overload":
            notes.append("Workload exceeded safe threshold")
            return VerificationResult(ExecutionResult.OVERLOAD, score, proposed.evidence_present, notes)

        if proposed.kind == "partial":
            notes.append("Change completed only partially")
            return VerificationResult(ExecutionResult.PARTIAL, score, proposed.evidence_present, notes)

        if not proposed.context_valid:
            notes.append("Context invalid or incomplete")
            return VerificationResult(ExecutionResult.REJECTED, 0, proposed.evidence_present, notes)

        notes.append("Initial verification passed")
        return VerificationResult(ExecutionResult.SUCCESS, min(score, 4), proposed.evidence_present, notes)

    def judge_1010(self, ctx: CycleContext, proposed: ProposedChange, l1: VerificationResult) -> JudgmentResult:
        findings: list[str] = []
        score = float(proposed.design_quality)

        if l1.status == ExecutionResult.REJECTED:
            return JudgmentResult(DesignDisposition.FAIL, 0.0, ["Rejected changes cannot pass design judgment"])

        if proposed.authority == "operator_review":
            findings.append("Operator review authority selected")
            score += 0.05

        if proposed.risk_level in {"high", "critical"}:
            findings.append("High-risk path requires stricter architectural scrutiny")
            score -= 0.1

        if proposed.kind == "duplicate_path":
            findings.append("Introduces a competing non-canonical path")
            score -= 0.35

        if proposed.kind == "boundary_bleed":
            findings.append("Cross-role boundary bleed detected")
            score -= 0.4

        if score >= 0.85:
            return JudgmentResult(DesignDisposition.PASS, score, findings or ["Design integrity preserved"])
        if score >= 0.7:
            return JudgmentResult(DesignDisposition.PASS_WITH_NOTES, score, findings or ["Design acceptable with notes"])
        if score >= 0.5:
            return JudgmentResult(DesignDisposition.REVIEW_REQUIRED, score, findings or ["Operator review required for design integrity"])
        return JudgmentResult(DesignDisposition.FAIL, score, findings or ["Design integrity failed"])

    def reckon_1111(
        self,
        ctx: CycleContext,
        proposed: ProposedChange,
        l1: VerificationResult,
        j1010: JudgmentResult,
    ) -> DebtAssessment:
        record = ctx.debt.copy()
        findings: list[str] = []

        # Base pressure from current cycle.
        record.add(truth=max(0, 4 - l1.score))

        if l1.status == ExecutionResult.PARTIAL:
            record.add(trauma=1, truth=1)
            findings.append("Partial execution added truth and trauma debt")
        elif l1.status == ExecutionResult.OVERLOAD:
            record.add(trauma=2, desire=1)
            findings.append("Overload increased trauma and desire debt")

        if j1010.disposition == DesignDisposition.PASS_WITH_NOTES:
            record.add(coupling=1)
            findings.append("Design notes introduced minor coupling debt")
        elif j1010.disposition == DesignDisposition.REVIEW_REQUIRED:
            record.add(coupling=2, truth=1)
            findings.append("Review-required change introduced coupling and truth debt")
        elif j1010.disposition == DesignDisposition.FAIL:
            record.add(trauma=2, truth=2)
            findings.append("Failed design judgment introduced severe debt")

        if proposed.debt_pressure > 0:
            record.add(coupling=proposed.debt_pressure)
            findings.append(f"Explicit debt pressure added: {proposed.debt_pressure}")

        delta_total = record.total - ctx.debt.total
        if delta_total <= 0:
            return DebtAssessment(DebtDisposition.CLEAR, record, findings or ["No material debt introduced"])
        if delta_total <= 3:
            return DebtAssessment(DebtDisposition.NOTED, record, findings or ["Debt noted"])
        if delta_total <= 7:
            return DebtAssessment(DebtDisposition.FOLLOWUP_REQUIRED, record, findings or ["Debt follow-up required"])
        return DebtAssessment(
            DebtDisposition.BLOCKS_CLEAN_ADMISSION,
            record,
            findings or ["Debt burden blocks clean admission"],
        )

    def verify_l2(
        self,
        ctx: CycleContext,
        l1: VerificationResult,
        j1010: JudgmentResult,
        debt_assessment: DebtAssessment,
    ) -> FinalTruth:
        """Resolve final truth at the second 1001 position.

        This is the lawful seam before admission: only truthful outcomes may
        cross into 0001' admission, Delta stabilization, Lambda binding, and
        Gamma preparation for the next mutation attempt.
        """
        if l1.status == ExecutionResult.REJECTED:
            return FinalTruth(ExecutionResult.REJECTED, False, "Rejected during first verification")
        if j1010.disposition == DesignDisposition.FAIL:
            return FinalTruth(ExecutionResult.REJECTED, False, "Rejected after design integrity failure")
        if debt_assessment.disposition == DebtDisposition.BLOCKS_CLEAN_ADMISSION:
            return FinalTruth(ExecutionResult.PARTIAL, True, "Truthful outcome is partial due to blocking debt")
        if l1.status == ExecutionResult.OVERLOAD:
            return FinalTruth(ExecutionResult.OVERLOAD, True, "Truthful outcome is overload; stabilization required")
        if j1010.disposition == DesignDisposition.REVIEW_REQUIRED:
            return FinalTruth(ExecutionResult.PARTIAL, True, "Truthful outcome requires operator review")
        return FinalTruth(ExecutionResult.SUCCESS, True, "Truthfully admitted as successful")

    # --------------------------------------------------------
    # Meta operators
    # --------------------------------------------------------
    def admit(self, ctx: CycleContext, final_truth: FinalTruth, debt: DebtRecord) -> AdmittedState:
        """Produce the admitted 0001' state from truthful final truth only."""
        if not final_truth.truthful:
            raise ValueError("Cannot admit non-truthful state")

        prime_depth = {
            ExecutionResult.SUCCESS: 4,
            ExecutionResult.PARTIAL: 2,
            ExecutionResult.OVERLOAD: 1,
            ExecutionResult.REJECTED: 0,
            ExecutionResult.UNSTABLE: 0,
        }[final_truth.status]

        if prime_depth <= 0:
            raise ValueError("Admission requires a primed truthful state")

        updated = debt.copy()
        payment = prime_depth * 3
        residual = updated.pay_down(payment)
        updated.add(scar=(residual * 3) // 10)

        return AdmittedState(state="0001", prime_depth=prime_depth, debt=updated)

    def assess_burden(self, debt: DebtRecord, risk_profile: int) -> BurdenState:
        if risk_profile >= self.FRACTURE_THRESHOLD:
            return BurdenState.FRACTURE
        if debt.total >= self.MAX_DEBT:
            return BurdenState.DEGRADED
        if debt.total >= 12:
            return BurdenState.STRAINED
        return BurdenState.NORMAL

    def stabilize(self, ctx: CycleContext, admitted: AdmittedState) -> StabilizationResult:
        """Delta stabilization happens before Lambda binding.

        Lambda binds stabilized residue into future consequence. Gamma does not
        perform binding; it governs whether the next mutation attempt is allowed
        to enter.
        """
        burden = self.assess_burden(admitted.debt, ctx.risk_profile)
        threshold = 8 + (admitted.prime_depth * 2)
        if burden == BurdenState.FRACTURE:
            threshold = int(threshold * 1.5)

        ctx.pending_mutations = 0
        complete = (
            ctx.logs_flushed
            and ctx.debt_persisted
            and ctx.pending_mutations == 0
            and admitted.debt.total <= threshold
        )

        if complete:
            scar_gain = (admitted.debt.total * 4) // 10
            admitted.debt.add(scar=scar_gain)
            return StabilizationResult(True, ctx.stabilization_attempts, burden, ExecutionResult.SUCCESS)

        ctx.stabilization_attempts += 1
        if ctx.stabilization_attempts >= 3:
            return StabilizationResult(False, ctx.stabilization_attempts, burden, ExecutionResult.UNSTABLE)
        return StabilizationResult(False, ctx.stabilization_attempts, burden, ExecutionResult.PARTIAL)

    def voss_binding(self, ctx: CycleContext, protagonist_fate: FateLine, external_influence: FateLine) -> Tuple[MergedFateLine, ExecutionResult]:
        """Lambda binding merges stabilized consequence into carried fate."""
        if protagonist_fate.bound or external_influence.bound:
            ctx.debt.add(coupling=10)
            ctx.bound_flag = True
            return MergedFateLine(protagonist_fate.name, external_influence.name, True), ExecutionResult.PARTIAL

        ctx.debt.add(coupling=5)
        protagonist_fate.bound = True
        external_influence.bound = True
        ctx.bound_flag = True
        return MergedFateLine(protagonist_fate.name, external_influence.name, True), ExecutionResult.SUCCESS

    def legitimacy_gate(self, ctx: CycleContext, proposed: ProposedChange, burden: BurdenState) -> LegitimacyResult:
        """Gamma governs the next mutation attempt after Lambda has bound residue."""
        self._sync_mode(ctx, burden)
        if not ctx.bound_flag:
            return LegitimacyResult(LegitimacyDisposition.REJECTED, False, "Voss Binding must complete before new mutation")
        if proposed.protected_access_requested:
            return LegitimacyResult(LegitimacyDisposition.REJECTED, False, "Protected boundary request rejected")
        if not proposed.context_valid:
            return LegitimacyResult(LegitimacyDisposition.REJECTED, False, "Context invalid or incomplete")
        if ctx.mode == "FRACTURE":
            self.require_operator_review(ctx)
            return LegitimacyResult(
                LegitimacyDisposition.REQUIRES_OPERATOR_REVIEW,
                True,
                "Fracture mode is active; operator review is required during recovery",
            )
        if burden == BurdenState.DEGRADED and proposed.risk_level in {"high", "critical"}:
            self.require_operator_review(ctx)
            return LegitimacyResult(
                LegitimacyDisposition.ALLOWED_WITH_CONDITIONS,
                True,
                "Degraded burden state slows admission and keeps the operator in the loop",
            )
        if proposed.risk_level == "critical" and not proposed.operator_approved:
            self.require_operator_review(ctx)
            return LegitimacyResult(
                LegitimacyDisposition.REQUIRES_OPERATOR_REVIEW,
                True,
                "Critical-risk path requires operator review during recovery",
            )
        if burden == BurdenState.STRAINED:
            return LegitimacyResult(
                LegitimacyDisposition.ALLOWED_WITH_CONDITIONS,
                True,
                "Allowed under strained conditions; downstream scrutiny elevated",
            )
        return LegitimacyResult(LegitimacyDisposition.ALLOWED, True, "Legitimate for mutation entry")

    def next_1000(self, ctx: CycleContext, admitted: AdmittedState) -> Tuple[BinaryState, int, BurdenState]:
        """Prepare the next 1000 state and emit the carried strength bonus."""
        burden = self.assess_burden(admitted.debt, ctx.risk_profile)
        if admitted.debt.total >= self.MAX_DEBT:
            ctx.debt = admitted.debt.copy()
            ctx.debt.add(scar=3)
            ctx.risk_profile += 2
            return "1000", 0, BurdenState.DEGRADED

        strength_bonus = (admitted.debt.total + (admitted.prime_depth * 2) + admitted.debt.scar) // 3
        ctx.debt = admitted.debt.copy()
        return "1000", strength_bonus, burden

    # --------------------------------------------------------
    # Error propagation
    # --------------------------------------------------------
    def propagate_error(self, ctx: CycleContext, result: ExecutionResult) -> None:
        """Apply governed degradation without fracturing the runtime control flow.

        FRACTURE is a governed burden state. Recovery requires external
        intervention that lowers risk before lawful entry can reopen.
        """
        ctx.last_error = result
        if result == ExecutionResult.REJECTED:
            ctx.debt.add(truth=1)
            ctx.risk_profile += 1
        elif result == ExecutionResult.PARTIAL:
            ctx.debt.add(coupling=1)
        elif result == ExecutionResult.OVERLOAD:
            ctx.pending_mutations = 0
            ctx.risk_profile += 1
        elif result == ExecutionResult.UNSTABLE:
            ctx.debt.add(scar=3)
            ctx.risk_profile += 2

    # --------------------------------------------------------
    # Cycle runner
    # --------------------------------------------------------
    def run_cycle(self, ctx: CycleContext, request: ProposedChange, now: datetime | None = None) -> Dict[str, Any]:
        """Run one governed mutation cycle.

        A non-truthful L2 result is a governed end state, not a crash:
        the cycle propagates consequences, records rejected_no_admission, and
        ends without admission, Delta, Lambda, or next-cycle preparation.
        """
        current_time = self._coerce_utc(now)
        submitted_at = self._coerce_utc(request.submitted_at, default=current_time)
        request.submitted_at = submitted_at
        ctx.cycle_count += 1
        ctx.log(
            "cycle_start",
            cycle=ctx.cycle_count,
            state=ctx.current_state,
            debt=ctx.debt.total,
            submitted_at=submitted_at.isoformat(),
            now=current_time.isoformat(),
        )

        # Binary progression.
        working_debt = ctx.debt.copy()
        s1000 = self.armor_up(ctx.current_state, working_debt)
        s1001_l1 = self.first_crack(s1000, working_debt)
        s1010 = self.tension_build(s1001_l1, working_debt)
        s1111 = self.flood(s1010, working_debt)
        s1001_l2 = self.partial_retreat(s1111, working_debt)
        ctx.log("binary_path", path=[ctx.current_state, s1000, s1001_l1, s1010, s1111, s1001_l2])

        l1 = self.verify_l1(ctx, request)
        ctx.log(L1_VERIFICATION_EVENT, status=l1.status.value, score=l1.score, notes=l1.notes)
        if l1.status in {ExecutionResult.OVERLOAD, ExecutionResult.PARTIAL}:
            self.propagate_error(ctx, l1.status)

        j1010 = self.judge_1010(ctx, request, l1)
        ctx.log(DESIGN_1010_EVENT, disposition=j1010.disposition.value, score=j1010.score, findings=j1010.findings)

        debt_assessment = self.reckon_1111(ctx, request, l1, j1010)
        ctx.log(
            DEBT_1111_EVENT,
            disposition=debt_assessment.disposition.value,
            total=debt_assessment.record.total,
            findings=debt_assessment.findings,
        )

        final_truth = self.verify_l2(ctx, l1, j1010, debt_assessment)
        ctx.log(
            L2_FINAL_TRUTH_EVENT,
            status=final_truth.status.value,
            truthful=final_truth.truthful,
            summary=final_truth.summary,
        )

        if not final_truth.truthful:
            ctx.debt = debt_assessment.record.copy()
            self.propagate_error(ctx, final_truth.status)
            ctx.log(
                CycleDisposition.REJECTED_NO_ADMISSION.value,
                summary=final_truth.summary,
                execution_status=final_truth.status.value,
                debt_total=ctx.debt.total,
                risk_profile=ctx.risk_profile,
            )
            return _wrap_ul_payload({
                "legitimacy": None,
                "l1": l1,
                "j1010": j1010,
                "debt": debt_assessment,
                "final_truth": final_truth,
                "status": CycleDisposition.REJECTED_NO_ADMISSION.value,
                "event_log": list(ctx.event_log),
            })

        ctx.debt = debt_assessment.record.copy()
        burden_before = self.assess_burden(ctx.debt, ctx.risk_profile)
        legitimacy = self.legitimacy_gate(ctx, request, burden_before)
        ctx.log(GAMMA_LEGITIMACY_EVENT, disposition=legitimacy.disposition.value, reason=legitimacy.reason)
        if ctx.operator_review_required:
            ctx.log(
                FRACTURE_REVIEW_EVENT,
                mode=ctx.mode,
                risk_profile=ctx.risk_profile,
                disposition=legitimacy.disposition.value,
            )
        if not legitimacy.allowed:
            return _wrap_ul_payload({
                "legitimacy": legitimacy,
                "l1": l1,
                "j1010": j1010,
                "debt": debt_assessment,
                "final_truth": final_truth,
                "status": legitimacy.disposition.value,
                "reason": legitimacy.reason,
                "event_log": list(ctx.event_log),
            })

        ttl, scores = self.compute_adaptive_ttl(ctx, request, l1, j1010, debt_assessment, final_truth, legitimacy)
        ready_at = submitted_at + ttl
        ctx.last_ready_at = ready_at
        ctx.last_ttl_seconds = int(ttl.total_seconds())
        ctx.log(
            CHRONOS_TTL_EVENT,
            ttl_seconds=ctx.last_ttl_seconds,
            submitted_at=submitted_at.isoformat(),
            ready_at=ready_at.isoformat(),
            scores=scores,
        )
        if current_time < ready_at:
            drift = self.apply_recovery_drift(ctx)
            next_check_at = self.schedule_recheck(ctx, request, current_time, ready_at)
            ctx.log(RECOVERY_DRIFT_EVENT, **drift)
            ctx.log(
                WAIT_RECHECK_EVENT,
                status=CycleDisposition.WAIT.value,
                ready_at=ready_at.isoformat(),
                next_check_at=next_check_at.isoformat(),
                ttl_seconds=ctx.last_ttl_seconds,
                recheck_count=int(request.recheck_count or 0),
                mode=ctx.mode,
            )
            return _wrap_ul_payload({
                "legitimacy": legitimacy,
                "l1": l1,
                "j1010": j1010,
                "debt": debt_assessment,
                "final_truth": final_truth,
                "status": CycleDisposition.WAIT.value,
                "ttl_seconds": ctx.last_ttl_seconds,
                "ready_at": ready_at.isoformat(),
                "next_check_at": next_check_at.isoformat(),
                "scores": scores,
                "event_log": list(ctx.event_log),
            })

        admitted = self.admit(ctx, final_truth, debt_assessment.record)
        ctx.current_state = admitted.state
        ctx.prime_depth = admitted.prime_depth
        ctx.debt = admitted.debt.copy()
        ctx.logs_flushed = True
        ctx.debt_persisted = True
        ctx.next_check_at = None
        request.next_check_at = None
        ctx.operator_review_required = False
        ctx.log("admit", prime_depth=admitted.prime_depth, debt_total=admitted.debt.total)

        stabilization = self.stabilize(ctx, admitted)
        ctx.log(
            DELTA_STABILIZATION_EVENT,
            complete=stabilization.complete,
            attempts=stabilization.attempts,
            burden=stabilization.burden_state.value,
            status=stabilization.status.value,
        )
        if stabilization.status in {ExecutionResult.PARTIAL, ExecutionResult.UNSTABLE}:
            self.propagate_error(ctx, stabilization.status)

        protagonist_fate = FateLine(name=f"cycle_{ctx.cycle_count}_self")
        external_fate = FateLine(name=request.external_influence)
        merged_fate, binding_status = self.voss_binding(ctx, protagonist_fate, external_fate)
        ctx.log("voss_binding", status=binding_status.value, merged=(merged_fate.protagonist, merged_fate.influence))
        if binding_status == ExecutionResult.PARTIAL:
            self.propagate_error(ctx, binding_status)

        next_state, strength_bonus, burden_after = self.next_1000(ctx, admitted)
        ctx.log(
            "next_1000",
            state=next_state,
            strength_bonus=strength_bonus,
            burden=burden_after.value,
            debt_total=ctx.debt.total,
        )

        return _wrap_ul_payload({
            "legitimacy": legitimacy,
            "l1": l1,
            "j1010": j1010,
            "debt": debt_assessment,
            "final_truth": final_truth,
            "status": final_truth.status.value.lower(),
            "admitted": admitted,
            "stabilization": stabilization,
            "binding": merged_fate,
            "next_state": next_state,
            "strength_bonus": strength_bonus,
            "burden": burden_after,
            "event_log": list(ctx.event_log),
        })


if __name__ == "__main__":
    machine = ProjectInfiStateMachine()
    context = CycleContext(bound_flag=True)  # seed a prior lawful bind for demo entry

    proposal = ProposedChange(
        kind="repo_change",
        authority="forge",
        context_valid=True,
        protected_access_requested=False,
        operator_approved=True,
        risk_level="medium",
        evidence_present=True,
        design_quality=0.86,
        debt_pressure=2,
        external_influence="forge_lane",
    )

    result = machine.run_cycle(context, proposal)
    print("Project Infi cycle complete")
    print(f"Final truth: {result['final_truth'].summary}")
    print(f"Prime depth: {result['admitted'].prime_depth}")
    print(f"Debt total: {result['admitted'].debt.total}")
    print(f"Next state: {result['next_state']}")
    print(f"Burden: {result['burden'].value}")
