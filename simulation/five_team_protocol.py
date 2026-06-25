"""Five-Team adversarial protocol — attack scoring, drift indices, amendment triggers."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

TeamRole = Literal["red", "blue", "black", "white", "gold"]
InvariantStatus = Literal["stable", "refined", "weakened", "broken"]
AmendmentTriggerId = Literal["A", "B", "C", "D"]
KernelBreakId = Literal["break_1", "break_2", "break_3", "break_4"]
ContinuityHealthSignal = Literal[
    "healthy",
    "rigid_fragile",
    "doctrine_mode",
    "kernel_failure",
    "in_progress",
]

ATTACK_SCORE_MAX = 10
DRIFT_INDEX_MAX = 12
AMENDMENT_ATTACK_THRESHOLD = 7
AMENDMENT_REPEAT_ROUNDS = 3
HIGH_DRIFT_THRESHOLD = 8
HIGH_ATTACK_THRESHOLD = 7
DEFAULT_MIN_ROUNDS = 10
DEFAULT_MAX_ROUNDS = 20
NON_TRIVIAL_ATTACK_THRESHOLD = 3


class AttackRecord(BaseModel):
    """Red or Black Team attack with S + N + E scoring."""

    round_id: int
    team: Literal["red", "black"]
    attack_id: str
    target: str
    description: str
    severity: int = Field(ge=0, le=4)
    novelty: int = Field(ge=0, le=3)
    exploitability: int = Field(ge=0, le=3)

    @property
    def attack_score(self) -> int:
        return min(ATTACK_SCORE_MAX, self.severity + self.novelty + self.exploitability)

    @property
    def is_non_trivial(self) -> bool:
        return self.attack_score >= NON_TRIVIAL_ATTACK_THRESHOLD


class DriftAssessment(BaseModel):
    """Gold Team drift indices — DD + RD + BD."""

    round_id: int
    definition_drift: int = Field(ge=0, le=4, default=0)
    rule_drift: int = Field(ge=0, le=4, default=0)
    behavior_drift: int = Field(ge=0, le=4, default=0)

    @property
    def drift_index(self) -> int:
        return min(
            DRIFT_INDEX_MAX,
            self.definition_drift + self.rule_drift + self.behavior_drift,
        )


class InvariantValidationRecord(BaseModel):
    """Blue + White + Gold invariant status for one round."""

    invariant_id: str
    round_id: int
    status: InvariantStatus
    red_attack_ids: list[str] = Field(default_factory=list)
    blue_defense: str = ""
    white_coherence: bool = True
    white_enforceable: bool = True
    white_necessary: bool = True
    notes: str = ""


class AmendmentTriggerResult(BaseModel):
    trigger: AmendmentTriggerId
    fired: bool
    explanation: str


class KernelFailureSnapshot(BaseModel):
    """Gold snapshot when a kernel failure is declared."""

    round_id: int
    last_stable_round: int | None = None
    failure_conditions: list[str] = Field(default_factory=list)
    drift_trajectory: list[int] = Field(default_factory=list)
    attack_trajectory: list[int] = Field(default_factory=list)


class KernelFailureEvent(BaseModel):
    break_id: KernelBreakId
    detected: bool
    explanation: str
    snapshot: KernelFailureSnapshot | None = None


class RoundProtocolResult(BaseModel):
    round_id: int
    attacks: list[AttackRecord] = Field(default_factory=list)
    drift: DriftAssessment
    invariant_records: list[InvariantValidationRecord] = Field(default_factory=list)
    max_attack_score: int = 0
    avg_attack_score: float = 0.0
    drift_index: int = 0
    continuity_signal: ContinuityHealthSignal = "in_progress"
    amendment_triggers: list[AmendmentTriggerResult] = Field(default_factory=list)
    amendment_required: bool = False
    kernel_failure: KernelFailureEvent | None = None
    red_exhausted: bool = False
    black_exhausted: bool = False


class CampaignConfig(BaseModel):
    subsystem: str = "CSS-1 + RA-COS-1 + CRK-1"
    invariant_target: str = "K4 — Reconstructability"
    min_rounds: int = DEFAULT_MIN_ROUNDS
    max_rounds: int = DEFAULT_MAX_ROUNDS


class CampaignState(BaseModel):
    config: CampaignConfig = Field(default_factory=CampaignConfig)
    rounds: list[RoundProtocolResult] = Field(default_factory=list)
    should_continue: bool = True
    stop_reason: str | None = None
    rounds_completed: int = 0

    @field_validator("rounds", mode="before")
    @classmethod
    def _ensure_list(cls, value: object) -> object:
        return value or []


def score_attack(severity: int, novelty: int, exploitability: int) -> int:
    """AttackScore = S + N + E (max 10)."""
    return min(
        ATTACK_SCORE_MAX,
        max(0, min(4, severity)) + max(0, min(3, novelty)) + max(0, min(3, exploitability)),
    )


def classify_continuity_signal(
    drift_index: int,
    attack_score: int,
) -> ContinuityHealthSignal:
    """
    High DriftIndex + low AttackScore → doctrine.
    High AttackScore + low DriftIndex → rigid but fragile.
    Balanced low drift + decreasing attack → healthy.
    """
    if drift_index >= HIGH_DRIFT_THRESHOLD and attack_score >= HIGH_ATTACK_THRESHOLD:
        return "doctrine_mode"
    if drift_index >= HIGH_DRIFT_THRESHOLD and attack_score < HIGH_ATTACK_THRESHOLD:
        return "doctrine_mode"
    if attack_score >= HIGH_ATTACK_THRESHOLD and drift_index < 4:
        return "rigid_fragile"
    if drift_index <= 4 and attack_score <= NON_TRIVIAL_ATTACK_THRESHOLD:
        return "healthy"
    return "in_progress"


def derive_drift_from_metrics(
    round_id: int,
    *,
    adm_drift_score: float,
    adm_high_drift: bool,
    k4_satisfied: bool,
    crk1_compliant: bool,
    prior_drift_index: int = 0,
) -> DriftAssessment:
    """Map Gold instrumentation to DD / RD / BD (automated heuristic)."""
    dd = 0
    rd = 0
    bd = 0

    if adm_drift_score >= 0.6:
        bd = 3
        rd = 2
    elif adm_drift_score >= 0.35:
        bd = 2
        rd = 1
    elif adm_drift_score >= 0.15:
        bd = 1

    if adm_high_drift:
        rd = max(rd, 2)
        dd = max(dd, 1)

    if not k4_satisfied:
        bd = max(bd, 3)
        dd = max(dd, 2)

    if not crk1_compliant:
        rd = max(rd, 3)
        dd = max(dd, 1)

    if prior_drift_index >= HIGH_DRIFT_THRESHOLD:
        dd = max(dd, 2)

    return DriftAssessment(
        round_id=round_id,
        definition_drift=dd,
        rule_drift=rd,
        behavior_drift=bd,
    )


def derive_attacks_from_chaos(
    round_id: int,
    chaos_results: list[dict[str, object]],
) -> list[AttackRecord]:
    """Black Team — score chaos fixtures as attacks."""
    attacks: list[AttackRecord] = []
    for index, result in enumerate(chaos_results):
        name = str(result.get("scenario", f"chaos-{index}"))
        vas_ok = bool(result.get("vas_validated"))
        passed = bool(result.get("chaos_test_passed"))

        if name == "acceptance_without_validation":
            attacks.append(
                AttackRecord(
                    round_id=round_id,
                    team="black",
                    attack_id=f"black-{round_id}-{index}",
                    target="VAS-1 / RAG-Loop",
                    description="Acceptance without validation — FAP bypass attempt",
                    severity=3,
                    novelty=2,
                    exploitability=2,
                )
            )
        elif not passed:
            attacks.append(
                AttackRecord(
                    round_id=round_id,
                    team="black",
                    attack_id=f"black-{round_id}-{index}",
                    target="RA-COS-1 integration",
                    description=f"Chaos scenario {name} produced unexpected survival",
                    severity=2,
                    novelty=1 if vas_ok else 2,
                    exploitability=2,
                )
            )
        else:
            attacks.append(
                AttackRecord(
                    round_id=round_id,
                    team="black",
                    attack_id=f"black-{round_id}-{index}",
                    target="RA-COS-1 integration",
                    description=f"Chaos scenario {name} — contained",
                    severity=1,
                    novelty=0,
                    exploitability=1,
                )
            )
    return attacks


def derive_red_attacks(
    round_id: int,
    *,
    k4_satisfied: bool,
    adm_high_drift: bool,
    psd_aggregate: float,
    invariant_target: str,
) -> list[AttackRecord]:
    """Red Team — PSDD-1 drift injection attacks from Gold metrics."""
    attacks: list[AttackRecord] = []

    if adm_high_drift:
        attacks.append(
            AttackRecord(
                round_id=round_id,
                team="red",
                attack_id=f"red-{round_id}-adm",
                target="ADM-1 accumulation drift",
                description="Accumulation drift exceeds steward cognitive load threshold",
                severity=2,
                novelty=2,
                exploitability=2,
            )
        )

    if psd_aggregate >= 0.5:
        attacks.append(
            AttackRecord(
                round_id=round_id,
                team="red",
                attack_id=f"red-{round_id}-psd",
                target="PSDD-1",
                description=f"Post-surpassment drift aggregate {psd_aggregate:.2f}",
                severity=2,
                novelty=1,
                exploitability=2,
            )
        )

    if not k4_satisfied:
        attacks.append(
            AttackRecord(
                round_id=round_id,
                team="red",
                attack_id=f"red-{round_id}-k4",
                target=invariant_target,
                description="K4 reconstructability invariant under stress",
                severity=4,
                novelty=2,
                exploitability=3,
            )
        )

    if not attacks:
        attacks.append(
            AttackRecord(
                round_id=round_id,
                team="red",
                attack_id=f"red-{round_id}-probe",
                target=invariant_target,
                description="Routine invariant probe — no elevated drift detected",
                severity=0,
                novelty=0,
                exploitability=0,
            )
        )

    return attacks


def evaluate_invariant_statuses(
    round_id: int,
    attacks: list[AttackRecord],
    drift: DriftAssessment,
    *,
    k4_satisfied: bool,
    crk1_compliant: bool,
    invariant_ids: list[str] | None = None,
) -> list[InvariantValidationRecord]:
    """Blue + White + Gold — record invariant validation status."""
    targets = invariant_ids or ["K1", "K2", "K3", "K4"]
    records: list[InvariantValidationRecord] = []

    for inv_id in targets:
        related = [attack for attack in attacks if inv_id.lower() in attack.target.lower() or inv_id in attack.target]
        max_score = max((attack.attack_score for attack in related), default=0)

        if inv_id == "K4" and not k4_satisfied:
            status: InvariantStatus = "broken" if max_score >= 7 else "weakened"
        elif max_score >= 7 and drift.rule_drift >= 2:
            status = "weakened"
        elif max_score >= 4 and drift.rule_drift >= 1:
            status = "refined"
        elif max_score >= 7:
            status = "weakened"
        else:
            status = "stable"

        if inv_id.startswith("K") and not crk1_compliant and status == "stable":
            status = "refined"

        records.append(
            InvariantValidationRecord(
                invariant_id=inv_id,
                round_id=round_id,
                status=status,
                red_attack_ids=[attack.attack_id for attack in related if attack.team == "red"],
                blue_defense=(
                    f"Invariant {inv_id} defended — attack score {max_score}, drift {drift.drift_index}."
                    if status in {"stable", "refined"}
                    else f"Invariant {inv_id} under stress — requires refinement or amendment."
                ),
                white_coherence=status != "broken",
                white_enforceable=crk1_compliant or status != "broken",
                white_necessary=True,
            )
        )

    return records


def evaluate_amendment_triggers(
    rounds: list[RoundProtocolResult],
    *,
    structural_contradiction: bool = False,
) -> list[AmendmentTriggerResult]:
    """CRK-1 amendment triggers A–D."""
    if not rounds:
        return [
            AmendmentTriggerResult(trigger="A", fired=False, explanation="No rounds yet."),
            AmendmentTriggerResult(trigger="B", fired=False, explanation="No rounds yet."),
            AmendmentTriggerResult(trigger="C", fired=False, explanation="No rounds yet."),
            AmendmentTriggerResult(trigger="D", fired=False, explanation="No rounds yet."),
        ]

    latest = rounds[-1]

    trigger_a = False
    trigger_a_explanation = "No repeated high-severity attacks on same target."
    target_high_rounds: dict[str, int] = {}
    for round_result in rounds:
        for attack in round_result.attacks:
            if attack.attack_score >= AMENDMENT_ATTACK_THRESHOLD:
                target_high_rounds[attack.target] = target_high_rounds.get(attack.target, 0) + 1
    for target, count in target_high_rounds.items():
        if count >= AMENDMENT_REPEAT_ROUNDS:
            trigger_a = True
            trigger_a_explanation = (
                f"Target '{target}' received AttackScore ≥ {AMENDMENT_ATTACK_THRESHOLD} "
                f"in {count} rounds (Trigger A)."
            )
            break

    trigger_b = structural_contradiction
    trigger_b_explanation = (
        "White Team identified structural contradiction between core invariants (Trigger B)."
        if trigger_b
        else "No structural contradiction detected."
    )

    trigger_c = latest.drift_index >= HIGH_DRIFT_THRESHOLD
    trigger_c_explanation = (
        f"DriftIndex {latest.drift_index} ≥ {HIGH_DRIFT_THRESHOLD} at kernel layer (Trigger C)."
        if trigger_c
        else f"DriftIndex {latest.drift_index} below kernel amendment threshold."
    )

    broken_core = [
        record
        for record in latest.invariant_records
        if record.status == "broken" and record.invariant_id in {"K1", "K2", "K3", "K4"}
    ]
    trigger_d = bool(broken_core) and not any(
        record.status == "refined" for record in latest.invariant_records if record.invariant_id in {"K1", "K2", "K3", "K4"}
    )
    trigger_d_explanation = (
        f"Core invariant(s) broken without repair path: {[r.invariant_id for r in broken_core]} (Trigger D)."
        if trigger_d
        else "No unrecoverable broken core invariants."
    )

    return [
        AmendmentTriggerResult(trigger="A", fired=trigger_a, explanation=trigger_a_explanation),
        AmendmentTriggerResult(trigger="B", fired=trigger_b, explanation=trigger_b_explanation),
        AmendmentTriggerResult(trigger="C", fired=trigger_c, explanation=trigger_c_explanation),
        AmendmentTriggerResult(trigger="D", fired=trigger_d, explanation=trigger_d_explanation),
    ]


def detect_kernel_failure(
    rounds: list[RoundProtocolResult],
    *,
    vas1_indistinguishable: bool = False,
    convergence_failure: bool = False,
) -> KernelFailureEvent | None:
    """Detect Break 1–4 conditions."""
    if not rounds:
        return None

    latest = rounds[-1]
    broken_count = sum(1 for record in latest.invariant_records if record.status == "broken")
    drift_trajectory = [round_result.drift_index for round_result in rounds]
    attack_trajectory = [round_result.max_attack_score for round_result in rounds]

    snapshot = KernelFailureSnapshot(
        round_id=latest.round_id,
        last_stable_round=next(
            (round_result.round_id for round_result in reversed(rounds) if round_result.continuity_signal == "healthy"),
            None,
        ),
        failure_conditions=[],
        drift_trajectory=drift_trajectory,
        attack_trajectory=attack_trajectory,
    )

    if broken_count >= 2:
        snapshot.failure_conditions.append(f"{broken_count} core invariants marked Broken")
        return KernelFailureEvent(
            break_id="break_1",
            detected=True,
            explanation="Unenforceable constitution — multiple core invariants Broken (Break 1).",
            snapshot=snapshot,
        )

    if (
        latest.drift_index >= HIGH_DRIFT_THRESHOLD
        and latest.max_attack_score >= HIGH_ATTACK_THRESHOLD
        and latest.continuity_signal == "doctrine_mode"
    ):
        snapshot.failure_conditions.append("High drift + high attack + doctrine redefinition pattern")
        return KernelFailureEvent(
            break_id="break_2",
            detected=True,
            explanation="Doctrine mode — invariants redefined to win arguments (Break 2).",
            snapshot=snapshot,
        )

    if vas1_indistinguishable:
        snapshot.failure_conditions.append("VAS-1 cannot distinguish continuity failures from narrative disagreement")
        return KernelFailureEvent(
            break_id="break_3",
            detected=True,
            explanation="Validation collapse — VAS-1 indistinguishable (Break 3).",
            snapshot=snapshot,
        )

    if convergence_failure:
        snapshot.failure_conditions.append("Teams cannot converge on system identity or behavior")
        return KernelFailureEvent(
            break_id="break_4",
            detected=True,
            explanation="Convergence failure — no shared model of system (Break 4).",
            snapshot=snapshot,
        )

    return None


def assess_team_exhaustion(round_result: RoundProtocolResult) -> tuple[bool, bool]:
    """Red exhausted when no non-trivial attacks; Black when all chaos contained trivially."""
    red_attacks = [attack for attack in round_result.attacks if attack.team == "red"]
    black_attacks = [attack for attack in round_result.attacks if attack.team == "black"]

    red_exhausted = not any(attack.is_non_trivial for attack in red_attacks)
    black_exhausted = all(attack.attack_score <= 2 for attack in black_attacks) if black_attacks else True

    return red_exhausted, black_exhausted


def should_stop_campaign(state: CampaignState) -> tuple[bool, str | None]:
    """
    Stopping rules:
    - Minimum 10 rounds before early stop
    - Stop when Red + Black exhausted AND min rounds met
    - Force stop at max_rounds
    - Force stop on kernel failure
    """
    config = state.config
    completed = len(state.rounds)

    if completed >= config.max_rounds:
        return True, f"Maximum rounds ({config.max_rounds}) reached."

    if completed < config.min_rounds:
        return False, None

    latest = state.rounds[-1]

    if latest.kernel_failure:
        return True, f"Kernel failure: {latest.kernel_failure.explanation}"

    if latest.drift_index >= 6 or latest.max_attack_score >= AMENDMENT_ATTACK_THRESHOLD:
        return False, None

    red_exhausted, black_exhausted = assess_team_exhaustion(latest)

    if red_exhausted and black_exhausted:
        return True, (
            f"Early stop after {completed} rounds — Red/Black attacks redundant "
            f"(max attack score {latest.max_attack_score})."
        )

    return False, None


def build_round_protocol(
    round_id: int,
    *,
    adm_drift_score: float,
    adm_high_drift: bool,
    k4_satisfied: bool,
    crk1_compliant: bool,
    psd_aggregate: float,
    chaos_results: list[dict[str, object]],
    invariant_target: str,
    prior_drift_index: int = 0,
    structural_contradiction: bool = False,
    vas1_indistinguishable: bool = False,
    convergence_failure: bool = False,
    prior_rounds: list[RoundProtocolResult] | None = None,
) -> RoundProtocolResult:
    """Assemble full protocol result for one round."""
    drift = derive_drift_from_metrics(
        round_id,
        adm_drift_score=adm_drift_score,
        adm_high_drift=adm_high_drift,
        k4_satisfied=k4_satisfied,
        crk1_compliant=crk1_compliant,
        prior_drift_index=prior_drift_index,
    )

    red_attacks = derive_red_attacks(
        round_id,
        k4_satisfied=k4_satisfied,
        adm_high_drift=adm_high_drift,
        psd_aggregate=psd_aggregate,
        invariant_target=invariant_target,
    )
    black_attacks = derive_attacks_from_chaos(round_id, chaos_results)
    all_attacks = red_attacks + black_attacks

    max_score = max((attack.attack_score for attack in all_attacks), default=0)
    avg_score = sum(attack.attack_score for attack in all_attacks) / len(all_attacks) if all_attacks else 0.0

    invariant_records = evaluate_invariant_statuses(
        round_id,
        all_attacks,
        drift,
        k4_satisfied=k4_satisfied,
        crk1_compliant=crk1_compliant,
    )

    continuity_signal = classify_continuity_signal(drift.drift_index, max_score)
    red_exhausted, black_exhausted = assess_team_exhaustion(
        RoundProtocolResult(
            round_id=round_id,
            attacks=all_attacks,
            drift=drift,
            max_attack_score=max_score,
            red_exhausted=False,
            black_exhausted=False,
        )
    )

    all_rounds = list(prior_rounds or []) + [
        RoundProtocolResult(
            round_id=round_id,
            attacks=all_attacks,
            drift=drift,
            invariant_records=invariant_records,
            max_attack_score=max_score,
            avg_attack_score=avg_score,
            drift_index=drift.drift_index,
            continuity_signal=continuity_signal,
            red_exhausted=red_exhausted,
            black_exhausted=black_exhausted,
        )
    ]

    amendment_triggers = evaluate_amendment_triggers(
        all_rounds,
        structural_contradiction=structural_contradiction,
    )
    amendment_required = any(trigger.fired for trigger in amendment_triggers)
    kernel_failure = detect_kernel_failure(
        all_rounds,
        vas1_indistinguishable=vas1_indistinguishable,
        convergence_failure=convergence_failure,
    )

    return RoundProtocolResult(
        round_id=round_id,
        attacks=all_attacks,
        drift=drift,
        invariant_records=invariant_records,
        max_attack_score=max_score,
        avg_attack_score=avg_score,
        drift_index=drift.drift_index,
        continuity_signal=continuity_signal,
        amendment_triggers=amendment_triggers,
        amendment_required=amendment_required,
        kernel_failure=kernel_failure,
        red_exhausted=red_exhausted,
        black_exhausted=black_exhausted,
    )


def format_attack_log(attacks: list[AttackRecord]) -> str:
    lines = ["| Team | ID | S+N+E | Target | Description |", "|------|-----|-------|--------|-------------|"]
    for attack in attacks:
        lines.append(
            f"| {attack.team} | {attack.attack_id} | {attack.attack_score} | "
            f"{attack.target} | {attack.description[:60]} |"
        )
    return "\n".join(lines)


def format_drift_report(drift: DriftAssessment) -> str:
    return (
        f"DriftIndex={drift.drift_index}/12 "
        f"(DD={drift.definition_drift}, RD={drift.rule_drift}, BD={drift.behavior_drift})"
    )
