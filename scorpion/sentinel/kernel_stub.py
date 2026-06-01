"""Kernel Sentinel stub (Stage 4 — native eBPF not in tree)."""

from __future__ import annotations

from pathlib import Path

from scorpion.sentinel.fixture import FixtureSentinel


class KernelSentinelStub:
    """Falls back to fixture ingest when path is NDJSON; else not_implemented."""

    adapter_id = "kernel-sentinel.stub.v1"

    def ingest(self, trace_path: str) -> list:
        target = Path(trace_path).expanduser().resolve()
        if target.suffix.lower() in {".ndjson", ".jsonl", ".json"}:
            return FixtureSentinel().ingest(trace_path)
        raise NotImplementedError(
            "KernelSentinel native capture is not implemented; provide normalized "
            "NDJSON export or see docs/subsystems/scorpion/KERNEL_SENTINEL_DESIGN.md"
        )

    def describe(self, trace_path: str) -> dict:
        target = Path(trace_path).expanduser().resolve()
        if target.exists() and target.suffix.lower() in {".ndjson", ".jsonl", ".json"}:
            return {
                "adapter_id": self.adapter_id,
                "status": "ndjson_bridge",
                "claim_label": "asserted",
                "note": "using fixture parser until eBPF adapter ships",
            }
        return {
            "adapter_id": self.adapter_id,
            "status": "not_implemented",
            "claim_label": "asserted",
        }
