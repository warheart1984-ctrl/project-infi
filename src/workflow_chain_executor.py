"""Governed workflow chain executor."""

# Mythic: Workflow Chain Executor
# Engineering: WorkflowChainExecutorEngine
from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.plug_discovery import match_plug_pattern
from src.plug_adapter_runtime import plug_adapter_runtime
from src.workflow_plugin_catalog import workflow_by_id

MODULE_ID = "AAIS-WCE-01"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1] / ".runtime"


class WorkflowChainExecutor:
    def __init__(self, *, runtime_dir: Path | None = None, repo_root: Path | None = None):
        self._runtime_dir = runtime_dir or _default_runtime_dir()
        self._repo_root = repo_root
        self._lock = threading.Lock()
        self._runs_dir = self._runtime_dir / "workflow_chain_runs"

    def execute(
        self,
        workflow_id: str,
        *,
        args: dict[str, Any] | None = None,
        operator_approved: bool = False,
        dry_run: bool = True,
    ) -> dict[str, Any]:
        bundle = workflow_by_id(workflow_id, repo_root=self._repo_root)
        if not bundle:
            return {"outcome": "not_found", "workflow_id": workflow_id}
        if not operator_approved:
            return {"outcome": "blocked", "reason": "operator_approved required", "workflow_id": workflow_id}
        run_id = f"wfr_{uuid4().hex[:12]}"
        steps_out: list[dict[str, Any]] = []
        for index, step in enumerate(list(bundle.get("steps") or [])):
            pattern = str(step.get("plug_pattern") or "")
            plug_id = pattern.rstrip(".*")
            exec_result = plug_adapter_runtime.execute_plug(
                plug_id,
                args={"workflow_id": workflow_id, "step_index": index, **dict(args or {})},
                dry_run=dry_run,
                operator_approved=operator_approved,
            )
            steps_out.append({"step": step, "result": exec_result})
        run = {
            "run_id": run_id,
            "workflow_id": workflow_id,
            "status": "completed",
            "dry_run": bool(dry_run),
            "started_at": _utc_now_iso(),
            "completed_at": _utc_now_iso(),
            "steps": steps_out,
        }
        with self._lock:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            path = self._runs_dir / f"{run_id}.json"
            path.write_text(json.dumps(run, sort_keys=True) + "\n", encoding="utf-8")
        if not dry_run:
            try:
                from src.ugr.rewards.reward_hooks import emit_workflow_chain_completed

                emit_workflow_chain_completed(
                    tenant_id=str((args or {}).get("tenant_id") or "global"),
                    operator_id=str((args or {}).get("operator_id") or "operator"),
                    workflow_id=workflow_id,
                    run_id=run_id,
                    step_count=len(steps_out),
                    dry_run=False,
                )
            except Exception:
                pass
        return run

    def get_run(self, workflow_id: str, run_id: str) -> dict[str, Any] | None:
        path = self._runs_dir / f"{run_id}.json"
        if not path.is_file():
            return None
        try:
            run = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        if str(run.get("workflow_id") or "") != workflow_id:
            return None
        return run


workflow_chain_executor = WorkflowChainExecutor()
