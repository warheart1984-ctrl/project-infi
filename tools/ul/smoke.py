#!/usr/bin/env python3
"""Run AAIS-UL smoke checks: sample payloads + substrate tests."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from tools.ul._common import FIXTURES_DIR, PROJECT_ROOT, ensure_project_root, print_json
from tools.ul.probe import probe_payload

SMOKE_SAMPLES: list[dict[str, Any]] = [
    {
        "id": "cognitive_bridge",
        "fixture": "cognitive_bridge.json",
        "expected_section": "protocol_trace",
    },
    {
        "id": "patch_plan",
        "fixture": "patch_plan.json",
        "expected_section": "proposal_state",
    },
    {
        "id": "forge_contractor",
        "fixture": "forge_contractor_ok.json",
        "expected_section": "tool_results",
    },
    {
        "id": "evolve_response",
        "fixture": "evolve_ok.json",
        "expected_section": "tool_results",
    },
    {
        "id": "cloud_forge_bundle",
        "fixture": "cloud_forge_bundle.json",
        "expected_section": "mission_context",
    },
    {
        "id": "immune_snapshot",
        "payload": {
            "system_mode": "normal",
            "event_count": 1,
            "incident_count": 0,
            "reason": "baseline",
        },
        "expected_section": "guardrail_state",
    },
    {
        "id": "governance_snapshot",
        "payload": {
            "roles": ["operator"],
            "active_break_glass": {"active": False},
            "request_count": 0,
            "event_count": 0,
        },
        "expected_section": "guardrail_state",
    },
    {
        "id": "v9_core_result",
        "fixture": "v9_core_result.json",
        "expected_section": "tool_results",
    },
    {
        "id": "v10_core_result",
        "fixture": "v10_core_result.json",
        "expected_section": "tool_results",
    },
    {
        "id": "mystic_reading",
        "fixture": "mystic_reading.json",
        "expected_section": "knowledge_context",
    },
    {
        "id": "patch_review",
        "fixture": "patch_review.json",
        "expected_section": "proposal_state",
    },
    {
        "id": "creative_runtime_snapshot",
        "fixture": "creative_runtime_snapshot.json",
        "expected_section": "runtime_context",
    },
    {
        "id": "spatial_reason_result",
        "payload": {
            "from": "gate",
            "to": "forge",
            "path": ["gate", "forge"],
            "distance": 1,
            "visible": True,
        },
        "expected_section": "tool_results",
    },
    {
        "id": "corrigibility_state",
        "payload": {
            "status": "steady",
            "total_corrections": 0,
            "recent": [],
            "pending": None,
        },
        "expected_section": "guardrail_state",
    },
    {
        "id": "operator_health_snapshot",
        "payload": {
            "module_id": "AAIS-OHS-01",
            "operator_state": "watch",
            "recommended_mode": "simplify",
            "cognitive_load_score": 0.42,
            "confidence": 0.55,
            "advisory_only": True,
        },
        "expected_section": "guardrail_state",
    },
    {
        "id": "run_ledger_record",
        "payload": {
            "id": "run_smoke",
            "session_id": "sess_smoke",
            "status": "open",
            "kind": "operator",
            "cisiv_stage": "implementation",
            "steps": [],
        },
        "expected_section": "protocol_trace",
    },
    {
        "id": "operator_readout",
        "payload": {
            "status": "empty",
            "trace_count": 0,
            "traces_path": ".runtime/ugr/traces.jsonl",
            "runtime_effect": "readout_only",
        },
        "expected_section": "protocol_trace",
    },
    {
        "id": "memory_smith_snapshot",
        "payload": {
            "review_count": 1,
            "durable_count": 0,
            "expired_count": 0,
            "project_summary": {"summary": "idle"},
        },
        "expected_section": "knowledge_context",
    },
    {
        "id": "knowledge_authority_snapshot",
        "payload": {
            "authority_order": [{"label": "memory"}],
            "preferences": {"preset": "docs_first"},
            "current_contract": "Canonical docs outrank supporting sources.",
            "summary": {"mode": "hybrid"},
            "memory": [],
            "documents": [],
        },
        "expected_section": "knowledge_context",
    },
    {
        "id": "invariant_validation",
        "payload": {
            "module_id": "aais.invariant_engine.bridge_guard",
            "status": "pass",
            "allows": True,
            "failed_invariants": [],
        },
        "expected_section": "guardrail_state",
    },
    {
        "id": "reasoning_exchange_result",
        "payload": {
            "protocol_id": "aais.reasoning_exchange",
            "protocol_version": "0.1",
            "status": "ACCEPT",
            "reason": None,
            "confidence_adjustment": 0.0,
        },
        "expected_section": "protocol_trace",
    },
    {
        "id": "governed_event_chain",
        "payload": {
            "module_id": "aais.governed_event_chain",
            "status": "proceed",
            "decision": "ALLOW",
            "runtime_context": "live_runtime",
            "advisory_only": True,
        },
        "expected_section": "guardrail_state",
    },
    {
        "id": "identity_module",
        "payload": {
            "source_module": "aais.governed_llm_module",
            "channel": "instruction",
            "label": "System identity",
            "content": "You are Jarvis, the governed AAIS runtime assistant.",
            "role": "system",
        },
        "expected_section": "identity",
    },
    {
        "id": "attachment",
        "payload": {
            "type": "attachment",
            "name": "blueprint.md",
            "mime_type": "text/markdown",
            "size": 4096,
        },
        "expected_section": "attachments",
    },
    {
        "id": "provider_preview",
        "payload": {
            "model": "gpt-4.1",
            "messages": [{"role": "user", "content": "Summarize the UL substrate."}],
            "mode": "fast",
            "stream": False,
        },
        "expected_section": "provider_payload",
    },
    {
        "id": "workspace_context",
        "payload": {
            "query": "aais_ul_substrate",
            "prompt_block": "Workspace context auto-attached",
            "results": [{"relative_path": "src/aais_ul_substrate.py"}],
            "summary": "Attached 1 workspace match.",
        },
        "expected_section": "workspace_context",
    },
]


def _load_sample(sample: dict[str, Any]) -> Any:
    if "payload" in sample:
        return sample["payload"]
    fixture_name = str(sample["fixture"])
    path = FIXTURES_DIR / fixture_name
    return json.loads(path.read_text(encoding="utf-8"))


def run_smoke(*, wrap: bool = True, run_pytest: bool = True) -> dict[str, Any]:
    ensure_project_root()
    from src.aais_ul.runtime import attach_ul_substrate

    results: list[dict[str, Any]] = []
    failures = 0

    for sample in SMOKE_SAMPLES:
        payload = _load_sample(sample)
        probe = probe_payload(payload, wrap=wrap)
        wrapped_ok = True
        wrapped_count = 0
        if wrap and isinstance(payload, dict):
            wrapped = attach_ul_substrate(payload)
            wrapped_count = int((wrapped.get("ul_trace") or {}).get("count") or 0)
            wrapped_ok = bool(wrapped.get("ul_substrate")) and wrapped_count > 0

        section_ok = probe.get("primary_section") == sample.get("expected_section")
        adapter_ok = bool(probe.get("primary_adapter"))
        ok = adapter_ok and section_ok and wrapped_ok
        if not ok:
            failures += 1

        results.append(
            {
                "id": sample["id"],
                "ok": ok,
                "expected_section": sample.get("expected_section"),
                "primary_adapter": probe.get("primary_adapter"),
                "primary_section": probe.get("primary_section"),
                "ul_trace_count": (probe.get("ul_trace") or {}).get("count"),
                "wrapped_ul_trace_count": wrapped_count,
            }
        )

    pytest_result = None
    if run_pytest:
        pytest_result = _run_pytest()

    report = {
        "sample_count": len(results),
        "failed_samples": failures,
        "samples": results,
        "pytest": pytest_result,
        "overall_ok": failures == 0 and (pytest_result or {}).get("ok", True),
    }
    return report


def _run_pytest() -> dict[str, Any]:
    command = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_aais_ul_substrate.py",
        "-q",
    ]
    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "ok": completed.returncode == 0,
        "exit_code": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def validate_lineage_graph(path: Path) -> dict[str, Any]:
    ensure_project_root()
    from src.ul_lineage import validate_graph

    graph = json.loads(path.read_text(encoding="utf-8"))
    report = validate_graph(graph)
    report["path"] = str(path)
    return report


def run_lineage_smoke(path: Path) -> dict[str, Any]:
    report = validate_lineage_graph(path)
    report["overall_ok"] = bool(report.get("passed"))
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run AAIS-UL smoke checks.")
    parser.add_argument(
        "--no-pytest",
        action="store_true",
        help="Skip pytest tests/test_aais_ul_substrate.py",
    )
    parser.add_argument(
        "--no-wrap",
        action="store_true",
        help="Skip attach_ul_substrate checks.",
    )
    parser.add_argument(
        "--lineage-graph",
        metavar="PATH",
        help="Validate a UL lineage graph fixture (skips standard smoke when set).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.lineage_graph:
        report = run_lineage_smoke(Path(args.lineage_graph))
        print_json(report)
        return 0 if report.get("overall_ok") else 1
    report = run_smoke(wrap=not args.no_wrap, run_pytest=not args.no_pytest)
    print_json(report)
    return 0 if report.get("overall_ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
