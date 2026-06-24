"""Mission #003 drift envelope stress protocol (M3-C)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from src.crk1.drift_simulator import DriftSimulator, is_admissible_drift_result
from src.crk1.mission_003_packet import (
    DRIFT_C1_BENIGN,
    DRIFT_C2_RISKY,
    DRIFT_C3_MALICIOUS,
    STRESS_BATTERY,
)
from src.crk1.mutation_ledger import CRK1MutationLedger, record_drift_test
from src.crk1.semantic_exposure_monitor import SemanticExposureMonitor

if TYPE_CHECKING:
    from src.crk1.runtime_facade import CRK1Runtime


@dataclass
class DriftStressResult:
    category: str
    mutation: dict[str, Any]
    ce_before: float
    se_before: float
    ce_after: float
    se_after: float
    constitutional: bool
    rejected: bool
    error: str = ""

    @property
    def passed(self) -> bool:
        return is_admissible_drift_result(
            {
                "constitutional": self.constitutional,
                "error": self.error or ("mutation_rejected" if self.rejected else None),
            }
        )


@dataclass
class DriftStressReport:
    results: list[DriftStressResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(item.passed for item in self.results)

    def by_category(self, category: str) -> list[DriftStressResult]:
        return [item for item in self.results if item.category == category]

    def summary(self) -> str:
        lines = ["CRK-1 Drift Envelope Stress (M3-C)"]
        for item in self.results:
            status = "PASS" if item.passed else "FAIL"
            lines.append(
                f"  [{status}] {item.category}: CE {item.ce_before:.4f}→{item.ce_after:.4f} "
                f"SE {item.se_before:.4f}→{item.se_after:.4f}"
            )
            if item.error:
                lines.append(f"           {item.error}")
        lines.append(f"Overall: {'PASS' if self.passed else 'FAIL'}")
        return "\n".join(lines)


class DriftStressProtocol:
    """
    Prove CE(S) and SE(S) cannot be driven down by any governance-admissible mutation.

    C1 — benign | C2 — risky but honest | C3 — malicious (must reject).
    """

    def __init__(self, runtime: CRK1Runtime) -> None:
        self.runtime = runtime
        self.sim = DriftSimulator(runtime, semantic_monitor=SemanticExposureMonitor(runtime))

    def test_mutation_set(
        self,
        mutations: list[dict[str, Any]],
        *,
        ledger: CRK1MutationLedger | None = None,
    ) -> list[DriftStressResult]:
        results: list[DriftStressResult] = []
        for mutation in mutations:
            drift = self.sim.test_drift_with_exposure(mutation)
            before = drift.get("before") or {}
            after = drift.get("after") or {}
            error = str(drift.get("error") or "")
            item = DriftStressResult(
                category=str(mutation.get("category", "?")),
                mutation=mutation,
                ce_before=float(before.get("CE", 0.0)),
                se_before=float(before.get("SE", 0.0)),
                ce_after=float(after.get("CE", 0.0)),
                se_after=float(after.get("SE", 0.0)),
                constitutional=bool(drift.get("constitutional")),
                rejected=bool(error),
                error=error,
            )
            results.append(item)
            if ledger is not None:
                record_drift_test(
                    ledger,
                    runtime=self.runtime,
                    mutation=mutation,
                    drift_result=drift,
                    proposer_identity=self.runtime.kernel.ledgers.identity.id,
                    justification=str(mutation.get("justification", "m3-c stress")),
                    evidence_ids=["EVD-CRK1-001"],
                )
        return results

    def run_all(self, *, record_ledger: bool = True) -> DriftStressReport:
        ledger = CRK1MutationLedger() if record_ledger else None
        report = DriftStressReport()
        report.results = self.test_mutation_set(STRESS_BATTERY, ledger=ledger)
        return report

    def run_c1_benign(self) -> list[DriftStressResult]:
        return self.test_mutation_set(DRIFT_C1_BENIGN)

    def run_c2_risky(self) -> list[DriftStressResult]:
        return self.test_mutation_set(DRIFT_C2_RISKY)

    def run_c3_malicious(self) -> list[DriftStressResult]:
        return self.test_mutation_set(DRIFT_C3_MALICIOUS)
