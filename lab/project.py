"""Lab project manager — manifest, directories, init."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from lab.capabilities import write_capability_profile
from lab.common import (
    DEFAULT_RUNTIME_ROOT,
    EXPERIMENTS_DIRNAME,
    MANIFEST_FILENAME,
    SESSIONS_DIRNAME,
    WORKSPACE_DIRNAME,
    write_json,
)
from lab.ledger import append_ledger_entry
from lab.spec import LabProjectSpec, SpecLoadError, ensure_default_instruments, load_lab_spec, write_spec_canonical
from lab.spine import write_spine_profile
from lab.worktree import WorktreeError, create_workspace
from src.datetime_compat import UTC


class ProjectError(RuntimeError):
    """Raised when lab project operations fail."""


def project_dir(project_id: str, *, runtime_root: Path | None = None) -> Path:
    root = (runtime_root or DEFAULT_RUNTIME_ROOT).expanduser().resolve()
    return root / project_id


def workspace_path(project_id: str, *, runtime_root: Path | None = None) -> Path:
    return project_dir(project_id, runtime_root=runtime_root) / WORKSPACE_DIRNAME


def load_manifest(project_id: str, *, runtime_root: Path | None = None) -> dict[str, Any]:
    path = project_dir(project_id, runtime_root=runtime_root) / MANIFEST_FILENAME
    if not path.is_file():
        raise ProjectError(f"lab project not initialized: {project_id}")
    import json

    return json.loads(path.read_text(encoding="utf-8"))


def init_project(
    *,
    spec_path: str | Path | None = None,
    project_id: str | None = None,
    source: str | Path = ".",
    branch: str | None = None,
    runtime_root: Path | None = None,
    ledger_path: Path | None = None,
) -> dict[str, Any]:
    """Initialize lab project: manifest, worktree, spine, capabilities."""
    if spec_path:
        try:
            spec = load_lab_spec(spec_path)
        except SpecLoadError as exc:
            raise ProjectError(str(exc)) from exc
    else:
        if not project_id:
            raise ProjectError("project_id required when spec_path is omitted")
        spec = LabProjectSpec(
            project_id=project_id,
            intent_summary=f"Lab project {project_id}",
            source_repo=str(source),
        )

    spec = ensure_default_instruments(spec)
    if project_id:
        spec = spec.model_copy(update={"project_id": project_id})

    out = project_dir(spec.project_id, runtime_root=runtime_root)
    if (out / MANIFEST_FILENAME).is_file():
        raise ProjectError(f"project already exists: {spec.project_id}")

    out.mkdir(parents=True, exist_ok=True)
    (out / EXPERIMENTS_DIRNAME).mkdir(exist_ok=True)
    (out / SESSIONS_DIRNAME).mkdir(exist_ok=True)

    ws = out / WORKSPACE_DIRNAME
    source_path = Path(source).expanduser()
    if not source_path.is_absolute():
        source_path = (Path.cwd() / source_path).resolve()

    try:
        wt_info = create_workspace(
            source_path=source_path,
            workspace_path=ws,
            branch=branch,
        )
    except WorktreeError as exc:
        raise ProjectError(str(exc)) from exc

    write_spec_canonical(spec, out)
    write_spine_profile(spec, out)
    write_capability_profile(spec, out)

    manifest: dict[str, Any] = {
        "manifest_version": "lab.lab_project_manifest.v1",
        "project_id": spec.project_id,
        "intent_summary": spec.intent_summary,
        "source_path": wt_info["source_path"],
        "workspace_path": wt_info["workspace_path"],
        "init_head": wt_info["init_head"],
        "init_at_utc": datetime.now(UTC).isoformat(),
        "isolation_mode": wt_info["isolation_mode"],
        "risk_level": spec.risk_level,
        "experiment_seq": 0,
        "open_tasks": [],
    }
    write_json(out / MANIFEST_FILENAME, manifest)

    append_ledger_entry(
        {
            "event": "init",
            "project_id": spec.project_id,
            "workspace_path": wt_info["workspace_path"],
            "init_head": wt_info["init_head"],
            "isolation_mode": wt_info["isolation_mode"],
        },
        ledger_path=ledger_path,
    )

    return {
        "project_id": spec.project_id,
        "output_dir": str(out.resolve()),
        "manifest_path": str((out / MANIFEST_FILENAME).resolve()),
        "workspace_path": wt_info["workspace_path"],
        "isolation_mode": wt_info["isolation_mode"],
    }


def project_status(project_id: str, *, runtime_root: Path | None = None) -> dict[str, Any]:
    manifest = load_manifest(project_id, runtime_root=runtime_root)
    ws = Path(manifest["workspace_path"])
    from lab.worktree import get_head_rev

    head = get_head_rev(ws) if ws.is_dir() else ""
    return {
        "project_id": project_id,
        "manifest": manifest,
        "workspace_head": head,
        "output_dir": str(project_dir(project_id, runtime_root=runtime_root).resolve()),
    }


def increment_experiment_seq(
    project_id: str,
    *,
    runtime_root: Path | None = None,
) -> tuple[int, str]:
    out = project_dir(project_id, runtime_root=runtime_root)
    manifest_path = out / MANIFEST_FILENAME
    import json

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    seq = int(manifest.get("experiment_seq", 0)) + 1
    manifest["experiment_seq"] = seq
    write_json(manifest_path, manifest)
    return seq, manifest_path.as_posix()
