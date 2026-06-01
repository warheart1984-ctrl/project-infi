"""Coding session runtime — governed agent API and receipts."""

from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from lab.common import (
    CAPABILITY_FILENAME,
    DEFAULT_RUNTIME_ROOT,
    RECEIPT_FILENAME,
    RECEIPT_VERSION,
    SESSIONS_DIRNAME,
    SPINE_FILENAME,
    json_stable,
    sha256_file,
    write_json,
)
from lab.experiment import create_experiment, finalize_experiment
from lab.ledger import append_ledger_entry
from lab.project import ProjectError, load_manifest, project_dir, workspace_path
from lab.spec import LabProjectSpec, load_lab_spec
from lab.tools import ToolInvocationReceipt, invoke_tool, list_tool_schemas
from lab.worktree import git_snapshot, get_head_rev
from src.datetime_compat import UTC


class SessionError(RuntimeError):
    """Raised when session operations fail."""


class LabSession:
    """Governed coding session bound to a lab project workspace."""

    def __init__(
        self,
        *,
        project_id: str,
        agent: str,
        session_id: str,
        spec: LabProjectSpec,
        manifest: dict[str, Any],
        workspace: Path,
        session_dir: Path,
        spine_profile: dict[str, Any],
        capability_profile: dict[str, Any],
        runtime_root: Path | None = None,
        ledger_path: Path | None = None,
    ) -> None:
        self.project_id = project_id
        self.agent = agent
        self.session_id = session_id
        self.spec = spec
        self.manifest = manifest
        self.workspace = workspace
        self.session_dir = session_dir
        self.spine_profile = spine_profile
        self.capability_profile = capability_profile
        self.runtime_root = runtime_root
        self.ledger_path = ledger_path

        self.confirmations: set[str] = set()
        self.files_read: list[str] = []
        self.files_written: list[str] = []
        self.tools_used: list[dict[str, Any]] = []
        self.tests_run: list[dict[str, Any]] = []
        self._experiment_id: str | None = None
        self._experiment_slug: str | None = None
        self._closed = False
        self.patch_review_ids: list[str] = []

        self._tool_log_path = session_dir / "tool_log.jsonl"
        self._tool_log_path.touch()

    @classmethod
    def open(
        cls,
        *,
        project_id: str,
        agent: str,
        session_id: str | None = None,
        runtime_root: Path | None = None,
        ledger_path: Path | None = None,
    ) -> LabSession:
        root = runtime_root or DEFAULT_RUNTIME_ROOT
        manifest = load_manifest(project_id, runtime_root=root)
        out = project_dir(project_id, runtime_root=root)
        spec_path = out / "LAB_PROJECT_SPEC.json"
        if not spec_path.is_file():
            raise SessionError(f"missing LAB_PROJECT_SPEC.json for {project_id}")
        spec = load_lab_spec(spec_path)
        ws = workspace_path(project_id, runtime_root=root)
        if not ws.is_dir():
            raise SessionError(f"workspace missing for {project_id}")

        spine = json.loads((out / SPINE_FILENAME).read_text(encoding="utf-8"))
        caps = json.loads((out / CAPABILITY_FILENAME).read_text(encoding="utf-8"))

        sid = session_id or _new_session_id()
        session_dir = out / SESSIONS_DIRNAME / sid
        session_dir.mkdir(parents=True, exist_ok=True)

        pre = git_snapshot(ws)
        write_json(session_dir / "pre_snapshot.json", pre)

        session = cls(
            project_id=project_id,
            agent=agent,
            session_id=sid,
            spec=spec,
            manifest=manifest,
            workspace=ws,
            session_dir=session_dir,
            spine_profile=spine,
            capability_profile=caps,
            runtime_root=root,
            ledger_path=ledger_path,
        )
        append_ledger_entry(
            {
                "event": "session_start",
                "project_id": project_id,
                "session_id": sid,
                "agent": agent,
                "pre_head": pre.get("head"),
            },
            ledger_path=ledger_path,
        )
        return session

    @classmethod
    def resume(
        cls,
        *,
        project_id: str,
        session_id: str,
        agent: str | None = None,
        runtime_root: Path | None = None,
        ledger_path: Path | None = None,
    ) -> LabSession:
        """Load an existing session directory without re-initializing snapshots."""
        root = runtime_root or DEFAULT_RUNTIME_ROOT
        manifest = load_manifest(project_id, runtime_root=root)
        out = project_dir(project_id, runtime_root=root)
        spec = load_lab_spec(out / "LAB_PROJECT_SPEC.json")
        ws = workspace_path(project_id, runtime_root=root)
        session_dir = out / SESSIONS_DIRNAME / session_id
        if not session_dir.is_dir():
            raise SessionError(f"session not found: {session_id}")

        spine = json.loads((out / SPINE_FILENAME).read_text(encoding="utf-8"))
        caps = json.loads((out / CAPABILITY_FILENAME).read_text(encoding="utf-8"))
        resolved_agent = agent
        open_path = session_dir / "SESSION_OPEN.json"
        if open_path.is_file():
            open_meta = json.loads(open_path.read_text(encoding="utf-8"))
            resolved_agent = resolved_agent or str(open_meta.get("agent") or "operator")

        session = cls(
            project_id=project_id,
            agent=resolved_agent or "operator",
            session_id=session_id,
            spec=spec,
            manifest=manifest,
            workspace=ws,
            session_dir=session_dir,
            spine_profile=spine,
            capability_profile=caps,
            runtime_root=root,
            ledger_path=ledger_path,
        )
        tool_log = session_dir / "tool_log.jsonl"
        if tool_log.is_file():
            for line in tool_log.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    row = json.loads(line)
                    session.tools_used.append(row)
                    if row.get("tool") == "read_file" and row.get("status") == "ok":
                        path = (row.get("args") or {}).get("path")
                        if path:
                            session.record_file_read(str(path))
                    if row.get("tool") == "write_file" and row.get("status") == "ok":
                        path = (row.get("args") or {}).get("path")
                        if path:
                            session.record_file_write(str(path))
        tests_path = session_dir / "test_results.json"
        if tests_path.is_file():
            session.tests_run = json.loads(tests_path.read_text(encoding="utf-8"))
        exp_meta = session_dir / "experiment_id.txt"
        if exp_meta.is_file():
            session._experiment_id = exp_meta.read_text(encoding="utf-8").strip()
        review_ids_path = session_dir / "patch_review_ids.json"
        if review_ids_path.is_file():
            payload = json.loads(review_ids_path.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                session.patch_review_ids = [str(item) for item in payload]
            elif isinstance(payload, dict):
                session.patch_review_ids = [str(item) for item in payload.get("review_ids") or []]
        return session

    @contextmanager
    def __enter__(self) -> Iterator[LabSession]:
        yield self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        if not self._closed:
            self.close(status="failed" if exc else "ok")

    def confirm(self, path: str) -> None:
        """Grant write confirmation for a high-impact path."""
        self.confirmations.add(path.replace("\\", "/"))

    def list_tools(self) -> list[dict[str, Any]]:
        return list_tool_schemas(self.spec)

    def project_context(self) -> dict[str, Any]:
        return {
            "manifest": self.manifest,
            "open_tasks": list(self.manifest.get("open_tasks") or []),
            "experiment_id": self._experiment_id,
            "session_id": self.session_id,
            "workspace_path": str(self.workspace.resolve()),
        }

    def begin_experiment(self, slug: str, *, description: str = "") -> dict[str, Any]:
        meta = create_experiment(
            self.project_id,
            slug,
            description=description,
            runtime_root=self.runtime_root,
        )
        self._experiment_id = meta["experiment_id"]
        self._experiment_slug = meta["slug"]
        (self.session_dir / "experiment_id.txt").write_text(self._experiment_id + "\n", encoding="utf-8")
        return meta

    def ensure_experiment(self) -> str | None:
        if self._experiment_id:
            return self._experiment_id
        return self.begin_experiment("session-edit")["experiment_id"]

    def invoke_tool(self, name: str, *, args: dict[str, Any] | None = None) -> ToolInvocationReceipt:
        return invoke_tool(self, name, args=args)

    def write_file(
        self,
        path: str,
        *,
        content: str,
        experiment_tag: str | None = None,
    ) -> ToolInvocationReceipt:
        if experiment_tag:
            self.begin_experiment(experiment_tag)
        return self.invoke_tool("write_file", args={"path": path, "content": content})

    def record_file_read(self, path: str) -> None:
        norm = path.replace("\\", "/")
        if norm not in self.files_read:
            self.files_read.append(norm)

    def record_file_write(self, path: str) -> None:
        norm = path.replace("\\", "/")
        if norm not in self.files_written:
            self.files_written.append(norm)

    def record_tool(self, receipt: ToolInvocationReceipt) -> None:
        payload = receipt.to_dict()
        self.tools_used.append(payload)
        with self._tool_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")

    def record_test(self, result: dict[str, Any]) -> None:
        self.tests_run.append(result)
        tests_path = self.session_dir / "test_results.json"
        tests_path.write_text(json_stable(self.tests_run, pretty=True) + "\n", encoding="utf-8")

    def close(self, *, status: str = "ok") -> dict[str, Any]:
        if self._closed:
            raise SessionError("session already closed")
        self._closed = True

        post = git_snapshot(self.workspace)
        write_json(self.session_dir / "post_snapshot.json", post)

        content_hashes: dict[str, str] = {}
        for rel in self.files_written:
            target = self.workspace / rel
            if target.is_file():
                content_hashes[rel] = sha256_file(target)

        from lab.forge_bridge import _load_patch_review_ids
        from src.stage2_fidelity_metrics import evaluate_lab_session_stage2

        patch_review_ids = _load_patch_review_ids(self)
        stage2_metrics = evaluate_lab_session_stage2(
            manifest_open_tasks=list(self.manifest.get("open_tasks") or []),
            tools_used=list(self.tools_used),
            files_written=list(self.files_written),
        )

        receipt: dict[str, Any] = {
            "receipt_version": RECEIPT_VERSION,
            "project": self.project_id,
            "session_id": self.session_id,
            "agent": self.agent,
            "status": status if status in ("ok", "failed") else "failed",
            "claim_label": "asserted",
            "files_read": list(self.files_read),
            "files_written": list(self.files_written),
            "tools_used": list(self.tools_used),
            "tests_run": list(self.tests_run),
            "experiment_id": self._experiment_id or "",
            "patch_review_ids": patch_review_ids,
            "stage2_metrics": stage2_metrics.to_dict(),
            "workspace_head_post": post.get("head") or get_head_rev(self.workspace),
            "content_hashes": content_hashes,
            "generated_at_utc": datetime.now(UTC).isoformat(),
        }
        write_json(self.session_dir / RECEIPT_FILENAME, receipt)

        if self._experiment_id:
            finalize_experiment(
                self.project_id,
                self._experiment_id,
                session_dir=self.session_dir,
                workspace=self.workspace,
                status=status,
                runtime_root=self.runtime_root,
            )

        append_ledger_entry(
            {
                "event": "session_end",
                "project_id": self.project_id,
                "session_id": self.session_id,
                "status": receipt["status"],
                "experiment_id": self._experiment_id,
            },
            ledger_path=self.ledger_path,
        )
        return receipt


def _new_session_id() -> str:
    stamp = datetime.now(UTC).strftime("%Y-%m-%d")
    suffix = datetime.now(UTC).strftime("%H%M%S")
    return f"sess-{stamp}-{suffix}"


def start_session_cli(
    *,
    project_id: str,
    agent: str,
    session_id: str | None = None,
    runtime_root: Path | None = None,
    ledger_path: Path | None = None,
) -> dict[str, Any]:
    """Start a session directory for operator-driven workflows."""
    session = LabSession.open(
        project_id=project_id,
        agent=agent,
        session_id=session_id,
        runtime_root=runtime_root,
        ledger_path=ledger_path,
    )
    meta = {
        "session_id": session.session_id,
        "agent": agent,
        "project_id": project_id,
        "session_dir": str(session.session_dir.resolve()),
    }
    write_json(session.session_dir / "SESSION_OPEN.json", meta)
    session._closed = False  # operator closes explicitly
    return meta


def end_session_cli(
    *,
    project_id: str,
    session_id: str,
    status: str = "ok",
    runtime_root: Path | None = None,
    ledger_path: Path | None = None,
) -> dict[str, Any]:
    """Close a session started via CLI."""
    root = runtime_root or DEFAULT_RUNTIME_ROOT
    session_dir = project_dir(project_id, runtime_root=root) / SESSIONS_DIRNAME / session_id
    receipt_path = session_dir / RECEIPT_FILENAME
    if receipt_path.is_file():
        return json.loads(receipt_path.read_text(encoding="utf-8"))

    open_meta_path = session_dir / "SESSION_OPEN.json"
    if not open_meta_path.is_file():
        raise SessionError(f"session not found: {session_id}")

    session = LabSession.resume(
        project_id=project_id,
        session_id=session_id,
        runtime_root=root,
        ledger_path=ledger_path,
    )
    session._closed = False
    return session.close(status=status)
