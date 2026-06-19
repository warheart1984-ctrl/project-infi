"""CC-01 backend abstraction: simulated workspace vs live Nova/mechanic HTTP."""

from __future__ import annotations

import hashlib
import json
import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from tools.stress import _chaos_common as chaos

SHARED_TARGET_REL = "agent/project/main.py"
FUNCTIONX_MARKER = "FunctionX"
CC01_NOVA_PREFIX = "cc01_nova_"


def _http_is_server_error(status: int | None) -> bool:
    """True for HTTP 5xx; safe when status is None (transport timeout)."""
    return status is not None and status >= 500


def _http_is_transport_failure(status: int | None) -> bool:
    """True when urllib layer failed (timeout, connection error)."""
    return status is None


def _http_failure_code(status: int | None) -> str:
    """Map HTTP/transport outcome to CC-01 failure code (empty if OK).

    Transport timeouts (status None) count as F-03 under saturation, not F-04 cascade.
    Server 5xx remains F-04 (true cascade from the mechanic).
    """
    if _http_is_transport_failure(status):
        return "F-03"
    if _http_is_server_error(status):
        return "F-04"
    return ""


@dataclass
class Cc01WorkloadResult:
    ctx_before: str
    ctx_after: str
    output_hash: str
    state_change: str
    conflict: bool
    failure_code: str
    latency_ms: int
    backend: str = "simulated"
    nova_request_id: str = ""
    nova_session_id: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


class CC01Backend(Protocol):
    backend_name: str
    unlogged_overwrites: list[dict[str, str]]
    context_bleeds: list[dict[str, str]]
    cascade_markers: list[str]

    def ensure_thread(self, thread_id: str) -> None: ...

    def get_context(self, thread_id: str) -> str: ...

    def snapshot_context(self, thread_id: str) -> None: ...

    def apply_edit(self, thread_id: str, payload: dict[str, Any]) -> Cc01WorkloadResult: ...

    def summarize_context(self, thread_id: str, target_thread: str) -> Cc01WorkloadResult: ...

    def run_codegen(self, thread_id: str, payload: dict[str, Any]) -> Cc01WorkloadResult: ...

    def record_debug(self, thread_id: str, note: str) -> Cc01WorkloadResult: ...

    def read_functionx_hashes(self) -> tuple[str, str]: ...

    def seed_target(self) -> None: ...

    def mark_cascade(self, reason: str) -> None: ...


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _auth_headers() -> dict[str, str]:
    token = os.environ.get("APP_BEARER_TOKEN") or os.environ.get("AAIS_BEARER_TOKEN")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


