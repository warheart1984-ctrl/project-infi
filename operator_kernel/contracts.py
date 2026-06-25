"""Shared contracts for lawful agent tasks (JSON-serializable)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class TaskConstraints(BaseModel):
    read_only: bool = False
    allow_shell: bool = False
    allow_git_commit: bool = False
    allow_network: bool = False
    max_steps: int = Field(default=12, ge=1, le=50)


class AgentProfile(BaseModel):
    id: str
    label: str
    description: str = ""
    constraints: TaskConstraints = Field(default_factory=TaskConstraints)


class CreateTaskRequest(BaseModel):
    goal: str
    workspace_root: str | None = None
    agent_id: str | None = None
    title: str | None = None
    constraints: TaskConstraints = Field(default_factory=TaskConstraints)


class CreateTaskResponse(BaseModel):
    task_id: str
    status: Literal["queued", "running", "awaiting_approval"] = "queued"


class AppendMessageRequest(BaseModel):
    text: str = Field(min_length=1)


class AppendMessageResponse(BaseModel):
    task_id: str
    status: Literal["queued", "running", "awaiting_approval"] = "running"


class PatchApprovalResponse(BaseModel):
    task_id: str
    status: str
    applied: bool = False
    path: str = ""
    message: str = ""


class RejectPatchRequest(BaseModel):
    reason: str = ""


class CancelTaskResponse(BaseModel):
    task_id: str
    status: Literal["cancelling", "cancelled"] = "cancelling"


class TaskDetailResponse(BaseModel):
    task_id: str
    meta: dict[str, Any] = Field(default_factory=dict)
    events: list[AgentEvent] = Field(default_factory=list)


class ApplyPatchBody(BaseModel):
    path: str
    diff: str
    root: str | None = None


class PatchPreviewBody(BaseModel):
    path: str
    old_content: str
    new_content: str


class TaskSummaryBody(BaseModel):
    summary: str


class ToolCall(BaseModel):
    id: str
    name: str
    args: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    id: str
    ok: bool
    data: dict[str, Any] | None = None
    error: str | None = None


class LawReceipt(BaseModel):
    tool_call_id: str | None = None
    capability: str = ""
    rsl: str = ""
    verdict: Literal["allow", "deny", "revise"] = "allow"
    reasons: list[str] = Field(default_factory=list)
    invariants: list[str] = Field(default_factory=list)


class AgentEvent(BaseModel):
    type: str
    task_id: str
    seq: int
    timestamp: str
    payload: dict[str, Any] = Field(default_factory=dict)


class LawfulAskRequest(BaseModel):
    intent: str
    context: dict[str, Any] = Field(default_factory=dict)
    tools: list[dict[str, Any]] = Field(default_factory=list)
    constraints: dict[str, Any] = Field(default_factory=dict)


class LawfulAskResponse(BaseModel):
    plan: dict[str, Any] = Field(default_factory=dict)
    steps: list[str] = Field(default_factory=list)
    tool_calls: list[ToolCall] = Field(default_factory=list)
    explanations: list[str] = Field(default_factory=list)
    receipts: list[dict[str, Any]] = Field(default_factory=list)
