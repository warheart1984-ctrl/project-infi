"""Full linguistic governance cycle — Wave 12 → 13 → 11 → queue → gates."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.governance_organs._paths import repo_root
from tools.linguistic_genome_lib import load_json


@dataclass
class FullGovernanceCycleReport:
    cycle_id: str
    generated_at: str
    phases: dict[str, Any] = field(default_factory=dict)
    passed: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "linguistic_full_governance_cycle_version": "linguistic_full_governance_cycle.v1",
            "cycle_id": self.cycle_id,
            "generated_at": self.generated_at,
            "phases": self.phases,
            "passed": self.passed,
            "errors": self.errors,
            "warnings": self.warnings,
        }


class LinguisticFullGovernanceCycleEngine:
    """Orchestrates predictive → calibration → reactive → queue → gates."""

    def __init__(self, root: Path | None = None):
        self.root = root or repo_root()
        self._governance = None

    def _gov(self) -> Any:
        if self._governance is None:
            from src.governance_organs.linguistic_governance_engine import (
                LinguisticGovernanceEngine,
            )

            self._governance = LinguisticGovernanceEngine(self.root)
        return self._governance

    def run_cycle(
        self,
        *,
        skip_gates: bool = False,
        skip_drift_refresh: bool = False,
        dry_run: bool = False,
    ) -> FullGovernanceCycleReport:
        now = datetime.now(timezone.utc)
        cycle_id = now.strftime("%Y%m%dT%H%M%SZ")
        phases: dict[str, Any] = {}
        errors: list[str] = []
        warnings: list[str] = []

        from src.governance_organs.linguistic_predictive_governance_engine import (
            LinguisticPredictiveGovernanceEngine,
        )
        from src.governance_organs.linguistic_forecast_calibration_engine import (
            LinguisticForecastCalibrationEngine,
        )
        from src.governance_organs.linguistic_governance_cycle_engine import (
            LinguisticGovernanceCycleEngine,
        )
        from src.governance_organs.linguistic_governance_queue_engine import (
            write_governance_queue,
        )

        from src.governance_organs.linguistic_drift_forecast_engine import (
            archive_forecast_before_write,
        )

        live_forecast = self.root / "governance/linguistic_drift_forecast.v1.json"
        had_prior_forecast = live_forecast.is_file()
        if had_prior_forecast and not dry_run:
            archived = archive_forecast_before_write(self.root)
            phases["forecast_archive"] = (
                str(archived.relative_to(self.root)).replace("\\", "/")
                if archived
                else None
            )

        cal = LinguisticForecastCalibrationEngine(self.root)
        cal_report = cal.run_cycle(
            dry_run=dry_run,
            use_archive_if_too_fresh=True,
        )
        phases["calibration"] = {
            "cycle_id": cal_report.cycle_id,
            "skipped": cal_report.skipped,
            "skip_reason": cal_report.skip_reason,
            "metrics": cal_report.metrics,
            "archive_aware": True,
        }
        if cal_report.skipped and had_prior_forecast:
            warnings.append(f"calibration skipped: {cal_report.skip_reason}")

        pred = LinguisticPredictiveGovernanceEngine(self.root)
        pred_report = pred.run_cycle(
            skip_drift_refresh=skip_drift_refresh,
            dry_run=dry_run,
        )
        phases["predictive"] = {
            "cycle_id": pred_report.cycle_id,
            "passed": pred_report.passed,
            "predicted_medium": pred_report.metrics.predicted_medium,
        }
        if not pred_report.passed:
            errors.extend(pred_report.errors)

        cycle = LinguisticGovernanceCycleEngine(self.root)
        react_report = cycle.run_cycle(
            skip_gates=True,
            skip_drift_refresh=skip_drift_refresh,
            dry_run=dry_run,
        )
        phases["reactive"] = {
            "cycle_id": react_report.cycle_id,
            "remediation_band": react_report.remediation_min_band,
            "remediations_written": react_report.phases.get("remediations_written", 0),
        }
        if not react_report.passed:
            errors.extend(react_report.errors)

        if not dry_run:
            queue_path = write_governance_queue(self.root)
            phases["queue"] = str(queue_path.relative_to(self.root)).replace("\\", "/")

            from src.governance_organs.linguistic_governance_work_order_engine import (
                sync_work_orders_from_queue,
            )

            synced = sync_work_orders_from_queue(self.root)
            phases["work_orders_synced"] = len(synced)

            from src.governance_organs.linguistic_governance_attestation_engine import (
                write_attestation,
            )

            att_path = write_attestation(self.root)
            phases["attestation"] = str(att_path.relative_to(self.root)).replace("\\", "/")
        else:
            phases["queue"] = None
            phases["work_orders_synced"] = 0
            phases["attestation"] = None

        if not skip_gates and not dry_run:
            gate_report = self._gov().run_all_gates()
            phases["meta_gates_passed"] = gate_report.passed
            if not gate_report.passed:
                errors.extend(gate_report.errors)

            import subprocess
            import sys as _sys

            for script, label in [
                ("tools/governance/check_linguistic_remediation_gate.py", "remediation_gate"),
                ("tools/governance/check_linguistic_predictive_gate.py", "predictive_gate"),
                ("tools/governance/check_linguistic_governance_cycle_gate.py", "cycle_gate"),
                ("tools/governance/check_linguistic_calibration_gate.py", "calibration_gate"),
                ("tools/governance/check_linguistic_work_order_gate.py", "work_order_gate"),
                ("tools/governance/check_linguistic_attestation_gate.py", "attestation_gate"),
            ]:
                proc = subprocess.run(
                    [_sys.executable, str(self.root / script)],
                    cwd=self.root,
                    capture_output=True,
                    text=True,
                )
                phases[label] = proc.returncode == 0
                if proc.returncode != 0:
                    warnings.append(f"{label} returned exit {proc.returncode}")
        else:
            phases["meta_gates_passed"] = None

        report = FullGovernanceCycleReport(
            cycle_id=cycle_id,
            generated_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            phases=phases,
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

        if not dry_run:
            self._persist(report)

        return report

    def _persist(self, report: FullGovernanceCycleReport) -> None:
        cycle_dir = self.root / "governance/linguistic_full_governance_cycles"
        cycle_dir.mkdir(parents=True, exist_ok=True)
        rel = f"governance/linguistic_full_governance_cycles/{report.cycle_id}.v1.json"
        path = self.root / rel
        path.write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")
        reg = self._gov().load_registry()
        reg["last_full_cycle_report"] = rel
        self._gov().save_registry(reg)