class SimulatedWorkspaceBackend:
    """In-process shared workspace (intentionally weak sync for F-01/F-02)."""

    backend_name = "simulated"

    def __init__(self, workspace: Any) -> None:
        self._ws = workspace

    @property
    def unlogged_overwrites(self) -> list[dict[str, str]]:
        return self._ws.unlogged_overwrites

    @property
    def context_bleeds(self) -> list[dict[str, str]]:
        return self._ws.context_bleeds

    @property
    def cascade_markers(self) -> list[str]:
        return self._ws.cascade_markers

    def mark_cascade(self, reason: str) -> None:
        self._ws.mark_cascade(reason)

    def ensure_thread(self, thread_id: str) -> None:
        self._ws.ensure_thread(thread_id)

    def get_context(self, thread_id: str) -> str:
        return self._ws.get_context(thread_id)

    def snapshot_context(self, thread_id: str) -> None:
        self._ws.snapshot_context(thread_id)

    def _edit_functionx_body(self, thread_id: str, variant: str) -> str:
        text = self._ws.read_file_text()
        lines = text.splitlines()
        new_lines: list[str] = []
        replaced = False
        for line in lines:
            if line.strip().startswith("def FunctionX"):
                new_lines.append(
                    f"def FunctionX(x: int, tag_{thread_id}: str = '{variant}') -> int:"
                )
                replaced = True
            else:
                new_lines.append(line)
        if not replaced:
            new_lines.append(
                f"\ndef FunctionX(x: int, tag_{thread_id}: str = '{variant}') -> int:\n    return x\n"
            )
        return "\n".join(new_lines) + "\n"

    def apply_edit(self, thread_id: str, payload: dict[str, Any]) -> Cc01WorkloadResult:
        started = time.perf_counter()
        self._ws.snapshot_context(thread_id)
        ctx_before = self._ws.get_context(thread_id)
        before_h, _ = self._ws.hashes()
        variant = str(payload.get("variant") or payload.get("content") or "burst")
        body = self._edit_functionx_body(thread_id, variant)
        self._ws.write(thread_id, body, op="edit")
        ctx_after = self._ws.update_context(thread_id, f"edit:{variant}")
        after_h, _ = self._ws.hashes()
        latency_ms = int((time.perf_counter() - started) * 1000)
        conflict = before_h != after_h
        failure = ""
        if self._ws.unlogged_overwrites:
            failure = "F-01"
        elif conflict and self._ws.last_writer and self._ws.last_writer != thread_id:
            failure = "F-01"
        return Cc01WorkloadResult(
            ctx_before=ctx_before,
            ctx_after=ctx_after,
            output_hash=after_h,
            state_change="edit_functionx_signature",
            conflict=conflict,
            failure_code=failure,
            latency_ms=latency_ms,
            backend=self.backend_name,
        )

    def run_codegen(self, thread_id: str, payload: dict[str, Any]) -> Cc01WorkloadResult:
        started = time.perf_counter()
        self._ws.snapshot_context(thread_id)
        ctx_before = self._ws.get_context(thread_id)
        before_h, _ = self._ws.hashes()
        note = str(payload.get("goal") or payload.get("content") or "extend")
        body = self._ws.read_file_text() + f"\n# codegen:{thread_id}:{note}\n"
        self._ws.write(thread_id, body, op="codegen")
        ctx_after = self._ws.update_context(thread_id, f"codegen:{note}")
        after_h, _ = self._ws.hashes()
        latency_ms = int((time.perf_counter() - started) * 1000)
        failure = "F-01" if self._ws.unlogged_overwrites else ""
        return Cc01WorkloadResult(
            ctx_before=ctx_before,
            ctx_after=ctx_after,
            output_hash=after_h,
            state_change="append_codegen",
            conflict=before_h != after_h,
            failure_code=failure,
            latency_ms=latency_ms,
            backend=self.backend_name,
        )

    def record_debug(self, thread_id: str, note: str) -> Cc01WorkloadResult:
        started = time.perf_counter()
        ctx_before = self._ws.get_context(thread_id)
        ctx_after = self._ws.update_context(thread_id, f"debug:{note}")
        latency_ms = int((time.perf_counter() - started) * 1000)
        return Cc01WorkloadResult(
            ctx_before=ctx_before,
            ctx_after=ctx_after,
            output_hash=_sha256_text(f"debug:{thread_id}:{note}"),
            state_change="debug_context_only",
            conflict=False,
            failure_code="",
            latency_ms=latency_ms,
            backend=self.backend_name,
        )

    def summarize_context(self, thread_id: str, target_thread: str) -> Cc01WorkloadResult:
        started = time.perf_counter()
        self._ws.snapshot_context(thread_id)
        ctx_before = self._ws.get_context(thread_id)
        summary = self._ws.summarize_from(thread_id, target_thread)
        ctx_after = self._ws.get_context(thread_id)
        latency_ms = int((time.perf_counter() - started) * 1000)
        before_h, after_h = self._ws.hashes()
        conflict = before_h != after_h
        failure = "F-02" if self._ws.context_bleeds else ""
        state_change = (
            "cross_thread_summarize" if target_thread != thread_id else "self_summarize"
        )
        return Cc01WorkloadResult(
            ctx_before=ctx_before,
            ctx_after=ctx_after,
            output_hash=_sha256_text(summary),
            state_change=state_change,
            conflict=bool(failure),
            failure_code=failure,
            latency_ms=latency_ms,
            backend=self.backend_name,
        )

    def read_functionx_hashes(self) -> tuple[str, str]:
        return self._ws.hashes()

    def seed_target(self) -> None:
        self._ws.seed_functionx()


