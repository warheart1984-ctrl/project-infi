from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from src.jarvis_types import TestPlan


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


def _guess_test_candidates(path: str) -> list[str]:
    normalized = str(path or "").replace("\\", "/").strip("/")
    if not normalized:
        return []
    path_obj = Path(normalized)
    stem = path_obj.stem
    suffix = path_obj.suffix.lower()
    if suffix == ".py":
        project_root = path_obj.parts[0] if path_obj.parts else ""
        return _unique(
            [
                f"{project_root}/tests/test_{stem}.py" if project_root else f"tests/test_{stem}.py",
                f"{project_root}/tests/{stem}_test.py" if project_root else f"tests/{stem}_test.py",
            ]
        )
    if suffix in {".js", ".jsx", ".ts", ".tsx"}:
        base = normalized[: -len(suffix)]
        return _unique([f"{base}.test{suffix}", f"{base}.spec{suffix}"])
    return []


class TestOracle:
    """Choose the smallest useful verification loop for a proposed code change."""

    def suggest_test_plan(
        self,
        change_impact: dict[str, Any],
        workspace_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        impacted_files = list(change_impact.get("affected_files") or [])
        recommended_tests = list(change_impact.get("recommended_tests") or [])
        for path in impacted_files:
            recommended_tests.extend(_guess_test_candidates(path))
        recommended_tests = _unique(recommended_tests, limit=8)

        regression_targets = []
        for path in impacted_files:
            lowered = path.lower()
            if lowered.endswith("api.py") or "/routes/" in lowered:
                regression_targets.append(f"route regression around {path}")
            elif "/frontend/" in lowered or lowered.endswith((".jsx", ".tsx")):
                regression_targets.append(f"ui regression around {path}")
            elif lowered.endswith("jarvis_operator.py") or lowered.endswith("conversation_memory.py"):
                regression_targets.append(f"operator state regression around {path}")
        regression_targets = _unique(regression_targets, limit=6)

        missing_coverage = []
        if impacted_files and not recommended_tests:
            for path in impacted_files[:4]:
                missing_coverage.append(
                    {
                        "target": path,
                        "warning": "No obvious nearby tests were found; consider adding focused coverage.",
                    }
                )

        if workspace_context and not impacted_files:
            impacted_files = _unique(
                [
                    result.get("relative_path")
                    for result in workspace_context.get("results", [])
                    if result.get("relative_path")
                ],
                limit=6,
            )

        confidence = 0.55
        if recommended_tests:
            confidence += 0.2
        if change_impact.get("risk_level") == "low":
            confidence += 0.1
        if missing_coverage:
            confidence -= 0.15
        confidence = max(0.05, min(round(confidence, 2), 0.99))

        plan = TestPlan(
            plan_id=f"testplan_{uuid4().hex}",
            changed_files=impacted_files[:8],
            recommended_tests=recommended_tests,
            regression_targets=regression_targets,
            missing_coverage=missing_coverage,
            confidence_score=confidence,
            summary=(
                f"TestOracle recommends {len(recommended_tests)} focused tests"
                + (" and flagged missing coverage." if missing_coverage else ".")
            ),
        )
        return plan.to_dict()

    def detect_missing_coverage(
        self,
        change_impact: dict[str, Any],
        workspace_context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        return list(self.suggest_test_plan(change_impact, workspace_context).get("missing_coverage") or [])
