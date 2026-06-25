use std::sync::Arc;

use anyhow::Result;

use crate::darz_contract::{DARZReasoner, GovernedReasoningRequest, GovernedReasoningResponse};
use crate::payload::{DecisionPayload, EventPayload};
use crate::query::ContinuityEngine;
use crate::storage::ContinuityStore;
use crate::types::{ContinuityEvent, EventId, EventType, ThreadId};

pub struct DARZOrchestrator<S: ContinuityStore, D: DARZReasoner> {
    pub continuity: Arc<ContinuityEngine<S>>,
    pub darz: Arc<D>,
}

impl<S: ContinuityStore, D: DARZReasoner> DARZOrchestrator<S, D> {
    pub fn new(continuity: Arc<ContinuityEngine<S>>, darz: Arc<D>) -> Self {
        Self { continuity, darz }
    }

    pub fn run(
        &self,
        request: GovernedReasoningRequest,
    ) -> Result<GovernedReasoningResponse> {
        self.darz.run_governed_reasoning(request)
    }

    #[allow(clippy::too_many_arguments)]
    pub fn record_decision_from_proposal(
        &self,
        thread_id: ThreadId,
        title: String,
        rationale: String,
        chosen_architecture: Option<EventId>,
        alternatives: Vec<EventId>,
        evidence_refs: Vec<EventId>,
        governance_refs: Vec<EventId>,
        lineage: Vec<EventId>,
    ) -> Result<ContinuityEvent> {
        let payload = DecisionPayload {
            title,
            rationale,
            chosen_architecture,
            alternatives,
            evidence_refs,
            governance_refs,
            outcome_summary: None,
        };

        self.continuity.append_event_typed(
            thread_id,
            EventType::Decision,
            EventPayload::Decision(payload),
            lineage,
        )
    }
}
