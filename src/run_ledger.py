# Mythic: Run Ledger Organ
# Engineering: RunLedgerEngine
from __future__ import annotations

from datetime import datetime
from src.datetime_compat import UTC
import json
from pathlib import Path
import threading
from typing import Any
from uuid import uuid4

from src.state_hygiene import (
    filter_operator_records,
    normalize_truth_scope,
    project_record,
)
from src.cisiv import CISIV_LOGBOOK_STAGES, infer_lifecycle_cisiv_stage, normalize_cisiv_stage


RUN_LEDGER_FILENAME = "run-ledger.json"


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _wrap_run_record(run: dict[str, Any]) -> dict[str, Any]:
    from src.aais_ul_substrate import attach_ul_substrate

    return attach_ul_substrate(dict(run))


class RunLedger:
    """Durable JSON-backed run history for multi-step Jarvis work."""

    def __init__(self, runtime_dir: str | Path | None = None):
        self.runtime_dir = Path(runtime_dir) if runtime_dir else None
        self._lock = threading.Lock()

    def configure_runtime_dir(self, runtime_dir: str | Path | None) -> None:
        self.runtime_dir = Path(runtime_dir) if runtime_dir else None

    def _resolve_path(self) -> Path:
        root = (
            self.runtime_dir.expanduser().resolve()
            if self.runtime_dir is not None
            else Path(__file__).resolve().parents[1] / ".runtime"
        )
        root.mkdir(parents=True, exist_ok=True)
        return root / RUN_LEDGER_FILENAME

    def _load_payload(self) -> dict[str, Any]:
        path = self._resolve_path()
        if not path.exists():
            return {"runs": [], "session_active_runs": {}}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"runs": [], "session_active_runs": {}}
        if not isinstance(payload, dict):
            return {"runs": [], "session_active_runs": {}}
        runs = payload.get("runs")
        if not isinstance(runs, list):
            runs = []
        session_active_runs = payload.get("session_active_runs")
        if not isinstance(session_active_runs, dict):
            session_active_runs = {}
        return {
            "runs": [self._normalize_run(run) for run in runs if isinstance(run, dict)],
            "session_active_runs": session_active_runs,
        }

    def _normalize_run(self, run: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(run)
        if not isinstance(normalized.get("steps"), list):
            normalized["steps"] = []
        if not isinstance(normalized.get("artifacts"), list):
            normalized["artifacts"] = []
        if not isinstance(normalized.get("action_ids"), list):
            normalized["action_ids"] = []
        if not isinstance(normalized.get("action_instance_ids"), list):
            normalized["action_instance_ids"] = []
        if not isinstance(normalized.get("meta"), dict):
            normalized["meta"] = {}
        normalized["cisiv_stage"] = normalize_cisiv_stage(
            normalized.get("cisiv_stage") or normalized["meta"].get("cisiv_stage"),
            default="implementation",
        )
        normalized["steps"] = [
            {
                **dict(step),
                "cisiv_stage": normalize_cisiv_stage(
                    step.get("cisiv_stage") or (step.get("meta") or {}).get("cisiv_stage"),
                    default=normalized["cisiv_stage"],
                ),
            }
            for step in normalized["steps"]
            if isinstance(step, dict)
        ]
        normalized["current_action"] = (
            dict(normalized.get("current_action"))
            if isinstance(normalized.get("current_action"), dict)
            else None
        )
        if normalized["current_action"] is not None:
            normalized["current_action"]["cisiv_stage"] = normalize_cisiv_stage(
                normalized["current_action"].get("cisiv_stage"),
                default=normalized["cisiv_stage"],
            )
        normalized["history_count"] = len(normalized["steps"])
        projected = project_record(normalized, kind="run", source_type="run")
        projected.pop("_state_hygiene_kind", None)
        return projected

    def _save_payload(self, payload: dict[str, Any]) -> None:
        self._resolve_path().write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _find_run_index(self, payload: dict[str, Any], run_id: str) -> int | None:
        for index, run in enumerate(payload.get("runs", [])):
            if str(run.get("id") or "") == str(run_id):
                return index
        return None

    def create_run(
        self,
        session_id: str,
        title: str,
        kind: str,
        meta: dict[str, Any] | None = None,
        run_id: str | None = None,
    ) -> dict[str, Any]:
        created_at = _utc_now()
        normalized_meta = dict(meta or {})
        cisiv_stage = normalize_cisiv_stage(normalized_meta.get("cisiv_stage"), default="implementation")
        normalized_meta["cisiv_stage"] = cisiv_stage
        run = {
            "id": run_id or f"run_{uuid4().hex}",
            "session_id": session_id,
            "title": str(title or "Jarvis run").strip() or "Jarvis run",
            "kind": str(kind or "operator").strip() or "operator",
            "status": "open",
            "summary": None,
            "created_at": created_at,
            "updated_at": created_at,
            "closed_at": None,
            "meta": normalized_meta,
            "cisiv_stage": cisiv_stage,
            "steps": [],
            "artifacts": [],
            "action_ids": [],
            "action_instance_ids": [],
            "current_action": None,
            "history_count": 0,
        }
        with self._lock:
            payload = self._load_payload()
            payload["runs"].append(run)
            payload["session_active_runs"][session_id] = run["id"]
            self._save_payload(payload)
        return _wrap_run_record(dict(run))

    def ensure_run(
        self,
        session_id: str,
        *,
        title: str,
        kind: str,
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            payload = self._load_payload()
            active_run_id = str(payload.get("session_active_runs", {}).get(session_id) or "").strip()
            if active_run_id:
                run_index = self._find_run_index(payload, active_run_id)
                if run_index is not None:
                    run = payload["runs"][run_index]
                    if str(run.get("status") or "") == "open":
                        return _wrap_run_record(dict(run))
            created_at = _utc_now()
            normalized_meta = dict(meta or {})
            cisiv_stage = normalize_cisiv_stage(normalized_meta.get("cisiv_stage"), default="implementation")
            normalized_meta["cisiv_stage"] = cisiv_stage
            run = {
                "id": f"run_{uuid4().hex}",
                "session_id": session_id,
                "title": str(title or "Jarvis run").strip() or "Jarvis run",
                "kind": str(kind or "operator").strip() or "operator",
                "status": "open",
                "summary": None,
                "created_at": created_at,
                "updated_at": created_at,
                "closed_at": None,
                "meta": normalized_meta,
                "cisiv_stage": cisiv_stage,
                "steps": [],
                "artifacts": [],
                "action_ids": [],
                "action_instance_ids": [],
                "current_action": None,
                "history_count": 0,
            }
            payload["runs"].append(run)
            payload["session_active_runs"][session_id] = run["id"]
            self._save_payload(payload)
            return _wrap_run_record(dict(run))

    def append_step(self, run_id: str, step: dict[str, Any]) -> dict[str, Any]:
        created_at = str(step.get("created_at") or _utc_now())
        with self._lock:
            payload = self._load_payload()
            run_index = self._find_run_index(payload, run_id)
            if run_index is None:
                raise FileNotFoundError(f"Run `{run_id}` was not found.")
            run = payload["runs"][run_index]
            entry = {
                "id": step.get("id") or f"step_{uuid4().hex}",
                "kind": str(step.get("kind") or "step"),
                "title": str(step.get("title") or step.get("summary") or "Step").strip() or "Step",
                "summary": str(step.get("summary") or "").strip(),
                "status": str(step.get("status") or "recorded").strip() or "recorded",
                "created_at": created_at,
                "meta": dict(step.get("meta") or {}),
                "cisiv_stage": normalize_cisiv_stage(
                    step.get("cisiv_stage") or (step.get("meta") or {}).get("cisiv_stage"),
                    default=run.get("cisiv_stage") or "implementation",
                ),
            }
            entry["meta"]["cisiv_stage"] = entry["cisiv_stage"]
            duplicate = run.get("steps", [])[-1:] or []
            if duplicate:
                latest = duplicate[0]
                if (
                    latest.get("kind") == entry["kind"]
                    and latest.get("title") == entry["title"]
                    and latest.get("summary") == entry["summary"]
                ):
                    return dict(self._normalize_run(latest))
            run.setdefault("steps", []).append(entry)
            run["updated_at"] = created_at
            run["history_count"] = len(run.get("steps", []))
            self._save_payload(payload)
        return dict(entry)

    def attach_artifact(self, run_id: str, artifact: dict[str, Any]) -> dict[str, Any]:
        entry = {
            "id": artifact.get("id") or f"artifact_{uuid4().hex}",
            "kind": str(artifact.get("kind") or "artifact"),
            "label": str(artifact.get("label") or artifact.get("kind") or "Artifact").strip() or "Artifact",
            "created_at": str(artifact.get("created_at") or _utc_now()),
            "payload": dict(artifact.get("payload") or {}),
        }
        with self._lock:
            payload = self._load_payload()
            run_index = self._find_run_index(payload, run_id)
            if run_index is None:
                raise FileNotFoundError(f"Run `{run_id}` was not found.")
            run = payload["runs"][run_index]
            run.setdefault("artifacts", []).append(entry)
            run["updated_at"] = entry["created_at"]
            self._save_payload(payload)
        return dict(entry)

    def close_run(self, run_id: str, status: str, summary: str | None = None) -> dict[str, Any]:
        closed_at = _utc_now()
        with self._lock:
            payload = self._load_payload()
            run_index = self._find_run_index(payload, run_id)
            if run_index is None:
                raise FileNotFoundError(f"Run `{run_id}` was not found.")
            run = payload["runs"][run_index]
            run["status"] = str(status or "completed").strip() or "completed"
            run["summary"] = str(summary).strip() if summary is not None else run.get("summary")
            run["closed_at"] = closed_at
            run["updated_at"] = closed_at
            if payload.get("session_active_runs", {}).get(run.get("session_id")) == run_id:
                payload["session_active_runs"].pop(run.get("session_id"), None)
            self._save_payload(payload)
            return _wrap_run_record(dict(self._normalize_run(run)))

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        with self._lock:
            payload = self._load_payload()
        index = self._find_run_index(payload, run_id)
        if index is None:
            return None
        return _wrap_run_record(dict(self._normalize_run(payload["runs"][index])))

    def list_runs(
        self,
        session_id: str | None = None,
        limit: int = 20,
        truth_scope: str = "live",
    ) -> list[dict[str, Any]]:
        capped_limit = min(max(1, int(limit or 20)), 100)
        with self._lock:
            payload = self._load_payload()
        runs = payload.get("runs", [])
        if session_id:
            runs = [run for run in runs if run.get("session_id") == session_id]
        ordered = sorted(
            runs,
            key=lambda item: (
                str(item.get("updated_at") or item.get("created_at") or ""),
                str(item.get("id") or ""),
            ),
            reverse=True,
        )
        projected = [dict(self._normalize_run(run)) for run in ordered]
        if normalize_truth_scope(truth_scope) != "all":
            projected = filter_operator_records(projected, truth_scope=truth_scope)
        return projected[:capped_limit]

    def append_lifecycle(self, session_id: str, lifecycle: dict[str, Any]) -> dict[str, Any] | None:
        action_instance_id = str(lifecycle.get("action_instance_id") or "").strip()
        stage = str(lifecycle.get("stage") or "").strip()
        if not session_id or not action_instance_id or not stage:
            return None
        action_label = str(lifecycle.get("action_label") or lifecycle.get("action_id") or "Jarvis action").strip()
        run = self.ensure_run(
            session_id,
            title=f"{action_label} run",
            kind="operator_action",
            meta={
                "action_id": lifecycle.get("action_id"),
                "cisiv_stage": infer_lifecycle_cisiv_stage(lifecycle),
            },
        )
        cisiv_stage = infer_lifecycle_cisiv_stage(lifecycle, default=run.get("cisiv_stage") or "implementation")
        step = self.append_step(
            run["id"],
            {
                "kind": "action_lifecycle",
                "title": f"{action_label}: {stage}",
                "summary": (
                    f"{action_label} is {stage} "
                    f"(approval: {lifecycle.get('approval_state')}, execution: {lifecycle.get('execution_state')})."
                ),
                "status": stage,
                "created_at": lifecycle.get(f"{stage}_at") or lifecycle.get("updated_at") or _utc_now(),
                "cisiv_stage": cisiv_stage,
                "meta": {
                    "action_id": lifecycle.get("action_id"),
                    "action_label": lifecycle.get("action_label"),
                    "action_instance_id": action_instance_id,
                    "approval_state": lifecycle.get("approval_state"),
                    "execution_state": lifecycle.get("execution_state"),
                    "result_status": lifecycle.get("result_status"),
                    "exit_code": lifecycle.get("exit_code"),
                    "error": lifecycle.get("error"),
                    "cisiv_stage": cisiv_stage,
                },
            },
        )
        with self._lock:
            payload = self._load_payload()
            run_index = self._find_run_index(payload, run["id"])
            if run_index is None:
                return step
            stored_run = payload["runs"][run_index]
            action_id = str(lifecycle.get("action_id") or "").strip()
            if action_id and action_id not in stored_run.get("action_ids", []):
                stored_run.setdefault("action_ids", []).append(action_id)
            if action_instance_id and action_instance_id not in stored_run.get("action_instance_ids", []):
                stored_run.setdefault("action_instance_ids", []).append(action_instance_id)
            stored_run["current_action"] = {
                "action_id": lifecycle.get("action_id"),
                "action_label": lifecycle.get("action_label"),
                "action_instance_id": action_instance_id,
                "stage": stage,
                "cisiv_stage": cisiv_stage,
                "approval_state": lifecycle.get("approval_state"),
                "execution_state": lifecycle.get("execution_state"),
                "result_status": lifecycle.get("result_status"),
                "exit_code": lifecycle.get("exit_code"),
                "updated_at": step["created_at"],
            }
            stored_run["updated_at"] = step["created_at"]
            stored_run["history_count"] = len(stored_run.get("steps", []))
            if stage in {"executed", "failed", "blocked"}:
                stored_run["status"] = (
                    "completed" if stage == "executed" else "failed" if stage == "failed" else "blocked"
                )
                stored_run["summary"] = step["summary"]
                stored_run["closed_at"] = step["created_at"]
                if payload.get("session_active_runs", {}).get(session_id) == stored_run["id"]:
                    payload["session_active_runs"].pop(session_id, None)
            self._save_payload(payload)
        return step

    def compact_runs(self) -> dict[str, Any]:
        """Expire non-live open runs so verification artifacts stop looking active."""
        expired_runs = 0
        now = _utc_now()
        with self._lock:
            payload = self._load_payload()
            for run in payload.get("runs", []):
                projected = self._normalize_run(run)
                if projected.get("status") != "open":
                    continue
                if projected.get("state_class") == "live":
                    continue
                run["status"] = "expired"
                run["summary"] = (
                    str(run.get("summary") or "").strip()
                    or "Expired by state hygiene compaction because this run was non-live operator history."
                )
                run["closed_at"] = now
                run["updated_at"] = now
                run["retention_status"] = "expired"
                session_id = str(run.get("session_id") or "").strip()
                if payload.get("session_active_runs", {}).get(session_id) == run.get("id"):
                    payload["session_active_runs"].pop(session_id, None)
                expired_runs += 1
            if expired_runs:
                self._save_payload(payload)
        return {"expired_runs": expired_runs}
