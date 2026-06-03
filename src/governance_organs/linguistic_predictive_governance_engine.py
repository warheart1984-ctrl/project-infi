"""Linguistic predictive governance engine — Wave 12 closed-loop forecast cycle."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.governance_organs._paths import repo_root
from src.governance_organs.linguistic_drift_forecast_engine import (
    BAND_ORDER,
    forecast_all,
    forecast_metrics_from_report,
    load_forecast_policy,
    preemptive_playbook_exists,
    write_forecast_report,
    write_preemptive_playbook,
)
from tools.linguistic_genome_lib import load_json


@dataclass
class PredictiveCycleMetrics:
    gene_count: int = 0
    predicted_high: int = 0
    predicted_medium: int = 0
    predicted_low: int = 0
    preemptive_written: int = 0


@dataclass
class LinguisticPredictiveCycleReport:
    cycle_id: str
    generated_at: str
    policy_mode: str
    metrics: PredictiveCycleMetrics
    phases: dict[str, Any] = field(default_factory=dict)
    preemptive_recommendations: list[dict[str, Any]] = field(default_factory=list)
    top_predicted: list[dict[str, Any]] = field(default_factory=list)
    passed: bool = True
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "linguistic_predictive_cycle_version": "linguistic_predictive_cycle.v1",
            "cycle_id": self.cycle_id,
            "generated_at": self.generated_at,
            "policy_mode": self.policy_mode,
            "metrics": asdict(self.metrics),
            "phases": self.phases,
            "preemptive_recommendations": self.preemptive_recommendations,
            "top_predicted": self.top_predicted,
        }


def _prune_predictive_history(root: Path, policy: dict[str, Any]) -> None:
    retain = int(policy.get("retain_predictive_cycle_history", 12))
    cycle_dir = root / "governance/linguistic_predictive_cycles"
    if not cycle_dir.is_dir():
        return
    files = sorted(cycle_dir.glob("*.v1.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in files[retain:]:
        old.unlink(missing_ok=True)


class LinguisticPredictiveGovernanceEngine:
    """Wave 12 — baseline → forecast → preempt → recommend → record."""

    def __init__(self, root: Path | None = None):
        self.root = root or repo_root()
        self.policy = load_forecast_policy(self.root)
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
        skip_drift_refresh: bool = False,
        dry_run: bool = False,
    ) -> LinguisticPredictiveCycleReport:
        now = datetime.now(timezone.utc)
        cycle_id = now.strftime("%Y%m%dT%H%M%SZ")
        reg = self._gov().load_registry()
        policy_mode = reg.get("policy_mode", "observe")
        phases: dict[str, Any] = {}
        errors: list[str] = []

        if not skip_drift_refresh:
            drift_ok = self._gov()._run_gate("linguistic-drift-gate").passed
            phases["drift_refreshed"] = drift_ok
            if not drift_ok:
                errors.append("linguistic-drift-gate failed during predictive cycle")
        else:
            phases["drift_refreshed"] = False

        phases["baseline_loaded"] = (
            self.root / reg.get("last_drift_report", "governance/linguistic_drift_report.v1.json")
        ).is_file()

        if dry_run:
            forecasts = forecast_all(self.root)
        else:
            forecast_path = write_forecast_report(self.root)
            phases["forecast_report"] = str(forecast_path.relative_to(self.root)).replace("\\", "/")
            forecasts = forecast_all(self.root)

        min_band = self.policy.get("min_predicted_band", "medium")
        min_rank = BAND_ORDER[min_band]
        top_n = int(self.policy.get("preemptive_top", 15))
        candidates = [f for f in forecasts if BAND_ORDER.get(f.predicted_band, 0) >= min_rank]
        candidates.sort(key=lambda f: (-f.predicted_risk_30d, f.gene))

        preempt_written = 0
        if not dry_run:
            for f in candidates[:top_n]:
                write_preemptive_playbook(f, self.root)
                preempt_written += 1
        phases["preemptive_written"] = preempt_written

        fm = forecast_metrics_from_report(
            {
                "forecasts": [asdict(f) for f in forecasts],
            }
        )
        metrics = PredictiveCycleMetrics(
            gene_count=len(forecasts),
            predicted_high=fm["predicted_high"],
            predicted_medium=fm["predicted_medium"],
            predicted_low=fm["predicted_low"],
            preemptive_written=preempt_written,
        )

        recommendations: list[dict[str, Any]] = []
        if metrics.predicted_high > 0:
            recommendations.append(
                {
                    "kind": "run_wave11_cycle",
                    "command": "make linguistic-governance-cycle",
                    "reason": f"{metrics.predicted_high} gene(s) predicted high within horizon",
                }
            )
        for f in candidates[:5]:
            if f.drivers:
                recommendations.append(
                    {
                        "kind": "watch_gene",
                        "gene": f.gene,
                        "predicted_band": f.predicted_band,
                        "lead_time_days": f.lead_time_days,
                        "reason": f.drivers[0],
                    }
                )

        report = LinguisticPredictiveCycleReport(
            cycle_id=cycle_id,
            generated_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            policy_mode=policy_mode,
            metrics=metrics,
            phases=phases,
            preemptive_recommendations=recommendations,
            top_predicted=[
                {
                    "gene": f.gene,
                    "current_band": f.current_band,
                    "predicted_band": f.predicted_band,
                    "predicted_risk_30d": f.predicted_risk_30d,
                    "lead_time_days": f.lead_time_days,
                }
                for f in forecasts[:15]
            ],
            passed=len(errors) == 0,
            errors=errors,
        )

        if policy_mode == "enforce" and not dry_run:
            for f in forecasts:
                if f.predicted_band == "high" and not preemptive_playbook_exists(f.gene, self.root):
                    report.passed = False
                    report.errors.append(
                        f"enforce: missing preemptive playbook for predicted-high gene {f.gene!r}"
                    )

        if not dry_run:
            self._persist_cycle(report, reg)

        return report

    def _persist_cycle(
        self, report: LinguisticPredictiveCycleReport, reg: dict[str, Any]
    ) -> Path:
        cycle_dir = self.root / "governance/linguistic_predictive_cycles"
        cycle_dir.mkdir(parents=True, exist_ok=True)
        rel_cycle = f"governance/linguistic_predictive_cycles/{report.cycle_id}.v1.json"
        out_path = self.root / rel_cycle
        out_path.write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")

        reg["last_forecast_report"] = "governance/linguistic_drift_forecast.v1.json"
        reg["last_predictive_cycle_report"] = rel_cycle
        reg["last_predictive_cycle_at"] = report.generated_at
        if "predictive_policy_ref" not in reg:
            reg["predictive_policy_ref"] = (
                "governance/linguistic_predictive_governance_policy.v1.json"
            )
        self._gov().save_registry(reg)
        _prune_predictive_history(self.root, self.policy)
        return out_path
