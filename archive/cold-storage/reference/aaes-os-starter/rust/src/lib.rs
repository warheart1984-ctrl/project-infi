//! AAES-OS cognitive pipeline stubs — see docs/contracts/AAES_OS_INTERFACE_V1.md

use serde::{Deserialize, Serialize};
use serde_json::Value;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Scope {
    pub name: String,
    pub resources: Option<Value>,
    pub ttl_ms: Option<u64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Constraint {
    pub key: String,
    pub value: Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PolicySet {
    pub name: String,
    pub rules: Vec<Value>,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Stage {
    Perception,
    Deliberation,
    Planning,
    Action,
    Check,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InvariantResult {
    pub status: String,
    pub messages: Option<Vec<String>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PolicyResult {
    pub status: String,
    pub messages: Option<Vec<String>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AAESPlan {
    pub id: String,
    pub description: String,
    pub steps: Vec<Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ActionResult {
    pub action_id: String,
    pub status: String,
    pub details: Option<Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AAESRequest {
    pub id: String,
    pub actor_id: String,
    pub timestamp: String,
    pub channel: String,
    pub payload: Value,
    pub scope: Scope,
    pub constraints: Option<Vec<Constraint>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AAESContext {
    pub request: AAESRequest,
    pub trace_id: String,
    pub session: Value,
    pub policies: PolicySet,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AAESStep {
    pub step_id: String,
    pub stage: Stage,
    pub input: Value,
    pub output: Value,
    pub metadata: Option<Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AAESDecision {
    pub decision_id: String,
    pub rationale: String,
    pub selected_plan: AAESPlan,
    pub rejected_plans: Vec<AAESPlan>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AAESAction {
    pub action_id: String,
    pub target: String,
    pub parameters: Value,
    pub preconditions: Option<Value>,
    pub postconditions: Option<Value>,
}

pub trait PerceptionEngine {
    fn perceive(&self, req: AAESRequest) -> anyhow::Result<AAESContext>;
}

pub trait DeliberationEngine {
    fn deliberate(&self, ctx: &AAESContext) -> anyhow::Result<Vec<AAESPlan>>;
}

pub trait PlanningEngine {
    fn select_plan(&self, ctx: &AAESContext, plans: Vec<AAESPlan>) -> anyhow::Result<AAESDecision>;
}

pub trait ActionEngine {
    fn execute(&self, ctx: &AAESContext, decision: AAESDecision) -> anyhow::Result<Vec<ActionResult>>;
}

pub trait InvariantEngine {
    fn check(&self, stage: Stage, ctx: &AAESContext, step: &AAESStep) -> anyhow::Result<InvariantResult>;
}

#[derive(Debug, Clone, Copy)]
pub enum TargetType {
    Plan,
    Action,
}

pub trait PolicyEngine {
    fn evaluate(
        &self,
        target: TargetType,
        ctx: &AAESContext,
        item: &Value,
    ) -> anyhow::Result<PolicyResult>;
}

pub trait ExecutionModule {
    fn name(&self) -> &'static str;
    fn can_handle(&self, action: &AAESAction) -> bool;
    fn execute(&self, action: &AAESAction, ctx: &AAESContext) -> anyhow::Result<ActionResult>;
}

pub struct AAESOrchestrator<P, D, PL, A, I>
where
    P: PerceptionEngine,
    D: DeliberationEngine,
    PL: PlanningEngine,
    A: ActionEngine,
    I: InvariantEngine,
{
    pub perception: P,
    pub deliberation: D,
    pub planning: PL,
    pub action: A,
    pub invariants: I,
}

impl<P, D, PL, A, I> AAESOrchestrator<P, D, PL, A, I>
where
    P: PerceptionEngine,
    D: DeliberationEngine,
    PL: PlanningEngine,
    A: ActionEngine,
    I: InvariantEngine,
{
    pub fn handle(&self, req: AAESRequest) -> anyhow::Result<Vec<ActionResult>> {
        let ctx = self.perception.perceive(req)?;
        let plans = self.deliberation.deliberate(&ctx)?;
        let decision = self.planning.select_plan(&ctx, plans)?;
        self.action.execute(&ctx, decision)
    }
}
