from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any


WORKSPACE_ROOT_ENV = "AAIS_WORKSPACE_ROOT"
MAX_PREVIEW_BYTES = 256_000
MAX_EXCERPT_CHARS = 220


def _clip_text(value: str, limit: int = MAX_EXCERPT_CHARS) -> str:
    normalized = " ".join(str(value or "").split()).strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def _hash_text(value: str) -> str:
    return hashlib.sha256(str(value or "").encode("utf-8")).hexdigest()[:12]


class PatchExecutionPreview:
    """Preview whether a review-first patch still aligns with the current workspace."""

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
            raise ValueError("Patch preview path must stay inside the workspace root.") from exc
        return candidate, str(candidate.relative_to(root)).replace("\\", "/")

    def _read_text(self, target: Path) -> str:
        size_bytes = target.stat().st_size
        if size_bytes > MAX_PREVIEW_BYTES:
            raise ValueError(f"Workspace file `{target.name}` exceeded the preview byte limit.")
        try:
            return target.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"Workspace file `{target.name}` is not a UTF-8 text file.") from exc

    def _extract_excerpt(self, content: str, needle: str | None) -> str | None:
        text = str(content or "")
        token = str(needle or "").strip()
        if not text:
            return None
        if token:
            index = text.find(token)
            if index >= 0:
                start = max(0, index - 100)
                end = min(len(text), index + len(token) + 120)
                return _clip_text(text[start:end])
        return _clip_text(text[:MAX_EXCERPT_CHARS])

    def preview_plan(self, plan: dict[str, Any]) -> dict[str, Any]:
        root = self._resolve_workspace_root()
        edits = [dict(edit) for edit in list(plan.get("edits") or []) if isinstance(edit, dict)]
        hunks = [dict(hunk) for hunk in list(plan.get("hunks") or []) if isinstance(hunk, dict)]

        by_path: dict[str, dict[str, Any]] = {}
        for edit in edits:
            path = str(edit.get("file_path") or "").strip()
            if not path:
                continue
            entry = by_path.setdefault(path, {"edits": [], "hunks": []})
            entry["edits"].append(edit)
        for hunk in hunks:
            path = str(hunk.get("file_path") or "").strip()
            if not path:
                continue
            entry = by_path.setdefault(path, {"edits": [], "hunks": []})
            entry["hunks"].append(hunk)

        files: list[dict[str, Any]] = []
        counts = {"aligned": 0, "drifted": 0, "missing": 0, "unknown": 0}

        for path in list(plan.get("target_files") or []) or list(by_path.keys()):
            target, relative = self._resolve_target_path(path)
            scoped = by_path.get(path) or {"edits": [], "hunks": []}
            issues: list[str] = []
            if not target.exists():
                counts["missing"] += 1
                files.append(
                    {
                        "path": relative,
                        "exists": False,
                        "status": "missing",
                        "current_hash": None,
                        "matched_anchor": False,
                        "matched_before_snippet": False,
                        "hunk_count": len(scoped["hunks"]),
                        "issues": ["Workspace file is missing."],
                        "excerpt": None,
                    }
                )
                continue

            content = self._read_text(target)
            matched_anchor = False
            matched_before = False
            excerpt = None

            for edit in scoped["edits"]:
                anchor = str(edit.get("anchor") or "").strip()
                before_snippet = str(edit.get("before_snippet") or "").strip()
                if anchor and anchor in content:
                    matched_anchor = True
                    excerpt = excerpt or self._extract_excerpt(content, anchor)
                elif anchor:
                    issues.append("Anchor no longer matches the current file.")

                if before_snippet and before_snippet in content:
                    matched_before = True
                    excerpt = excerpt or self._extract_excerpt(content, before_snippet)
                elif before_snippet:
                    issues.append("Before snippet no longer matches the current file.")

            if matched_anchor or matched_before:
                status = "aligned"
                counts["aligned"] += 1
            elif scoped["edits"]:
                status = "drifted"
                counts["drifted"] += 1
            else:
                status = "unknown"
                counts["unknown"] += 1
                excerpt = excerpt or self._extract_excerpt(content, None)

            files.append(
                {
                    "path": relative,
                    "exists": True,
                    "status": status,
                    "current_hash": _hash_text(content),
                    "matched_anchor": matched_anchor,
                    "matched_before_snippet": matched_before,
                    "hunk_count": len(scoped["hunks"]),
                    "issues": issues,
                    "excerpt": excerpt or self._extract_excerpt(content, None),
                }
            )

        if counts["drifted"] or counts["missing"]:
            overall_status = "mixed" if counts["aligned"] else "drifted"
        elif counts["aligned"]:
            overall_status = "aligned"
        else:
            overall_status = "unknown"

        return {
            "plan_id": str(plan.get("plan_id") or "").strip(),
            "workspace_root": str(root),
            "status": overall_status,
            "ready_for_review": counts["drifted"] == 0 and counts["missing"] == 0,
            "counts": counts,
            "files": files,
            "summary": (
                f"Patch preview checked {len(files)} file(s): "
                f"{counts['aligned']} aligned, {counts['drifted']} drifted, "
                f"{counts['missing']} missing."
            ),
        }
