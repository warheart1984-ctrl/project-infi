use anyhow::Result;
use serde::{Deserialize, Serialize};

use crate::query::ContinuityEngine;
use crate::storage::ContinuityStore;
use crate::types::{ContinuityEvent, EventId, ThreadId};

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct GovernedReasoningRequest {
    pub thread_id: ThreadId,
    pub problem_statement: String,
    pub scope: String,
    pub time_horizon: Option<String>,
    pub invariants: Vec<String>,
    pub constraints: Vec<String>,
    pub evidence_requirements: Vec<String>,
    pub context_event_ids: Vec<EventId>,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct ReasoningStep {
    pub description: String,
    pub used_events: Vec<EventId>,
    pub produced_events: Vec<EventId>,
    pub invariants_checked: Vec<String>,
    pub violations: Vec<String>,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct GovernedReasoningResponse {
    pub proposals: Vec<EventId>,
    pub trace_steps: Vec<ReasoningStep>,
    pub evidence_refs: Vec<EventId>,
    pub invariants_checked: Vec<String>,
    pub violations: Vec<String>,
}

pub trait FOSContextProvider {
    fn get_events(&self, ids: &[EventId]) -> Result<Vec<ContinuityEvent>>;
    fn get_thread_events(&self, thread_id: ThreadId) -> Result<Vec<ContinuityEvent>>;
}

impl<S: ContinuityStore> FOSContextProvider for ContinuityEngine<S> {
    fn get_events(&self, ids: &[EventId]) -> Result<Vec<ContinuityEvent>> {
        let mut out = Vec::new();
        for id in ids {
            if let Some(event) = self.get_event(*id)? {
                out.push(event);
            }
        }
        Ok(out)
    }

    fn get_thread_events(&self, thread_id: ThreadId) -> Result<Vec<ContinuityEvent>> {
        self.list_events_for_thread(thread_id)
    }
}

pub trait DARZReasoner {
    fn run_governed_reasoning(
        &self,
        request: GovernedReasoningRequest,
    ) -> Result<GovernedReasoningResponse>;
}
