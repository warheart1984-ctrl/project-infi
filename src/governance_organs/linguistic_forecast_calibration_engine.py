"""Linguistic forecast calibration engine — Wave 13 predict→verify loop."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.governance_organs._paths import repo_root
from tools.linguistic_drift_predictor import score_gene
from tools.linguistic_genome_lib import load_json

BAND_ORDER = {"high": 3, "medium": 2, "low": 1}


def load_calibration_policy(root: Path | None = None) -> dict[str, Any]:
    root = root or repo_root()
    reg_path = root / "governance/meta_linguistic_registry.v1.json"
    policy_ref = "governance/linguistic_forecast_calibration_policy.v1.json"
    if reg_path.is_file():
        reg = load_json(reg_path)
        policy_ref = reg.get("calibration_policy_ref", policy_ref)
    path = root / policy_ref
    if not path.is_file():
        return {
            "version": "linguistic_forecast_calibration_policy.v1",
            "min_forecast_age_hours": 1,
            "max_calibration_age_days": 14,
            "auto_tune_weights": False,
            "weight_adjust_step": 0.05,
            "retain_calibration_history": 12,
            "retain_forecast_archive": 5,
            "allow_archive_for_same_session_calibration": True,
        }
    return load_json(path)


def load_prior_forecast_for_calibration(
    root: Path | None = None,
    *,
    use_archive_if_too_fresh: bool = True,
) -> tuple[dict[str, Any] | None, str, str]:
    """Return (forecast, cycle_id, source) where source is live|archive."""
    root = root or repo_root()
    policy = load_calibration_policy(root)
    forecast, cycle_id = _load_prior_forecast(root)
    if forecast and _forecast_age_ok(forecast, policy):
        return forecast, cycle_id, "live"
    if use_archive_if_too_fresh and policy.get(
        "allow_archive_for_same_session_calibration", True
    ):
        from src.governance_organs.linguistic_drift_forecast_engine import (
            load_latest_forecast_archive,
        )

        archived = load_latest_forecast_archive(root)
        if archived:
            return archived, cycle_id, "archive"
    if forecast:
        return forecast, cycle_id, "live"
    return None, cycle_id, ""


def _load_prior_forecast(root: Path) -> tuple[dict[str, Any] | None, str]:
    reg_path = root / "governance/meta_linguistic_registry.v1.json"
    path = root / "governance/linguistic_drift_forecast.v1.json"
    cycle_id = ""
    if reg_path.is_file():
        reg = load_json(reg_path)
        ref = reg.get("last_forecast_report")
        if ref:
            path = root / ref
        cycle_id = reg.get("last_predictive_cycle_id", "") or ""
    if path.is_file():
        return load_json(path), cycle_id
    return None, cycle_id


def _forecast_age_ok(forecast: dict[str, Any], policy: dict[str, Any]) -> bool:
    generated = forecast.get("generated_at", "")
    try:
        ts = datetime.strptime(generated, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return False
    min_hours = int(policy.get("min_forecast_age_hours", 1))
    return datetime.now(timezone.utc) - ts >= timedelta(hours=min_hours)


def _classify_outcome_v2(predicted_band: str, actual_band: str) -> str:
    pred_rank = BAND_ORDER.get(predicted_band, 1)
    act_rank = BAND_ORDER.get(actual_band, 1)
    if pred_rank == act_rank:
        return "stable"
    if pred_rank > act_rank:
        return "false_alarm"
    if pred_rank < act_rank:
        return "miss"
    return "hit"


def calibrate_forecast(
    root: Path | None = None,
    *,
    forecast: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    root = root or repo_root()
    policy = load_calibration_policy(root)
    if forecast is None:
        forecast, _ = _load_prior_forecast(root)
        if forecast and not _forecast_age_ok(forecast, policy):
            forecast, _, source = load_prior_forecast_for_calibration(root)
            if source != "archive":
                return None
    if not forecast:
        return None

    forecast_by_gene = {e["gene"]: e for e in forecast.get("forecasts") or [] if e.get("gene")}
    gene_records: list[dict[str, Any]] = []
    signal_stats: dict[str, dict[str, int]] = {}

    for gene, fc in forecast_by_gene.items():
        actual = score_gene(gene, root)
        predicted_band = fc.get("predicted_band", "low")
        actual_band = actual.band
        outcome = _classify_outcome_v2(predicted_band, actual_band)
        predicted_risk = int(fc.get("predicted_risk_30d", 0))
        actual_risk = actual.drift_risk
        lead_time = int(fc.get("lead_time_days", 30))
        lead_ok = (
            BAND_ORDER.get(actual_band, 1) >= BAND_ORDER.get(predicted_band, 1)
            if outcome in {"hit", "miss"}
            else False
        )

        gene_records.append(
            {
                "gene": gene,
                "predicted_band": predicted_band,
                "actual_band": actual_band,
                "predicted_risk_30d": predicted_risk,
                "actual_risk": actual_risk,
                "risk_delta": actual_risk - predicted_risk,
                "band_outcome": outcome,
                "lead_time_days": lead_time,
                "lead_time_accuracy": lead_ok,
            }
        )

        for sig in fc.get("signals") or {}:
            if sig not in signal_stats:
                signal_stats[sig] = {"false_alarm_count": 0, "miss_count": 0, "hit_count": 0}
            if outcome == "false_alarm":
                signal_stats[sig]["false_alarm_count"] += 1
            elif outcome == "miss":
                signal_stats[sig]["miss_count"] += 1
            elif outcome in {"hit", "stable"}:
                signal_stats[sig]["hit_count"] += 1

    n = len(gene_records) or 1
    hits = sum(1 for r in gene_records if r["band_outcome"] in {"hit", "stable"})
    false_alarms = sum(1 for r in gene_records if r["band_outcome"] == "false_alarm")
    misses = sum(1 for r in gene_records if r["band_outcome"] == "miss")
    stables = sum(1 for r in gene_records if r["band_outcome"] == "stable")
    mae = round(
        sum(abs(r["risk_delta"]) for r in gene_records) / n,
        2,
    )

    weight_adjustments = _recommend_weight_adjustments(signal_stats, policy)
    recommended_weights = _apply_weight_recommendations(root, weight_adjustments, policy)

    return {
        "linguistic_forecast_calibration_version": "linguistic_forecast_calibration.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "forecast_generated_at": forecast.get("generated_at", ""),
        "forecast_cycle_id": "",
        "metrics": {
            "gene_count": len(gene_records),
            "band_hit_rate": round(hits / n, 3),
            "false_alarm_rate": round(false_alarms / n, 3),
            "miss_rate": round(misses / n, 3),
            "stable_rate": round(stables / n, 3),
            "mean_abs_risk_error": mae,
        },
        "signal_attribution": signal_stats,
        "weight_adjustments": weight_adjustments,
        "recommended_weights": recommended_weights,
        "gene_records": gene_records,
    }


def _recommend_weight_adjustments(
    signal_stats: dict[str, dict[str, int]],
    policy: dict[str, Any],
) -> list[dict[str, Any]]:
    step = float(policy.get("weight_adjust_step", 0.05))
    recs: list[dict[str, Any]] = []
    for signal, stats in signal_stats.items():
        fa = stats.get("false_alarm_count", 0)
        miss = stats.get("miss_count", 0)
        if fa > miss + 2:
            recs.append(
                {
                    "signal": signal,
                    "direction": "decrease",
                    "suggested_delta": -step,
                    "reason": f"{fa} false alarms vs {miss} misses for {signal}",
                }
            )
        elif miss > fa + 2:
            recs.append(
                {
                    "signal": signal,
                    "direction": "increase",
                    "suggested_delta": step,
                    "reason": f"{miss} misses vs {fa} false alarms for {signal}",
                }
            )
        else:
            recs.append(
                {
                    "signal": signal,
                    "direction": "hold",
                    "suggested_delta": 0.0,
                    "reason": "balanced false_alarm/miss ratio",
                }
            )
    return recs


def _apply_weight_recommendations(
    root: Path,
    adjustments: list[dict[str, Any]],
    policy: dict[str, Any],
) -> dict[str, float]:
    from src.governance_organs.linguistic_drift_forecast_engine import load_forecast_policy

    fp = load_forecast_policy(root)
    weights = dict(fp.get("weights") or {})
    step = float(policy.get("weight_adjust_step", 0.05))
    for adj in adjustments:
        sig = adj.get("signal", "")
        if sig not in weights:
            continue
        direction = adj.get("direction", "hold")
        if direction == "decrease":
            weights[sig] = max(0.05, weights[sig] - step)
        elif direction == "increase":
            weights[sig] = min(0.50, weights[sig] + step)
    total = sum(weights.values()) or 1.0
    return {k: round(v / total, 3) for k, v in weights.items()}


def write_calibration_report(
    root: Path | None = None,
    output: str | Path | None = None,
) -> Path | None:
    root = root or repo_root()
    report = calibrate_forecast(root)
    if not report:
        return None
    out = Path(output) if output else root / "governance/linguistic_forecast_calibration.v1.json"
    if not out.is_absolute():
        out = root / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return out


def load_calibration_report(root: Path | None = None) -> dict[str, Any] | None:
    root = root or repo_root()
    reg_path = root / "governance/meta_linguistic_registry.v1.json"
    path = root / "governance/linguistic_forecast_calibration.v1.json"
    if reg_path.is_file():
        reg = load_json(reg_path)
        ref = reg.get("last_calibration_report")
        if ref:
            path = root / ref
    if path.is_file():
        return load_json(path)
    return None


def calibration_stale(root: Path | None = None) -> bool:
    root = root or repo_root()
    policy = load_calibration_policy(root)
    report = load_calibration_report(root)
    if not report:
        return True
    generated = report.get("generated_at", "")
    try:
        ts = datetime.strptime(generated, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return True
    max_days = int(policy.get("max_calibration_age_days", 14))
    return datetime.now(timezone.utc) - ts > timedelta(days=max_days)


def apply_auto_tune_weights(root: Path | None = None) -> bool:
    root = root or repo_root()
    policy = load_calibration_policy(root)
    if not policy.get("auto_tune_weights"):
        return False
    report = load_calibration_report(root)
    if not report or not report.get("recommended_weights"):
        return False
    pred_policy_path = root / "governance/linguistic_predictive_governance_policy.v1.json"
    if not pred_policy_path.is_file():
        return False
    data = load_json(pred_policy_path)
    data["weights"] = report["recommended_weights"]
    pred_policy_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return True


@dataclass
class CalibrationCycleReport:
    cycle_id: str
    generated_at: str
    skipped: bool
    skip_reason: str = ""
    calibration_path: str = ""
    metrics: dict[str, Any] = field(default_factory=dict)
    passed: bool = True
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "linguistic_calibration_cycle_version": "linguistic_calibration_cycle.v1",
            "cycle_id": self.cycle_id,
            "generated_at": self.generated_at,
            "skipped": self.skipped,
            "skip_reason": self.skip_reason,
            "calibration_path": self.calibration_path,
            "metrics": self.metrics,
            "passed": self.passed,
            "errors": self.errors,
        }


def _prune_calibration_history(root: Path, policy: dict[str, Any]) -> None:
    retain = int(policy.get("retain_calibration_history", 12))
    cycle_dir = root / "governance/linguistic_calibration_cycles"
    if not cycle_dir.is_dir():
        return
    files = sorted(cycle_dir.glob("*.v1.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in files[retain:]:
        old.unlink(missing_ok=True)


class LinguisticForecastCalibrationEngine:
    """Wave 13a — calibrate Wave 12 forecasts against current drift."""

    def __init__(self, root: Path | None = None):
        self.root = root or repo_root()
        self.policy = load_calibration_policy(self.root)
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
        dry_run: bool = False,
        use_archive_if_too_fresh: bool = True,
    ) -> CalibrationCycleReport:
        now = datetime.now(timezone.utc)
        cycle_id = now.strftime("%Y%m%dT%H%M%SZ")
        forecast, _, source = load_prior_forecast_for_calibration(
            self.root, use_archive_if_too_fresh=use_archive_if_too_fresh
        )

        if not forecast:
            return CalibrationCycleReport(
                cycle_id=cycle_id,
                generated_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                skipped=True,
                skip_reason="no prior forecast report",
            )

        if source == "live" and not _forecast_age_ok(forecast, self.policy):
            return CalibrationCycleReport(
                cycle_id=cycle_id,
                generated_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                skipped=True,
                skip_reason="forecast younger than min_forecast_age_hours",
            )

        report_data = calibrate_forecast(self.root, forecast=forecast)
        if not report_data:
            return CalibrationCycleReport(
                cycle_id=cycle_id,
                generated_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                skipped=True,
                skip_reason="calibration produced no report",
            )

        rel_path = ""
        if not dry_run:
            out = write_calibration_report(self.root)
            if out:
                rel_path = str(out.relative_to(self.root)).replace("\\", "/")
                reg = self._gov().load_registry()
                reg["last_calibration_report"] = rel_path
                reg["last_calibration_at"] = report_data["generated_at"]
                if "calibration_policy_ref" not in reg:
                    reg["calibration_policy_ref"] = (
                        "governance/linguistic_forecast_calibration_policy.v1.json"
                    )
                self._gov().save_registry(reg)
                apply_auto_tune_weights(self.root)

                cycle_dir = self.root / "governance/linguistic_calibration_cycles"
                cycle_dir.mkdir(parents=True, exist_ok=True)
                cycle_path = cycle_dir / f"{cycle_id}.v1.json"
                cycle_payload = {
                    "linguistic_calibration_cycle_version": "linguistic_calibration_cycle.v1",
                    "cycle_id": cycle_id,
                    "generated_at": report_data["generated_at"],
                    "calibration_report": rel_path,
                    "metrics": report_data.get("metrics", {}),
                }
                cycle_path.write_text(
                    json.dumps(cycle_payload, indent=2) + "\n", encoding="utf-8"
                )
                _prune_calibration_history(self.root, self.policy)

        return CalibrationCycleReport(
            cycle_id=cycle_id,
            generated_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            skipped=False,
            calibration_path=rel_path,
            metrics=report_data.get("metrics", {}),
            passed=True,
        )
