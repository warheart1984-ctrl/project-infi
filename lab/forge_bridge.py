"""Lab ↔ Forge bridge — review-first patch plans from governed lab sessions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TYPE_CHECKING

from src.patch_review_store import PatchReviewStore
from src.patchforge import PatchForge

if TYPE_CHECKING:
    from lab.session import LabSession


def build_lab_workspace_context(session: LabSession, *, goal: str, file_limit: int = 6) -> dict[str, Any]:
    """Build a PatchForge-compatible workspace context rooted at the lab worktree."""
    workspace = session.workspace.resolve()
    files: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []

    candidates: list[Path] = []
    for pattern in ("**/*.py", "**/*.md", "**/*.yaml", "**/*.json"):
        for path in workspace.glob(pattern):
            if path.is_file() and ".git" not in path.parts:
                candidates.append(path)
    candidates.sort(key=lambda item: item.stat().st_mtime, reverse=True)

    goal_tokens = {token for token in goal.lower().split() if len(token) > 3}
    ranked = sorted(
        candidates,
        key=lambda path: sum(1 for token in goal_tokens if token in path.name.lower()),
        reverse=True,
    )

    for path in ranked[:file_limit]:
        rel = path.relative_to(workspace).as_posix()
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        truncated = len(content) > 4000
        files.append(
            {
                "relative_path": rel,
                "content": content[:4000],
                "truncated": truncated,
            }
        )
        snippet = content[:240].replace("\n", " ")
        results.append({"relative_path": rel, "snippet": snippet})

    return {
        "workspace_root": str(workspace),
        "goal": goal,
        "files": files,
        "results": results,
        "lab_session_id": session.session_id,
        "lab_project_id": session.project_id,
    }


def create_lab_patch_plan(session: LabSession, *, goal: str) -> dict[str, Any]:
    """Generate a review-first patch plan from the lab workspace."""
    context = build_lab_workspace_context(session, goal=goal)
    forge = PatchForge()
    plan = forge.build_patch_plan(goal, context)
    plan["lab_session_id"] = session.session_id
    plan["lab_project_id"] = session.project_id
    plan["workspace_root"] = context["workspace_root"]
    return plan


def create_lab_patch_review(
    session: LabSession,
    *,
    goal: str,
    patch_plan: dict[str, Any] | None = None,
    review_store: PatchReviewStore | None = None,
) -> dict[str, Any]:
    """Persist a patch review linked to the lab session (never auto-apply)."""
    plan = patch_plan or create_lab_patch_plan(session, goal=goal)
    store = review_store or _lab_review_store(session)
    review = store.create_review(session_id=session.session_id, patch_plan=plan)
    review_ids = _load_patch_review_ids(session)
    review_id = str(review.get("review_id") or review.get("id") or "")
    if review_id and review_id not in review_ids:
        review_ids.append(review_id)
        _save_patch_review_ids(session, review_ids)
    return {
        "review": review,
        "patch_plan": plan,
        "review_ids": review_ids,
        "apply_gate": review.get("apply_gate"),
    }


def _lab_review_store(session: LabSession) -> PatchReviewStore:
    runtime_dir = session.session_dir / "patch_reviews"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    return PatchReviewStore(runtime_dir=runtime_dir)


def _patch_review_ids_path(session: LabSession) -> Path:
    return session.session_dir / "patch_review_ids.json"


def _load_patch_review_ids(session: LabSession) -> list[str]:
    path = _patch_review_ids_path(session)
    if not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [str(item) for item in payload]
    if isinstance(payload, dict):
        return [str(item) for item in payload.get("review_ids") or []]
    return []


def _save_patch_review_ids(session: LabSession, review_ids: list[str]) -> None:
    path = _patch_review_ids_path(session)
    path.write_text(json.dumps({"review_ids": review_ids}, indent=2) + "\n", encoding="utf-8")
