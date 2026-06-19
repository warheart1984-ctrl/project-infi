#!/usr/bin/env python
"""CC-01 Controlled Collapse Test Set (CIEMS Harness).

Simulates multi-thread agent workspace contention against a shared
``agent/project/main.py`` and symbolic ``FunctionX`` object. Forces
observable failure modes (F-01..F-05), logs every event in the required
JSON schema, and emits a pass/fail verdict for Jon.

Engineering module: ``cc01_controlled_collapse_harness``
Mythic label (docs only): CIEMS Controlled Collapse

Nova matrix runs (60s / 120s / 180s): restart the mock sandbox between legs if
the server slows after 2–3 minutes; ``NovaBackend`` uses longer HTTP timeouts for
degraded mock endpoints.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import queue
import random
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from tools.stress._chaos_common import check_health
from tools.stress.cc01_backend import Cc01WorkloadResult, build_backend

ROOT = Path(__file__).resolve().parents[2]
NOVA_MAX_THREADS = 8
NOVA_MAX_DURATION_SEC = 180.0

FAILURE_MEANINGS: dict[str, str] = {
    "F-01": "Race condition / overwrite",
    "F-02": "Context bleed",
    "F-03": "Queue or HTTP starvation under saturation",
    "F-04": "Cascade failure",
    "F-05": "Non-deterministic output",
}

FILE_TARGET = "agent/project/main.py"
SYMBOLIC_OBJECT = "FunctionX"

INITIAL_MAIN_PY = '''"""Shared agent project file under CC-01 contention."""

def FunctionX(x: int) -> int:
    """Symbolic object under contention."""
    return x * 2
'''

WORKLOAD_MIX: dict[str, float] = {
    "codegen": 0.40,
    "edit": 0.30,
    "debug": 0.20,
    "summarize": 0.10,
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_obj(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return _sha256_text(payload)


@dataclass
class CiemsEvent:
    timestamp: str
    thread_id: str
    event_type: str
    input: str
    context_hash_before: str
    context_hash_after: str
    output_hash: str
    state_change: str
    file_target: str
    conflict_flag: bool
    failure_code: str
    latency_ms: int

    nova_request_id: str = ""
    nova_session_id: str = ""
    backend: str = "simulated"

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "thread_id": self.thread_id,
            "event_type": self.event_type,
            "input": self.input,
            "context_hash_before": self.context_hash_before,
            "context_hash_after": self.context_hash_after,
            "output_hash": self.output_hash,
            "state_change": self.state_change,
            "file_target": self.file_target,
            "conflict_flag": self.conflict_flag,
            "failure_code": self.failure_code,
            "latency_ms": self.latency_ms,
            "backend": self.backend,
            "nova_request_id": self.nova_request_id,
            "nova_session_id": self.nova_session_id,
        }


@dataclass
class Cc01Verdict:
    pass_gate: bool
    would_pass: bool
    failure_counts: dict[str, int] = field(default_factory=dict)
    violations: list[str] = field(default_factory=list)
    trace_samples: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    total_events: int = 0
    duration_sec: float = 0.0
    backend: str = "simulated"


class SharedAgentWorkspace:
    """Intentionally weakly synchronized shared workspace (diagnostic)."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.project_dir = root / "agent" / "project"
        self.main_path = self.project_dir / "main.py"
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.main_path.write_text(INITIAL_MAIN_PY, encoding="utf-8")
        self._file_lock = threading.Lock()  # logging only; writes are racy by design
        self._context_lock = threading.Lock()
        self.contexts: dict[str, dict[str, Any]] = {}
        self.last_writer: str | None = None
        self.last_logged_file_hash: str = _sha256_text(INITIAL_MAIN_PY)
        self.unlogged_overwrites: list[dict[str, str]] = []
        self.context_bleeds: list[dict[str, str]] = []
        self.cascade_markers: list[str] = []

    def context_hash(self, thread_id: str) -> str:
        with self._context_lock:
            ctx = self.contexts.setdefault(thread_id, {"thread_id": thread_id, "notes": []})
            return _sha256_obj(ctx)

    def update_context(self, thread_id: str, note: str) -> str:
        with self._context_lock:
            ctx = self.contexts.setdefault(thread_id, {"thread_id": thread_id, "notes": []})
            ctx["notes"].append(note)
            return _sha256_obj(ctx)

    def read_file_text(self) -> str:
        return self.main_path.read_text(encoding="utf-8")

    def file_hash(self) -> str:
        return _sha256_text(self.read_file_text())

    def write_file_racy(self, thread_id: str, new_content: str) -> tuple[bool, str]:
        """Write without exclusive lock to surface F-01 races."""
        before = self.read_file_text()
        before_hash = _sha256_text(before)
        time.sleep(random.uniform(0.001, 0.008))  # widen race window
        self.main_path.write_text(new_content, encoding="utf-8")
        after_hash = _sha256_text(new_content)
        self.last_writer = thread_id
        if before_hash != self.last_logged_file_hash and self.last_writer != thread_id:
            self.unlogged_overwrites.append(
                {
                    "thread_id": thread_id,
                    "before_hash": before_hash,
                    "expected_logged_hash": self.last_logged_file_hash,
                }
            )
        return before_hash != after_hash, after_hash

    def record_logged_write(self, file_hash: str) -> None:
        with self._file_lock:
            self.last_logged_file_hash = file_hash

    def inject_context_bleed(self, reader: str, donor: str) -> bool:
        with self._context_lock:
            donor_ctx = self.contexts.get(donor)
            if not donor_ctx:
                return False
            reader_ctx = self.contexts.setdefault(reader, {"thread_id": reader, "notes": []})
            leaked = f"BLEED_FROM_{donor}:{donor_ctx.get('notes', [])[-3:]}"
            reader_ctx["foreign_context"] = leaked
            self.context_bleeds.append({"reader": reader, "donor": donor, "payload": leaked})
            return True

    def mark_cascade(self, reason: str) -> None:
        self.cascade_markers.append(reason)

    def ensure_thread(self, thread_id: str) -> None:
        self.context_hash(thread_id)

    def get_context(self, thread_id: str) -> str:
        return self.context_hash(thread_id)

    def snapshot_context(self, thread_id: str) -> None:
        self.update_context(thread_id, "snapshot")

    def hashes(self) -> tuple[str, str]:
        content = self.read_file_text()
        return self.file_hash(), _sha256_text(content[:512])

    def write(self, thread_id: str, content: str, *, op: str) -> None:
        _, fhash = self.write_file_racy(thread_id, content)
        self.record_logged_write(fhash)

    def summarize_from(self, thread_id: str, target_thread: str) -> str:
        if target_thread != thread_id:
            self.inject_context_bleed(thread_id, target_thread)
            with self._context_lock:
                ctx = self.contexts.get(thread_id, {})
                foreign = ctx.get("foreign_context", "missing")
            return f"summary:{thread_id}:{foreign}"
        return f"deterministic_summary:{thread_id}"

    def seed_functionx(self) -> None:
        return


