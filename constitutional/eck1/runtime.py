"""ECK-1 Runtime — canonical epistemic pipeline executor."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from constitutional.core.models import StateObject
from constitutional.eck1.models import ContinuityState, ECK1PipelineResult
from constitutional.eck1.registers import (
    ECK1_CONTINUITY_STATE_ID,
    load_calibration_register,
    load_environment_register,
    save_calibration_register,
    save_environment_register,
)
from constitutional.eck1.transitions import (
    append_to_ledgers,
    calibration_transition,
    environment_state_from_inputs,
    judgment_transition,
    perception_transition,
    prior_state_from_inputs,
    significance_transition,
)
from constitutional.priors.ledger import load_prior_ledger, save_prior_ledger
from constitutional.salience.ledger import load_salience_ledger, save_salience_ledger
from constitutional.runtime.runtime import ConstitutionalStateRuntime


class ECK1Registers:
    """Bundle of ECK-1 ledgers and registers."""

    def __init__(self, csr: ConstitutionalStateRuntime) -> None:
        self.csr = csr
        self.prior = _PriorRegister(csr)
        self.salience = _SalienceRegister(csr)
        self.env = _EnvironmentRegister(csr)
        self.calibration = _CalibrationRegister()
        self.judgment = _JudgmentRegister()
        self.significance = _SignificanceRegister()
        self.continuity = _ContinuityRegister(csr)


class _PriorRegister:
    def __init__(self, csr: ConstitutionalStateRuntime) -> None:
        self._csr = csr

    def load(self, steward_inputs: dict[str, Any]):
        return prior_state_from_inputs(steward_inputs)


class _SalienceRegister:
    def __init__(self, csr: ConstitutionalStateRuntime) -> None:
        self._csr = csr

    def derive(self, priors, env):
        return perception_transition(priors, env)


class _EnvironmentRegister:
    def __init__(self, csr: ConstitutionalStateRuntime) -> None:
        self._csr = csr

    def load(self, steward_inputs: dict[str, Any] | None = None):
        return environment_state_from_inputs(steward_inputs or {})


class _CalibrationRegister:
    def derive(self, salience, env):
        return calibration_transition(salience, env)


class _JudgmentRegister:
    def derive(self, calibration, steward_inputs: dict[str, Any]):
        return judgment_transition(
            calibration,
            decision_id=steward_inputs.get("decision_id", "unknown"),
            outcome=steward_inputs.get("outcome", "pending"),
            rationale=steward_inputs.get("rationale", ""),
            applied_invariants=steward_inputs.get("applied_invariants"),
            applied_purpose_clauses=steward_inputs.get("applied_purpose_clauses"),
            steward_id=steward_inputs.get("steward_id", "steward"),
        )


class _SignificanceRegister:
    def derive(self, judgment, steward_inputs: dict[str, Any] | None = None):
        inputs = steward_inputs or {}
        return significance_transition(
            judgment,
            artifact_id=inputs.get("artifact_id", judgment.decision_id),
            tier=inputs.get("tier", 2),
            rationale=inputs.get("significance_rationale", judgment.rationale),
        )


class _ContinuityRegister:
    def __init__(self, csr: ConstitutionalStateRuntime) -> None:
        self._csr = csr

    def preserve(self, priors, salience, env, calibration, judgment, significance, continuity: ContinuityState) -> None:
        prior_ledger = load_prior_ledger(self._csr)
        salience_ledger = load_salience_ledger(self._csr)
        calibration_register = load_calibration_register(self._csr)
        environment_register = load_environment_register(self._csr)

        append_to_ledgers(
            prior_ledger,
            salience_ledger,
            calibration_register,
            environment_register,
            priors=priors,
            salience=salience,
            environment=env,
            calibration=calibration,
        )
        save_prior_ledger(self._csr, prior_ledger)
        save_salience_ledger(self._csr, salience_ledger)
        save_calibration_register(self._csr, calibration_register)
        save_environment_register(self._csr, environment_register)

        self._csr.register_or_replace_state(
            StateObject(
                state_id=ECK1_CONTINUITY_STATE_ID,
                state_type="eck1_continuity",
                current_state="Observed",
            )
        )
        self._csr.put_domain_doc(ECK1_CONTINUITY_STATE_ID, "eck1_continuity", continuity)


class ECK1Runtime:
    """Runs the mandatory ECK-1 epistemic pipeline."""

    def __init__(self, csr: ConstitutionalStateRuntime) -> None:
        self.csr = csr
        self.reg = ECK1Registers(csr)

    def run(
        self,
        steward_inputs: dict[str, Any],
        *,
        continuity_indices: ContinuityState | None = None,
        snapshot_at: datetime | None = None,
    ) -> ECK1PipelineResult:
        now = snapshot_at or datetime.now(UTC).replace(microsecond=0)
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)

        priors = self.reg.prior.load(steward_inputs)
        env = self.reg.env.load(steward_inputs)
        salience = self.reg.salience.derive(priors, env)
        calibration = self.reg.calibration.derive(salience, env)
        judgment = self.reg.judgment.derive(calibration, steward_inputs)
        significance = self.reg.significance.derive(judgment, steward_inputs)

        continuity = continuity_indices or ContinuityState(captured_at=now)
        self.reg.continuity.preserve(
            priors, salience, env, calibration, judgment, significance, continuity
        )

        return ECK1PipelineResult(
            priors=priors,
            salience=salience,
            environment=env,
            calibration=calibration,
            judgment=judgment,
            significance=significance,
            continuity=continuity,
        )
