from __future__ import annotations

from typing import Any

from nova.node.event_bus import EventBus


class RuntimeHooks:
    def __init__(self, bus: EventBus) -> None:
        self.bus = bus

    def on_patch_applied(self, patch_id: str, files: list[str], receipt: dict[str, Any]) -> None:
        self.bus.emit("governance.patch_applied", "applied", {"patch_id": patch_id, "files": files})
        self.on_receipt_verified(receipt)

    def on_patch_generated(self, trace_id: str, file_path: str, diff_hash: str) -> None:
        self.bus.emit(
            "governance.patch_generated",
            "generated",
            {"trace_id": trace_id, "file_path": file_path, "diff_hash": diff_hash},
        )

    def on_patch_rejected(self, patch_id: str, reason: str, receipt: dict[str, Any]) -> None:
        self.bus.emit("governance.patch_rejected", "rejected", {"patch_id": patch_id, "reason": reason})
        self.on_receipt_verified(receipt)

    def on_hunk_applied(self, patch_id: str, hunk_id: str, receipt: dict[str, Any]) -> None:
        self.bus.emit("governance.hunk_applied", "applied", {"patch_id": patch_id, "hunk_id": hunk_id})
        self.on_receipt_verified(receipt)

    def on_hunk_rejected(self, patch_id: str, hunk_id: str, receipt: dict[str, Any]) -> None:
        self.bus.emit("governance.hunk_rejected", "rejected", {"patch_id": patch_id, "hunk_id": hunk_id})
        self.on_receipt_verified(receipt)

    def on_patch_rollback(self, patch_id: str, to_revision: str, receipt: dict[str, Any]) -> None:
        self.bus.emit(
            "governance.patch_rollback",
            "rollback",
            {"patch_id": patch_id, "to_revision": to_revision},
        )
        self.on_receipt_verified(receipt)

    def on_test_run_started(self, suite: str) -> None:
        self.bus.emit("test.run_started", "started", {"suite": suite})

    def on_test_run_completed(self, suite: str, summary: dict[str, Any], receipt: dict[str, Any]) -> None:
        self.bus.emit("test.run_completed", "completed", {"suite": suite, "summary": summary})
        self.on_receipt_verified(receipt)

    def on_test_failure_detected(self, test_name: str, output: str, receipt: dict[str, Any]) -> None:
        self.bus.emit("test.failure", "detected", {"test_name": test_name, "output": output})
        self.on_receipt_verified(receipt)

    def on_commit_created(self, commit_hash: str, receipt: dict[str, Any]) -> None:
        self.bus.emit("git.commit", "created", {"commit_hash": commit_hash})
        self.on_receipt_verified(receipt)

    def on_branch_changed(self, branch: str) -> None:
        self.bus.emit("git.branch_changed", "changed", {"branch": branch})

    def on_tool_invoked(self, tool_name: str, args_hash: str, governed_state: str, trace_id: str) -> None:
        self.bus.emit(
            "tool.invoked",
            "started",
            {
                "tool_name": tool_name,
                "args_hash": args_hash,
                "governed_state": governed_state,
                "trace_id": trace_id,
            },
        )

    def on_tool_completed(self, tool_name: str, output_hash: str, duration_ms: int, trace_id: str) -> None:
        self.bus.emit(
            "tool.completed",
            "completed",
            {
                "tool_name": tool_name,
                "output_hash": output_hash,
                "duration_ms": duration_ms,
                "trace_id": trace_id,
            },
        )

    def on_receipt_verified(self, receipt: dict[str, Any]) -> None:
        self.bus.emit("governance.receipt_verified", "verified", _receipt_payload(receipt))

    def on_receipt_blocked(self, receipt: dict[str, Any]) -> None:
        self.bus.emit("governance.receipt_blocked", "blocked", _receipt_payload(receipt))

    def on_replay_started(self, trace_id: str) -> None:
        self.bus.emit("replay.started", "started", {"trace_id": trace_id})

    def on_replay_completed(self, trace_id: str, receipt: dict[str, Any]) -> None:
        self.bus.emit("replay.completed", "completed", {"trace_id": trace_id})
        self.on_receipt_verified(receipt)

    def on_replay_drift(self, trace_id: str, details: dict[str, Any]) -> None:
        self.bus.emit(
            "replay.drift_detected",
            "detected",
            {"trace_id": trace_id, "details": details, "severity": "high"},
        )

    def on_node_online(self) -> None:
        self.bus.emit("node.online", "online", {})

    def on_node_offline(self, reason: str) -> None:
        self.bus.emit("node.offline", "offline", {"reason": reason})

    def on_latency_spike(self, latency_ms: int) -> None:
        self.bus.emit("node.latency_spike", "spike", {"latency_ms": latency_ms, "severity": "medium"})


def _receipt_payload(receipt: dict[str, Any]) -> dict[str, Any]:
    return {
        "trace_id": receipt.get("trace_id"),
        "policy_version": receipt.get("policy_version"),
        "receipt_hash": receipt.get("receipt_hash"),
        "reason": receipt.get("reason"),
        "tool_name": receipt.get("tool_name") or receipt.get("tool"),
    }
