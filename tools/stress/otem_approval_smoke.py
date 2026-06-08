#!/usr/bin/env python
"""Live Level-10 OTEM approval path smoke test against running AAIS on :8000."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BASE = os.environ.get("AAIS_STRESS_BASE", "http://127.0.0.1:8000").rstrip("/")
LEGACY = f"{BASE}/legacy_api"
TIMEOUT = 30
OTEM_TASK = (
    "Use OTEM to design a daily brief workflow that emails the operator every morning."
)
REPORT_PATH = ROOT / "ci-artifacts" / "otem_approval_smoke_report.json"


def _headers() -> dict[str, str]:
    hdrs = {"Content-Type": "application/json"}
    token = os.environ.get("APP_BEARER_TOKEN") or os.environ.get("AAIS_BEARER_TOKEN")
    if token:
        hdrs["Authorization"] = f"Bearer {token}"
    return hdrs


def _req(method: str, url: str, body: dict | None = None) -> tuple[int, dict | str]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=_headers(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, raw


def main() -> int:
    report: dict = {"base": BASE, "steps": [], "ok": False}
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    def step(name: str, status: int, detail: dict | str, *, ok: bool) -> None:
        report["steps"].append({"name": name, "status": status, "ok": ok, "detail": detail})

    status, health = _req("GET", f"{BASE}/health")
    step("health", status, health, ok=status == 200)
    if status != 200:
        _write_report(report, "health preflight failed")
        return 1

    status, otem_status = _req(
        "GET",
        f"{LEGACY}/api/jarvis/otem-execution-substrate/status",
    )
    step("otem_execution_substrate_status", status, otem_status, ok=status == 200)
    if status != 200:
        _write_report(report, "otem status preflight failed")
        return 1

    status, session = _req("POST", f"{LEGACY}/api/chat/sessions", {"title": "otem-smoke"})
    session_id = session.get("session_id") if isinstance(session, dict) else None
    step("create_chat_session", status, {"session_id": session_id}, ok=status in {200, 201} and bool(session_id))
    if status not in {200, 201} or not session_id:
        _write_report(report, "chat session create failed")
        return 1

    status, message = _req(
        "POST",
        f"{LEGACY}/api/chat/sessions/{session_id}/message",
        {"message": OTEM_TASK},
    )
    step("otem_chat_message", status, _summarize(message), ok=status == 200)
    if status != 200:
        _write_report(report, "OTEM chat message failed")
        return 1

    status, approvals_payload = _req("GET", f"{BASE}/workflows/approvals")
    approvals = approvals_payload
    if isinstance(approvals_payload, dict):
        approvals = approvals_payload.get("approvals") or []
    pending = []
    if isinstance(approvals, list):
        pending = [
            item
            for item in approvals
            if item.get("step_type") == "otem_execution_substrate"
            and item.get("status") == "pending"
        ]
    step("list_pending_approvals", status, {"count": len(pending)}, ok=status == 200 and pending)
    if status != 200 or not pending:
        _write_report(report, "no pending OTEM approval after chat turn")
        return 1

    approval_id = pending[0]["id"]
    status, approve = _req(
        "POST",
        f"{BASE}/workflows/approvals/{approval_id}",
        {"action": "approve"},
    )
    step("approve_otem_execution", status, approve, ok=status == 200)
    if status != 200:
        _write_report(report, "approve failed")
        return 1

    status, post_status = _req(
        "GET",
        f"{LEGACY}/api/jarvis/otem-execution-substrate/status",
    )
    active = post_status.get("active_workflows") if isinstance(post_status, dict) else None
    step(
        "post_approve_substrate_status",
        status,
        {"active_workflows": active},
        ok=status == 200,
    )

    report["ok"] = True
    report["summary"] = "Level-10 OTEM approve path completed without 5xx"
    _save_report(report)
    print(f"OK: {report['summary']}")
    print(f"Report: {REPORT_PATH}")
    return 0


def _summarize(payload: dict | str) -> dict | str:
    if not isinstance(payload, dict):
        return payload
    meta = payload.get("metadata") or {}
    return {
        "has_workflow_handoff": bool(meta.get("workflow_handoff") or payload.get("workflow_handoff")),
        "has_execution_approval_queue": bool(
            meta.get("execution_approval_queue") or payload.get("execution_approval_queue")
        ),
        "reply_len": len(str(payload.get("reply") or payload.get("response") or "")),
    }


def _save_report(report: dict) -> None:
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def _write_report(report: dict, summary: str) -> None:
    report["summary"] = summary
    _save_report(report)
    print(f"FAIL: {summary}", file=sys.stderr)
    print(f"Report: {REPORT_PATH}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
