"""MECH-APPLY-01 — review-gated patch plan conversion (never writes customer repo)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.patch_review_store import PatchReviewStore


def load_mechanic_patch_plan(case_dir: Path) -> dict[str, Any]:
    path = case_dir / "patch_plan.v1.json"
    if not path.is_file():
        raise ValueError(f"patch_plan.v1.json not found under {case_dir}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("patch_plan.v1.json must be an object")
    return payload


def mechanic_patch_plan_to_review_plan(
    mechanic_plan: dict[str, Any],
    *,
    case_id: str,
    goal: str = "",
) -> dict[str, Any]:
    """Convert mechanic patch_plan.v1 patches into PatchForge-compatible plan."""
    patches = list(mechanic_plan.get("patches") or [])
    target_files = sorted(
        {
            str(p.get("target_path") or "").strip()
            for p in patches
            if str(p.get("target_path") or "").strip()
        }
    )
    edits: list[dict[str, Any]] = []
    rationale: list[str] = []
    for patch in patches:
        path = str(patch.get("target_path") or "unknown")
        code = str(patch.get("code") or "")
        suggestion = str(patch.get("suggestion") or patch.get("action") or "")
        edits.append(
            {
                "file_path": path,
                "summary": f"[{code}] {suggestion}".strip(),
                "rationale": f"Mechanic invariant drift {code}; provisional rebuild suggestion.",
                "anchor": None,
                "before_snippet": f"Current state flagged by {code}",
                "after_snippet": suggestion or f"Apply governed fix for {code}",
            }
        )
        rationale.append(f"{path}: address {code} via review-first patch.")

    plan_id = f"mechanic_{case_id}_{uuid4().hex[:10]}"
    resolved_goal = goal.strip() or f"Mechanic rebuild for case {case_id} ({len(patches)} patch(es))"
    return {
        "plan_id": plan_id,
        "goal": resolved_goal,
        "target_files": target_files,
        "edits": edits,
        "rationale": rationale,
        "risks": [
            {
                "level": "medium" if patches else "low",
                "message": "Mechanic patch plan is provisional; operator review required before apply.",
            }
        ],
        "test_suggestions": ["pytest tests/test_mechanic.py -q"],
        "changed_files": target_files,
        "verification_checklist": ["make mechanic-gate"],
        "unified_diff": "",
        "hunks": [],
        "hunk_count": 0,
        "review_complete": False,
        "status": "proposal_only",
        "preview_only": True,
        "mechanic_case_id": case_id,
        "mechanic_schema": str(mechanic_plan.get("schema_version") or "patch_plan.v1"),
        "safety_state": "dry_run_only",
    }


def create_apply_review(
    *,
    case_id: str,
    case_dir: Path,
    runtime_dir: Path | None = None,
    session_id: str | None = None,
    goal: str = "",
) -> dict[str, Any]:
    """Create patch review records only; never mutates customer repository."""
    mechanic_plan = load_mechanic_patch_plan(case_dir)
    review_plan = mechanic_patch_plan_to_review_plan(mechanic_plan, case_id=case_id, goal=goal)
    store_root = runtime_dir or (case_dir / "patch_reviews")
    store = PatchReviewStore(runtime_dir=store_root)
    review = store.create_review(session_id=session_id or case_id, patch_plan=review_plan)

    review_index_path = case_dir / "mechanic_patch_review_ids.json"
    review_ids = _load_review_ids(review_index_path)
    review_id = str(review.get("review_id") or review.get("id") or "")
    if review_id and review_id not in review_ids:
        review_ids.append(review_id)
        review_index_path.write_text(json.dumps({"review_ids": review_ids}, indent=2), encoding="utf-8")

    return {
        "mode": "apply-review",
        "case_id": case_id,
        "review_id": review_id,
        "review": review,
        "patch_plan": review_plan,
        "review_ids": review_ids,
        "safety_state": "dry_run_only",
        "claim_label": "asserted",
        "customer_repo_mutated": False,
    }


def _load_review_ids(path: Path) -> list[str]:
    if not path.is_file():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if isinstance(payload, list):
        return [str(item) for item in payload]
    if isinstance(payload, dict):
        return [str(item) for item in payload.get("review_ids") or []]
    return []
