#!/usr/bin/env python3
"""Operator Kernel + Agent Loop E2E validation (mapped to actual API routes)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
KERNEL_BASE = os.environ.get("OPERATOR_KERNEL_URL", "http://127.0.0.1:8790").rstrip("/")


def _http_json(method: str, path: str, body: dict | None = None, timeout: float = 30.0) -> tuple[int, Any]:
    url = f"{KERNEL_BASE}{path}"
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw) if raw else {"detail": raw}
        except json.JSONDecodeError:
            payload = {"detail": raw}
        return exc.code, payload


def _latest_event_seq(task_id: str) -> int:
    """Highest event seq on a task (so follow-up SSE does not replay approval events)."""
    status, body = _http_json("GET", f"/agent/tasks/{task_id}")
    if status != 200 or not isinstance(body, dict):
        return 0
    events = body.get("events") or []
    if not events:
        nested = body.get("meta")
        if isinstance(nested, dict):
            pass
        events = body.get("events") or []
    return max((int(e.get("seq") or 0) for e in events if isinstance(e, dict)), default=0)


def _parse_sse_block(block: str, events: list[dict[str, Any]]) -> None:
    for line in block.splitlines():
        if line.startswith("data: "):
            try:
                events.append(json.loads(line[6:]))
            except json.JSONDecodeError:
                pass


def _sse_collect(task_id: str, after: int = 0, max_seconds: float = 120.0) -> list[dict[str, Any]]:
    url = f"{KERNEL_BASE}/agent/tasks/{task_id}/events?after={after}"
    events: list[dict[str, Any]] = []
    deadline = time.time() + max_seconds
    req = urllib.request.Request(url, headers={"Accept": "text/event-stream"})
    with urllib.request.urlopen(req, timeout=max_seconds + 5) as resp:
        buffer = ""
        while time.time() < deadline:
            chunk = resp.read(4096)
            if not chunk:
                break
            buffer += chunk.decode("utf-8", errors="replace")
            while "\n\n" in buffer:
                block, buffer = buffer.split("\n\n", 1)
                _parse_sse_block(block, events)
                types = {e.get("type") for e in events}
                if "task_completed" in types or "task_cancelled" in types or "error" in types:
                    return events
    return events


def _sse_collect_until(
    task_id: str,
    until_types: set[str],
    after: int = 0,
    max_seconds: float = 60.0,
) -> list[dict[str, Any]]:
    """Collect SSE events until any of until_types appears (do not wait for task completion)."""
    url = f"{KERNEL_BASE}/agent/tasks/{task_id}/events?after={after}"
    events: list[dict[str, Any]] = []
    deadline = time.time() + max_seconds
    req = urllib.request.Request(url, headers={"Accept": "text/event-stream"})
    with urllib.request.urlopen(req, timeout=max_seconds + 5) as resp:
        buffer = ""
        while time.time() < deadline:
            chunk = resp.read(4096)
            if not chunk:
                break
            buffer += chunk.decode("utf-8", errors="replace")
            while "\n\n" in buffer:
                block, buffer = buffer.split("\n\n", 1)
                _parse_sse_block(block, events)
                if until_types & {e.get("type") for e in events}:
                    return events
    return events


def _wait_health(max_seconds: float = 45.0) -> dict[str, Any]:
    deadline = time.time() + max_seconds
    last: dict[str, Any] = {}
    while time.time() < deadline:
        try:
            status, body = _http_json("GET", "/health", timeout=3.0)
            if status == 200 and isinstance(body, dict):
                last = body
                if body.get("status") == "ok" and body.get("lawful_brain_reachable"):
                    return body
        except Exception:
            pass
        time.sleep(0.5)
    return last


def main() -> int:
    results: list[dict[str, Any]] = []

    # Test 1
    health = _wait_health()
    t1_ok = health.get("status") == "ok" and health.get("lawful_brain_reachable") is True
    results.append(
        {
            "test": 1,
            "name": "Kernel Health & Lawful Brain Reachability",
            "pass": t1_ok,
            "detail": health,
            "note": "GET /health",
        }
    )
    if not t1_ok:
        _print_report(results)
        return 1

    # Test 2
    status, created = _http_json(
        "POST",
        "/agent/tasks",
        {
            "goal": "Create a new file hello.py that prints Hello World",
            "agent_id": "builder",
            "constraints": {"read_only": False, "allow_shell": False, "max_steps": 8},
        },
    )
    task_id = created.get("task_id") if isinstance(created, dict) else None
    t2_ok = status == 200 and bool(task_id)
    results.append(
        {
            "test": 2,
            "name": "Create Task",
            "pass": t2_ok,
            "detail": {"http_status": status, "body": created},
            "note": "POST /agent/tasks with goal (not input)",
        }
    )
    if not t2_ok:
        _print_report(results)
        return 1

    # Test 3 + 4 (SSE + patch)
    events = _sse_collect(task_id, max_seconds=180.0)
    types = [e.get("type") for e in events]
    t3_ok = (
        "task_started" in types
        and ("assistant_message" in types or "plan_updated" in types)
        and ("tool_called" in types or "task_completed" in types)
    )
    results.append(
        {
            "test": 3,
            "name": "SSE Event Stream",
            "pass": t3_ok,
            "detail": {"event_types": types, "event_count": len(events)},
            "note": "GET /agent/tasks/{id}/events - plan used assistant_message/tool_called",
        }
    )

    write_calls = [e for e in events if e.get("type") == "tool_called" and (e.get("payload") or {}).get("name") == "write_patch"]
    patch_previews = [e for e in events if e.get("type") == "patch_preview"]
    completed = [e for e in events if e.get("type") == "task_completed"]
    awaiting = any((e.get("payload") or {}).get("status") == "awaiting_approval" for e in completed)
    patch_ok = False
    patch_detail: dict[str, Any] = {}
    if write_calls:
        args = (write_calls[0].get("payload") or {}).get("args") or {}
        diff = args.get("diff") or ""
        path = args.get("path") or "hello.py"
        patch_detail = {
            "path": path,
            "diff_preview": diff[:500],
            "patch_preview_events": len(patch_previews),
            "awaiting_approval": awaiting,
        }
        patch_ok = (
            "hello.py" in path
            and ("+" in diff or "@@" in diff)
            and len(patch_previews) >= 1
            and awaiting
        )
    t4_ok = False
    file_has_hello = False
    file_content = ""
    if patch_ok:
        approve_status, approve_body = _http_json("POST", f"/agent/tasks/{task_id}/approve_patch")
        patch_detail["approve_http"] = approve_status
        patch_detail["approve_body"] = approve_body
        t4_ok = approve_status == 200 and isinstance(approve_body, dict) and approve_body.get("applied") is True
        if t4_ok:
            time.sleep(0.5)
            f_status, f_body = _http_json("GET", "/workspace/file?path=hello.py")
            if f_status == 200 and isinstance(f_body, dict):
                file_content = f_body.get("content") or ""
                file_has_hello = "Hello World" in file_content
            t4_ok = t4_ok and file_has_hello
        patch_detail["file_on_disk"] = file_has_hello
        patch_detail["file_preview"] = file_content[:120]
    last_event_seq = _latest_event_seq(task_id) if task_id else max((e.get("seq") or 0) for e in events) if events else 0
    results.append(
        {
            "test": 4,
            "name": "Patch Proposal + Apply",
            "pass": t4_ok,
            "detail": patch_detail,
            "note": "write_patch preview -> awaiting_approval -> POST approve_patch -> workspace/file",
        }
    )

    # Test 5 - cancel (second task)
    status, created2 = _http_json(
        "POST",
        "/agent/tasks",
        {
            "goal": "Analyze the entire workspace tree in detail and propose many incremental improvements",
            "agent_id": "builder",
            "constraints": {"read_only": False, "allow_shell": False, "max_steps": 12},
        },
    )
    task2 = created2.get("task_id") if isinstance(created2, dict) else None
    cancel_ok = False
    cancel_detail: dict[str, Any] = {}
    if task2:
        cancel_result: dict[str, Any] = {}

        def _fire_cancel() -> None:
            c_status, c_body = _http_json("POST", f"/agent/tasks/{task2}/cancel")
            cancel_result["http"] = c_status
            cancel_result["body"] = c_body

        threading.Thread(target=_fire_cancel, daemon=True).start()
        final = _sse_collect(task2, max_seconds=90.0)
        ftypes = [e.get("type") for e in final]
        tool_after_cancel = False
        if "task_cancelled" in ftypes:
            cancel_idx = ftypes.index("task_cancelled")
            tool_after_cancel = any(t == "tool_called" for t in ftypes[cancel_idx + 1 :])
        cancel_status_ok = cancel_result.get("http") == 200 and (
            (cancel_result.get("body") or {}).get("status") in ("cancelling", "cancelled")
        )
        cancel_ok = cancel_status_ok and "task_cancelled" in ftypes and not tool_after_cancel
        cancel_detail = {"cancel_http": cancel_result.get("http"), "cancel_body": cancel_result.get("body"), "event_types": ftypes}
    else:
        cancel_detail = {"error": "no task_id from create"}
    results.append(
        {
            "test": 5,
            "name": "Cancel Mid-Run",
            "pass": cancel_ok,
            "detail": cancel_detail,
            "note": "POST /agent/tasks/{id}/cancel",
        }
    )

    # Test 6 - follow-up
    status, msg = _http_json(
        "POST",
        f"/agent/tasks/{task_id}/message",
        {"text": "Modify hello.py to print Hello Jon"},
    )
    max_seq = last_event_seq
    follow_events = _sse_collect(task_id, after=max_seq, max_seconds=120.0) if status == 200 else []
    follow_types = [e.get("type") for e in follow_events]
    follow_awaiting = any(
        (e.get("payload") or {}).get("status") == "awaiting_approval"
        for e in follow_events
        if e.get("type") == "task_completed"
    )
    approve_follow_http: int | None = None
    approve_follow_body: dict[str, Any] | None = None
    if follow_awaiting:
        approve_follow_http, approve_follow_raw = _http_json("POST", f"/agent/tasks/{task_id}/approve_patch")
        approve_follow_body = approve_follow_raw if isinstance(approve_follow_raw, dict) else None
        time.sleep(0.5)
    file_has_jon = False
    f_status, f_body = _http_json("GET", "/workspace/file?path=hello.py")
    if f_status == 200 and isinstance(f_body, dict):
        content = f_body.get("content") or ""
        file_has_jon = "Hello Jon" in content or "Jon" in content
    t6_ok = (
        status == 200
        and ("task_started" in follow_types or "task_completed" in follow_types)
        and (not follow_awaiting or (approve_follow_http == 200 and (approve_follow_body or {}).get("applied") is True))
        and file_has_jon
    )
    results.append(
        {
            "test": 6,
            "name": "Follow-Up",
            "pass": t6_ok,
            "detail": {
                "message_http": status,
                "follow_event_types": follow_types,
                "follow_awaiting_approval": follow_awaiting,
                "approve_follow_http": approve_follow_http,
                "approve_follow_body": approve_follow_body,
                "file_has_jon": file_has_jon,
            },
            "note": "POST /agent/tasks/{id}/message (not /followup)",
        }
    )

    # Test 7
    t_status, tree = _http_json("GET", "/workspace/tree")
    paths: list[str] = []
    if isinstance(tree, dict):
        for n in tree.get("nodes", []) or []:
            if isinstance(n, dict) and n.get("path"):
                paths.append(str(n["path"]))
        for p in tree.get("files", []) or []:
            if isinstance(p, str):
                paths.append(p)
    paths = list(dict.fromkeys(paths))
    t7_ok = t_status == 200 and any("hello.py" in (p or "") for p in paths) and file_has_jon
    results.append(
        {
            "test": 7,
            "name": "Workspace Tree + File Viewer",
            "pass": t7_ok,
            "detail": {"tree_status": t_status, "hello_paths": [p for p in paths if p and "hello" in p]},
            "note": "GET /workspace/tree and /workspace/file",
        }
    )

    # Test 8 - desktop build (optional if dotnet missing)
    build_script = ROOT / "scripts" / "build_operator_desktop.ps1"
    t8_ok = False
    t8_detail: dict[str, Any] = {}
    if os.environ.get("OPERATOR_E2E_SKIP_DESKTOP", "").strip().lower() in {"1", "true", "yes", "on"}:
        t8_ok = True
        t8_detail = {"skipped": True, "reason": "OPERATOR_E2E_SKIP_DESKTOP"}
    elif build_script.is_file():
        proc = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(build_script),
                "-SkipInstaller",
            ],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=600,
        )
        t8_ok = proc.returncode == 0
        t8_detail = {
            "returncode": proc.returncode,
            "stdout_tail": (proc.stdout or "")[-2000:],
            "stderr_tail": (proc.stderr or "")[-2000:],
        }
        dist = ROOT / "dist" / "operator-desktop"
        if dist.is_dir():
            zips = list(dist.glob("OperatorDesktop-*.zip"))
            t8_detail["portable_zips"] = [str(z) for z in zips]
    else:
        t8_detail = {"error": "build script missing"}
    results.append(
        {
            "test": 8,
            "name": "Desktop Build",
            "pass": t8_ok,
            "detail": t8_detail,
            "note": "scripts/build_operator_desktop.ps1 -SkipInstaller",
        }
    )

    _print_report(results, events=events)
    all_pass = all(r["pass"] for r in results)
    return 0 if all_pass else 1


def _print_report(results: list[dict[str, Any]], events: list[dict[str, Any]] | None = None) -> None:
    print("\n=== Operator Kernel E2E Validation Report ===\n")
    for r in results:
        mark = "PASS" if r["pass"] else "FAIL"
        print(f"[{mark}] Test {r['test']}: {r['name']}")
        if r.get("note"):
            print(f"       {r['note']}")
    if events:
        print("\n--- SSE sample (last 15 events) ---")
        for e in events[-15:]:
            print(json.dumps({"seq": e.get("seq"), "type": e.get("type"), "payload": e.get("payload")}, default=str)[:300])
    print("\n--- Route mapping (plan vs implementation) ---")
    print("  POST /v1/tasks              -> POST /agent/tasks (body: goal, not input)")
    print("  GET  /v1/tasks/{id}/events  -> GET  /agent/tasks/{id}/events")
    print("  POST /v1/tasks/{id}/cancel -> POST /agent/tasks/{id}/cancel")
    print("  POST /v1/tasks/{id}/followup -> POST /agent/tasks/{id}/message")
    print("  agent_thought               -> assistant_message")
    print("  tool_call                   -> tool_called")
    passed = sum(1 for r in results if r["pass"])
    print(f"\nSummary: {passed}/{len(results)} passed\n")


if __name__ == "__main__":
    sys.exit(main())
