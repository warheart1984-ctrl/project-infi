#!/usr/bin/env python3
import argparse
import json
import os
import statistics
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class GateThreshold:
    category: str
    pct_increase: float
    sec_increase: float

    def allowed_duration(self, anchor_duration: float) -> float:
        pct_cap = anchor_duration * (1.0 + self.pct_increase / 100.0)
        sec_cap = anchor_duration + self.sec_increase
        return max(pct_cap, sec_cap)


@dataclass(frozen=True)
class BandSettings:
    pct_increase: float
    sec_increase: float
    z_threshold: float
    min_stddev_sec: float

    @classmethod
    def from_dict(cls, raw: dict[str, Any], fallback: "BandSettings") -> "BandSettings":
        def pick(key: str, fallback_value: float) -> float:
            value = raw.get(key, fallback_value)
            try:
                return float(value)
            except (TypeError, ValueError):
                return fallback_value

        return cls(
            pct_increase=pick("pct_increase", fallback.pct_increase),
            sec_increase=pick("sec_increase", fallback.sec_increase),
            z_threshold=pick("z_threshold", fallback.z_threshold),
            min_stddev_sec=pick("min_stddev_sec", fallback.min_stddev_sec),
        )


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise SystemExit(f"Invalid float for {name}: {raw}") from exc


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise SystemExit(f"Invalid integer for {name}: {raw}") from exc


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _scenario_key(s: dict[str, Any]) -> str:
    if "scenario_id" in s and str(s["scenario_id"]).strip():
        return str(s["scenario_id"]).strip()
    sid = s.get("id")
    return str(sid).strip() if sid is not None else ""


def _scenario_name(s: dict[str, Any]) -> str:
    name = str(s.get("name", "")).strip()
    if name:
        return name
    key = _scenario_key(s)
    return f"scenario-{key}" if key else "scenario-unknown"


def _scenario_tags(s: dict[str, Any]) -> set[str]:
    raw = s.get("tags", [])
    if not isinstance(raw, list):
        return set()
    return {str(item).strip() for item in raw if str(item).strip()}


def _scenario_tag_list(s: dict[str, Any]) -> list[str]:
    raw = s.get("tags", [])
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for item in raw:
        value = str(item).strip()
        if value:
            out.append(value)
    return out


def _threshold_for_tags(tags: set[str], default: GateThreshold, qemu: GateThreshold, rr: GateThreshold) -> GateThreshold:
    if "qemu_boot" in tags:
        return qemu
    if "resume" in tags or "rollback" in tags:
        return rr
    return default


def _format_pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2f}%"


def _safe_mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return float(statistics.mean(values))


def _safe_std(values: list[float]) -> float:
    if len(values) <= 1:
        return 0.0
    return float(statistics.pstdev(values))


def _history_series_from_bundle(bundle: dict[str, Any]) -> tuple[dict[str, list[float]], list[float], int]:
    by_scenario: dict[str, list[float]] = {}
    total_series: list[float] = []
    run_count = 0
    for run in bundle.get("runs", []):
        summary = run.get("matrix_summary")
        if not isinstance(summary, dict):
            continue
        run_count += 1
        total = summary.get("total_duration_sec")
        if isinstance(total, (int, float)):
            total_series.append(float(total))
        for scenario in summary.get("scenarios", []):
            if str(scenario.get("status", "")).lower() in {"skipped"}:
                continue
            sid = _scenario_key(scenario)
            if not sid:
                continue
            dur = scenario.get("duration_sec")
            if not isinstance(dur, (int, float)):
                continue
            by_scenario.setdefault(sid, []).append(float(dur))
    return by_scenario, total_series, run_count


