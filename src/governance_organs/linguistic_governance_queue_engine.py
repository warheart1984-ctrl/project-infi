"""Linguistic governance queue engine — Wave 13 prescriptive operator backlog."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.governance_organs._paths import repo_root
from src.governance_organs.linguistic_cascade_engine import load_cascade_policy
from src.governance_organs.linguistic_drift_forecast_engine import load_forecast_report
from src.governance_organs.linguistic_forecast_calibration_engine import load_calibration_report
from tools.linguistic_drift_predictor import score_gene
from tools.linguistic_genome_lib import load_genome, load_json

BAND_ORDER = {"high": 3, "medium": 2, "low": 1}


def _urgency_score(
    *,
    current_risk: int,
    predicted_risk: int,
    current_band: str,
    predicted_band: str,
    calibration_outcome: str = "",
    lineage_fanout: float = 0.0,
) -> float:
    rank_delta = BAND_ORDER.get(predicted_band, 1) - BAND_ORDER.get(current_band, 1)
    score = predicted_risk * 0.4 + current_risk * 0.3 + max(0, rank_delta) * 15
    if calibration_outcome == "miss":
        score += 12
    if calibration_outcome == "false_alarm":
        score += 4
    if lineage_fanout >= 60:
        score += 8
    return round(score, 1)


def _merge_actions(gene: str, root: Path) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    preempt = root / "governance/linguistic_preemptive_remediations" / f"{gene}.v1.json"
    remed = root / "governance/linguistic_remediations" / f"{gene}.v1.json"
    for path in (preempt, remed):
        if path.is_file():
            data = load_json(path)
            for act in data.get("actions") or []:
                if act not in actions:
                    actions.append(act)

    genome = load_genome(gene, root)
    if genome:
        children = (genome.get("lineage") or {}).get("children") or []
        if children:
            actions.append(
                {
                    "kind": "cascade_report",
                    "command": f"python tools/linguistic_cascade_report.py --gene {gene}",
                    "note": "Review lineage cascade impact",
                }
            )
    return actions


def build_governance_queue(
    root: Path | None = None,
    *,
    top: int = 30,
) -> dict[str, Any]:
    root = root or repo_root()
    items_by_gene: dict[str, dict[str, Any]] = {}

    calibration = load_calibration_report(root)
    cal_by_gene = {
        r["gene"]: r for r in (calibration or {}).get("gene_records") or [] if r.get("gene")
    }

    forecast = load_forecast_report(root)
    for entry in (forecast or {}).get("forecasts") or []:
        gene = entry.get("gene", "")
        if not gene:
            continue
        sources = ["forecast"]
        if (root / "governance/linguistic_preemptive_remediations" / f"{gene}.v1.json").is_file():
            sources.append("preemptive")
        if (root / "governance/linguistic_remediations" / f"{gene}.v1.json").is_file():
            sources.append("remediation")
        cal = cal_by_gene.get(gene, {})
        current = score_gene(gene, root)
        urgency = _urgency_score(
            current_risk=current.drift_risk,
            predicted_risk=int(entry.get("predicted_risk_30d", current.drift_risk)),
            current_band=entry.get("current_band", current.band),
            predicted_band=entry.get("predicted_band", "low"),
            calibration_outcome=cal.get("band_outcome", ""),
            lineage_fanout=float(current.signals.get("lineage_fanout", 0)),
        )
        items_by_gene[gene] = {
            "gene": gene,
            "urgency_score": urgency,
            "sources": list(dict.fromkeys(sources)),
            "current_band": current.band,
            "predicted_band": entry.get("predicted_band"),
            "current_risk": current.drift_risk,
            "predicted_risk_30d": entry.get("predicted_risk_30d"),
            "calibration_outcome": cal.get("band_outcome", ""),
            "recommended_actions": _merge_actions(gene, root),
        }

    for gene, cal in cal_by_gene.items():
        if cal.get("band_outcome") == "miss" and gene not in items_by_gene:
            current = score_gene(gene, root)
            items_by_gene[gene] = {
                "gene": gene,
                "urgency_score": _urgency_score(
                    current_risk=current.drift_risk,
                    predicted_risk=int(cal.get("predicted_risk_30d", 0)),
                    current_band=cal.get("actual_band", current.band),
                    predicted_band=cal.get("predicted_band", "low"),
                    calibration_outcome="miss",
                    lineage_fanout=float(current.signals.get("lineage_fanout", 0)),
                ),
                "sources": ["calibration"],
                "current_band": cal.get("actual_band"),
                "predicted_band": cal.get("predicted_band"),
                "current_risk": cal.get("actual_risk"),
                "predicted_risk_30d": cal.get("predicted_risk_30d"),
                "calibration_outcome": "miss",
                "recommended_actions": _merge_actions(gene, root),
            }

    cascade_policy = load_cascade_policy(root)
    min_fanout = float(cascade_policy.get("cascade_scan_min_fanout", 4))
    for path in (root / "governance/linguistic_remediations").glob("*.v1.json"):
        gene = path.stem.replace(".v1", "")
        if gene in items_by_gene:
            if "remediation" not in items_by_gene[gene]["sources"]:
                items_by_gene[gene]["sources"].append("remediation")
            continue
        current = score_gene(gene, root)
        if float(current.signals.get("lineage_fanout", 0)) < min_fanout * 15:
            continue
        items_by_gene[gene] = {
            "gene": gene,
            "urgency_score": _urgency_score(
                current_risk=current.drift_risk,
                predicted_risk=current.drift_risk,
                current_band=current.band,
                predicted_band=current.band,
                lineage_fanout=float(current.signals.get("lineage_fanout", 0)),
            ),
            "sources": ["remediation"],
            "current_band": current.band,
            "predicted_band": current.band,
            "current_risk": current.drift_risk,
            "predicted_risk_30d": current.drift_risk,
            "calibration_outcome": "",
            "recommended_actions": _merge_actions(gene, root),
        }

    from src.governance_organs.linguistic_governance_work_order_engine import load_work_order

    for gene, item in items_by_gene.items():
        wo = load_work_order(gene, root)
        item["work_order_status"] = wo.get("status", "pending") if wo else "pending"

    items = sorted(items_by_gene.values(), key=lambda x: (-x["urgency_score"], x["gene"]))
    return {
        "linguistic_governance_queue_version": "linguistic_governance_queue.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "items": items[:top],
    }


def write_governance_queue(
    root: Path | None = None,
    output: str | Path | None = None,
    *,
    top: int = 30,
) -> Path:
    root = root or repo_root()
    payload = build_governance_queue(root, top=top)
    out = Path(output) if output else root / "governance/linguistic_governance_queue.v1.json"
    if not out.is_absolute():
        out = root / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    reg_path = root / "governance/meta_linguistic_registry.v1.json"
    if reg_path.is_file():
        from src.governance_organs.linguistic_governance_engine import LinguisticGovernanceEngine

        reg = load_json(reg_path)
        rel = str(out.relative_to(root)).replace("\\", "/")
        reg["last_governance_queue"] = rel
        LinguisticGovernanceEngine(root).save_registry(reg)

    return out


def format_queue_markdown(queue: dict[str, Any]) -> str:
    lines = [
        "# Linguistic governance queue",
        "",
        f"Generated: {queue.get('generated_at', '')}",
        "",
        "| Rank | Gene | Urgency | Current | Predicted | Sources |",
        "|------|------|---------|---------|-----------|---------|",
    ]
    for i, item in enumerate(queue.get("items") or [], 1):
        sources = ", ".join(item.get("sources") or [])
        lines.append(
            f"| {i} | `{item.get('gene')}` | {item.get('urgency_score')} | "
            f"{item.get('current_band')} | {item.get('predicted_band')} | {sources} |"
        )
    lines.append("")
    return "\n".join(lines)


def load_governance_queue(root: Path | None = None) -> dict[str, Any] | None:
    root = root or repo_root()
    reg_path = root / "governance/meta_linguistic_registry.v1.json"
    path = root / "governance/linguistic_governance_queue.v1.json"
    if reg_path.is_file():
        reg = load_json(reg_path)
        ref = reg.get("last_governance_queue")
        if ref:
            path = root / ref
    if path.is_file():
        return load_json(path)
    return None


def queue_priority_genes(root: Path | None = None, top: int = 15) -> list[str]:
    queue = load_governance_queue(root)
    if not queue:
        return []
    return [item["gene"] for item in (queue.get("items") or [])[:top] if item.get("gene")]
