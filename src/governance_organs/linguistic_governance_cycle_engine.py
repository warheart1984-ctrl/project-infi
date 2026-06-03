"""Linguistic governance cycle engine — Wave 11 self-optimizing closed loop."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.governance_organs._paths import repo_root
from src.governance_organs.linguistic_cascade_engine import cascade_impact
from src.governance_organs.linguistic_remediation_engine import playbook_exists, write_playbook
from tools.linguistic_drift_predictor import DriftScore, score_gene
from tools.linguistic_genome_lib import list_all_genes, load_genome, load_json

BAND_ORDER = {"high": 3, "medium": 2, "low": 1}


@dataclass
class CycleMetrics:
    gene_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    mean_drift_risk: float = 0.0
    playbook_count: int = 0
    playbook_coverage_pct: float = 100.0


@dataclass
class LinguisticGovernanceCycleReport:
    cycle_id: str
    generated_at: str
    policy_mode: str
    remediation_min_band: str
    metrics: CycleMetrics
    phases: dict[str, Any] = field(default_factory=dict)
    deltas_from_previous: dict[str, float | int] = field(default_factory=dict)
    optimization_recommendations: list[dict[str, Any]] = field(default_factory=list)
    top_at_risk: list[dict[str, Any]] = field(default_factory=list)
    cascade_summaries: list[dict[str, Any]] = field(default_factory=list)
    passed: bool = True
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "linguistic_governance_cycle_version": "linguistic_governance_cycle.v1",
            "cycle_id": self.cycle_id,
            "generated_at": self.generated_at,
            "policy_mode": self.policy_mode,
            "remediation_min_band": self.remediation_min_band,
            "metrics": asdict(self.metrics),
            "deltas_from_previous": self.deltas_from_previous,
            "phases": self.phases,
            "optimization_recommendations": self.optimization_recommendations,
            "top_at_risk": self.top_at_risk,
            "cascade_summaries": self.cascade_summaries,
        }


def load_cycle_policy(root: Path | None = None) -> dict[str, Any]:
    root = root or repo_root()
    reg_path = root / "governance/meta_linguistic_registry.v1.json"
    policy_ref = "governance/linguistic_governance_cycle_policy.v1.json"
    if reg_path.is_file():
        reg = load_json(reg_path)
        policy_ref = reg.get("cycle_policy_ref", policy_ref)
    path = root / policy_ref
    if not path.is_file():
        return {
            "version": "linguistic_governance_cycle_policy.v1",
            "default_remediation_min_band": "medium",
            "remediation_top": 20,
            "cascade_scan_min_fanout": 4,
            "cascade_scan_max_parents": 10,
            "enforce_recommend_after_high_streak": 2,
            "high_drift_threshold_for_enforce_hint": 3,
            "auto_tune_policy": False,
            "max_cycle_age_days": 7,
            "retain_cycle_history": 12,
        }
    return load_json(path)


def _metrics_from_scores(scores: list[DriftScore], root: Path) -> CycleMetrics:
    if not scores:
        return CycleMetrics()
    high = [s for s in scores if s.band == "high"]
    medium = [s for s in scores if s.band == "medium"]
    low = [s for s in scores if s.band == "low"]
    playbook_count = sum(1 for s in high if playbook_exists(s.gene, root))
    coverage = 100.0
    if high:
        coverage = round(100.0 * playbook_count / len(high), 1)
    return CycleMetrics(
        gene_count=len(scores),
        high_count=len(high),
        medium_count=len(medium),
        low_count=len(low),
        mean_drift_risk=round(sum(s.drift_risk for s in scores) / len(scores), 2),
        playbook_count=playbook_count,
        playbook_coverage_pct=coverage,
    )


def _load_previous_cycle(root: Path) -> dict[str, Any] | None:
    reg_path = root / "governance/meta_linguistic_registry.v1.json"
    if not reg_path.is_file():
        return None
    reg = load_json(reg_path)
    prev_ref = reg.get("last_cycle_report")
    if not prev_ref:
        return None
    path = root / prev_ref
    if path.is_file():
        return load_json(path)
    return None


def _compute_deltas(
    current: CycleMetrics, previous: dict[str, Any] | None
) -> dict[str, float | int]:
    if not previous:
        return {}
    prev_m = previous.get("metrics") or {}
    deltas: dict[str, float | int] = {}
    if "high_count" in prev_m:
        deltas["high_count_delta"] = current.high_count - int(prev_m["high_count"])
    if "medium_count" in prev_m:
        deltas["medium_count_delta"] = current.medium_count - int(prev_m["medium_count"])
    if "mean_drift_risk" in prev_m:
        deltas["mean_drift_risk_delta"] = round(
            current.mean_drift_risk - float(prev_m["mean_drift_risk"]), 2
        )
    if "playbook_coverage_pct" in prev_m:
        deltas["playbook_coverage_pct_delta"] = round(
            current.playbook_coverage_pct - float(prev_m["playbook_coverage_pct"]), 1
        )
    return deltas


def _adaptive_remediation_band(
    metrics: CycleMetrics,
    policy: dict[str, Any],
    previous: dict[str, Any] | None,
    forecast_metrics: dict[str, int] | None = None,
) -> str:
    default = policy.get("default_remediation_min_band", "medium")
    fm = forecast_metrics or {}
    pred_high = int(fm.get("predicted_high", 0))
    pred_medium = int(fm.get("predicted_medium", 0))
    if metrics.high_count > 0 or pred_high > 0:
        return "high"
    if metrics.medium_count >= 5 or pred_medium >= 5:
        return "medium"
    if metrics.high_count == 0 and metrics.medium_count < 5 and pred_medium < 5:
        return "low"
    return default


def _optimization_recommendations(
    metrics: CycleMetrics,
    policy: dict[str, Any],
    policy_mode: str,
    remediation_band: str,
    scores: list[DriftScore],
    previous: dict[str, Any] | None,
    cascade_summaries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    recs: list[dict[str, Any]] = []
    high_threshold = int(policy.get("high_drift_threshold_for_enforce_hint", 3))
    streak_needed = int(policy.get("enforce_recommend_after_high_streak", 2))

    high_streak = 0
    if metrics.high_count > 0:
        high_streak = 1
        if previous and int((previous.get("metrics") or {}).get("high_count", 0)) > 0:
            high_streak = 2

    if (
        metrics.high_count >= high_threshold
        and high_streak >= streak_needed
        and policy_mode == "observe"
    ):
        recs.append(
            {
                "kind": "policy_mode",
                "suggested": "enforce",
                "reason": (
                    f"high drift count {metrics.high_count} for {high_streak}+ cycle(s); "
                    "consider enforce to require playbooks and cascade_ack"
                ),
            }
        )

    recs.append(
        {
            "kind": "remediation_min_band",
            "suggested": remediation_band,
            "reason": "adaptive band from current drift distribution",
        }
    )

    priority = [s for s in scores if s.band in {"high", "medium"}]
    priority.sort(key=lambda s: (-s.drift_risk, s.gene))
    if priority:
        recs.append(
            {
                "kind": "priority_genes",
                "genes": [s.gene for s in priority[:10]],
                "reason": "top at-risk genes for operator review",
            }
        )

    for summary in cascade_summaries:
        if summary.get("high_drift_children", 0) > 0:
            parent = summary["parent_gene"]
            recs.append(
                {
                    "kind": "cascade_report",
                    "gene": parent,
                    "command": f"python tools/linguistic_cascade_report.py --gene {parent}",
                    "reason": "parent has high-drift children in cascade scan",
                }
            )

    if metrics.high_count > 0 and metrics.playbook_coverage_pct < 100:
        recs.append(
            {
                "kind": "generate_remediations",
                "command": (
                    "python tools/governance/generate_linguistic_remediations.py "
                    f"--min-band high --top {policy.get('remediation_top', 20)}"
                ),
                "reason": "high-drift genes missing remediation playbooks",
            }
        )

    return recs


def _cascade_scan_parents(
    scores: list[DriftScore],
    root: Path,
    policy: dict[str, Any],
) -> list[dict[str, Any]]:
    min_fanout = float(policy.get("cascade_scan_min_fanout", 4))
    max_parents = int(policy.get("cascade_scan_max_parents", 10))
    candidates: list[tuple[float, str, DriftScore]] = []
    for s in scores:
        if BAND_ORDER.get(s.band, 0) < BAND_ORDER["medium"]:
            continue
        fanout = float(s.signals.get("lineage_fanout", 0))
        if fanout < min_fanout:
            continue
        genome = load_genome(s.gene, root)
        children = (genome.get("lineage") or {}).get("children") or [] if genome else []
        if not children:
            continue
        candidates.append((fanout, s.gene, s))

    candidates.sort(key=lambda x: (-x[0], x[1]))
    summaries: list[dict[str, Any]] = []
    for _, gene, score in candidates[:max_parents]:
        genome = load_genome(gene, root)
        if not genome:
            continue
        ssp = genome.get("ssp") or {}
        before = {
            "mythic_label": ssp.get("mythic_label", ""),
            "engineering_class": ssp.get("engineering_class", ""),
        }
        after = dict(before)
        after["mythic_label"] = f"{before.get('mythic_label', '')} (cycle-scan)"
        impact = cascade_impact(gene, {"genome": before}, {"genome": after}, root)
        high_children = sum(1 for c in impact.children if c.drift_band == "high")
        summaries.append(
            {
                "parent_gene": gene,
                "child_count": len(impact.children),
                "high_drift_children": high_children,
                "parent_drift_band": score.band,
            }
        )
    return summaries


def _prune_cycle_history(root: Path, policy: dict[str, Any]) -> None:
    retain = int(policy.get("retain_cycle_history", 12))
    cycle_dir = root / "governance/linguistic_governance_cycles"
    if not cycle_dir.is_dir():
        return
    files = sorted(cycle_dir.glob("*.v1.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in files[retain:]:
        old.unlink(missing_ok=True)


class LinguisticGovernanceCycleEngine:
    """Wave 11 — measure, remediate, cascade-scan, optimize, record."""

    def __init__(self, root: Path | None = None):
        self.root = root or repo_root()
        self.policy = load_cycle_policy(self.root)
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
    ) -> LinguisticGovernanceCycleReport:
        now = datetime.now(timezone.utc)
        cycle_id = now.strftime("%Y%m%dT%H%M%SZ")
        reg = self._gov().load_registry()
        policy_mode = reg.get("policy_mode", "observe")
        previous = _load_previous_cycle(self.root)

        phases: dict[str, Any] = {}
        errors: list[str] = []

        if not skip_gates:
            gate_report = self._gov().run_all_gates()
            phases["gates_passed"] = gate_report.passed
            if not gate_report.passed:
                errors.extend(gate_report.errors)
        else:
            phases["gates_passed"] = None

        if not skip_drift_refresh:
            drift_ok = self._gov()._run_gate("linguistic-drift-gate").passed
            phases["drift_refreshed"] = drift_ok
            if not drift_ok:
                errors.append("linguistic-drift-gate failed during cycle")
        else:
            phases["drift_refreshed"] = False

        genes = list_all_genes(self.root)
        scores = [score_gene(g, self.root) for g in genes]
        metrics = _metrics_from_scores(scores, self.root)

        forecast_report = None
        forecast_metrics: dict[str, int] | None = None
        if self.policy.get("use_forecast_in_cycle", True):
            from src.governance_organs.linguistic_drift_forecast_engine import (
                forecast_metrics_from_report,
                forecast_stale,
                load_forecast_report,
            )

            if forecast_stale(self.root):
                phases["forecast_consumed"] = False
            else:
                forecast_report = load_forecast_report(self.root)
                forecast_metrics = forecast_metrics_from_report(forecast_report)
                phases["forecast_consumed"] = forecast_report is not None

        remediation_band = _adaptive_remediation_band(
            metrics, self.policy, previous, forecast_metrics
        )
        min_rank = BAND_ORDER[remediation_band]

        remed_written = 0
        if not dry_run:
            at_risk = [s for s in scores if BAND_ORDER.get(s.band, 0) >= min_rank]
            if forecast_report and self.policy.get("use_forecast_in_cycle", True):
                score_by_gene = {s.gene: s for s in scores}
                for entry in forecast_report.get("forecasts") or []:
                    gene = entry.get("gene", "")
                    pb = entry.get("predicted_band", "low")
                    if gene and BAND_ORDER.get(pb, 0) >= min_rank and gene in score_by_gene:
                        if score_by_gene[gene] not in at_risk:
                            at_risk.append(score_by_gene[gene])
            at_risk.sort(key=lambda s: (-s.drift_risk, s.gene))
            top_n = int(self.policy.get("remediation_top", 20))
            for s in at_risk[:top_n]:
                write_playbook(s, self.root, write_delta_files=False)
                remed_written += 1
        phases["remediations_written"] = remed_written

        cascade_summaries = _cascade_scan_parents(scores, self.root, self.policy)
        phases["cascade_parents_scanned"] = len(cascade_summaries)

        deltas = _compute_deltas(metrics, previous)
        top_at_risk = [
            {"gene": s.gene, "drift_risk": s.drift_risk, "band": s.band}
            for s in sorted(scores, key=lambda x: (-x.drift_risk, x.gene))[:15]
        ]
        if forecast_report and self.policy.get("use_forecast_in_cycle", True):
            forecast_top = sorted(
                forecast_report.get("forecasts") or [],
                key=lambda x: -int(x.get("predicted_risk_30d", 0)),
            )[:10]
            merged_genes: list[str] = []
            for entry in forecast_top:
                g = entry.get("gene")
                if g:
                    merged_genes.append(g)
            for item in top_at_risk:
                if item["gene"] not in merged_genes:
                    merged_genes.append(item["gene"])
            top_at_risk = []
            score_map = {s.gene: s for s in scores}
            fc_map = {e["gene"]: e for e in forecast_report.get("forecasts") or []}
            for g in merged_genes[:15]:
                if g in fc_map:
                    e = fc_map[g]
                    top_at_risk.append(
                        {
                            "gene": g,
                            "drift_risk": e.get("predicted_risk_30d", 0),
                            "band": e.get("predicted_band", "low"),
                            "source": "forecast",
                        }
                    )
                elif g in score_map:
                    s = score_map[g]
                    top_at_risk.append(
                        {
                            "gene": g,
                            "drift_risk": s.drift_risk,
                            "band": s.band,
                            "source": "reactive",
                        }
                    )
        opt_recs = _optimization_recommendations(
            metrics,
            self.policy,
            policy_mode,
            remediation_band,
            scores,
            previous,
            cascade_summaries,
        )

        if self.policy.get("auto_tune_policy") and not dry_run:
            for rec in opt_recs:
                if rec.get("kind") == "policy_mode" and rec.get("suggested") == "enforce":
                    reg["policy_mode"] = "enforce"
                    self._gov().save_registry(reg)
                    policy_mode = "enforce"
                    break

        report = LinguisticGovernanceCycleReport(
            cycle_id=cycle_id,
            generated_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            policy_mode=policy_mode,
            remediation_min_band=remediation_band,
            metrics=metrics,
            phases=phases,
            deltas_from_previous=deltas,
            optimization_recommendations=opt_recs,
            top_at_risk=top_at_risk,
            cascade_summaries=cascade_summaries,
            passed=len(errors) == 0,
            errors=errors,
        )

        if policy_mode == "enforce" and metrics.high_count > 0:
            if metrics.playbook_coverage_pct < 100:
                report.passed = False
                report.errors.append(
                    "enforce mode: high-drift genes lack remediation playbooks"
                )

        if not dry_run:
            self._persist_cycle(report, reg)

        return report

    def _persist_cycle(
        self, report: LinguisticGovernanceCycleReport, reg: dict[str, Any]
    ) -> Path:
        cycle_dir = self.root / "governance/linguistic_governance_cycles"
        cycle_dir.mkdir(parents=True, exist_ok=True)
        rel = f"governance/linguistic_governance_cycles/{report.cycle_id}.v1.json"
        out_path = self.root / rel
        out_path.write_text(
            json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8"
        )
        reg["last_cycle_report"] = rel
        reg["last_cycle_id"] = report.cycle_id
        reg["last_cycle_at"] = report.generated_at
        if "cycle_policy_ref" not in reg:
            reg["cycle_policy_ref"] = "governance/linguistic_governance_cycle_policy.v1.json"
        self._gov().save_registry(reg)
        _prune_cycle_history(self.root, self.policy)
        return out_path

    def load_latest_cycle(self) -> dict[str, Any] | None:
        return _load_previous_cycle(self.root)

    def cycle_stale(self) -> bool:
        reg = self._gov().load_registry()
        last_at = reg.get("last_cycle_at")
        if not last_at:
            return True
        try:
            ts = datetime.strptime(last_at, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            return True
        max_days = int(self.policy.get("max_cycle_age_days", 7))
        return datetime.now(timezone.utc) - ts > timedelta(days=max_days)
