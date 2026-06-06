"""Evaluate base vs adapter Jarvis modes with governed acceptance criteria."""

from __future__ import annotations

import argparse
import json
import os
import statistics
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import src.api as api
from evals.run_mode_eval import MockEvalModel, _aggregate_mode, _default_output_path, _load_prompts, _run_one
from src.conversation_memory import conversation_memory
from src.jarvis_lora_training_validator import validate_eval_report


ACCEPTANCE_PROFILES = {
    "default": {
        "plan_pass_rate_floor_delta": 0.1,
        "latency_multiplier": 1.5,
    }
}


def _default_report_path(root: Path, run_id: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return root / ".runtime" / "evals" / f"adapter-eval-{run_id[:8]}-{timestamp}.json"


def _run_suite(client, prompts, *, use_adapter_env: dict[str, str] | None, mock_model: bool):
    original_env = {key: os.environ.get(key) for key in (
        "AAIS_ENABLE_TEXT_ADAPTERS",
        "AAIS_TEXT_ADAPTER_PATH",
        "AAIS_TEXT_ADAPTER_FAST_PATH",
        "AAIS_TEXT_ADAPTER_THINK_PATH",
        "AAIS_TEXT_MODEL_NAME",
    )}

    try:
        for key, value in original_env.items():
            if key in (use_adapter_env or {}):
                if use_adapter_env[key] is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = use_adapter_env[key]
            elif use_adapter_env is None:
                os.environ.pop("AAIS_ENABLE_TEXT_ADAPTERS", None)
                os.environ.pop("AAIS_TEXT_ADAPTER_PATH", None)
                os.environ.pop("AAIS_TEXT_ADAPTER_FAST_PATH", None)
                os.environ.pop("AAIS_TEXT_ADAPTER_THINK_PATH", None)

        conversation_memory.sessions.clear()
        patcher = None
        if mock_model:
            patcher = patch("src.api.init_ai", return_value=(MockEvalModel(), object()))
            patcher.start()

        results = []
        try:
            for prompt_def in prompts:
                for response_mode in ("fast", "think"):
                    results.append(_run_one(client, prompt_def, response_mode))
        finally:
            if patcher is not None:
                patcher.stop()
            conversation_memory.sessions.clear()
        return results
    finally:
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _build_comparisons(base_results, adapter_results):
    adapter_index = {
        (item["prompt_id"], item["response_mode"]): item for item in adapter_results
    }
    comparisons = []
    for base_item in base_results:
        key = (base_item["prompt_id"], base_item["response_mode"])
        adapter_item = adapter_index.get(key)
        if not adapter_item:
            continue
        comparisons.append(
            {
                "prompt_id": base_item["prompt_id"],
                "response_mode": base_item["response_mode"],
                "base_status_code": base_item["status_code"],
                "adapter_status_code": adapter_item["status_code"],
                "base_preview": base_item.get("response_preview"),
                "adapter_preview": adapter_item.get("response_preview"),
            }
        )
    return comparisons


def _evaluate_acceptance(base_aggs, adapter_aggs, profile_name: str):
    profile = ACCEPTANCE_PROFILES.get(profile_name, ACCEPTANCE_PROFILES["default"])
    failures: list[str] = []

    for mode in ("fast", "think"):
        base = base_aggs.get(mode) or {}
        adapter = adapter_aggs.get(mode) or {}
        if not base or not adapter:
            failures.append(f"{mode}:missing_mode_aggregates")
            continue

        if adapter.get("runs", 0) != base.get("runs", 0):
            failures.append(f"{mode}:run_count_mismatch")

        base_plan = float(base.get("plan_pass_rate") or 0)
        adapter_plan = float(adapter.get("plan_pass_rate") or 0)
        if adapter_plan < base_plan - float(profile["plan_pass_rate_floor_delta"]):
            failures.append(f"{mode}:plan_pass_rate_regression")

        base_workspace = float(base.get("avg_workspace_hits") or 0)
        adapter_workspace = float(adapter.get("avg_workspace_hits") or 0)
        if adapter_workspace < base_workspace:
            failures.append(f"{mode}:workspace_hits_regression")

        base_latency = float(base.get("avg_latency_ms") or 0)
        adapter_latency = float(adapter.get("avg_latency_ms") or 0)
        if base_latency > 0 and adapter_latency > base_latency * float(profile["latency_multiplier"]):
            failures.append(f"{mode}:latency_ceiling_exceeded")

    return {"passed": not failures, "failures": failures}


def _update_adapter_metadata(metadata_path: Path, report_path: Path, passed: bool):
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["eval_report_path"] = str(report_path)
    metadata["promotion_status"] = "eval_passed" if passed else "draft"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--adapter-metadata",
        required=True,
        help="Path to final/adapter_metadata.json for the candidate adapter.",
    )
    parser.add_argument(
        "--prompts",
        default="evals/mode_eval_prompts.json",
        help="JSON prompt set.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional output report path.",
    )
    parser.add_argument(
        "--acceptance-profile",
        default="default",
        help="Named acceptance profile (default only in v2).",
    )
    parser.add_argument(
        "--mock-model",
        action="store_true",
        help="Use deterministic mock model for smoke eval.",
    )
    args = parser.parse_args()

    metadata_path = (
        (ROOT / args.adapter_metadata).resolve()
        if not Path(args.adapter_metadata).is_absolute()
        else Path(args.adapter_metadata)
    )
    if not metadata_path.exists():
        raise FileNotFoundError(f"Adapter metadata not found: {metadata_path}")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    run_id = str(metadata.get("run_id") or "")
    adapter_dir = metadata_path.parent
    base_model = str(metadata.get("base_model") or "Qwen/Qwen2.5-1.5B-Instruct")

    prompts_path = (
        (ROOT / args.prompts).resolve()
        if not Path(args.prompts).is_absolute()
        else Path(args.prompts)
    )
    output_path = (
        _default_report_path(ROOT, run_id or "unknown")
        if not args.output
        else (ROOT / args.output).resolve() if not Path(args.output).is_absolute() else Path(args.output)
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    prompts = _load_prompts(prompts_path)
    client = api.app.test_client()

    base_results = _run_suite(client, prompts, use_adapter_env=None, mock_model=args.mock_model)
    adapter_env = {
        "AAIS_ENABLE_TEXT_ADAPTERS": "1",
        "AAIS_TEXT_ADAPTER_PATH": str(adapter_dir),
        "AAIS_TEXT_ADAPTER_FAST_PATH": str(adapter_dir),
        "AAIS_TEXT_ADAPTER_THINK_PATH": str(adapter_dir),
        "AAIS_TEXT_MODEL_NAME": base_model,
    }
    adapter_results = _run_suite(client, prompts, use_adapter_env=adapter_env, mock_model=args.mock_model)

    base_aggs = {"fast": _aggregate_mode(base_results, "fast"), "think": _aggregate_mode(base_results, "think")}
    adapter_aggs = {
        "fast": _aggregate_mode(adapter_results, "fast"),
        "think": _aggregate_mode(adapter_results, "think"),
    }
    comparisons = _build_comparisons(base_results, adapter_results)
    acceptance = _evaluate_acceptance(base_aggs, adapter_aggs, args.acceptance_profile)

    for comparison in comparisons:
        if comparison["base_status_code"] != 200 or comparison["adapter_status_code"] != 200:
            acceptance["passed"] = False
            acceptance["failures"].append(
                f"{comparison['prompt_id']}:{comparison['response_mode']}:non_200_status"
            )

    report = {
        "jarvis_lora_eval_report_version": "jarvis_lora_eval_report.v1",
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "adapter_metadata_path": str(metadata_path.relative_to(ROOT)).replace("\\", "/")
        if metadata_path.is_relative_to(ROOT)
        else str(metadata_path),
        "acceptance_profile": args.acceptance_profile,
        "mock_model": bool(args.mock_model),
        "base": base_aggs,
        "adapter": adapter_aggs,
        "deltas": {
            mode: {
                "avg_workspace_hits": round(
                    float((adapter_aggs.get(mode) or {}).get("avg_workspace_hits") or 0)
                    - float((base_aggs.get(mode) or {}).get("avg_workspace_hits") or 0),
                    2,
                ),
                "plan_pass_rate": round(
                    float((adapter_aggs.get(mode) or {}).get("plan_pass_rate") or 0)
                    - float((base_aggs.get(mode) or {}).get("plan_pass_rate") or 0),
                    2,
                ),
            }
            for mode in ("fast", "think")
            if base_aggs.get(mode) and adapter_aggs.get(mode)
        },
        "comparisons": comparisons,
        "acceptance": acceptance,
    }

    report_errors = validate_eval_report(report)
    if report_errors:
        raise ValueError(f"Invalid eval report: {'; '.join(report_errors)}")

    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    _update_adapter_metadata(metadata_path, output_path, acceptance["passed"])

    print(f"Saved adapter eval report to: {output_path}")
    print(f"Acceptance passed: {acceptance['passed']}")
    if acceptance["failures"]:
        for failure in acceptance["failures"]:
            print(f"  - {failure}")


if __name__ == "__main__":
    main()
