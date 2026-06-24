"""CRK-1 Mission #003 Reproduction Certifier."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from src.crk1.drift_stress_protocol import DriftStressProtocol
from src.crk1.crk1_redteam_suite import CRK1RedTeamSuite
from src.crk1.mission_003_packet import compute_packet_fingerprint
from src.crk1.external_reproduction_harness import (
    ExternalReproductionHarness,
    prepare_continuity_substrate,
)
from src.crk1.kernel_ledger import bootstrap_kernel_ledger_entry
from src.crk1.semantic_ledger import bootstrap_semantic_ledger

if TYPE_CHECKING:
    from src.continuity.constitutional_runtime import ConstitutionalRuntime
    from src.crk1.runtime_facade import CRK1Runtime


@dataclass
class CertificationLevels:
    r1_substrate: bool = False
    r2_invariants: bool = False
    r3_reproduction: bool = False
    r4_red_team: bool = False
    r5_drift: bool = False

    @property
    def certified(self) -> bool:
        return all(
            [
                self.r1_substrate,
                self.r2_invariants,
                self.r3_reproduction,
                self.r4_red_team,
                self.r5_drift,
            ]
        )


@dataclass
class Mission003CertificationReport:
    mission: str = "003"
    version: str = "1.0"
    levels: CertificationLevels = field(default_factory=CertificationLevels)
    kernel_ledger_hash: str = ""
    implementation_hash: str = ""
    packet_fingerprint: str = ""
    semantic_ledger_signature: str = ""
    timestamp: str = ""
    drift_tests_run: int = 0
    drift_tests_passed: int = 0
    detail: str = ""

    @property
    def certified(self) -> bool:
        return self.levels.certified

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission": self.mission,
            "version": self.version,
            "certified": self.certified,
            "levels": {
                "R1_substrate": self.levels.r1_substrate,
                "R2_invariants": self.levels.r2_invariants,
                "R3_reproduction": self.levels.r3_reproduction,
                "R4_red_team": self.levels.r4_red_team,
                "R5_drift": self.levels.r5_drift,
            },
            "kernel_ledger_hash": self.kernel_ledger_hash,
            "implementation_hash": self.implementation_hash,
            "packet_fingerprint": self.packet_fingerprint,
            "semantic_ledger_signature": self.semantic_ledger_signature,
            "timestamp": self.timestamp,
            "drift_tests_run": self.drift_tests_run,
            "drift_tests_passed": self.drift_tests_passed,
            "detail": self.detail,
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


class Mission003Certifier:
    """Issue Mission #003 certification for a live CRK-1 runtime."""

    def __init__(self, runtime: CRK1Runtime) -> None:
        self.runtime = runtime
        self._prepare_substrate()

    @classmethod
    def from_runtime(cls, kernel: ConstitutionalRuntime) -> Mission003Certifier:
        from src.crk1.runtime_facade import CRK1Runtime

        return cls(CRK1Runtime(kernel))

    def _prepare_substrate(self) -> None:
        """Warm interpretive substrate for certification (public APIs only)."""
        prepare_continuity_substrate(self.runtime)

    def certify(self) -> Mission003CertificationReport:
        report = Mission003CertificationReport()
        report.timestamp = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

        kernel_entry = bootstrap_kernel_ledger_entry(self.runtime)
        semantic_ledger = bootstrap_semantic_ledger(self.runtime)
        report.kernel_ledger_hash = kernel_entry.entry_hash()
        report.semantic_ledger_signature = semantic_ledger.signature
        report.packet_fingerprint = compute_packet_fingerprint()
        report.implementation_hash = report.packet_fingerprint

        repro = ExternalReproductionHarness(self.runtime).run_all()
        report.levels.r1_substrate = repro.steps[0].passed and repro.steps[2].passed
        report.levels.r2_invariants = (
            repro.steps[5].passed and repro.steps[7].passed and repro.steps[8].passed
        )
        report.levels.r3_reproduction = repro.passed

        prepare_continuity_substrate(self.runtime)
        red_team = CRK1RedTeamSuite(self.runtime).run_full()
        report.levels.r4_red_team = red_team.attacks_passed

        drift_report = DriftStressProtocol(self.runtime).run_all()
        report.drift_tests_run = len(drift_report.results)
        report.drift_tests_passed = sum(1 for item in drift_report.results if item.passed)
        report.levels.r5_drift = drift_report.passed

        if not report.certified:
            parts: list[str] = []
            if not report.levels.r1_substrate:
                parts.append("R1")
            if not report.levels.r2_invariants:
                parts.append("R2")
            if not report.levels.r3_reproduction:
                parts.append("R3")
            if not report.levels.r4_red_team:
                parts.append("R4")
            if not report.levels.r5_drift:
                parts.append("R5")
            report.detail = f"failed levels: {', '.join(parts)}"

        return report
