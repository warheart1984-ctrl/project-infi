from typing import Any, Literal
from pydantic import BaseModel, Field


class ExternalSuggestionAdmissionRequest(BaseModel):
    external_suggestion: dict[str, Any] | None = None
    external_suggestion_usage: str | None = Field(default=None, max_length=32)
    law_filter_applied: bool = False
    admitted_external_form: str | None = Field(default=None, max_length=4000)

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    session_id: str = Field(default="default", min_length=1, max_length=200)

class ChatResponse(BaseModel):
    response: str
    used_tool: str | None = None
    tool_result: str | None = None
    session_id: str
    cache_hit: bool = False
    route: str | None = None


class JarvisCompatContext(BaseModel):
    session_id: str | None = Field(default=None, min_length=1, max_length=200)
    system_prompt: str | None = Field(default=None, max_length=4000)
    persona_mode: str | None = Field(default=None, max_length=64)
    provider: str | None = Field(default=None, max_length=64)
    provider_mode: str | None = Field(default=None, max_length=64)
    requested_specialists: list[str] = Field(default_factory=list)
    requested_specialist_preset: str | None = Field(default=None, max_length=128)


class JarvisCompatRequest(BaseModel):
    input: str = Field(..., min_length=1, max_length=8000)
    context: JarvisCompatContext | None = None
    mode: Literal["normal", "think", "research"] = "normal"


class JarvisCompatResponse(BaseModel):
    output: str
    trace: dict[str, Any] | None = None
    status: Literal["ok", "degraded", "blocked"]
    session_id: str | None = None
    runtime: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    mode: Literal["normal", "think", "research"] | None = None


class JarvisMemoryWriteRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=8000)
    tags: list[str] = Field(default_factory=list)
    source: str | None = Field(default=None, max_length=128)
    category: str | None = Field(default=None, max_length=128)
    kind: str | None = Field(default=None, max_length=128)
    why: str | None = Field(default=None, max_length=4000)

class AgentRequest(BaseModel):
    goal: str = Field(..., min_length=1, max_length=8000)
    session_id: str = Field(default="default", min_length=1, max_length=200)

class AgentStep(BaseModel):
    step: str
    result: str
    critique: str

class AgentResponse(BaseModel):
    plan: list[str]
    steps: list[AgentStep]
    final_response: str
    session_id: str

class JobResponse(BaseModel):
    job_id: str
    status: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    result: dict | None = None
    error: str | None = None

class RagIndexRequest(BaseModel):
    path: str = Field(default="", max_length=500)

class RagIndexResponse(BaseModel):
    indexed_files: int
    indexed_chunks: int

class RagQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    session_id: str = Field(default="default", min_length=1, max_length=200)

class RagQueryResponse(BaseModel):
    answer: str
    chunks_used: list[str]


class WorkflowTrigger(BaseModel):
    id: str | None = None
    type: str
    label: str
    config: dict[str, str] = Field(default_factory=dict)


class WorkflowStep(BaseModel):
    id: str
    order: int
    type: str
    label: str
    config: dict[str, str] = Field(default_factory=dict)


class WorkflowEdge(BaseModel):
    id: str
    source: str
    sourceHandle: str | None = None
    target: str


class WorkflowPayload(BaseModel):
    name: str
    trigger: WorkflowTrigger | None = None
    steps: list[WorkflowStep] = Field(default_factory=list)
    edges: list[WorkflowEdge] = Field(default_factory=list)


class WorkflowDraftRequest(ExternalSuggestionAdmissionRequest):
    prompt: str = Field(default="", max_length=4000)
    name: str | None = Field(default=None, max_length=200)
    cisiv_stage: str | None = Field(default=None, max_length=32)


class WorkflowSaveRequest(ExternalSuggestionAdmissionRequest):
    id: str | None = None
    name: str = Field(..., min_length=1, max_length=200)
    nodes: list[dict[str, Any]] = Field(default_factory=list)
    edges: list[dict[str, Any]] = Field(default_factory=list)
    config: WorkflowPayload
    cisiv_stage: str | None = Field(default=None, max_length=32)


class WorkflowRunRequest(ExternalSuggestionAdmissionRequest):
    id: str = Field(..., min_length=1, max_length=200)
    trigger_data: dict[str, Any] | None = None
    cisiv_stage: str | None = Field(default=None, max_length=32)


class WorkflowSimulateRequest(ExternalSuggestionAdmissionRequest):
    id: str | None = None
    workflow: WorkflowPayload
    cisiv_stage: str | None = Field(default=None, max_length=32)


class WorkflowApprovalActionRequest(BaseModel):
    action: str = Field(..., pattern="^(approve|reject)$")


class OnboardingCompleteRequest(ExternalSuggestionAdmissionRequest):
    goal: str = Field(default="", max_length=4000)
    tools: list[str] = Field(default_factory=list)
    cisiv_stage: str | None = Field(default=None, max_length=32)


class AuthRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64, pattern=r"^[A-Za-z0-9._-]+$")
    password: str = Field(..., min_length=8, max_length=128)


class AuthLoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=128)


class AuthRefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1, max_length=4096)


class AuthUserResponse(BaseModel):
    id: str
    username: str
    role: str
    active: bool
    created_at: str
    updated_at: str


class AuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: AuthUserResponse


class AuthStatusResponse(BaseModel):
    auth_required: bool
    registration_allowed: bool
    authenticated: bool
    user: AuthUserResponse | None = None
