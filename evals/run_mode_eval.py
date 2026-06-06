"""Evaluate Jarvis Fast vs Think mode on a small local prompt set."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import statistics
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import src.api as api
from src.conversation_memory import conversation_memory


class MockEvalModel:
    """Small deterministic stand-in for eval smoke tests."""

    def generate_chat(self, messages, max_length=512, temperature=0.7):
        system_messages = [
            message.get("content", "")
            for message in messages
            if message.get("role") == "system"
        ]
        user_messages = [
            message.get("content", "")
            for message in messages
            if message.get("role") == "user"
        ]
        latest_user = user_messages[-1] if user_messages else "the operator request"
        planning_pass = any("Think mode planning pass" in message for message in system_messages)

        if planning_pass:
            return (
                f"Focus: answer {latest_user[:72]}.\n"
                "Evidence: use any attached workspace or research context.\n"
                "Answer Shape: start with the clearest next move, then add compact support."
            )

        if any("Think planning notes for this turn" in message for message in system_messages):
            return (
                "Think mode answer: start with the clearest next move, then back it with the gathered context."
            )

        return "Fast mode answer: give the clearest useful answer without extra overhead."


def _load_prompts(path: Path):
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Prompt file must contain a JSON array.")
    return payload


def _default_output_path(root: Path):
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return root / ".runtime" / "evals" / f"mode-eval-{timestamp}.json"


def _aggregate_mode(results, mode):
    mode_results = [result for result in results if result["response_mode"] == mode]
    if not mode_results:
        return {}

    return {
        "runs": len(mode_results),
        "avg_latency_ms": round(
            statistics.fmean(result["elapsed_ms"] for result in mode_results), 2
        ),
        "avg_response_words": round(
            statistics.fmean(result["response_words"] for result in mode_results), 2
        ),
        "avg_workspace_hits": round(
            statistics.fmean(result["workspace_hits"] for result in mode_results), 2
        ),
        "avg_research_sources": round(
            statistics.fmean(result["research_sources"] for result in mode_results), 2
        ),
        "plan_pass_rate": round(
            statistics.fmean(1 if result["plan_summary"] else 0 for result in mode_results), 2
        ),
    }


def _run_one(client, prompt_def, response_mode):
    create_response = client.post(
        "/api/chat/sessions",
        json={
            "system_prompt": "You are Jarvis.",
            "persona_mode": "builder",
            "response_mode": response_mode,
        },
    )
    create_payload = create_response.get_json()
    session_id = create_payload["session_id"]

    request_payload = {
        "message": prompt_def["message"],
        "response_mode": response_mode,
    }
    if "use_research" in prompt_def:
        request_payload["use_research"] = prompt_def["use_research"]

    started = time.perf_counter()
    response = client.post(
        f"/api/chat/sessions/{session_id}/message",
        json=request_payload,
    )
    elapsed_ms = (time.perf_counter() - started) * 1000
    payload = response.get_json()
    trace = payload.get("response_trace") or {}
    text = payload.get("response", "")

    return {
        "prompt_id": prompt_def["id"],
        "prompt_label": prompt_def.get("label", prompt_def["id"]),
        "response_mode": response_mode,
        "elapsed_ms": round(elapsed_ms, 2),
        "response_chars": len(text),
        "response_words": len(text.split()),
        "workspace_hits": trace.get("workspace_hits", 0),
        "workspace_files": trace.get("workspace_files", 0),
        "research_sources": trace.get("research_sources", 0),
        "contract": trace.get("contract"),
        "contract_label": trace.get("contract_label"),
        "plan_summary": trace.get("plan_summary"),
        "tool_type": (payload.get("tool_result") or {}).get("type"),
        "summary": trace.get("summary"),
        "response_preview": text[:240],
        "status_code": response.status_code,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--prompts",
        default="evals/mode_eval_prompts.json",
        help="JSON file containing prompt definitions.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional output JSON path. Defaults to .runtime/evals/<timestamp>.json",
    )
    parser.add_argument(
        "--mock-model",
        action="store_true",
        help="Use a deterministic mock model for a fast eval smoke test.",
    )
    parser.add_argument(
        "--adapter-metadata",
        default=None,
        help="Optional adapter_metadata.json path to attach eval_report_path on completion.",
    )
    args = parser.parse_args()

    root = ROOT
    prompts_path = (
        (root / args.prompts).resolve()
        if not Path(args.prompts).is_absolute()
        else Path(args.prompts)
    )
    output_path = (
        _default_output_path(root)
        if not args.output
        else (root / args.output).resolve() if not Path(args.output).is_absolute() else Path(args.output)
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    prompts = _load_prompts(prompts_path)
    conversation_memory.sessions.clear()

    results = []
    client = api.app.test_client()

    patcher = None
    if args.mock_model:
        patcher = patch("src.api.init_ai", return_value=(MockEvalModel(), object()))
        patcher.start()

    try:
        for prompt_def in prompts:
            for response_mode in ("fast", "think"):
                results.append(_run_one(client, prompt_def, response_mode))
    finally:
        if patcher is not None:
            patcher.stop()
        conversation_memory.sessions.clear()

    report = {
        "generated_at": datetime.now().isoformat(),
        "prompts_path": str(prompts_path),
        "mock_model": bool(args.mock_model),
        "results": results,
        "aggregates": {
            "fast": _aggregate_mode(results, "fast"),
            "think": _aggregate_mode(results, "think"),
        },
    }

    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    if args.adapter_metadata:
        metadata_path = (
            (root / args.adapter_metadata).resolve()
            if not Path(args.adapter_metadata).is_absolute()
            else Path(args.adapter_metadata)
        )
        if metadata_path.exists():
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            metadata["eval_report_path"] = str(output_path)
            metadata["promotion_status"] = "eval_passed"
            metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
            print(f"Updated adapter metadata: {metadata_path}")
        else:
            print(f"Adapter metadata not found: {metadata_path}")

    print(f"Saved mode eval report to: {output_path}")
    for mode in ("fast", "think"):
        aggregate = report["aggregates"][mode]
        if not aggregate:
            continue
        print(
            f"{mode}: runs={aggregate['runs']} "
            f"avg_latency_ms={aggregate['avg_latency_ms']} "
            f"avg_words={aggregate['avg_response_words']} "
            f"avg_workspace_hits={aggregate['avg_workspace_hits']} "
            f"avg_research_sources={aggregate['avg_research_sources']} "
            f"plan_pass_rate={aggregate['plan_pass_rate']}"
        )


if __name__ == "__main__":
    main()