class NovaBackend:
    """Live Nova / mechanic paths via legacy Flask API."""

    backend_name = "nova"

    def __init__(
        self,
        *,
        base_url: str | None = None,
        queue_name: str = "cc01-chaos",
        repo_root: Path | None = None,
        max_qps: float = 8.0,
    ) -> None:
        if base_url:
            chaos.configure_base(base_url)
        self.queue_name = queue_name
        self.repo_root = Path(repo_root or Path.cwd())
        self._max_qps = max(0.5, max_qps)
        self._last_request_at = 0.0
        self._rate_lock = threading.Lock()
        self._sessions: dict[str, str] = {}
        self._session_lock = threading.Lock()
        self._target_path = SHARED_TARGET_REL.replace("/", os.sep)
        self.unlogged_overwrites: list[dict[str, str]] = []
        self.context_bleeds: list[dict[str, str]] = []
        self.cascade_markers: list[str] = []

    def mark_cascade(self, reason: str) -> None:
        self.cascade_markers.append(reason)

    def _throttle(self) -> None:
        with self._rate_lock:
            min_gap = 1.0 / self._max_qps
            now = time.perf_counter()
            wait = min_gap - (now - self._last_request_at)
            if wait > 0:
                time.sleep(wait)
            self._last_request_at = time.perf_counter()

    def _req(
        self,
        method: str,
        path: str,
        *,
        json_body: dict | None = None,
        timeout: int = 180,
        max_body: int = 8000,
    ) -> tuple[int | None, Any]:
        self._throttle()
        headers = {"Content-Type": "application/json", **_auth_headers()}
        return chaos._req(
            method,
            path,
            json_body=json_body,
            headers=headers,
            timeout=timeout,
            max_body=max_body,
            parse_json=True,
        )

    def ensure_thread(self, thread_id: str) -> None:
        with self._session_lock:
            if thread_id in self._sessions:
                return
        mechanic_case_id = f"{CC01_NOVA_PREFIX}{self.queue_name}_{thread_id}"
        payload = {
            "persona_mode": "super_nova",
            "mechanic_case_id": mechanic_case_id,
            "metadata": {"cc01_thread_id": thread_id, "cc01_queue": self.queue_name},
        }
        # Session payloads exceed 8KB; do not truncate before JSON parse.
        status, body = self._req(
            "POST", "/api/chat/sessions", json_body=payload, timeout=45, max_body=0
        )
        if status not in (200, 201) or not isinstance(body, dict):
            raise RuntimeError(f"create_session failed thread={thread_id} status={status} body={body!r}")
        session_id = str(body.get("session_id") or body.get("id") or "").strip()
        if not session_id:
            raise RuntimeError(f"create_session missing session_id: {body!r}")
        act_status, act_body = self._req(
            "POST",
            f"/api/chat/sessions/{session_id}/super-nova/activate",
            json_body={"reason": "cc01_harness"},
            timeout=90,
            max_body=0,
        )
        if act_status not in (200, 409):
            raise RuntimeError(
                f"super_nova activate failed thread={thread_id} status={act_status} body={act_body!r}"
            )
        with self._session_lock:
            self._sessions[thread_id] = session_id

    def _session_id(self, thread_id: str) -> str:
        with self._session_lock:
            sid = self._sessions.get(thread_id)
        if not sid:
            self.ensure_thread(thread_id)
            with self._session_lock:
                sid = self._sessions[thread_id]
        return sid or ""

    def get_context(self, thread_id: str) -> str:
        sid = self._session_id(thread_id)
        return f"nova_session={sid} queue={self.queue_name}"

    def snapshot_context(self, thread_id: str) -> None:
        return

    def _read_target_content(self) -> tuple[str, str]:
        status, body = self._req(
            "GET",
            f"/api/jarvis/workspace/file?path={SHARED_TARGET_REL}&max_chars=8000",
            timeout=30,
        )
        if status != 200 or not isinstance(body, dict):
            return "", _sha256_text("")
        content = str(body.get("content") or body.get("text") or "")
        return content, _sha256_text(content)

    def _forge(
        self,
        thread_id: str,
        *,
        task: str,
        kind: str = "generate_diff",
        change_intent: str = "cc01_chaos",
    ) -> tuple[int, dict[str, Any], int]:
        started = time.perf_counter()
        session_id = self._session_id(thread_id)
        payload = {
            "task": task,
            "kind": kind,
            "session_id": session_id,
            "focus_files": [SHARED_TARGET_REL],
            "change_intent": change_intent,
            "target_scope": SHARED_TARGET_REL,
            "constraints": {"cc01_queue": self.queue_name, "cc01_thread": thread_id},
        }
        status, body = self._req("POST", "/api/jarvis/forge/code", json_body=payload, timeout=180)
        latency_ms = int((time.perf_counter() - started) * 1000)
        if not isinstance(body, dict):
            body = {"raw": body}
        return status, body, latency_ms

    def _chat_message(self, thread_id: str, message: str) -> tuple[int, dict[str, Any], int]:
        started = time.perf_counter()
        session_id = self._session_id(thread_id)
        payload = {"message": message, "stream": False}
        status, body = self._req(
            "POST",
            f"/api/chat/sessions/{session_id}/message",
            json_body=payload,
            timeout=180,
        )
        latency_ms = int((time.perf_counter() - started) * 1000)
        if not isinstance(body, dict):
            body = {"raw": body}
        return status, body, latency_ms

    def apply_edit(self, thread_id: str, payload: dict[str, Any]) -> Cc01WorkloadResult:
        ctx_before = self.get_context(thread_id)
        _, before_hash = self._read_target_content()
        snippet = str(payload.get("content") or f"edit {FUNCTIONX_MARKER} on {SHARED_TARGET_REL}")
        task = (
            f"CC-01 injection edit for thread {thread_id}. "
            f"Apply a minimal change to {SHARED_TARGET_REL} preserving {FUNCTIONX_MARKER}. "
            f"Change: {snippet}"
        )
        status, body, latency_ms = self._forge(thread_id, task=task, kind="generate_diff", change_intent="cc01_edit")
        _, after_hash = self._read_target_content()
        task_id = str(body.get("task_id") or "")
        failure = ""
        if before_hash and after_hash and before_hash != after_hash:
            failure = "F-01"
            self.unlogged_overwrites.append(
                {"thread_id": thread_id, "before_hash": before_hash, "after_hash": after_hash}
            )
        failure = failure or _http_failure_code(status)
        return Cc01WorkloadResult(
            ctx_before=ctx_before,
            ctx_after=self.get_context(thread_id),
            output_hash=after_hash or before_hash,
            state_change="edit_applied" if status == 200 else f"edit_http_{status}",
            conflict=bool(before_hash and after_hash and before_hash != after_hash),
            failure_code=failure,
            latency_ms=latency_ms,
            backend=self.backend_name,
            nova_request_id=task_id,
            nova_session_id=self._session_id(thread_id),
            extra={"http_status": status, "forge": body},
        )

    def run_codegen(self, thread_id: str, payload: dict[str, Any]) -> Cc01WorkloadResult:
        ctx_before = self.get_context(thread_id)
        _, before_hash = self._read_target_content()
        goal = str(payload.get("goal") or f"extend {FUNCTIONX_MARKER} in {SHARED_TARGET_REL}")
        task = f"CC-01 codegen thread {thread_id}: {goal}"
        status, body, latency_ms = self._forge(thread_id, task=task, kind="generate_diff", change_intent="cc01_codegen")
        _, after_hash = self._read_target_content()
        task_id = str(body.get("task_id") or "")
        failure = ""
        if before_hash and after_hash and before_hash != after_hash:
            failure = "F-01"
            self.unlogged_overwrites.append(
                {"thread_id": thread_id, "before_hash": before_hash, "after_hash": after_hash}
            )
        failure = failure or _http_failure_code(status)
        return Cc01WorkloadResult(
            ctx_before=ctx_before,
            ctx_after=self.get_context(thread_id),
            output_hash=after_hash or before_hash,
            state_change="codegen_applied" if status == 200 else f"codegen_http_{status}",
            conflict=bool(before_hash and after_hash and before_hash != after_hash),
            failure_code=failure,
            latency_ms=latency_ms,
            backend=self.backend_name,
            nova_request_id=task_id,
            nova_session_id=self._session_id(thread_id),
            extra={"http_status": status},
        )

    def summarize_context(self, thread_id: str, target_thread: str) -> Cc01WorkloadResult:
        ctx_before = self.get_context(thread_id)
        target_sid = self._session_id(target_thread)
        prompt = (
            f"Summarize the workspace and session context for CC-01 thread {target_thread}. "
            f"Target session id is {target_sid}. "
            f"Do not reference other threads. One paragraph."
        )
        status, body, latency_ms = self._chat_message(thread_id, prompt)
        text = json.dumps(body, sort_keys=True)[:4000]
        bleed = target_sid in text and thread_id != target_thread
        failure = "F-02" if bleed else ""
        if bleed:
            self.context_bleeds.append(
                {"reader": thread_id, "donor": target_thread, "payload": text[:200]}
            )
        if status == 409:
            failure = failure or "F-03"
        return Cc01WorkloadResult(
            ctx_before=ctx_before,
            ctx_after=self.get_context(thread_id),
            output_hash=_sha256_text(text),
            state_change="context_summarized",
            conflict=bool(failure),
            failure_code=failure,
            latency_ms=latency_ms,
            backend=self.backend_name,
            nova_request_id=str(body.get("message_id") or uuid.uuid4().hex[:12]),
            nova_session_id=self._session_id(thread_id),
            extra={"http_status": status, "target_session_id": target_sid},
        )

    def read_functionx_hashes(self) -> tuple[str, str]:
        content, digest = self._read_target_content()
        return digest, _sha256_text(content[:512])

    def seed_target(self) -> None:
        target = self.repo_root / SHARED_TARGET_REL
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text(
                "def FunctionX(x: int) -> int:\n    return x\n",
                encoding="utf-8",
            )

    def record_debug(self, thread_id: str, note: str) -> Cc01WorkloadResult:
        started = time.perf_counter()
        ctx_before = self.get_context(thread_id)
        status, body, latency_ms = self._chat_message(
            thread_id,
            f"CC-01 debug probe for thread {thread_id}: {note}",
        )
        text = json.dumps(body, sort_keys=True)[:2000]
        failure = _http_failure_code(status)
        return Cc01WorkloadResult(
            ctx_before=ctx_before,
            ctx_after=self.get_context(thread_id),
            output_hash=_sha256_text(text),
            state_change="debug_message",
            conflict=bool(failure),
            failure_code=failure,
            latency_ms=latency_ms,
            backend=self.backend_name,
            nova_request_id=str(body.get("message_id") or ""),
            nova_session_id=self._session_id(thread_id),
            extra={"http_status": status},
        )


def build_backend(
    *,
    mode: str,
    workspace: Any | None = None,
    repo_root: Path | None = None,
    base_url: str | None = None,
    queue_name: str = "cc01-chaos",
    max_qps: float = 8.0,
) -> tuple[CC01Backend, str]:
    """Return (backend, backend_label) for CC-01 harness."""
    if mode == "simulated":
        if workspace is None:
            raise ValueError("workspace required for simulated backend")
        return SimulatedWorkspaceBackend(workspace), "simulated"
    if mode == "nova":
        root = repo_root or Path.cwd()
        return (
            NovaBackend(
                base_url=base_url,
                queue_name=queue_name,
                repo_root=root,
                max_qps=max_qps,
            ),
            "nova",
        )
    raise ValueError(f"unknown backend mode: {mode!r}")
