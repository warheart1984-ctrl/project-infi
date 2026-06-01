from __future__ import annotations

from datetime import datetime
from src.datetime_compat import UTC
import hashlib
import os
from pathlib import Path
from typing import Any


WORKSPACE_ROOT_ENV = "AAIS_WORKSPACE_ROOT"
DISALLOWED_AFTER_SNIPPET_MARKERS = (
    "review-first patch placeholder",
    "review first patch placeholder",
)
MAX_APPLY_BYTES = 256_000


def _hash_text(value: str) -> str:
    return hashlib.sha256(str(value or "").encode("utf-8")).hexdigest()[:12]


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


class PatchApplyEngine:
    """Apply a review-approved patch plan inside the workspace root."""

    def __init__(self, workspace_root: str | Path | None = None):
        self.workspace_root = Path(workspace_root) if workspace_root else None

    def configure_workspace_root(self, workspace_root: str | Path | None) -> None:
        self.workspace_root = Path(workspace_root) if workspace_root else None

    def _resolve_workspace_root(self) -> Path:
        if os.getenv(WORKSPACE_ROOT_ENV):
            return Path(os.getenv(WORKSPACE_ROOT_ENV)).expanduser().resolve()
        if self.workspace_root is not None:
            return self.workspace_root.expanduser().resolve()
        return Path(__file__).resolve().parents[2]

    def _resolve_target_path(self, relative_path: str) -> tuple[Path, str]:
        root = self._resolve_workspace_root()
        candidate = (root / str(relative_path or "")).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise ValueError("Patch apply path must stay inside the workspace root.") from exc
        return candidate, str(candidate.relative_to(root)).replace("\\", "/")

    def _read_text(self, target: Path) -> str:
        size_bytes = target.stat().st_size
        if size_bytes > MAX_APPLY_BYTES:
            raise ValueError(f"Workspace file `{target.name}` exceeded the apply byte limit.")
        try:
            return target.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"Workspace file `{target.name}` is not a UTF-8 text file.") from exc

    def _normalize_after_snippet(self, value: str, newline: str) -> str:
        normalized = str(value or "").replace("\r\n", "\n")
        if newline != "\n":
            normalized = normalized.replace("\n", newline)
        return normalized

    def _validate_review_gate(self, review: dict[str, Any]) -> None:
        gate = dict(review.get("apply_gate") or {})
        if gate.get("ready"):
            return
        blockers = [str(item).strip() for item in list(gate.get("blockers") or []) if str(item).strip()]
        if not blockers:
            blockers = ["Review approval is required before Jarvis can apply a patch."]
        raise ValueError(" ".join(blockers))

    def _validate_edit(self, edit: dict[str, Any], relative_path: str) -> None:
        after_snippet = str(edit.get("after_snippet") or "").strip()
        if not after_snippet:
            raise ValueError(f"Patch edit for `{relative_path}` is missing an after_snippet.")
        lowered = after_snippet.lower()
        if any(marker in lowered for marker in DISALLOWED_AFTER_SNIPPET_MARKERS):
            raise ValueError(
                f"Patch review `{relative_path}` still contains proposal placeholder text and cannot be applied."
            )
        if not str(edit.get("before_snippet") or "").strip() and not str(edit.get("anchor") or "").strip():
            raise ValueError(f"Patch edit for `{relative_path}` must include a before_snippet or anchor.")

    def apply_review(self, review: dict[str, Any]) -> dict[str, Any]:
        self._validate_review_gate(review)

        plan = dict(review.get("patch_plan") or {})
        edits = [dict(edit) for edit in list(plan.get("edits") or []) if isinstance(edit, dict)]
        if not edits:
            raise ValueError("Patch review does not contain any editable patch operations.")

        workspace_root = self._resolve_workspace_root()
        grouped_updates: dict[str, dict[str, Any]] = {}

        for edit in edits:
            relative_path = str(edit.get("file_path") or "").strip()
            if not relative_path:
                raise ValueError("Each patch edit must include file_path.")
            self._validate_edit(edit, relative_path)
            target_path, normalized_path = self._resolve_target_path(relative_path)
            if not target_path.exists():
                raise ValueError(f"Patch target `{normalized_path}` no longer exists.")
            current = grouped_updates.get(normalized_path)
            if current is None:
                original_text = self._read_text(target_path)
                grouped_updates[normalized_path] = {
                    "target_path": target_path,
                    "relative_path": normalized_path,
                    "original_text": original_text,
                    "working_text": original_text,
                    "edits": [],
                }
                current = grouped_updates[normalized_path]

            working_text = str(current["working_text"])
            newline = "\r\n" if "\r\n" in working_text else "\n"
            match_text = str(edit.get("before_snippet") or "").strip()
            if match_text and match_text not in working_text:
                match_text = ""
            if not match_text:
                match_text = str(edit.get("anchor") or "").strip()
            if not match_text:
                raise ValueError(f"Patch target `{normalized_path}` no longer matches the reviewed seam.")

            match_count = working_text.count(match_text)
            if match_count != 1:
                raise ValueError(
                    f"Patch target `{normalized_path}` matched {match_count} reviewed seams. "
                    "Jarvis will not apply an ambiguous patch."
                )

            replacement = self._normalize_after_snippet(str(edit.get("after_snippet") or ""), newline)
            current["working_text"] = working_text.replace(match_text, replacement, 1)
            current["edits"].append(
                {
                    "summary": str(edit.get("summary") or "").strip(),
                    "matched_text": match_text,
                    "replacement_hash": _hash_text(replacement),
                }
            )

        files: list[dict[str, Any]] = []
        for update in grouped_updates.values():
            original_text = str(update["original_text"])
            working_text = str(update["working_text"])
            if working_text == original_text:
                raise ValueError(
                    f"Patch apply for `{update['relative_path']}` produced no material change."
                )
            update["target_path"].write_text(working_text, encoding="utf-8")
            files.append(
                {
                    "path": update["relative_path"],
                    "before_hash": _hash_text(original_text),
                    "after_hash": _hash_text(working_text),
                    "edit_count": len(update["edits"]),
                    "edits": list(update["edits"]),
                }
            )

        rollback_notes = [
            "Jarvis did not silently revert files after apply. Review the changed files before any rollback.",
            "If this workspace is tracked in git, inspect git diff and restore only the specific changed files you want to undo.",
        ]
        rollback_notes.extend(
            [
                f"{item['path']}: restore against pre-apply hash {item['before_hash']} if you need to revert this file."
                for item in files
            ]
        )

        return {
            "review_id": str(review.get("id") or "").strip(),
            "workspace_root": str(workspace_root),
            "status": "applied",
            "applied_at": _utc_now(),
            "goal": str(review.get("goal") or plan.get("goal") or "").strip(),
            "changed_files": [item["path"] for item in files],
            "file_count": len(files),
            "files": files,
            "summary": (
                f"Applied {sum(item['edit_count'] for item in files)} reviewed edit(s) "
                f"across {len(files)} file(s)."
            ),
            "rollback_notes": rollback_notes,
        }
