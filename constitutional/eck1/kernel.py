"""ECK-1 minimal reference implementation (normative spec § appendix)."""

from __future__ import annotations

from typing import Any

from constitutional.eck1.models import SignificanceState
from constitutional.eck1.runtime import ECK1Registers, ECK1Runtime


class ECK1:
    """The smallest runnable kernel that satisfies the ECK-1 spec."""

    def __init__(self, registers: ECK1Registers) -> None:
        self.reg = registers

    def run(self, steward_inputs: dict[str, Any]) -> SignificanceState:
        priors = self.reg.prior.load(steward_inputs)
        env = self.reg.env.load(steward_inputs)
        salience = self.reg.salience.derive(priors, env)
        calibration = self.reg.calibration.derive(salience, env)
        judgment = self.reg.judgment.derive(calibration, steward_inputs)
        significance = self.reg.significance.derive(judgment, steward_inputs)

        from constitutional.eck1.models import ContinuityState

        self.reg.continuity.preserve(
            priors,
            salience,
            env,
            calibration,
            judgment,
            significance,
            ContinuityState(),
        )
        return significance


def eck1_from_csr(csr) -> ECK1:
    """Construct minimal ECK1 kernel from a ConstitutionalStateRuntime."""
    return ECK1(ECK1Registers(csr))


def eck1_runtime_from_csr(csr) -> ECK1Runtime:
    return ECK1Runtime(csr)
