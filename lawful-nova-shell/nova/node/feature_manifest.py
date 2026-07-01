from __future__ import annotations

from typing import Any


FEATURE_MANIFEST: dict[str, Any] = {
    "node": {
        "id": "local-node-01",
        "version": "1.0.0",
        "description": "Sovereign Node feature manifest for Nova Desktop",
        "startup": {
            "auto_load": True,
            "health_check": True,
            "governance_mode": "strict",
        },
    },
    "modules": {
        "core": [
            "file_search",
            "symbol_search",
            "patch_manager",
            "terminal",
            "test_runner",
            "git_panel",
        ],
        "nova_specific": [
            "governance_receipt_inspector",
            "replay_timeline",
            "tool_registry",
            "node_health_strip",
            "local_model_selector",
            "explain_tool",
        ],
        "power_user": [
            "command_palette",
            "context_builder",
            "explain_mode",
            "project_templates",
            "safety_rails",
        ],
    },
    "ui_panels": [
        {
            "name": "DiffViewer",
            "component": "diff_panel",
            "features": ["apply_patch", "reject_hunk", "rollback_patch"],
        },
        {
            "name": "Terminal",
            "component": "terminal_panel",
            "features": ["run_tests", "run_app", "run_lint", "link_output"],
        },
        {
            "name": "TestRunner",
            "component": "test_panel",
            "features": ["run_file_tests", "run_failed_tests", "fix_failure"],
        },
        {
            "name": "GitPanel",
            "component": "git_panel",
            "features": ["changed_files", "staged_diff", "commit_generator", "pr_summary"],
        },
        {
            "name": "GovernanceInspector",
            "component": "governance_panel",
            "features": ["policy_version", "trace_id", "input_output_hashes"],
        },
        {
            "name": "ReplayTimeline",
            "component": "replay_panel",
            "features": ["deterministic_replay", "drift_warning", "rollback"],
        },
        {
            "name": "NodeHealth",
            "component": "health_strip",
            "metrics": ["model", "online_status", "receipts_count", "latency", "governance_state"],
        },
        {
            "name": "ModelSelector",
            "component": "model_dropdown",
            "models": [
                "qwen2.5-coder:3b",
                "qwen2.5-coder:7b",
                "deepseek-coder:6.7b",
                "coding-substrate-1:latest",
                "gemma4:latest",
            ],
        },
    ],
    "governance": {
        "receipts": {
            "verify_function": "verify_receipt",
            "ledger_path": "./ledger/receipts.db",
            "replay_path": "./ledger/replay.db",
        },
        "policies": {
            "enforcement": "strict",
            "versioning": "semantic",
            "audit_log": True,
        },
    },
    "templates": [
        "python_fastapi",
        "node_express",
        "rust_actix",
        "governed_nova_tool",
        "local_ai_app",
    ],
    "safety": {
        "auto_write": False,
        "warn_large_patches": True,
        "warn_secrets": True,
        "confirm_dependency_changes": True,
    },
    "runtime": {
        "hooks": {
            "on_patch_applied": {
                "emit": "governance.patch_applied",
                "record_receipt": True,
                "replayable": True,
            },
            "on_patch_generated": {
                "emit": "governance.patch_generated",
                "record_receipt": True,
            },
            "on_patch_rejected": {
                "emit": "governance.patch_rejected",
                "record_receipt": True,
            },
            "on_hunk_applied": {
                "emit": "governance.hunk_applied",
                "record_receipt": True,
            },
            "on_hunk_rejected": {
                "emit": "governance.hunk_rejected",
                "record_receipt": True,
            },
            "on_patch_rollback": {
                "emit": "governance.patch_rollback",
                "record_receipt": True,
                "replayable": True,
            },
            "on_test_run_started": {
                "emit": "test.run_started",
                "attach_context": True,
            },
            "on_test_run_completed": {
                "emit": "test.run_completed",
                "record_receipt": True,
                "attach_output": True,
            },
            "on_test_failure_detected": {
                "emit": "test.failure",
                "record_receipt": True,
                "auto_context": "failing_test_output",
            },
            "on_commit_created": {
                "emit": "git.commit",
                "record_receipt": True,
            },
            "on_branch_changed": {
                "emit": "git.branch_changed",
            },
            "on_tool_invoked": {
                "emit": "tool.invoked",
                "record_receipt": True,
                "include": ["tool_name", "args_hash", "governed_state"],
            },
            "on_tool_completed": {
                "emit": "tool.completed",
                "record_receipt": True,
                "include": ["output_hash", "duration_ms"],
            },
            "on_receipt_verified": {
                "emit": "governance.receipt_verified",
                "update_health": True,
            },
            "on_receipt_blocked": {
                "emit": "governance.receipt_blocked",
                "update_health": True,
                "attach_policy": True,
            },
            "on_replay_started": {
                "emit": "replay.started",
                "attach_trace": True,
            },
            "on_replay_completed": {
                "emit": "replay.completed",
                "record_receipt": True,
            },
            "on_replay_drift": {
                "emit": "replay.drift_detected",
                "severity": "high",
                "auto_flag": True,
                "suggest_rollback": True,
            },
            "on_node_online": {
                "emit": "node.online",
                "update_health": True,
            },
            "on_node_offline": {
                "emit": "node.offline",
                "update_health": True,
            },
            "on_latency_spike": {
                "emit": "node.latency_spike",
                "severity": "medium",
            },
        },
    },
    "event_bus": {
        "channels": ["governance.*", "test.*", "git.*", "tool.*", "replay.*", "node.*", "substrate.*"],
        "transport": "internal",
        "persistence": True,
        "max_events": 5000,
        "canonical_stream": {
            "format": "jsonl",
            "schemaVersion": "substrate-event-v1",
            "path": ".runtime/node/substrate-events.jsonl",
            "adapters": ["http-json", "sse-ready", "in-process"],
        },
    },
}


def feature_manifest() -> dict[str, Any]:
    return FEATURE_MANIFEST
