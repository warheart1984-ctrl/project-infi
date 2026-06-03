"""Linguistic drift forecast engine — Wave 12 forward-looking drift anticipation."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.governance_organs._paths import repo_root
from tools.linguistic_drift_predictor import DriftScore, score_gene
from tools.linguistic_genome_lib import list_all_genes, list_snapshots, load_genome, load_json

BAND_ORDER = {"high": 3, "medium": 2, "low": 1}


def _band(score: int) -> str:
    if score >= 67:
        return "high"
    if score >= 34:
        return "medium"
    return "low"


@dataclass
class ForecastScore:
    gene: str
    current_risk: int
    current_band: str
    predicted_risk_30d: int
    predicted_band: str
    lead_time_days: int
    signals: dict[str, float] = field(default_factory=dict)
    drivers: list[str] = field(default_factory=list)


def load_forecast_policy(root: Path | None = None) -> dict[str, Any]:
    root = root or repo_root()
    reg_path = root / "governance/meta_linguistic_registry.v1.json"
    policy_ref = "governance/linguistic_predictive_governance_policy.v1.json"
    if reg_path.is_file():
        reg = load_json(reg_path)
        policy_ref = reg.get("predictive_policy_ref", policy_ref)
    path = root / policy_ref
    if not path.is_file():
        return {
            "version": "linguistic_predictive_governance_policy.v1",
            "horizon_days": 30,
            "min_predicted_band": "medium",
            "preemptive_top": 15,
            "weights": {
                "trajectory_delta": 0.25,
                "latent_alignment": 0.30,
                "mutation_pressure": 0.20,
                "parent_forecast": 0.15,
                "ecosystem_trend": 0.10,
            },
            "max_forecast_age_days": 7,
            "retain_predictive_cycle_history": 12,
        }
    return load_json(path)


def _trajectory_delta(gene: str, root: Path, horizon_days: int = 30) -> float:
    snaps = list_snapshots(gene, root)
    if len(snaps) <= 1:
        return 0.0
    cutoff = datetime.now(timezone.utc) - timedelta(days=horizon_days)
    recent_fps: list[str] = []
    for sp in snaps[-5:]:
        data = load_json(sp)
        ts = data.get("captured_at", "")
        try:
            when = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            continue
        if when >= cutoff:
            fp = (data.get("fingerprints") or {}).get("combined", "")
            if fp:
                recent_fps.append(fp)
    if len(recent_fps) <= 1:
        recent_count = sum(
            1
            for sp in snaps
            if load_json(sp).get("captured_at", "") >= cutoff.isoformat()[:10]
        )
        return min(recent_count * 12.0, 60.0)
    changes = sum(
        1 for i in range(1, len(recent_fps)) if recent_fps[i] != recent_fps[i - 1]
    )
    return min(changes * 20.0 + len(recent_fps) * 5.0, 80.0)


def _mutation_pressure(gene: str, root: Path) -> float:
    pressure = 0.0
    from src.governance_organs.mutation_engine import MutationEngine

    engine = MutationEngine(root)
    for proposal in engine.list_proposals(gene):
        if proposal.mutation_kind == "linguistic_layer":
            if proposal.status in {"draft", "pending", "proposed"}:
                pressure = max(pressure, 25.0)
            else:
                pressure = max(pressure, 15.0)
    delta_dir = root / "schemas/deltas"
    if delta_dir.is_dir():
        for path in delta_dir.glob(f"{gene}_*_linguistic.json"):
            pressure = max(pressure, 20.0)
    return pressure


def _ecosystem_trend(root: Path) -> float:
    cycle_dir = root / "governance/linguistic_governance_cycles"
    if not cycle_dir.is_dir():
        return 0.0
    files = sorted(cycle_dir.glob("*.v1.json"), key=lambda p: p.name)[-2:]
    if len(files) < 2:
        return 0.0
    deltas = []
    for path in files:
        data = load_json(path)
        d = (data.get("deltas_from_previous") or {}).get("mean_drift_risk_delta")
        if d is not None:
            deltas.append(float(d))
    if not deltas:
        return 0.0
    avg = sum(deltas) / len(deltas)
    if avg > 0:
        return min(avg * 10.0, 30.0)
    return 0.0


def _parent_genes_at_risk(root: Path) -> set[str]:
    at_risk: set[str] = set()
    reg_path = root / "governance/meta_linguistic_registry.v1.json"
    if reg_path.is_file():
        reg = load_json(reg_path)
        cycle_ref = reg.get("last_cycle_report")
        if cycle_ref:
            cycle_path = root / cycle_ref
            if cycle_path.is_file():
                cycle = load_json(cycle_path)
                for entry in cycle.get("top_at_risk") or []:
                    g = entry.get("gene")
                    if g:
                        at_risk.add(g)
    forecast_path = root / "governance/linguistic_drift_forecast.v1.json"
    if forecast_path.is_file():
        data = load_json(forecast_path)
        sorted_fc = sorted(
            data.get("forecasts") or [],
            key=lambda x: -int(x.get("predicted_risk_30d", 0)),
        )
        for entry in sorted_fc[:15]:
            g = entry.get("gene")
            if g:
                at_risk.add(g)
    return at_risk


def _parent_forecast_signal(gene: str, root: Path, parents_at_risk: set[str]) -> float:
    genome = load_genome(gene, root)
    if not genome:
        return 0.0
    parents = (genome.get("lineage") or {}).get("parents") or []
    hits = [p for p in parents if p in parents_at_risk]
    if not hits:
        return 0.0
    return min(15.0 + len(hits) * 5.0, 40.0)


def _latent_alignment_signal(current: DriftScore) -> float:
    gap = float(current.signals.get("alignment_gap", 0))
    if gap >= 40 and current.band == "low":
        return min(gap * 0.75, 70.0)
    if gap >= 40 and current.band == "medium":
        return min(gap * 0.4, 35.0)
    return 0.0


def _lead_time_days(current_band: str, predicted_band: str, delta_risk: int) -> int:
    if BAND_ORDER[predicted_band] <= BAND_ORDER[current_band]:
        return 0
    if delta_risk <= 0:
        return 30
    days = int(round(30 * (BAND_ORDER[predicted_band] - BAND_ORDER[current_band]) / max(delta_risk / 20.0, 1)))
    return max(1, min(days, 30))


def forecast_gene(
    gene: str,
    root: Path | None = None,
    *,
    current: DriftScore | None = None,
    policy: dict[str, Any] | None = None,
    ecosystem_trend: float | None = None,
    parents_at_risk: set[str] | None = None,
) -> ForecastScore:
    root = root or repo_root()
    policy = policy or load_forecast_policy(root)
    weights = policy.get("weights") or {}
    horizon = int(policy.get("horizon_days", 30))

    current = current or score_gene(gene, root)
    eco = ecosystem_trend if ecosystem_trend is not None else _ecosystem_trend(root)
    parents = parents_at_risk if parents_at_risk is not None else _parent_genes_at_risk(root)

    signals = {
        "trajectory_delta": _trajectory_delta(gene, root, horizon),
        "latent_alignment": _latent_alignment_signal(current),
        "mutation_pressure": _mutation_pressure(gene, root),
        "parent_forecast": _parent_forecast_signal(gene, root, parents),
        "ecosystem_trend": eco,
    }

    boost = int(
        round(
            signals["trajectory_delta"] * float(weights.get("trajectory_delta", 0.25))
            + signals["latent_alignment"] * float(weights.get("latent_alignment", 0.30))
            + signals["mutation_pressure"] * float(weights.get("mutation_pressure", 0.20))
            + signals["parent_forecast"] * float(weights.get("parent_forecast", 0.15))
            + signals["ecosystem_trend"] * float(weights.get("ecosystem_trend", 0.10))
        )
    )
    predicted = max(0, min(100, current.drift_risk + boost))
    predicted_band = _band(predicted)

    drivers: list[str] = []
    if signals["latent_alignment"] >= 30:
        drivers.append("latent alignment gap (header/doc vs genome ssp)")
    if signals["trajectory_delta"] >= 20:
        drivers.append("rising linguistic snapshot trajectory")
    if signals["mutation_pressure"] >= 15:
        drivers.append("pending or draft MP-LING linguistic mutation")
    if signals["parent_forecast"] >= 10:
        drivers.append("parent gene in forecast or cycle at-risk set")
    if signals["ecosystem_trend"] >= 5:
        drivers.append("ecosystem mean drift trending upward")

    lead = _lead_time_days(current.band, predicted_band, predicted - current.drift_risk)

    return ForecastScore(
        gene=gene,
        current_risk=current.drift_risk,
        current_band=current.band,
        predicted_risk_30d=predicted,
        predicted_band=predicted_band,
        lead_time_days=lead,
        signals=signals,
        drivers=drivers,
    )


def forecast_all(root: Path | None = None) -> list[ForecastScore]:
    root = root or repo_root()
    policy = load_forecast_policy(root)
    eco = _ecosystem_trend(root)
    genes = list_all_genes(root)
    currents = {g: score_gene(g, root) for g in genes}

    preliminary: list[ForecastScore] = []
    for gene in genes:
        preliminary.append(
            forecast_gene(
                gene,
                root,
                current=currents[gene],
                policy=policy,
                ecosystem_trend=eco,
                parents_at_risk=set(),
            )
        )
    parents_at_risk = {f.gene for f in sorted(preliminary, key=lambda x: -x.predicted_risk_30d)[:15]}
    reg_parents = _parent_genes_at_risk(root)
    parents_at_risk |= reg_parents

    results: list[ForecastScore] = []
    for gene in genes:
        results.append(
            forecast_gene(
                gene,
                root,
                current=currents[gene],
                policy=policy,
                ecosystem_trend=eco,
                parents_at_risk=parents_at_risk,
            )
        )
    results.sort(key=lambda f: (-f.predicted_risk_30d, f.gene))
    return results


def write_forecast_report(
    root: Path | None = None,
    output: str | Path | None = None,
) -> Path:
    root = root or repo_root()
    policy = load_forecast_policy(root)
    forecasts = forecast_all(root)
    out = Path(output) if output else root / "governance/linguistic_drift_forecast.v1.json"
    if not out.is_absolute():
        out = root / out
    payload = {
        "linguistic_drift_forecast_version": "linguistic_drift_forecast.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "horizon_days": int(policy.get("horizon_days", 30)),
        "ecosystem_trend": _ecosystem_trend(root),
        "forecasts": [asdict(f) for f in forecasts],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return out


def load_forecast_report(root: Path | None = None) -> dict[str, Any] | None:
    root = root or repo_root()
    reg_path = root / "governance/meta_linguistic_registry.v1.json"
    path = root / "governance/linguistic_drift_forecast.v1.json"
    if reg_path.is_file():
        reg = load_json(reg_path)
        ref = reg.get("last_forecast_report")
        if ref:
            path = root / ref
    if path.is_file():
        return load_json(path)
    return None


def forecast_metrics_from_report(report: dict[str, Any] | None) -> dict[str, int]:
    if not report:
        return {"predicted_high": 0, "predicted_medium": 0, "predicted_low": 0}
    high = medium = low = 0
    for f in report.get("forecasts") or []:
        band = f.get("predicted_band", "low")
        if band == "high":
            high += 1
        elif band == "medium":
            medium += 1
        else:
            low += 1
    return {
        "predicted_high": high,
        "predicted_medium": medium,
        "predicted_low": low,
    }


def build_preemptive_playbook(forecast: ForecastScore, root: Path | None = None) -> dict[str, Any]:
    root = root or repo_root()
    from tools.linguistic_genome_lib import load_genome

    genome = load_genome(forecast.gene, root)
    actions: list[dict[str, Any]] = []
    module = ""
    if genome:
        for entry in (genome.get("runtime") or {}).get("surface") or []:
            if isinstance(entry, dict) and entry.get("kind") == "module":
                module = entry.get("path") or ""
                break

    if "latent alignment" in " ".join(forecast.drivers).lower() and module:
        actions.append(
            {
                "kind": "watch_wave2_header",
                "path": module,
                "note": "Add # Engineering header before band escalates",
            }
        )
    if "MP-LING" in " ".join(forecast.drivers):
        actions.append(
            {
                "kind": "watch_mp_ling",
                "command": f"python tools/governance/apply_linguistic_mutation.py --dry-run --gene {forecast.gene}",
                "note": "Review draft linguistic delta before apply",
            }
        )
    if "parent gene" in " ".join(forecast.drivers).lower():
        parents = (genome.get("lineage") or {}).get("parents") or [] if genome else []
        if parents:
            actions.append(
                {
                    "kind": "watch_cascade",
                    "command": f"python tools/linguistic_cascade_report.py --gene {parents[0]}",
                    "note": "Parent at risk — monitor cascade",
                }
            )
    if forecast.predicted_band in {"medium", "high"}:
        actions.append(
            {
                "kind": "schedule_remediation",
                "command": (
                    f"python tools/governance/generate_linguistic_remediations.py "
                    f"--gene {forecast.gene}"
                ),
                "note": "Pre-generate remediation when predicted band materializes",
            }
        )

    return {
        "linguistic_preemptive_playbook_version": "linguistic_preemptive_playbook.v1",
        "gene": forecast.gene,
        "current_band": forecast.current_band,
        "predicted_band": forecast.predicted_band,
        "predicted_risk_30d": forecast.predicted_risk_30d,
        "lead_time_days": forecast.lead_time_days,
        "drivers": forecast.drivers,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actions": actions,
    }


def write_preemptive_playbook(forecast: ForecastScore, root: Path | None = None) -> Path:
    root = root or repo_root()
    playbook = build_preemptive_playbook(forecast, root)
    out_dir = root / "governance/linguistic_preemptive_remediations"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{forecast.gene}.v1.json"
    out_path.write_text(json.dumps(playbook, indent=2) + "\n", encoding="utf-8")
    return out_path


def preemptive_playbook_exists(gene: str, root: Path | None = None) -> bool:
    root = root or repo_root()
    return (root / "governance/linguistic_preemptive_remediations" / f"{gene}.v1.json").is_file()


def forecast_stale(root: Path | None = None) -> bool:
    root = root or repo_root()
    policy = load_forecast_policy(root)
    report = load_forecast_report(root)
    if not report:
        return True
    generated = report.get("generated_at", "")
    try:
        ts = datetime.strptime(generated, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return True
    max_days = int(policy.get("max_forecast_age_days", 7))
    return datetime.now(timezone.utc) - ts > timedelta(days=max_days)
