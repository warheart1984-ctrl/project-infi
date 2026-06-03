"""Linguistic governance operator day — Wave 17 unified orchestrator."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.governance_organs._paths import repo_root


@dataclass
class LinguisticGovernanceDayReport:
    day_id: str
    generated_at: str
    phases: dict[str, Any] = field(default_factory=dict)
    passed: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "linguistic_governance_day_version": "linguistic_governance_day.v1",
            "day_id": self.day_id,
            "generated_at": self.generated_at,
            "phases": self.phases,
            "passed": self.passed,
            "errors": self.errors,
            "warnings": self.warnings,
        }


class LinguisticGovernanceDayEngine:
    """Orchestrates full cycle → attestation refresh → meta gates → optional stack gate."""

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

    def run_day(
        self,
        *,
        fast: bool = False,
        dry_run: bool = False,
        continue_on_error: bool = False,
        with_stack_gate: bool = False,
    ) -> LinguisticGovernanceDayReport:
        now = datetime.now(timezone.utc)
        day_id = now.strftime("%Y%m%dT%H%M%SZ")
        phases: dict[str, Any] = {}
        errors: list[str] = []
        warnings: list[str] = []

        from src.governance_organs.linguistic_full_governance_cycle_engine import (
            LinguisticFullGovernanceCycleEngine,
        )

        cycle_engine = LinguisticFullGovernanceCycleEngine(self.root)
        cycle_report = cycle_engine.run_cycle(
            skip_gates=True,
            skip_drift_refresh=fast,
            dry_run=dry_run,
        )
        phases["full_cycle"] = {
            "cycle_id": cycle_report.cycle_id,
            "passed": cycle_report.passed,
            "phases": cycle_report.phases,
        }
        if not cycle_report.passed:
            errors.extend(cycle_report.errors)
        warnings.extend(cycle_report.warnings)

        if not dry_run:
            from src.governance_organs.linguistic_governance_attestation_engine import (
                write_attestation,
            )
            from src.governance_organs.linguistic_governance_work_order_engine import (
                sync_work_orders_from_queue,
            )

            synced = sync_work_orders_from_queue(self.root)
            phases["work_orders_synced"] = len(synced)
            att_path = write_attestation(self.root)
            phases["attestation"] = str(att_path.relative_to(self.root)).replace(
                "\\", "/"
            )
        else:
            phases["work_orders_synced"] = 0
            phases["attestation"] = None

        gate_report = self._gov().run_all_gates()
        phases["meta_gates"] = {
            "passed": gate_report.passed,
            "policy_mode": gate_report.policy_mode,
            "results": [
                {"name": r.name, "passed": r.passed, "detail": r.detail}
                for r in gate_report.results
            ],
        }
        if not gate_report.passed:
            errors.extend(gate_report.errors)

        if with_stack_gate and not dry_run:
            stack_script = self.root / "tools/governance/check_linguistic_governance_stack_gate.py"
            proc = subprocess.run(
                [sys.executable, str(stack_script)],
                cwd=self.root,
                capture_output=True,
                text=True,
            )
            phases["stack_gate_passed"] = proc.returncode == 0
            if proc.returncode != 0:
                detail = (proc.stderr or proc.stdout or "").strip().splitlines()
                msg = detail[-1] if detail else f"stack gate exit {proc.returncode}"
                errors.append(f"linguistic-governance-stack-gate: {msg}")
        else:
            phases["stack_gate_passed"] = None

        passed = len(errors) == 0
        if not continue_on_error and errors and not passed:
            pass

        report = LinguisticGovernanceDayReport(
            day_id=day_id,
            generated_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            phases=phases,
            passed=passed,
            errors=errors,
            warnings=warnings,
        )

        if not dry_run:
            self._persist(report)

        return report

    def _persist(self, report: LinguisticGovernanceDayReport) -> None:
        day_dir = self.root / "governance/linguistic_governance_days"
        day_dir.mkdir(parents=True, exist_ok=True)
        rel = f"governance/linguistic_governance_days/{report.day_id}.v1.json"
        path = self.root / rel
        path.write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")
        reg = self._gov().load_registry()
        reg["last_governance_day_at"] = report.generated_at
        reg["last_governance_day_report"] = rel
        self._gov().save_registry(reg)
