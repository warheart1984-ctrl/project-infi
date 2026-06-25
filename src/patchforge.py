from __future__ import annotations

import difflib
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.jarvis_types import PatchEdit, PatchHunk, PatchLineAction, PatchPlan, RiskNote


def _unique(values: list[str], *, limit: int | None = None) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        normalized = str(value or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
        if limit is not None and len(ordered) >= limit:
            break
    return ordered


class PatchForge:
    """Turn workspace analysis into a review-first patch proposal."""

    def build_patch_plan(
        self,
        request: str,
        workspace_context: dict[str, Any] | None,
        *,
        change_impact: dict[str, Any] | None = None,
        test_plan: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        goal = " ".join(str(request or "").split()).strip() or "Propose the smallest safe patch."
        workspace_context = workspace_context or {}
        change_impact = change_impact or {}
        test_plan = test_plan or {}

        target_files = _unique(
            list(change_impact.get("affected_files") or [])
            + [
                result.get("relative_path")
                for result in workspace_context.get("results", [])
                if result.get("relative_path")
            ]
            + [
                preview.get("relative_path")
                for preview in workspace_context.get("files", [])
                if preview.get("relative_path")
            ],
            limit=6,
        )

        preview_by_path = {
            preview.get("relative_path"): preview
            for preview in workspace_context.get("files", [])
            if preview.get("relative_path")
        }
        result_by_path = {
            result.get("relative_path"): result
            for result in workspace_context.get("results", [])
            if result.get("relative_path")
        }

        edits: list[PatchEdit] = []
        rationale: list[str] = []
        for path in target_files:
            preview = preview_by_path.get(path) or {}
            result = result_by_path.get(path) or {}
            snippet = str(preview.get("content") or result.get("snippet") or "").strip()
            anchor = str(result.get("snippet") or "").strip() or None
            summary = f"Adjust {Path(path).name} to address: {goal}"
            edit_rationale = "This file sits inside the impact cone for the requested change."
            edits.append(
                PatchEdit(
                    file_path=path,
                    summary=summary,
                    rationale=edit_rationale,
                    anchor=anchor,
                    before_snippet=snippet[:220] or None,
                    after_snippet=f"Review-first patch placeholder for {Path(path).name}.",
                )
            )
            rationale.append(f"{path}: keep the patch as small as possible around the current seam.")

        risks: list[RiskNote] = []
        risk_level = str(change_impact.get("risk_level") or "low")
        if risk_level == "high":
            risks.append(
                RiskNote(
                    level="high",
                    message="The impact cone touches broad integration seams; keep this proposal review-first.",
                )
            )
        elif risk_level == "medium":
            risks.append(
                RiskNote(
                    level="medium",
                    message="This patch crosses at least one integration seam and should be verified narrowly.",
                )
            )
        if not test_plan.get("recommended_tests"):
            risks.append(
                RiskNote(
                    level="medium" if target_files else "low",
                    message="No obvious focused test path was found yet.",
                )
            )

        plan = PatchPlan(
            plan_id=f"patch_{uuid4().hex}",
            goal=goal,
            target_files=target_files,
            edits=edits,
            rationale=rationale,
            risks=risks,
            test_suggestions=list(test_plan.get("recommended_tests") or change_impact.get("recommended_tests") or []),
            changed_files=list(target_files),
            verification_checklist=_unique(
                list(test_plan.get("recommended_tests") or [])
                + list(test_plan.get("regression_targets") or []),
                limit=10,
            ),
            unified_diff="",
            hunks=self._build_review_hunks(edits),
            hunk_count=0,
            review_complete=False,
            status="proposal_only",
            preview_only=True,
        )
        plan.hunk_count = len(plan.hunks)
        plan.review_complete = len(plan.hunks) == 0
        plan.unified_diff = self.render_unified_diff(plan.to_dict())
        from src.aais_ul.runtime import wrap_runtime_snapshot

        return wrap_runtime_snapshot(plan.to_dict())

    def render_unified_diff(self, plan: dict[str, Any]) -> str:
        """Render an honest proposal diff preview without mutating files."""
        lines = ["# PatchForge proposal-only diff preview"]
        for edit in plan.get("edits", []):
            path = str(edit.get("file_path") or "unknown")
            before_text = self._edit_before_preview(edit)
            after_text = self._edit_after_preview(edit)
            lines.append(_build_unified_diff(path, before_text, after_text))
            lines.append("")
        return "\n".join(lines).strip()

    def summarize_patch(self, plan: dict[str, Any]) -> dict[str, Any]:
        return {
            "plan_id": plan.get("plan_id"),
            "status": plan.get("status"),
            "goal": plan.get("goal"),
            "target_count": len(plan.get("target_files") or []),
            "changed_files": list(plan.get("changed_files") or []),
            "verification_checklist": list(plan.get("verification_checklist") or []),
            "hunk_count": len(plan.get("hunks") or []),
            "review_complete": bool(plan.get("review_complete")),
            "summary": (
                f"PatchForge proposed a review-first patch across "
                f"{len(plan.get('target_files') or [])} file(s) "
                f"and exposed {len(plan.get('hunks') or [])} review hunk(s)."
            ),
        }

    def _build_review_hunks(self, edits: list[PatchEdit]) -> list[PatchHunk]:
        hunks: list[PatchHunk] = []
        for edit in edits:
            file_hunks = _build_patch_hunks(
                edit.file_path,
                self._edit_before_preview(edit),
                self._edit_after_preview(edit),
            )
            for hunk in file_hunks:
                hunk.index = len(hunks)
                hunks.append(hunk)
        return hunks

    def _edit_before_preview(self, edit: PatchEdit | dict[str, Any]) -> str:
        return (
            str(
                (edit.anchor if isinstance(edit, PatchEdit) else edit.get("anchor"))
                or (edit.before_snippet if isinstance(edit, PatchEdit) else edit.get("before_snippet"))
                or "review current implementation"
            ).strip()
            + "\n"
        )

    def _edit_after_preview(self, edit: PatchEdit | dict[str, Any]) -> str:
        summary = str(edit.summary if isinstance(edit, PatchEdit) else edit.get("summary") or "").strip()
        rationale = str(edit.rationale if isinstance(edit, PatchEdit) else edit.get("rationale") or "").strip()
        after_snippet = str(
            (edit.after_snippet if isinstance(edit, PatchEdit) else edit.get("after_snippet"))
            or summary
            or "apply the smallest safe edit"
        ).strip()
        lines = [f"proposed change: {after_snippet}"]
        if rationale:
            lines.append(f"why: {rationale}")
        return "\n".join(lines).strip() + "\n"


def _build_unified_diff(path: str, before: str, after: str) -> str:
    diff_lines = difflib.unified_diff(
        before.splitlines(),
        after.splitlines(),
        fromfile=f"a/{path}",
        tofile=f"b/{path}",
        lineterm="",
    )
    return "\n".join(diff_lines) or f"No textual diff for `{path}`."


def _build_patch_hunks(path: str, before: str, after: str) -> list[PatchHunk]:
    before_lines = before.splitlines(keepends=True)
    after_lines = after.splitlines(keepends=True)
    matcher = difflib.SequenceMatcher(a=before_lines, b=after_lines)
    hunks: list[PatchHunk] = []
    for group in matcher.get_grouped_opcodes(3):
        changed = [tuple(opcode) for opcode in group if opcode[0] != "equal"]
        if not changed:
            continue
        before_start = group[0][1]
        before_end = group[-1][2]
        after_start = group[0][3]
        after_end = group[-1][4]
        additions = sum(
            j2 - j1 for tag, _, _, j1, j2 in changed if tag in {"replace", "insert"}
        )
        deletions = sum(
            i2 - i1 for tag, i1, i2, _, _ in changed if tag in {"replace", "delete"}
        )
        header = (
            f"@@ -{_format_unified_range(before_start, before_end - before_start)} "
            f"+{_format_unified_range(after_start, after_end - after_start)} @@"
        )
        diff_lines = [header]
        line_actions: list[PatchLineAction] = []
        for tag, i1, i2, j1, j2 in group:
            if tag in {"equal", "replace", "delete"}:
                diff_lines.extend(
                    f"{' ' if tag == 'equal' else '-'}{_display_diff_line(line)}"
                    for line in before_lines[i1:i2]
                )
            if tag in {"replace", "insert"}:
                diff_lines.extend(
                    f"+{_display_diff_line(line)}" for line in after_lines[j1:j2]
                )
            if tag != "equal":
                line_actions.extend(
                    _build_line_actions_for_opcode(
                        before_lines=before_lines,
                        after_lines=after_lines,
                        opcode=(tag, i1, i2, j1, j2),
                        start_index=len(line_actions),
                    )
                )
        hunks.append(
            PatchHunk(
                index=len(hunks),
                file_path=path,
                scope="proposal_preview",
                header=header,
                diff="\n".join(diff_lines),
                additions=additions,
                deletions=deletions,
                before_start=before_start + 1,
                before_count=before_end - before_start,
                after_start=after_start + 1,
                after_count=after_end - after_start,
                lines=line_actions,
                line_count=len(line_actions),
            )
        )
    return hunks


def _build_line_actions_for_opcode(
    *,
    before_lines: list[str],
    after_lines: list[str],
    opcode: tuple[str, int, int, int, int],
    start_index: int,
) -> list[PatchLineAction]:
    tag, i1, i2, j1, j2 = opcode
    previous_lines = before_lines[i1:i2]
    next_lines = after_lines[j1:j2]
    unit_count = max(len(previous_lines), len(next_lines))
    actions: list[PatchLineAction] = []
    for offset in range(unit_count):
        before_text = (
            _display_diff_line(previous_lines[offset])
            if offset < len(previous_lines)
            else None
        )
        after_text = (
            _display_diff_line(next_lines[offset])
            if offset < len(next_lines)
            else None
        )
        diff_parts: list[str] = []
        if before_text is not None:
            diff_parts.append(f"-{before_text}")
        if after_text is not None:
            diff_parts.append(f"+{after_text}")
        actions.append(
            PatchLineAction(
                index=start_index + offset,
                kind=tag,
                before_line_number=(i1 + offset + 1) if offset < len(previous_lines) else None,
                after_line_number=(j1 + offset + 1) if offset < len(next_lines) else None,
                before_text=before_text,
                after_text=after_text,
                diff="\n".join(diff_parts),
            )
        )
    return actions


def _display_diff_line(line: str) -> str:
    return line[:-1] if line.endswith("\n") else line


def _format_unified_range(start_index: int, length: int) -> str:
    start = start_index + 1
    if length == 0:
        return f"{max(start - 1, 0)},0"
    if length == 1:
        return str(start)
    return f"{start},{length}"
