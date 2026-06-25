use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum EventType {
    Intent,
    Decision,
    Execution,
    Result,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum SpanState {
    Init,
    Intended,
    Decided,
    Executing,
    Resulted,
    Closed,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum Role {
    User,
    Runtime,
    Executor,
    Governor,
    Observer,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum StepType {
    Ingress,
    InvariantCheck,
    PolicyEval,
    ModuleRoute,
    Decide,
    Execute,
    Verify,
    EmitTrace,
    Complete,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum InvariantId {
    SiAuthenticity,
    SiTraceability,
    SiCausality,
    SiReconstructability,
    SiIdentity,
    SiReversibility,
    SiConstitution,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AuthEnvelope {
    pub role: Role,
    pub actor_id: String,
    pub signature_hash: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RuntimeContext {
    pub runtime_version: String,
    pub invariant_version: String,
    pub prompt_hash: String,
    pub decision_policy_hash: String,
    pub toolchain_hash: String,
    pub memory_snapshot_hash: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct TraceEvent {
    pub event_id: String,
    pub span_id: String,
    pub event_type: EventType,
    pub timestamp_utc: String,
    pub auth: AuthEnvelope,
    pub runtime_context: RuntimeContext,
    pub payload: serde_json::Value,
    pub parent_event_id: Option<String>,
    pub parent_span_id: Option<String>,
    pub event_hash: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReconstructedSpan {
    pub span_id: String,
    pub state: SpanState,
    pub events: Vec<TraceEvent>,
    pub runtime_context: RuntimeContext,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AAESRequest {
    pub trace_id: String,
    pub intent_payload: serde_json::Value,
    pub runtime_context: RuntimeContext,
    pub auth: AuthEnvelope,
    pub module_id: Option<String>,
    pub parent_span_id: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum StepStatus {
    Pending,
    Ok,
    Failed,
    Skipped,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AAESStep {
    pub step_type: StepType,
    pub step_id: String,
    pub input_hash: String,
    pub output_hash: Option<String>,
    pub status: StepStatus,
    pub error: Option<crate::error::AaesError>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AAESDecision {
    pub allowed: bool,
    pub reason_code: String,
    pub policy_hash: String,
    pub governor_auth: AuthEnvelope,
    pub payload: serde_json::Value,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AAESAction {
    pub action_id: String,
    pub tool: String,
    pub args: serde_json::Value,
    pub executor_auth: AuthEnvelope,
    pub rollback_possible: bool,
}