class Cc01ControlledCollapseHarness:
    """CC-01 harness orchestrator."""

    def __init__(
        self,
        *,
        workspace_root: Path,
        num_threads: int = 12,
        duration_sec: float = 120.0,
        queue_capacity: int = 8,
        seed: int | None = None,
        backend_mode: str = "simulated",
        nova_base_url: str | None = None,
        nova_queue_name: str = "cc01-chaos",
        max_qps: float = 8.0,
        repo_root: Path | None = None,
    ) -> None:
        self.workspace_root = workspace_root
        self.num_threads = num_threads
        self.duration_sec = duration_sec
        self.queue_capacity = queue_capacity
        self.rng = random.Random(seed)
        self.backend_mode = backend_mode
        self.workspace = SharedAgentWorkspace(workspace_root)
        self.backend, self._backend_label = build_backend(
            mode=backend_mode,
            workspace=self.workspace,
            repo_root=repo_root or ROOT,
            base_url=nova_base_url,
            queue_name=nova_queue_name,
            max_qps=max_qps,
        )
        self.backend.seed_target()
        self.events: list[CiemsEvent] = []
        self.events_lock = threading.Lock()
        self.stop_at = 0.0
        self.request_queue: queue.Queue[tuple[str, str, str] | None] = queue.Queue(
            maxsize=queue_capacity
        )
        self.paused_threads: set[str] = set()
        self.pause_lock = threading.Lock()
        self.determinism_violations: list[dict[str, str]] = []
        self.starvation_events: list[dict[str, Any]] = []
        self.global_stall = False
        # Last known per-thread context; starvation path must not call get_context().
        self._ctx_cache: dict[str, str] = {}

    def _remember_ctx(self, thread_id: str, ctx: str) -> None:
        self._ctx_cache[thread_id] = ctx

    def _safe_get_context(self, thread_id: str) -> str:
        """Resolve context without killing the injector on backend/transport errors."""
        cached = self._ctx_cache.get(thread_id, "")
        try:
            ctx = self.backend.get_context(thread_id)
        except Exception:
            return cached
        if ctx:
            self._remember_ctx(thread_id, ctx)
            return ctx
        return cached

    def _emit(
        self,
        *,
        thread_id: str,
        event_type: str,
        input_text: str,
        ctx_before: str,
        ctx_after: str,
        output_hash: str,
        state_change: str,
        conflict: bool,
        failure_code: str,
        latency_ms: int,
        backend: str | None = None,
        nova_request_id: str = "",
        nova_session_id: str = "",
    ) -> None:
        event = CiemsEvent(
            timestamp=_utc_now(),
            thread_id=thread_id,
            event_type=event_type,
            input=input_text,
            context_hash_before=ctx_before,
            context_hash_after=ctx_after,
            output_hash=output_hash,
            state_change=state_change,
            file_target=FILE_TARGET,
            conflict_flag=conflict,
            failure_code=failure_code,
            latency_ms=latency_ms,
            backend=backend or self._backend_label,
            nova_request_id=nova_request_id,
            nova_session_id=nova_session_id,
        )
        self._remember_ctx(thread_id, ctx_after)
        with self.events_lock:
            self.events.append(event)

    def _emit_from_result(
        self,
        thread_id: str,
        event_type: str,
        input_text: str,
        result: Cc01WorkloadResult,
    ) -> None:
        self._emit(
            thread_id=thread_id,
            event_type=event_type,
            input_text=input_text,
            ctx_before=result.ctx_before,
            ctx_after=result.ctx_after,
            output_hash=result.output_hash,
            state_change=result.state_change,
            conflict=result.conflict,
            failure_code=result.failure_code,
            latency_ms=result.latency_ms,
            backend=result.backend,
            nova_request_id=result.nova_request_id,
            nova_session_id=result.nova_session_id,
        )

    def _pick_workload(self) -> str:
        roll = self.rng.random()
        cumulative = 0.0
        for name, weight in WORKLOAD_MIX.items():
            cumulative += weight
            if roll <= cumulative:
                return name
        return "summarize"

    def _handle_workload(self, thread_id: str, workload: str, payload: str) -> None:
        if self._is_paused(thread_id):
            time.sleep(0.05)
            return

        if workload == "codegen":
            result = self.backend.run_codegen(thread_id, {"goal": payload or "extend"})
        elif workload == "edit":
            variant = payload or "burst"
            result = self.backend.apply_edit(
                thread_id,
                {"variant": variant, "content": variant},
            )
        elif workload == "debug":
            result = self.backend.record_debug(thread_id, payload or workload)
        elif workload == "summarize":
            donor = payload if payload.startswith("thread-") else thread_id
            result = self.backend.summarize_context(thread_id, donor)
        else:
            return

        self._emit_from_result(thread_id, f"workload_{workload}", payload or workload, result)

    def _is_paused(self, thread_id: str) -> bool:
        with self.pause_lock:
            return thread_id in self.paused_threads

    def _worker(self, thread_id: str) -> None:
        try:
            self.backend.ensure_thread(thread_id)
        except Exception as exc:
            self.backend.mark_cascade(str(exc))
            self._emit(
                thread_id=thread_id,
                event_type="worker_session_failed",
                input_text=str(exc),
                ctx_before="",
                ctx_after="",
                output_hash="",
                state_change="ensure_thread_failed",
                conflict=True,
                failure_code="F-04",
                latency_ms=0,
            )
            return

        while time.monotonic() < self.stop_at:
            try:
                item = self.request_queue.get(timeout=0.25)
            except queue.Empty:
                continue
            if item is None:
                break
            _, workload, payload = item
            try:
                self._handle_workload(thread_id, workload, payload)
            except Exception as exc:
                self.backend.mark_cascade(str(exc))
                ctx = self._ctx_cache.get(thread_id, "")
                self._emit(
                    thread_id=thread_id,
                    event_type="worker_exception",
                    input_text=str(exc),
                    ctx_before=ctx,
                    ctx_after=ctx,
                    output_hash="",
                    state_change="cascade_failure",
                    conflict=True,
                    failure_code="F-04",
                    latency_ms=0,
                )
            finally:
                self.request_queue.task_done()

    def _enqueue(self, thread_id: str, workload: str, payload: str = "") -> bool:
        enqueued_at = time.monotonic()
        try:
            self.request_queue.put((thread_id, workload, payload), timeout=2.0)
            return True
        except queue.Full:
            waited_ms = int((time.monotonic() - enqueued_at) * 1000)
            self.starvation_events.append(
                {"thread_id": thread_id, "workload": workload, "waited_ms": waited_ms}
            )
            # Do not call get_context()/ensure_thread() — extra Nova HTTP under saturation
            # triggered F-04 cascades (session create timeouts).
            ctx = self._ctx_cache.get(thread_id, "")
            self._emit(
                thread_id=thread_id,
                event_type="queue_starvation",
                input_text=workload,
                ctx_before=ctx,
                ctx_after=ctx,
                output_hash="",
                state_change="queue_full",
                conflict=True,
                failure_code="F-03",
                latency_ms=waited_ms,
            )
            return False

    def _dispatch_injection(self, choice: str) -> None:
        if choice == "A":
            self._inject_mid_write_interrupt()
        elif choice == "B":
            self._inject_conflicting_edit_burst()
        elif choice == "C":
            self._inject_context_swap_trick()
        elif choice == "D":
            self._inject_load_spike()

    def _injector_loop(self) -> None:
        """Run mandatory A–D injections on a schedule, then random extras."""
        start = time.monotonic()
        # Guaranteed injections at spec fractions so short CI runs still log all four.
        fractions = (0.12, 0.32, 0.52, 0.72)
        scheduled: list[tuple[float, str]] = [
            (start + self.duration_sec * frac, label) for frac, label in zip(fractions, ("A", "B", "C", "D"))
        ]
        next_idx = 0
        extras = ["A", "B", "C", "D"]

        while time.monotonic() < self.stop_at:
            now = time.monotonic()
            if next_idx < len(scheduled) and now >= scheduled[next_idx][0]:
                label = scheduled[next_idx][1]
                try:
                    self._dispatch_injection(label)
                except Exception as exc:
                    if hasattr(self.backend, "mark_cascade"):
                        self.backend.mark_cascade(f"injection_{label}:{exc}")
                next_idx += 1
                continue

            if next_idx >= len(scheduled):
                time.sleep(self.rng.uniform(3.0, 8.0))
                if time.monotonic() >= self.stop_at:
                    break
                self._dispatch_injection(self.rng.choice(extras))
                continue

            wait = min(0.25, max(0.05, scheduled[next_idx][0] - now))
            time.sleep(wait)

    def _inject_mid_write_interrupt(self) -> None:
        victim = f"thread-{self.rng.randint(0, self.num_threads - 1)}"
        with self.pause_lock:
            self.paused_threads.add(victim)
        self._emit(
            thread_id="injector",
            event_type="injection_A_mid_write_interrupt",
            input_text=victim,
            ctx_before="",
            ctx_after="",
            output_hash="",
            state_change=f"pause:{victim}",
            conflict=False,
            failure_code="",
            latency_ms=0,
        )
        time.sleep(self.rng.uniform(0.2, 0.6))
        with self.pause_lock:
            self.paused_threads.discard(victim)
        self._emit(
            thread_id="injector",
            event_type="injection_A_resume",
            input_text=victim,
            ctx_before="",
            ctx_after="",
            output_hash="",
            state_change=f"resume:{victim}",
            conflict=False,
            failure_code="",
            latency_ms=0,
        )

    def _inject_conflicting_edit_burst(self) -> None:
        targets = [f"thread-{self.rng.randint(0, self.num_threads - 1)}" for _ in range(3)]
        if self.backend_mode == "nova":
            threads: list[threading.Thread] = []

            def _burst_edit(tid: str, variant: str) -> None:
                try:
                    self.backend.ensure_thread(tid)
                    result = self.backend.apply_edit(
                        tid,
                        {"variant": variant, "content": variant},
                    )
                    self._emit_from_result(
                        tid,
                        "injection_B_edit_burst",
                        variant,
                        result,
                    )
                except Exception as exc:
                    self.backend.mark_cascade(str(exc))

            for i, tid in enumerate(targets):
                thread = threading.Thread(
                    target=_burst_edit,
                    args=(tid, f"burst-{i}"),
                    daemon=True,
                )
                threads.append(thread)
                thread.start()
            for thread in threads:
                thread.join(timeout=30.0)
            file_hash = ""
            try:
                file_hash = self.backend.read_functionx_hashes()[0]
            except Exception:
                pass
        else:
            for tid in targets:
                self._enqueue(tid, "edit", "conflict_burst")
            file_hash = self.workspace.file_hash()
        self._emit(
            thread_id="injector",
            event_type="injection_B_conflicting_edit_burst",
            input_text=",".join(targets),
            ctx_before="",
            ctx_after="",
            output_hash=file_hash,
            state_change="triple_functionx_edit",
            conflict=True,
            failure_code="F-01",
            latency_ms=0,
        )

    def _inject_context_swap_trick(self) -> None:
        reader = f"thread-{self.rng.randint(0, self.num_threads - 1)}"
        donor = f"thread-{self.rng.randint(0, self.num_threads - 1)}"
        while donor == reader:
            donor = f"thread-{self.rng.randint(0, self.num_threads - 1)}"
        ctx_before = self._safe_get_context(reader)
        if self.backend_mode == "nova":
            try:
                self.backend.ensure_thread(reader)
                self.backend.ensure_thread(donor)
                self.backend.record_debug(donor, "seed_for_context_swap")
                result = self.backend.summarize_context(reader, donor)
                self._emit_from_result(
                    reader,
                    "injection_C_context_swap_workload",
                    f"{reader}->{donor}",
                    result,
                )
            except Exception as exc:
                self.backend.mark_cascade(str(exc))
        else:
            # Seed donor context so F-02 bleed is observable, not "missing donor".
            self._enqueue(donor, "debug", "seed_for_context_swap")
            time.sleep(0.05)
            self._enqueue(reader, "summarize", donor)
        self._emit(
            thread_id="injector",
            event_type="injection_C_context_swap",
            input_text=f"{reader}->{donor}",
            ctx_before=ctx_before,
            ctx_after=self._safe_get_context(reader),
            output_hash="",
            state_change="cross_thread_summary_request",
            conflict=True,
            failure_code="F-02",
            latency_ms=0,
        )

    def _inject_load_spike(self) -> None:
        burst: list[str] = []
        for i in range(20):
            tid = f"thread-{self.rng.randint(0, self.num_threads - 1)}"
            workload = self._pick_workload()
            ok = self._enqueue(tid, workload, f"spike-{i}")
            burst.append(f"{tid}:{workload}:{'ok' if ok else 'starved'}")
        self._emit(
            thread_id="injector",
            event_type="injection_D_load_spike",
            input_text=";".join(burst),
            ctx_before="",
            ctx_after="",
            output_hash="",
            state_change="rapid_fire_20",
            conflict=True,
            failure_code="F-03",
            latency_ms=0,
        )

    def _scheduler_loop(self) -> None:
        while time.monotonic() < self.stop_at:
            tid = f"thread-{self.rng.randint(0, self.num_threads - 1)}"
            workload = self._pick_workload()
            self._enqueue(tid, workload, "")
            time.sleep(self.rng.uniform(0.05, 0.35))

    def run(self) -> Cc01Verdict:
        self.stop_at = time.monotonic() + self.duration_sec
        workers = [
            threading.Thread(target=self._worker, args=(f"thread-{i}",), daemon=True)
            for i in range(self.num_threads)
        ]
        injector = threading.Thread(target=self._injector_loop, daemon=True)
        scheduler = threading.Thread(target=self._scheduler_loop, daemon=True)

        started = time.monotonic()
        for t in workers:
            t.start()
        injector.start()
        scheduler.start()

        while time.monotonic() < self.stop_at:
            time.sleep(0.2)

        self.stop_at = time.monotonic()
        for _ in workers:
            try:
                self.request_queue.put(None, timeout=1.0)
            except queue.Full:
                pass
        for t in workers:
            t.join(timeout=5.0)
        injector.join(timeout=2.0)
        scheduler.join(timeout=2.0)

        return self._build_verdict(duration_sec=time.monotonic() - started)

    def _build_verdict(self, *, duration_sec: float) -> Cc01Verdict:
        failure_counts: dict[str, int] = {code: 0 for code in FAILURE_MEANINGS}
        trace_samples: dict[str, list[dict[str, Any]]] = {code: [] for code in FAILURE_MEANINGS}

        for event in self.events:
            if event.failure_code:
                failure_counts[event.failure_code] = failure_counts.get(event.failure_code, 0) + 1
                bucket = trace_samples.setdefault(event.failure_code, [])
                if len(bucket) < 2:
                    bucket.append(event.to_dict())

        violations: list[str] = []
        if self.backend.unlogged_overwrites:
            violations.append("unlogged_overwrite_detected")
        if self.backend.context_bleeds:
            violations.append("cross_thread_context_leakage")
        if self.starvation_events and len(self.starvation_events) > self.num_threads:
            violations.append("queue_starvation_exceeded_threshold")
        if self.backend.cascade_markers:
            violations.append("cascade_failure_detected")
        if self.determinism_violations:
            violations.append("determinism_drift_detected")
        if self.global_stall:
            violations.append("global_stall")

        would_pass = True
        if self.backend.unlogged_overwrites:
            would_pass = False
        if self.backend.context_bleeds:
            would_pass = False
        if self.global_stall:
            would_pass = False
        if not self.events:
            would_pass = False
            violations.append("no_events_logged")

        return Cc01Verdict(
            pass_gate=False,  # diagnostic only; not a CI gate yet
            would_pass=would_pass,
            failure_counts={k: v for k, v in failure_counts.items() if v},
            violations=violations,
            trace_samples={k: v for k, v in trace_samples.items() if v},
            total_events=len(self.events),
            duration_sec=duration_sec,
            backend=self._backend_label,
        )

    def write_artifacts(self, out_dir: Path, verdict: Cc01Verdict) -> dict[str, Path]:
        out_dir.mkdir(parents=True, exist_ok=True)
        log_path = out_dir / "cc01_events.jsonl"
        with log_path.open("w", encoding="utf-8") as handle:
            for event in self.events:
                handle.write(json.dumps(event.to_dict(), ensure_ascii=True) + "\n")

        summary_path = out_dir / "cc01_summary.json"
        summary_path.write_text(
            json.dumps(
                {
                    "pass": verdict.pass_gate,
                    "would_pass": verdict.would_pass,
                    "backend": verdict.backend,
                    "failure_counts": verdict.failure_counts,
                    "violations": verdict.violations,
                    "trace_samples": verdict.trace_samples,
                    "total_events": verdict.total_events,
                    "duration_sec": verdict.duration_sec,
                    "failure_meanings": FAILURE_MEANINGS,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return {"log": log_path, "summary": summary_path}


def run_cc01(
    *,
    workspace_root: Path,
    out_dir: Path,
    duration_sec: float = 120.0,
    num_threads: int = 12,
    seed: int | None = None,
    backend: str = "simulated",
    nova_base_url: str | None = None,
    nova_queue_name: str = "cc01-chaos",
    max_qps: float = 8.0,
    repo_root: Path | None = None,
) -> Cc01Verdict:
    harness = Cc01ControlledCollapseHarness(
        workspace_root=workspace_root,
        num_threads=num_threads,
        duration_sec=duration_sec,
        seed=seed,
        backend_mode=backend,
        nova_base_url=nova_base_url,
        nova_queue_name=nova_queue_name,
        max_qps=max_qps,
        repo_root=repo_root or ROOT,
    )
    verdict = harness.run()
    harness.write_artifacts(out_dir, verdict)
    return verdict


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CC-01 CIEMS Controlled Collapse harness")
    parser.add_argument("--duration", type=float, default=120.0, help="Run duration seconds (90-180)")
    parser.add_argument("--threads", type=int, default=12, help="Concurrent threads")
    parser.add_argument("--workspace", type=Path, default=ROOT / ".runtime" / "cc01-ciems" / "workspace")
    parser.add_argument("--out", type=Path, default=ROOT / ".runtime" / "cc01-ciems")
    parser.add_argument("--seed", type=int, default=None, help="RNG seed for replay")
    parser.add_argument(
        "--backend",
        choices=("simulated", "nova"),
        default="simulated",
        help="simulated in-process workspace or live Nova HTTP",
    )
    parser.add_argument("--nova-base-url", default=None, help="Nova API base URL (default from env)")
    parser.add_argument(
        "--nova-queue-name",
        default="cc01-chaos",
        help="Sandbox queue prefix for Nova sessions (cc01_nova_* ids)",
    )
    parser.add_argument("--max-qps", type=float, default=8.0, help="Nova request rate cap")
    parser.add_argument("--repo-root", type=Path, default=ROOT, help="Repo root for Nova target seeding")
    args = parser.parse_args(argv)

    min_duration = 60.0 if args.backend == "nova" else 90.0
    duration = max(min_duration, min(180.0, args.duration))
    threads = args.threads
    if args.backend == "nova":
        duration = min(duration, NOVA_MAX_DURATION_SEC)
        threads = min(threads, NOVA_MAX_THREADS)
        status, health_body = check_health(args.nova_base_url)
        if status != 200:
            raise SystemExit(f"Nova preflight failed: HTTP {status} — {health_body!s}"[:500])

    verdict = run_cc01(
        workspace_root=args.workspace,
        out_dir=args.out,
        duration_sec=duration,
        num_threads=threads,
        seed=args.seed,
        backend=args.backend,
        nova_base_url=args.nova_base_url,
        nova_queue_name=args.nova_queue_name,
        max_qps=args.max_qps,
        repo_root=args.repo_root,
    )
    print(
        json.dumps(
            {
                "pass": verdict.pass_gate,
                "would_pass": verdict.would_pass,
                "backend": verdict.backend,
                "failure_counts": verdict.failure_counts,
                "violations": verdict.violations,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
