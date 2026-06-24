"""CRK-1 Drift Simulator — constitutional wind tunnel for CE(S) and SE(S)."""

from __future__ import annotations

from typing import Any, Callable

from src.crk1.consequence_lattice import (
    ConsequenceExposure,
    apply_amendment_with_drift_check,
    consequence_exposure,
    validate_drift_envelope,
)
from src.crk1.errors import ConstitutionalError
from src.crk1.runtime_facade import CRK1Runtime
from src.crk1.semantic_exposure_monitor import SemanticExposureMonitor

MutationTarget = str
CeFn = Callable[[CRK1Runtime], float]
SeFn = Callable[[CRK1Runtime], float]


def is_admissible_drift_result(result: dict[str, Any]) -> bool:
    """True when mutation applied under envelope or was constitutionally rejected."""
    if result.get("constitutional"):
        return True
    return bool(result.get("error"))


class DriftSimulator:
    """
    Deterministic simulator for testing CE(S) and SE(S) under mutation.

    Checks K6 (constitutional drift envelope) and K11 (interpretive drift envelope).
    """

    def __init__(
        self,
        runtime: CRK1Runtime,
        ce_fn: CeFn | None = None,
        se_fn: SeFn | None = None,
        *,
        semantic_monitor: SemanticExposureMonitor | None = None,
        mutation_ledger: Any | None = None,
    ) -> None:
        self.runtime = runtime
        self._monitor = semantic_monitor or SemanticExposureMonitor(runtime)
        self.runtime.attach_semantic_monitor(self._monitor)
        self._mutation_ledger = mutation_ledger
        self.CE: CeFn = ce_fn or (lambda rt: consequence_exposure(rt).score)
        self.SE: SeFn = se_fn or (lambda _rt: self._monitor.measure_exposure())

    def apply_mutation(self, mutation: dict[str, Any]) -> None:
        """
        Apply a constitutional, interpretive, or governance mutation.

        mutation = {
          "changes": {...},
          "target": "constitution" | "interpretation" | "governance"
        }
        """
        target: MutationTarget = mutation.get("target", "constitution")
        changes: dict[str, Any] = dict(mutation.get("changes") or {})

        if target == "interpretation":
            self.runtime.apply_semantic_drift()
            return

        if target == "governance":
            self.runtime.apply_amendment(changes)
            return

        apply_amendment_with_drift_check(self.runtime, changes)

    def measure(self) -> dict[str, float]:
        return {"CE": self.CE(self.runtime), "SE": self.SE(self.runtime)}

    def test_drift(self, mutation: dict[str, Any]) -> dict[str, Any]:
        before = self.measure()
        try:
            self.apply_mutation(mutation)
        except ConstitutionalError:
            return {
                "mutation": mutation,
                "before": before,
                "after": before,
                "CE_preserved": False,
                "SE_preserved": False,
                "constitutional": False,
                "error": "mutation_rejected",
            }
        after = self.measure()
        ce_ok = after["CE"] >= before["CE"] - 1e-9
        se_ok = after["SE"] >= before["SE"] - 1e-9
        result = {
            "mutation": mutation,
            "before": before,
            "after": after,
            "CE_preserved": ce_ok,
            "SE_preserved": se_ok,
            "constitutional": ce_ok and se_ok,
        }
        self._maybe_record_mutation(mutation, result)
        return result

    def _maybe_record_mutation(self, mutation: dict[str, Any], result: dict[str, Any]) -> None:
        if self._mutation_ledger is None:
            return
        from src.crk1.mutation_ledger import record_drift_test

        proposer = self.runtime.kernel.ledgers.identity.id
        record_drift_test(
            self._mutation_ledger,
            runtime=self.runtime,
            mutation=mutation,
            drift_result=result,
            proposer_identity=proposer,
            justification=str(mutation.get("justification", "")),
            evidence_ids=list(mutation.get("evidence_ids") or []),
        )

    def test_mutation_set(self, mutations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [self.test_drift(mutation) for mutation in mutations]

    def test_drift_with_exposure(
        self,
        mutation: dict[str, Any],
    ) -> dict[str, Any]:
        """Extended result including full ConsequenceExposure before/after."""
        ce_before = consequence_exposure(self.runtime)
        se_before = self.SE(self.runtime)
        before = {"CE": ce_before.score, "SE": se_before}
        try:
            self.apply_mutation(mutation)
        except ConstitutionalError as exc:
            return {
                "mutation": mutation,
                "before": before,
                "after": before,
                "ce_detail_before": ce_before.to_dict(),
                "ce_detail_after": ce_before.to_dict(),
                "CE_preserved": False,
                "SE_preserved": False,
                "constitutional": False,
                "error": str(exc),
            }
        ce_after = consequence_exposure(self.runtime)
        se_after = self.SE(self.runtime)
        after = {"CE": ce_after.score, "SE": se_after}
        try:
            validate_drift_envelope(ce_before, ce_after)
            ce_ok = True
        except ConstitutionalError:
            ce_ok = False
        se_ok = se_after >= se_before - 1e-9
        result = {
            "mutation": mutation,
            "before": before,
            "after": after,
            "ce_detail_before": ce_before.to_dict(),
            "ce_detail_after": ce_after.to_dict(),
            "CE_preserved": ce_ok,
            "SE_preserved": se_ok,
            "constitutional": ce_ok and se_ok,
        }
        self._maybe_record_mutation(mutation, result)
        return result
