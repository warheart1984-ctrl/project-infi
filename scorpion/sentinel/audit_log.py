"""Audit-export Sentinel: normalized NDJSON or linux audit text lines."""

from __future__ import annotations

import json
import re
from pathlib import Path

from scorpion.events import TraceEvent, load_events_from_path

_AUDIT_SYSCALL = re.compile(
    r"type=SYSCALL\s+.*?\bsyscall=(\w+).*?(?:success=yes|success=no)",
    re.IGNORECASE,
)


class AuditExportSentinel:
    """Stage 4 userspace adapter — no eBPF; reads export files only."""

    adapter_id = "audit-export-sentinel.v1"

    def ingest(self, trace_path: str) -> list[TraceEvent]:
        target = Path(trace_path).expanduser().resolve()
        if not target.exists():
            raise FileNotFoundError(f"trace not found: {target}")
        first_line = ""
        for line in target.read_text(encoding="utf-8").splitlines():
            if line.strip():
                first_line = line.strip()
                break
        if first_line.startswith("{"):
            return load_events_from_path(str(target))
        return self._parse_audit_text(target)

    def _parse_audit_text(self, path: Path) -> list[TraceEvent]:
        events: list[TraceEvent] = []
        ts = 0
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            ts += 1_000_000
            match = _AUDIT_SYSCALL.search(stripped)
            if match:
                op = match.group(1).lower()
                mapped = op if op in {"open", "read", "write", "close"} else "open"
                events.append(
                    TraceEvent(
                        ts_ns=ts,
                        domain="syscall_sequence",
                        actor="audit:pid",
                        payload={"op": mapped, "raw": op},
                        lineage_id="audit-text",
                    )
                )
            elif "uid=" in stripped:
                uid_match = re.search(r"\buid=(\d+)", stripped)
                if uid_match:
                    events.append(
                        TraceEvent(
                            ts_ns=ts,
                            domain="privilege_transition",
                            actor="audit:pid",
                            payload={"uid": int(uid_match.group(1))},
                            lineage_id="audit-text",
                        )
                    )
        return sorted(events, key=lambda e: (e.ts_ns, e.domain))

    def describe(self, trace_path: str) -> dict:
        try:
            events = self.ingest(trace_path)
            return {
                "adapter_id": self.adapter_id,
                "trace_path": trace_path,
                "event_count": len(events),
                "format": "ndjson" if str(trace_path).endswith(".ndjson") else "auto",
                "claim_label": "proven",
            }
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            return {
                "adapter_id": self.adapter_id,
                "trace_path": trace_path,
                "claim_label": "rejected",
                "error": str(exc),
            }