def _load_band_config(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    data = _load_json(path)
    if not isinstance(data, dict):
        return {}
    return data


def _resolve_band(
    scenario_id: str,
    scenario_tags: list[str],
    category: str,
    band_config: dict[str, Any],
    base_band: BandSettings,
) -> tuple[str, BandSettings, bool]:
    scenario_overrides = band_config.get("scenario_overrides", {})
    if isinstance(scenario_overrides, dict):
        raw = scenario_overrides.get(scenario_id)
        if isinstance(raw, dict):
            return (f"scenario:{scenario_id}", BandSettings.from_dict(raw, base_band), True)

    tag_defaults = band_config.get("tag_defaults", {})
    if isinstance(tag_defaults, dict):
        for tag in scenario_tags:
            raw = tag_defaults.get(tag)
            if isinstance(raw, dict):
                return (f"tag:{tag}", BandSettings.from_dict(raw, base_band), True)

    category_defaults = band_config.get("category_defaults", {})
    if isinstance(category_defaults, dict):
        raw = category_defaults.get(category)
        if isinstance(raw, dict):
            return (f"category:{category}", BandSettings.from_dict(raw, base_band), True)

    return ("global_fallback", base_band, False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check installer matrix performance gates.")
    parser.add_argument("--current", required=True, help="Path to current matrix-summary.json")
    parser.add_argument("--baseline", required=False, default="", help="Path to fallback baseline matrix-summary.json")
    parser.add_argument("--history-bundle", required=False, default="", help="Path to bundled historical summaries")
    parser.add_argument("--previous-report", required=False, default="", help="Path to previous run performance-report.json")
    parser.add_argument("--bands-config", required=False, default="", help="Path to scenario tolerance bands config")
    parser.add_argument("--mode", choices=["warn", "fail"], default=os.environ.get("PERF_GATES_MODE", "warn"))
    parser.add_argument("--report-json", default="ci-artifacts/performance-report.json")
    parser.add_argument("--report-md", default="ci-artifacts/performance-report.md")
    args = parser.parse_args()

    default_gate = GateThreshold(
        category="scenario_spike",
        pct_increase=_env_float("PERF_SCENARIO_PCT", 20.0),
        sec_increase=_env_float("PERF_SCENARIO_SEC", 30.0),
    )
    qemu_gate = GateThreshold(
        category="qemu_boot",
        pct_increase=_env_float("PERF_QEMU_PCT", 25.0),
        sec_increase=_env_float("PERF_QEMU_SEC", 20.0),
    )
    rr_gate = GateThreshold(
        category="resume_rollback",
        pct_increase=_env_float("PERF_RR_PCT", 30.0),
        sec_increase=_env_float("PERF_RR_SEC", 15.0),
    )
    total_pct = _env_float("PERF_TOTAL_PCT", 15.0)
    history_window = _env_int("PERF_HISTORY_WINDOW", 30)
    burn_in_min = _env_int("PERF_BURNIN_MIN_SAMPLES", 10)
    z_threshold = _env_float("PERF_ZSCORE_THRESHOLD", 2.5)
    min_stddev_sec = _env_float("PERF_MIN_STDDEV_SEC", 1.0)
    required_breach_streak = _env_int("PERF_BREACH_STREAK_THRESHOLD", 2)

    current_path = Path(args.current)
    baseline_path = Path(args.baseline) if args.baseline else None
    history_bundle_path = Path(args.history_bundle) if args.history_bundle else None
    previous_report_path = Path(args.previous_report) if args.previous_report else None
    bands_config_path = Path(args.bands_config) if args.bands_config else None
    report_json_path = Path(args.report_json)
    report_md_path = Path(args.report_md)
    report_json_path.parent.mkdir(parents=True, exist_ok=True)
    report_md_path.parent.mkdir(parents=True, exist_ok=True)

    current = _load_json(current_path)
    baseline: dict[str, Any] | None = None
    if baseline_path is not None and baseline_path.exists():
        baseline = _load_json(baseline_path)

    history_bundle: dict[str, Any] = {"runs": []}
    if history_bundle_path is not None and history_bundle_path.exists():
        history_bundle = _load_json(history_bundle_path)
    history_by_scenario, history_total_series, history_run_count = _history_series_from_bundle(history_bundle)

    previous_report: dict[str, Any] | None = None
    if previous_report_path is not None and previous_report_path.exists():
        previous_report = _load_json(previous_report_path)
    previous_streak = int((previous_report or {}).get("summary", {}).get("consecutive_breach_streak", 0) or 0)
    band_config = _load_band_config(bands_config_path)

    baseline_map = {}
    baseline_run_id = "unavailable"
    if baseline is not None:
        baseline_map = {_scenario_key(s): s for s in baseline.get("scenarios", []) if _scenario_key(s)}
        baseline_run_id = str(baseline.get("run_id", "unknown"))

    scenario_rows: list[dict[str, Any]] = []
    breaches: list[dict[str, Any]] = []
    notes: list[str] = []
    custom_band_count = 0

    if history_run_count == 0:
        notes.append("Historical summary bundle unavailable; using fallback baseline-only thresholds where possible.")
    if history_run_count < burn_in_min:
        notes.append(f"Burn-in active: {history_run_count}/{burn_in_min} historical successful runs available.")

    for cur in current.get("scenarios", []):
        sid = _scenario_key(cur)
        if not sid:
            continue
        if str(cur.get("status", "")).lower() in {"skipped"}:
            continue

        cur_dur = float(cur.get("duration_sec", 0.0) or 0.0)
        tags = _scenario_tags(cur)
        tag_list = _scenario_tag_list(cur)
        gate = _threshold_for_tags(tags, default_gate, qemu_gate, rr_gate)
        base_band = BandSettings(
            pct_increase=gate.pct_increase,
            sec_increase=gate.sec_increase,
            z_threshold=z_threshold,
            min_stddev_sec=min_stddev_sec,
        )
        band_key, band, uses_custom_band = _resolve_band(sid, tag_list, gate.category, band_config, base_band)
        if uses_custom_band:
            custom_band_count += 1
        history_values = history_by_scenario.get(sid, [])
        sample_size = len(history_values)
        mean_dur = _safe_mean(history_values)
        std_dur = _safe_std(history_values)
        effective_std = max(std_dur, band.min_stddev_sec) if sample_size > 1 else 0.0

        fallback_base_dur = None
        if sid in baseline_map:
            base_candidate = float(baseline_map[sid].get("duration_sec", 0.0) or 0.0)
            if base_candidate > 0:
                fallback_base_dur = base_candidate

        delta_sec = None
        delta_pct = None
        zscore = None
        allowed_duration = None
        breach = False
        model_used = ""

        if sample_size >= burn_in_min:
            model_used = "zscore_like"
            zscore = 0.0 if effective_std <= 0 else (cur_dur - mean_dur) / effective_std
            allowed_duration = GateThreshold(gate.category, band.pct_increase, band.sec_increase).allowed_duration(mean_dur)
            breach = bool(cur_dur > allowed_duration and zscore >= band.z_threshold)
            delta_sec = cur_dur - mean_dur
            delta_pct = (delta_sec / mean_dur * 100.0) if mean_dur > 0 else None
        elif fallback_base_dur is not None:
            model_used = "fallback_baseline"
            allowed_duration = GateThreshold(gate.category, band.pct_increase, band.sec_increase).allowed_duration(fallback_base_dur)
            breach = cur_dur > allowed_duration
            delta_sec = cur_dur - fallback_base_dur
            delta_pct = (delta_sec / fallback_base_dur * 100.0) if fallback_base_dur > 0 else None
            mean_dur = fallback_base_dur
        else:
            model_used = "insufficient_data"

        row = {
            "scenario_id": sid,
            "name": _scenario_name(cur),
            "tags": sorted(tags),
            "status": cur.get("status", "unknown"),
            "model_used": model_used,
            "sample_size": sample_size,
            "history_mean_duration_sec": round(mean_dur, 3),
            "history_stddev_duration_sec": round(std_dur, 3),
            "current_duration_sec": round(cur_dur, 3),
            "delta_sec": round(delta_sec, 3) if delta_sec is not None else None,
            "delta_pct": round(delta_pct, 3) if delta_pct is not None else None,
            "zscore": round(zscore, 3) if zscore is not None else None,
            "z_threshold": band.z_threshold if model_used == "zscore_like" else None,
            "min_stddev_sec": band.min_stddev_sec,
            "gate_category": gate.category,
            "band_key": band_key,
            "uses_custom_band": uses_custom_band,
            "band_fallback_used": not uses_custom_band,
            "effective_thresholds": {
                "pct_increase": band.pct_increase,
                "sec_increase": band.sec_increase,
                "z_threshold": band.z_threshold,
                "min_stddev_sec": band.min_stddev_sec,
            },
            "allowed_duration_sec": round(allowed_duration, 3) if allowed_duration is not None else None,
            "breach": breach,
            "reason": (
                "zscore_and_floor_breach"
                if (model_used == "zscore_like" and breach)
                else ("baseline_floor_breach" if (model_used == "fallback_baseline" and breach) else model_used)
            ),
        }
        scenario_rows.append(row)
        if breach:
            breaches.append(row)

    total_row = None
    current_total = float(current.get("total_duration_sec", 0.0) or 0.0)
    total_sample_size = len(history_total_series)
    total_mean = _safe_mean(history_total_series)
    total_std = _safe_std(history_total_series)
    total_effective_std = max(total_std, min_stddev_sec) if total_sample_size > 1 else 0.0
    total_zscore = None
    total_allowed = None
    total_breach = False
    total_model = ""

    if total_sample_size >= burn_in_min:
        total_model = "zscore_like"
        total_zscore = 0.0 if total_effective_std <= 0 else (current_total - total_mean) / total_effective_std
        total_allowed = total_mean * (1.0 + total_pct / 100.0)
        total_breach = bool(current_total > total_allowed and total_zscore >= z_threshold)
    elif baseline is not None:
        base_total = float(baseline.get("total_duration_sec", 0.0) or 0.0)
        if base_total > 0:
            total_model = "fallback_baseline"
            total_mean = base_total
            total_allowed = base_total * (1.0 + total_pct / 100.0)
            total_breach = current_total > total_allowed
    else:
        total_model = "insufficient_data"

    if total_model:
        total_row = {
            "scenario_id": "total",
            "name": "InstallerMatrixTotalDuration",
            "tags": ["aggregate"],
            "status": "computed",
            "model_used": total_model,
            "sample_size": total_sample_size,
            "history_mean_duration_sec": round(total_mean, 3),
            "history_stddev_duration_sec": round(total_std, 3),
            "current_duration_sec": round(current_total, 3),
            "delta_sec": round(current_total - total_mean, 3) if total_mean > 0 else None,
            "delta_pct": round(((current_total - total_mean) / total_mean * 100.0), 3) if total_mean > 0 else None,
            "zscore": round(total_zscore, 3) if total_zscore is not None else None,
            "z_threshold": z_threshold if total_model == "zscore_like" else None,
            "gate_category": "installer_total",
            "allowed_duration_sec": round(total_allowed, 3) if total_allowed is not None else None,
            "breach": total_breach,
            "reason": (
                "zscore_and_floor_breach"
                if (total_model == "zscore_like" and total_breach)
                else ("baseline_floor_breach" if (total_model == "fallback_baseline" and total_breach) else total_model)
            ),
        }
        if total_breach:
            breaches.append(total_row)

    qemu_rows = [row for row in scenario_rows if "qemu_boot" in set(row.get("tags", []))]
    rr_rows = [row for row in scenario_rows if ("resume" in set(row.get("tags", [])) or "rollback" in set(row.get("tags", [])))]
    qemu_breaches = [row for row in qemu_rows if row.get("breach")]
    rr_breaches = [row for row in rr_rows if row.get("breach")]

    current_run_id = str(current.get("run_id", "unknown"))
    current_breach = len(breaches) > 0
    consecutive_breach_streak = (previous_streak + 1) if current_breach else 0
    enforcement_ready = history_run_count >= burn_in_min
    should_fail = bool(
        args.mode == "fail"
        and enforcement_ready
        and current_breach
        and consecutive_breach_streak >= required_breach_streak
    )

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": args.mode,
        "history_window": history_window,
        "history_runs_available": history_run_count,
        "burn_in_min_samples": burn_in_min,
        "enforcement_ready": enforcement_ready,
        "current_summary_path": str(current_path),
        "baseline_summary_path": str(baseline_path) if baseline_path else "",
        "history_bundle_path": str(history_bundle_path) if history_bundle_path else "",
        "previous_report_path": str(previous_report_path) if previous_report_path else "",
        "bands_config_path": str(bands_config_path) if bands_config_path else "",
        "current_run_id": current_run_id,
        "baseline_run_id": baseline_run_id,
        "thresholds": {
            "scenario_spike": {"pct": default_gate.pct_increase, "sec": default_gate.sec_increase},
            "qemu_boot": {"pct": qemu_gate.pct_increase, "sec": qemu_gate.sec_increase},
            "resume_rollback": {"pct": rr_gate.pct_increase, "sec": rr_gate.sec_increase},
            "installer_total_pct": total_pct,
            "zscore_threshold": z_threshold,
            "min_stddev_sec": min_stddev_sec,
            "breach_streak_threshold": required_breach_streak,
        },
        "summary": {
            "compared_scenarios": len(scenario_rows),
            "breach_count": len(breaches),
            "qemu_breach_count": len(qemu_breaches),
            "resume_rollback_breach_count": len(rr_breaches),
            "custom_band_scenarios": custom_band_count,
            "current_breach": current_breach,
            "previous_breach_streak": previous_streak,
            "consecutive_breach_streak": consecutive_breach_streak,
            "gate_decision": "fail" if should_fail else "warn_or_pass",
            "should_fail": should_fail,
        },
        "notes": notes,
        "scenario_comparisons": scenario_rows,
        "total_comparison": total_row,
        "breaches": breaches,
    }

    report_json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Performance Gate Report",
        "",
        f"- mode: `{args.mode}`",
        f"- current_run_id: `{current_run_id}`",
        f"- baseline_run_id: `{baseline_run_id}`",
        f"- history_runs_available: `{history_run_count}`",
        f"- burn_in_min_samples: `{burn_in_min}`",
        f"- enforcement_ready: `{str(enforcement_ready).lower()}`",
        f"- compared_scenarios: `{len(scenario_rows)}`",
        f"- breach_count: `{len(breaches)}`",
        f"- qemu_breach_count: `{len(qemu_breaches)}`",
        f"- resume_rollback_breach_count: `{len(rr_breaches)}`",
        f"- custom_band_scenarios: `{custom_band_count}`",
        f"- previous_breach_streak: `{previous_streak}`",
        f"- consecutive_breach_streak: `{consecutive_breach_streak}`",
        f"- gate_decision: `{'fail' if should_fail else 'warn_or_pass'}`",
        "",
    ]
    if notes:
        lines.append("## Notes")
        lines.extend(f"- {note}" for note in notes)
        lines.append("")

    if breaches:
        lines.append("## Breaches")
        for row in breaches:
            lines.append(
                "- {name} ({sid}): current={cur}s mean={mean}s delta={delta}s ({pct}) zscore={z} samples={samples} gate={gate} allowed={allowed}s model={model}".format(
                    name=row.get("name"),
                    sid=row.get("scenario_id"),
                    cur=row.get("current_duration_sec"),
                    mean=row.get("history_mean_duration_sec"),
                    delta=row.get("delta_sec"),
                    pct=_format_pct(row.get("delta_pct")),
                    z=row.get("zscore"),
                    samples=row.get("sample_size"),
                    gate=row.get("gate_category"),
                    allowed=row.get("allowed_duration_sec"),
                    model=f"{row.get('model_used')}[{row.get('band_key')}]",
                )
            )
    else:
        lines.append("## Breaches")
        lines.append("- none")

    report_md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    headline = (
        "Performance gates: history_runs={history} burn_in={burnin} breaches={breaches} "
        "custom_band_scenarios={custom_bands} streak={streak} mode={mode} decision={decision}"
    ).format(
        history=history_run_count,
        burnin=burn_in_min,
        breaches=len(breaches),
        custom_bands=custom_band_count,
        streak=consecutive_breach_streak,
        mode=args.mode,
        decision="fail" if should_fail else "pass",
    )
    print(headline)

    return 1 if should_fail else 0


if __name__ == "__main__":
    sys.exit(main())
