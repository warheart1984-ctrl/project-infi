"""Experiment tracking — diffs, logs, indexed metadata."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from lab.common import EXPERIMENTS_DIRNAME, RECEIPT_FILENAME, json_stable, write_json
from lab.project import increment_experiment_seq, project_dir
from lab.worktree import git_diff, revert_workspace


class ExperimentError(RuntimeError):
    """Raised when experiment operations fail."""


_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    lowered = text.lower().strip()
    slug = _SLUG_RE.sub("-", lowered).strip("-")
    return slug[:48] or "experiment"


def experiment_id_from(seq: int, slug: str) -> str:
    return f"exp-{seq:03d}-{slugify(slug)}"


def experiments_dir(project_id: str, *, runtime_root: Path | None = None) -> Path:
    return project_dir(project_id, runtime_root=runtime_root) / EXPERIMENTS_DIRNAME


def create_experiment(
    project_id: str,
    slug: str,
    *,
    description: str = "",
    runtime_root: Path | None = None,
) -> dict[str, Any]:
    seq, _ = increment_experiment_seq(project_id, runtime_root=runtime_root)
    exp_id = experiment_id_from(seq, slug)
    out = experiments_dir(project_id, runtime_root=runtime_root) / exp_id
    out.mkdir(parents=True, exist_ok=True)
    meta = {
        "experiment_version": "lab.experiment.v1",
        "experiment_id": exp_id,
        "project_id": project_id,
        "slug": slugify(slug),
        "description": description,
        "status": "open",
    }
    write_json(out / "EXPERIMENT.json", meta)
    (out / "tool_log.jsonl").touch()
    return meta


def finalize_experiment(
    project_id: str,
    experiment_id: str,
    *,
    session_dir: Path | None = None,
    workspace: Path,
    status: str,
    runtime_root: Path | None = None,
) -> dict[str, Any]:
    out = experiments_dir(project_id, runtime_root=runtime_root) / experiment_id
    if not out.is_dir():
        raise ExperimentError(f"experiment not found: {experiment_id}")

    exp_path = out / "EXPERIMENT.json"
    meta = json.loads(exp_path.read_text(encoding="utf-8"))
    meta["status"] = status
    diff_text = git_diff(workspace)
    (out / "session.diff").write_text(diff_text, encoding="utf-8")
    meta["diff_bytes"] = len(diff_text.encode("utf-8"))

    if session_dir:
        receipt_src = session_dir / RECEIPT_FILENAME
        if receipt_src.is_file():
            (out / RECEIPT_FILENAME).write_text(
                receipt_src.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        tool_src = session_dir / "tool_log.jsonl"
        if tool_src.is_file():
            (out / "tool_log.jsonl").write_text(
                tool_src.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        tests_src = session_dir / "test_results.json"
        if tests_src.is_file():
            (out / "test_results.json").write_text(
                tests_src.read_text(encoding="utf-8"),
                encoding="utf-8",
            )

    write_json(exp_path, meta)
    return meta


def list_experiments(
    project_id: str,
    *,
    file_filter: str | None = None,
    status_filter: str | None = None,
    runtime_root: Path | None = None,
) -> list[dict[str, Any]]:
    base = experiments_dir(project_id, runtime_root=runtime_root)
    if not base.is_dir():
        return []
    results: list[dict[str, Any]] = []
    for child in sorted(base.iterdir()):
        if not child.is_dir():
            continue
        exp_file = child / "EXPERIMENT.json"
        if not exp_file.is_file():
            continue
        meta = json.loads(exp_file.read_text(encoding="utf-8"))
        if status_filter and meta.get("status") != status_filter:
            continue
        if file_filter:
            diff_path = child / "session.diff"
            if diff_path.is_file():
                if file_filter not in diff_path.read_text(encoding="utf-8", errors="replace"):
                    continue
            else:
                continue
        meta["experiment_dir"] = str(child.resolve())
        results.append(meta)
    return results


def show_experiment(
    project_id: str,
    experiment_id: str,
    *,
    runtime_root: Path | None = None,
) -> dict[str, Any]:
    out = experiments_dir(project_id, runtime_root=runtime_root) / experiment_id
    if not out.is_dir():
        raise ExperimentError(f"experiment not found: {experiment_id}")
    exp_path = out / "EXPERIMENT.json"
    meta = json.loads(exp_path.read_text(encoding="utf-8"))
    meta["diff_path"] = str((out / "session.diff").resolve()) if (out / "session.diff").is_file() else ""
    return meta


def revert_experiment(
    project_id: str,
    experiment_id: str,
    *,
    workspace: Path,
    confirm: bool = False,
) -> dict[str, Any]:
    if not confirm:
        raise ExperimentError("revert requires --confirm")
    show_experiment(project_id, experiment_id)
    revert_workspace(workspace)
    return {"project_id": project_id, "experiment_id": experiment_id, "reverted": True}
