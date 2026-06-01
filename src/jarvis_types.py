from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


RiskLevel = Literal["low", "medium", "high"]


@dataclass(slots=True)
class WorkspaceRef:
    file_path: str
    symbol: str | None = None
    line_start: int | None = None
    line_end: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RiskNote:
    level: RiskLevel
    message: str
    target: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ActionRecord:
    action_id: str
    session_id: str
    run_id: str | None
    kind: str
    status: str
    created_at: str
    updated_at: str
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PatchEdit:
    file_path: str
    summary: str
    rationale: str
    anchor: str | None = None
    before_snippet: str | None = None
    after_snippet: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PatchLineAction:
    index: int
    kind: str
    before_line_number: int | None
    after_line_number: int | None
    before_text: str | None
    after_text: str | None
    diff: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PatchHunk:
    index: int
    file_path: str
    scope: str
    header: str
    diff: str
    additions: int
    deletions: int
    before_start: int
    before_count: int
    after_start: int
    after_count: int
    lines: list[PatchLineAction] = field(default_factory=list)
    line_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["lines"] = [line.to_dict() for line in self.lines]
        payload["line_count"] = self.line_count or len(self.lines)
        return payload


@dataclass(slots=True)
class PatchPlan:
    plan_id: str
    goal: str
    target_files: list[str]
    edits: list[PatchEdit]
    hunks: list[PatchHunk] = field(default_factory=list)
    rationale: list[str] = field(default_factory=list)
    risks: list[RiskNote] = field(default_factory=list)
    test_suggestions: list[str] = field(default_factory=list)
    changed_files: list[str] = field(default_factory=list)
    verification_checklist: list[str] = field(default_factory=list)
    unified_diff: str = ""
    hunk_count: int = 0
    review_complete: bool = True
    status: str = "proposal_only"
    preview_only: bool = True

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["edits"] = [edit.to_dict() for edit in self.edits]
        payload["hunks"] = [hunk.to_dict() for hunk in self.hunks]
        payload["risks"] = [risk.to_dict() for risk in self.risks]
        payload["hunk_count"] = self.hunk_count or len(self.hunks)
        return payload


@dataclass(slots=True)
class ChangeImpact:
    impact_id: str
    focus_path: str | None
    symbol: str | None
    affected_files: list[str]
    affected_symbols: list[dict[str, Any]] = field(default_factory=list)
    recommended_tests: list[str] = field(default_factory=list)
    risk_level: RiskLevel = "low"
    integration_seams: list[dict[str, Any]] = field(default_factory=list)
    repo_map: dict[str, Any] = field(default_factory=dict)
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class TestPlan:
    __test__ = False

    plan_id: str
    changed_files: list[str]
    recommended_tests: list[str] = field(default_factory=list)
    regression_targets: list[str] = field(default_factory=list)
    missing_coverage: list[dict[str, Any]] = field(default_factory=list)
    confidence_score: float = 0.0
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ProviderDecision:
    decision_id: str
    engine_path: str
    fallback_path: str
    confidence: float
    summary: str
    hidden_reason: str
    route_kind: str = "primary"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
