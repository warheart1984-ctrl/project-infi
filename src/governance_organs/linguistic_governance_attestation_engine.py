"""Linguistic governance attestation digest — Wave 14 closed-loop health."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.governance_organs._paths import repo_root
from src.governance_organs.linguistic_drift_forecast_engine import (
    forecast_stale,
    load_forecast_report,
)
from src.governance_organs.linguistic_forecast_calibration_engine import (
    calibration_stale,
    load_calibration_report,
)
from src.governance_organs.linguistic_governance_queue_engine import load_governance_queue
from src.governance_organs.linguistic_governance_work_order_engine import (
    load_all_work_orders,
    work_order_summary,
)
from tools.linguistic_genome_lib import load_json

ATTESTATION_VERSION = "linguistic_governance_attestation.v1"


def load_cadence_policy(root: Path | None = None) -> dict[str, Any]:
    root = root or repo_root()
    path = root / "governance/linguistic_governance_cadence_policy.v1.json"
    if not path.is_file():
        return {
            "version": "linguistic_governance_cadence_policy.v1",
            "max_forecast_age_days": 7,
            "max_calibration_age_days": 14,
            "max_queue_age_days": 7,
            "max_full_cycle_age_days": 7,
            "max_attestation_age_days": 7,
            "max_pending_work_order_days": 14,
            "retain_attestation_history": 12,
            "enforce_min_closed_loop_score": 60,
            "enforce_block_on_stale_attestation": True,
            "enforce_block_on_unaligned_attested_loop": True,
            "enforce_block_on_pending_work_orders": False,
        }
    return load_json(path)


def _prune_attestation_history(root: Path, policy: dict[str, Any]) -> None:
    retain = int(policy.get("retain_attestation_history", 12))
    cycle_dir = root / "governance/linguistic_attestation_cycles"
    if not cycle_dir.is_dir():
        return
    files = sorted(cycle_dir.glob("*.v1.json"), key=lambda p: p.name, reverse=True)
    for old in files[retain:]:
        old.unlink(missing_ok=True)


def list_attestation_cycles(root: Path | None = None) -> list[Path]:
    root = root or repo_root()
    cycle_dir = root / "governance/linguistic_attestation_cycles"
    if not cycle_dir.is_dir():
        return []
    return sorted(cycle_dir.glob("*.v1.json"), key=lambda p: p.name, reverse=True)


def load_latest_attestation_cycle(root: Path | None = None) -> dict[str, Any] | None:
    files = list_attestation_cycles(root)
    if not files:
        return None
    return load_json(files[0])


def load_prior_attestation_cycle(root: Path | None = None) -> dict[str, Any] | None:
    files = list_attestation_cycles(root)
    if len(files) < 2:
        return None
    return load_json(files[1])


def attestation_diff(root: Path | None = None) -> dict[str, Any]:
    """Compare latest attestation cycle to prior."""
    root = root or repo_root()
    latest = load_attestation(root) or load_latest_attestation_cycle(root)
    prior = load_prior_attestation_cycle(root)
    if not latest:
        return {"present": False}
    out: dict[str, Any] = {
        "present": True,
        "latest_generated_at": latest.get("generated_at"),
        "latest_score": int(latest.get("closed_loop_score", 0)),
        "prior_score": None,
        "score_delta": None,
        "recommendation_changes": [],
    }
    if prior:
        out["prior_generated_at"] = prior.get("generated_at")
        out["prior_score"] = int(prior.get("closed_loop_score", 0))
        out["score_delta"] = out["latest_score"] - out["prior_score"]
        latest_actions = {r.get("action") for r in (latest.get("recommendations") or [])}
        prior_actions = {r.get("action") for r in (prior.get("recommendations") or [])}
        out["recommendation_changes"] = sorted(latest_actions ^ prior_actions)
    return out


def _parse_ts(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _age_days(ts: str) -> float | None:
    dt = _parse_ts(ts)
    if not dt:
        return None
    return (datetime.now(timezone.utc) - dt).total_seconds() / 86400


def _forecast_summary(root: Path) -> dict[str, Any]:
    report = load_forecast_report(root)
    if not report:
        return {"present": False, "predicted_medium_high": 0}
    medium_high = 0
    for entry in report.get("forecasts") or []:
        band = entry.get("predicted_band", "low")
        if band in ("medium", "high"):
            medium_high += 1
    return {
        "present": True,
        "generated_at": report.get("generated_at", ""),
        "predicted_medium_high": medium_high,
        "stale": forecast_stale(root),
    }


def _calibration_summary(root: Path) -> dict[str, Any]:
    report = load_calibration_report(root)
    if not report:
        return {"present": False}
    metrics = report.get("metrics") or {}
    return {
        "present": True,
        "generated_at": report.get("generated_at", ""),
        "band_hit_rate": metrics.get("band_hit_rate"),
        "false_alarm_rate": metrics.get("false_alarm_rate"),
        "miss_rate": metrics.get("miss_rate"),
        "stale": calibration_stale(root),
    }


def _queue_summary(root: Path) -> dict[str, Any]:
    queue = load_governance_queue(root)
    if not queue:
        return {"present": False, "item_count": 0, "top_genes": []}
    items = queue.get("items") or []
    return {
        "present": True,
        "generated_at": queue.get("generated_at", ""),
        "item_count": len(items),
        "top_genes": [i.get("gene") for i in items[:5] if i.get("gene")],
    }


def _full_cycle_summary(root: Path, reg: dict[str, Any]) -> dict[str, Any]:
    rel = reg.get("last_full_cycle_report")
    if not rel:
        return {"present": False}
    path = root / rel
    if not path.is_file():
        return {"present": False}
    data = load_json(path)
    phases = data.get("phases") or {}
    return {
        "present": True,
        "cycle_id": data.get("cycle_id"),
        "generated_at": data.get("generated_at"),
        "passed": data.get("passed", True),
        "phase_keys": sorted(phases.keys()),
    }


def _compute_closed_loop_score(
    *,
    reg: dict[str, Any],
    forecast: dict[str, Any],
    calibration: dict[str, Any],
    queue: dict[str, Any],
    work_orders: dict[str, Any],
    full_cycle: dict[str, Any],
) -> int:
    score = 100
    if not reg.get("last_predictive_cycle_at"):
        score -= 15
    if not reg.get("last_cycle_at"):
        score -= 15
    if calibration.get("stale") or not calibration.get("present"):
        score -= 15
    if forecast.get("stale") or not forecast.get("present"):
        score -= 10
    if not queue.get("present"):
        score -= 10
    if not full_cycle.get("present") or not full_cycle.get("passed"):
        score -= 15
    pending = int(work_orders.get("pending", 0))
    if pending > 5:
        score -= min(20, pending * 2)
    miss = float(calibration.get("miss_rate") or 0)
    if miss > 0.2:
        score -= 10
    return max(0, min(100, score))


def _recommendations(
    *,
    forecast: dict[str, Any],
    calibration: dict[str, Any],
    queue: dict[str, Any],
    full_cycle: dict[str, Any],
    work_orders: dict[str, Any],
) -> list[dict[str, Any]]:
    recs: list[dict[str, Any]] = []
    if forecast.get("stale"):
        recs.append({"action": "run_predictive_cycle", "reason": "forecast stale or missing"})
    if calibration.get("stale"):
        recs.append({"action": "run_calibration_cycle", "reason": "calibration stale or missing"})
    if not queue.get("present"):
        recs.append({"action": "build_governance_queue", "reason": "queue missing"})
    if not full_cycle.get("present"):
        recs.append({"action": "run_full_governance_cycle", "reason": "no full cycle on record"})
    elif not full_cycle.get("passed"):
        recs.append({"action": "review_full_cycle_errors", "reason": "last full cycle did not pass"})
    if int(work_orders.get("pending", 0)) > 0:
        recs.append(
            {
                "action": "triage_work_orders",
                "reason": f"{work_orders['pending']} pending work order(s)",
            }
        )
    return recs


def build_attestation(root: Path | None = None) -> dict[str, Any]:
    root = root or repo_root()
    reg_path = root / "governance/meta_linguistic_registry.v1.json"
    reg = load_json(reg_path) if reg_path.is_file() else {}
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    forecast = _forecast_summary(root)
    calibration = _calibration_summary(root)
    queue = _queue_summary(root)
    work_orders = work_order_summary(root)
    full_cycle = _full_cycle_summary(root, reg)

    registry_summary = {
        "policy_mode": reg.get("policy_mode", "observe"),
        "last_gate_run_at": reg.get("last_gate_run_at"),
        "last_forecast_at": reg.get("last_predictive_cycle_at"),
        "last_calibration_at": reg.get("last_calibration_at"),
        "last_cycle_at": reg.get("last_cycle_at"),
        "last_work_order_sync_at": reg.get("last_work_order_sync_at"),
        "last_attestation_at": reg.get("last_attestation_at"),
    }

    score = _compute_closed_loop_score(
        reg=reg,
        forecast=forecast,
        calibration=calibration,
        queue=queue,
        work_orders=work_orders,
        full_cycle=full_cycle,
    )

    return {
        "linguistic_governance_attestation_version": ATTESTATION_VERSION,
        "generated_at": now,
        "closed_loop_score": score,
        "policy_mode": reg.get("policy_mode", "observe"),
        "registry_summary": registry_summary,
        "forecast_summary": forecast,
        "calibration_summary": calibration,
        "queue_summary": queue,
        "work_order_summary": work_orders,
        "full_cycle_summary": full_cycle,
        "meta_gate_summary": {
            "last_gate_run_at": reg.get("last_gate_run_at"),
        },
        "recommendations": _recommendations(
            forecast=forecast,
            calibration=calibration,
            queue=queue,
            full_cycle=full_cycle,
            work_orders=work_orders,
        ),
    }


def write_attestation(
    root: Path | None = None,
    output: str | Path | None = None,
) -> Path:
    root = root or repo_root()
    payload = build_attestation(root)
    out = Path(output) if output else root / "governance/linguistic_governance_attestation.v1.json"
    if not out.is_absolute():
        out = root / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    policy = load_cadence_policy(root)
    cycle_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    cycle_dir = root / "governance/linguistic_attestation_cycles"
    cycle_dir.mkdir(parents=True, exist_ok=True)
    cycle_path = cycle_dir / f"{cycle_id}.v1.json"
    cycle_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _prune_attestation_history(root, policy)

    reg_path = root / "governance/meta_linguistic_registry.v1.json"
    if reg_path.is_file():
        from src.governance_organs.linguistic_governance_engine import LinguisticGovernanceEngine

        reg = load_json(reg_path)
        rel = str(out.relative_to(root)).replace("\\", "/")
        reg["last_attestation_report"] = rel
        reg["last_attestation_at"] = payload["generated_at"]
        if "cadence_policy_ref" not in reg:
            reg["cadence_policy_ref"] = (
                "governance/linguistic_governance_cadence_policy.v1.json"
            )
        LinguisticGovernanceEngine(root).save_registry(reg)

    return out


def load_attestation(root: Path | None = None) -> dict[str, Any] | None:
    root = root or repo_root()
    reg_path = root / "governance/meta_linguistic_registry.v1.json"
    path = root / "governance/linguistic_governance_attestation.v1.json"
    if reg_path.is_file():
        reg = load_json(reg_path)
        ref = reg.get("last_attestation_report")
        if ref:
            path = root / ref
    if path.is_file():
        return load_json(path)
    return None


def attestation_stale(root: Path | None = None) -> bool:
    root = root or repo_root()
    policy = load_cadence_policy(root)
    max_days = int(policy.get("max_attestation_age_days", 7))
    att = load_attestation(root)
    if not att:
        return True
    age = _age_days(att.get("generated_at", ""))
    return age is None or age > max_days


def format_attestation_markdown(att: dict[str, Any]) -> str:
    lines = [
        "# Linguistic governance attestation",
        "",
        f"Generated: {att.get('generated_at', '')}",
        f"Closed-loop score: **{att.get('closed_loop_score', 0)}** / 100",
        f"Policy mode: {att.get('policy_mode', 'observe')}",
        "",
        "## Summaries",
        "",
    ]
    for key in ("forecast_summary", "calibration_summary", "queue_summary", "work_order_summary"):
        lines.append(f"- **{key}**: `{att.get(key)}`")
    lines.append("")
    recs = att.get("recommendations") or []
    if recs:
        lines.append("## Recommendations")
        lines.append("")
        for r in recs:
            lines.append(f"- {r.get('action')}: {r.get('reason')}")
        lines.append("")
    return "\n".join(lines)
