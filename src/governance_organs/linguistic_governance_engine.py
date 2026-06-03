"""Meta-linguistic governance engine — orchestrates Waves 0–10 linguistic gates."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.governance_organs._paths import repo_root
from src.governance_organs.linguistic_cascade_engine import (
    cascade_impact,
    validate_cascade_ack,
)
from tools.linguistic_genome_lib import load_json


@dataclass
class GateResult:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class MetaLinguisticGateReport:
    passed: bool
    policy_mode: str
    results: list[GateResult] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


GATE_COMMANDS: dict[str, list[str]] = {
    "naming-gate": ["tools/naming_protocol_lint.py"],
    "naming-genome-gate": [
        "tools/governance/check_naming_genome.py",
        "--snapshot",
    ],
    "linguistic-mutation-gate": ["tools/governance/check_linguistic_mutation_gate.py"],
    "linguistic-drift-gate": [
        "tools/linguistic_drift_predictor.py",
        "--json",
        "-o",
        "governance/linguistic_drift_report.v1.json",
    ],
}


class LinguisticGovernanceEngine:
    def __init__(self, root: Path | None = None):
        self.root = root or repo_root()
        self.registry_path = self.root / "governance/meta_linguistic_registry.v1.json"

    def load_registry(self) -> dict[str, Any]:
        if self.registry_path.is_file():
            return load_json(self.registry_path)
        return {
            "meta_linguistic_registry_version": "meta_linguistic_registry.v1",
            "policy_mode": "observe",
            "gates": list(GATE_COMMANDS.keys()),
            "cascade_policy_ref": "governance/linguistic_cascade_policy.v1.json",
            "remediation_dir": "governance/linguistic_remediations",
        }

    def save_registry(self, data: dict[str, Any]) -> None:
        data["last_gate_run_at"] = datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.registry_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def _run_gate(self, gate_name: str) -> GateResult:
        parts = GATE_COMMANDS.get(gate_name)
        if not parts:
            return GateResult(gate_name, False, "unknown gate")
        script = self.root / parts[0]
        args = [sys.executable, str(script), *parts[1:]]
        proc = subprocess.run(
            args,
            cwd=self.root,
            capture_output=True,
            text=True,
            timeout=600,
        )
        detail = (proc.stdout or proc.stderr or "").strip().splitlines()
        suffix = detail[-1] if detail else f"exit {proc.returncode}"
        return GateResult(gate_name, proc.returncode == 0, suffix)

    def run_all_gates(self, *, strict: bool = False) -> MetaLinguisticGateReport:
        reg = self.load_registry()
        mode = reg.get("policy_mode", "observe")
        report = MetaLinguisticGateReport(passed=True, policy_mode=mode)

        for gate_name in reg.get("gates") or list(GATE_COMMANDS.keys()):
            result = self._run_gate(gate_name)
            report.results.append(result)
            if not result.passed:
                report.errors.append(f"{gate_name}: {result.detail}")
                report.passed = False

        if mode == "enforce":
            drift_path = self.root / reg.get(
                "last_drift_report", "governance/linguistic_drift_report.v1.json"
            )
            if drift_path.is_file():
                data = load_json(drift_path)
                for entry in data.get("scores") or []:
                    if entry.get("band") == "high":
                        gene = entry.get("gene", "")
                        pb = (
                            self.root
                            / "governance/linguistic_remediations"
                            / f"{gene}.v1.json"
                        )
                        if not pb.is_file():
                            report.errors.append(
                                f"high drift gene {gene!r} missing remediation playbook"
                            )
                            report.passed = False
        elif not strict:
            pass

        self.save_registry(reg)
        return report

    def refresh_drift_report(self) -> int:
        return self._run_gate("linguistic-drift-gate").passed is True and 0 or 1

    def run_cycle(self, **kwargs: Any) -> Any:
        """Wave 11 — closed-loop measure → remediate → optimize."""
        from src.governance_organs.linguistic_governance_cycle_engine import (
            LinguisticGovernanceCycleEngine,
        )

        return LinguisticGovernanceCycleEngine(self.root).run_cycle(**kwargs)

    def run_predictive_cycle(self, **kwargs: Any) -> Any:
        """Wave 12 — forecast → preempt → record."""
        from src.governance_organs.linguistic_predictive_governance_engine import (
            LinguisticPredictiveGovernanceEngine,
        )

        return LinguisticPredictiveGovernanceEngine(self.root).run_cycle(**kwargs)

    def run_calibration_cycle(self, **kwargs: Any) -> Any:
        """Wave 13a — calibrate prior forecast vs current drift."""
        from src.governance_organs.linguistic_forecast_calibration_engine import (
            LinguisticForecastCalibrationEngine,
        )

        return LinguisticForecastCalibrationEngine(self.root).run_cycle(**kwargs)

    def build_governance_queue(self, **kwargs: Any) -> Any:
        """Wave 13b — prescriptive operator queue."""
        from src.governance_organs.linguistic_governance_queue_engine import (
            write_governance_queue,
        )

        return write_governance_queue(self.root, **kwargs)

    def run_full_cycle(self, **kwargs: Any) -> Any:
        """Full cycle — calibrate → predict → react → queue → gates."""
        from src.governance_organs.linguistic_full_governance_cycle_engine import (
            LinguisticFullGovernanceCycleEngine,
        )

        return LinguisticFullGovernanceCycleEngine(self.root).run_cycle(**kwargs)

    def sync_work_orders(self) -> Any:
        """Wave 14 — sync work orders from governance queue."""
        from src.governance_organs.linguistic_governance_work_order_engine import (
            sync_work_orders_from_queue,
        )

        return sync_work_orders_from_queue(self.root)

    def run_attestation(self, **kwargs: Any) -> Any:
        """Wave 14 — unified closed-loop attestation digest."""
        from src.governance_organs.linguistic_governance_attestation_engine import (
            write_attestation,
        )

        return write_attestation(self.root, **kwargs)

    def check_cascade_policy(
        self, gene: str, delta: dict[str, Any]
    ) -> tuple[list[str], list[str]]:
        errors = validate_cascade_ack(delta, self.root)
        warnings: list[str] = []
        before = delta.get("before") or {}
        after = delta.get("after") or {}
        impact = cascade_impact(
            gene,
            {"genome": before},
            {"genome": after},
            self.root,
        )
        if impact.parent_changed and impact.children:
            high = [c for c in impact.children if c.drift_band == "high"]
            if high:
                warnings.append(
                    f"cascade: {len(high)} child(ren) at high drift after parent change"
                )
        return errors, warnings

    @classmethod
    def gate_main(cls) -> int:
        import argparse

        parser = argparse.ArgumentParser(description="Meta-linguistic governance gate")
        parser.add_argument("--gate", action="store_true", help="Run all linguistic gates")
        parser.add_argument("--strict", action="store_true")
        args = parser.parse_args()

        engine = cls()
        if args.gate or not any([args.strict]):
            report = engine.run_all_gates(strict=args.strict)
            for w in report.warnings:
                print(f"WARNING: {w}", file=sys.stderr)
            for e in report.errors:
                print(f"ERROR: {e}", file=sys.stderr)
            if report.passed:
                print(
                    f"meta-linguistic-gate: PASS ({len(report.results)} gates, mode={report.policy_mode})"
                )
                return 0
            print("meta-linguistic-gate: FAIL")
            return 1
        return 0


def main() -> int:
    return LinguisticGovernanceEngine.gate_main()


if __name__ == "__main__":
    _root = Path(__file__).resolve().parents[2]
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))
    raise SystemExit(main())
