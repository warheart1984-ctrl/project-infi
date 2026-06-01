"""Pure deterministic invariant evaluators over normalized event streams."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from scorpion.events import TraceEvent


_CATALOG_PATH = Path(__file__).resolve().parent / "os_invariants.v1.json"


def load_invariant_catalog() -> dict[str, Any]:
    return json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))


def _drift(invariant_id: str, summary: str, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "invariant_id": invariant_id,
        "drift_detected": True,
        "drift_summary": summary,
        "evidence": evidence,
    }


def _eval_syscall(events: list[TraceEvent], spec: dict[str, Any]) -> list[dict[str, Any]]:
    drifts: list[dict[str, Any]] = []
    allowed = spec.get("allowed_sequence") or []
    by_actor: dict[str, list[str]] = {}
    for event in events:
        if event.domain != "syscall_sequence":
            continue
        op = str(event.payload.get("op") or "")
        by_actor.setdefault(event.actor, []).append(op)
    for actor, ops in by_actor.items():
        seen_open = False
        for index, op in enumerate(ops):
            if op == "open":
                seen_open = True
            elif op in {"read", "write"} and not seen_open:
                drifts.append(
                    _drift(
                        "syscall_sequence",
                        f"{op} before open for {actor}",
                        {"actor": actor, "index": index, "op": op},
                    )
                )
            elif op == "close":
                seen_open = False
        if allowed and ops:
            for index in range(1, len(ops)):
                if ops[index] == "read" and ops[index - 1] not in {"open", "read", "write"}:
                    drifts.append(
                        _drift(
                            "syscall_sequence",
                            f"syscall order violation for {actor}",
                            {"actor": actor, "ops": ops},
                        )
                    )
                    break
    return drifts


def _eval_scheduler(events: list[TraceEvent], spec: dict[str, Any]) -> list[dict[str, Any]]:
    drifts: list[dict[str, Any]] = []
    max_delta = int(spec.get("max_tick_delta_ns") or 5_000_000)
    ticks = [e for e in events if e.domain == "scheduler_rhythm"]
    for index in range(1, len(ticks)):
        delta = ticks[index].ts_ns - ticks[index - 1].ts_ns
        if delta > max_delta:
            drifts.append(
                _drift(
                    "scheduler_rhythm",
                    f"tick delta {delta}ns exceeds {max_delta}ns",
                    {"delta_ns": delta, "actor": ticks[index].actor},
                )
            )
    return drifts


def _eval_memory(events: list[TraceEvent], spec: dict[str, Any]) -> list[dict[str, Any]]:
    del spec
    drifts: list[dict[str, Any]] = []
    balance = 0
    for event in events:
        if event.domain != "memory_lifecycle":
            continue
        op = str(event.payload.get("op") or "")
        size = int(event.payload.get("bytes") or 0)
        if op == "alloc":
            balance += size
        elif op == "free":
            balance -= size
        if balance < 0:
            drifts.append(
                _drift(
                    "memory_lifecycle",
                    f"free exceeded alloc for {event.actor}",
                    {"actor": event.actor, "balance": balance},
                )
            )
            balance = 0
    if balance > 0:
        drifts.append(
            _drift(
                "memory_lifecycle",
                f"unpaired alloc leak precursor ({balance} bytes)",
                {"remaining_bytes": balance},
            )
        )
    return drifts


def _eval_fd(events: list[TraceEvent], spec: dict[str, Any]) -> list[dict[str, Any]]:
    del spec
    drifts: list[dict[str, Any]] = []
    open_fds: dict[str, set[int]] = {}
    for event in events:
        if event.domain != "fd_flow":
            continue
        op = str(event.payload.get("op") or "")
        fd = int(event.payload.get("fd") or 0)
        actor = event.actor
        if op == "open":
            open_fds.setdefault(actor, set()).add(fd)
        elif op == "close":
            open_fds.setdefault(actor, set()).discard(fd)
    for actor, fds in open_fds.items():
        if fds:
            drifts.append(
                _drift(
                    "fd_flow",
                    f"unclosed fds {sorted(fds)} for {actor}",
                    {"actor": actor, "open_fds": sorted(fds)},
                )
            )
    return drifts


def _eval_ipc(events: list[TraceEvent], spec: dict[str, Any]) -> list[dict[str, Any]]:
    drifts: list[dict[str, Any]] = []
    allowed = spec.get("allowed_sequence") or []
    by_actor: dict[str, list[str]] = {}
    for event in events:
        if event.domain != "ipc_choreography":
            continue
        by_actor.setdefault(event.actor, []).append(str(event.payload.get("op") or ""))
    for actor, ops in by_actor.items():
        if not allowed:
            continue
        rank = {name: index for index, name in enumerate(allowed)}
        last = -1
        for op in ops:
            if op not in rank:
                continue
            if rank[op] < last:
                drifts.append(
                    _drift(
                        "ipc_choreography",
                        f"ipc order violation for {actor}",
                        {"actor": actor, "ops": ops},
                    )
                )
                break
            last = rank[op]
        if ops and ops[-1] != "close":
            drifts.append(
                _drift(
                    "ipc_choreography",
                    f"ipc session not closed for {actor}",
                    {"actor": actor, "ops": ops},
                )
            )
    return drifts


def _eval_privilege(events: list[TraceEvent], spec: dict[str, Any]) -> list[dict[str, Any]]:
    drifts: list[dict[str, Any]] = []
    allowed = set(spec.get("allowed_uids") or [0, 1000])
    for event in events:
        if event.domain != "privilege_transition":
            continue
        uid = int(event.payload.get("uid") or -1)
        if uid not in allowed:
            drifts.append(
                _drift(
                    "privilege_transition",
                    f"uid {uid} not in allowed set for {event.actor}",
                    {"actor": event.actor, "uid": uid, "allowed": sorted(allowed)},
                )
            )
    return drifts


def _eval_entropy(events: list[TraceEvent], spec: dict[str, Any]) -> list[dict[str, Any]]:
    drifts: list[dict[str, Any]] = []
    floor = float(spec.get("min_entropy_bits") or 4.0)
    for event in events:
        if event.domain != "entropy_signature":
            continue
        bits = float(event.payload.get("entropy_bits") or 0)
        if bits < floor:
            drifts.append(
                _drift(
                    "entropy_signature",
                    f"entropy {bits} below floor {floor}",
                    {"actor": event.actor, "entropy_bits": bits},
                )
            )
    return drifts


def _eval_timing(events: list[TraceEvent], spec: dict[str, Any]) -> list[dict[str, Any]]:
    drifts: list[dict[str, Any]] = []
    max_lat = int(spec.get("max_latency_ns") or 10_000_000)
    pending: dict[str, int] = {}
    for event in events:
        if event.domain != "timing_delta":
            continue
        op = str(event.payload.get("op") or "")
        pair = str(event.payload.get("pair_id") or "default")
        key = f"{event.actor}:{pair}"
        if op == "start":
            pending[key] = event.ts_ns
        elif op == "end" and key in pending:
            latency = event.ts_ns - pending[key]
            if latency > max_lat:
                drifts.append(
                    _drift(
                        "timing_delta",
                        f"latency {latency}ns exceeds {max_lat}ns",
                        {"actor": event.actor, "pair_id": pair, "latency_ns": latency},
                    )
                )
            del pending[key]
    return drifts


_EVALUATORS = {
    "syscall_sequence": _eval_syscall,
    "scheduler_rhythm": _eval_scheduler,
    "memory_lifecycle": _eval_memory,
    "fd_flow": _eval_fd,
    "ipc_choreography": _eval_ipc,
    "privilege_transition": _eval_privilege,
    "entropy_signature": _eval_entropy,
    "timing_delta": _eval_timing,
}


def evaluate_all(events: list[TraceEvent]) -> list[dict[str, Any]]:
    catalog = load_invariant_catalog()
    drifts: list[dict[str, Any]] = []
    for item in catalog.get("invariants") or []:
        inv_id = str(item.get("id") or "")
        runner = _EVALUATORS.get(inv_id)
        if runner:
            drifts.extend(runner(events, item))
    return sorted(drifts, key=lambda d: (str(d.get("invariant_id")), str(d.get("drift_summary"))))
