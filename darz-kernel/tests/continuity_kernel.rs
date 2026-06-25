use std::sync::Arc;

use darz_kernel::darz_contract::{
    DARZReasoner, GovernedReasoningRequest, GovernedReasoningResponse, ReasoningStep,
};
use darz_kernel::darz_orchestrator::DARZOrchestrator;
use darz_kernel::{
    ContinuityEngine, DecisionPayload, EventPayload, EventType, InMemoryContinuityStore,
};

#[test]
fn serde_tagged_payload_round_trips_kind_and_data() {
    let payload = EventPayload::Decision(DecisionPayload {
        title: "Adopt continuity kernel".to_string(),
        rationale: "Typed events preserve governance evidence.".to_string(),
        chosen_architecture: None,
        alternatives: Vec::new(),
        evidence_refs: Vec::new(),
        governance_refs: Vec::new(),
        outcome_summary: None,
    });

    let json = serde_json::to_value(&payload).expect("serialize payload");
    assert_eq!(json["kind"], "Decision");
    assert_eq!(json["data"]["title"], "Adopt continuity kernel");

    let decoded: EventPayload = serde_json::from_value(json).expect("deserialize payload");
    assert_eq!(decoded, payload);
}

#[test]
fn continuity_engine_appends_typed_decision_with_lineage() {
    let engine = ContinuityEngine::new(InMemoryContinuityStore::default());
    let thread = engine
        .create_thread(None, Some("civilization-memory".to_string()))
        .expect("thread");

    let evidence = engine
        .append_event_typed(
            thread.id,
            EventType::Evidence,
            EventPayload::Evidence(darz_kernel::EvidencePayload {
                source: "test".to_string(),
                summary: "proof".to_string(),
                details: None,
            }),
            Vec::new(),
        )
        .expect("evidence");

    let decision = engine
        .append_decision(
            thread.id,
            DecisionPayload {
                title: "Bind DAR-Z to FOS".to_string(),
                rationale: "Continuity requires typed evidence.".to_string(),
                chosen_architecture: None,
                alternatives: Vec::new(),
                evidence_refs: vec![evidence.id],
                governance_refs: Vec::new(),
                outcome_summary: None,
            },
            vec![evidence.id],
        )
        .expect("decision");

    assert_eq!(decision.event_type, EventType::Decision);
    assert_eq!(decision.lineage, vec![evidence.id]);
    assert_eq!(engine.list_events_for_thread(thread.id).unwrap().len(), 2);
}

struct EchoReasoner;

impl DARZReasoner for EchoReasoner {
    fn run_governed_reasoning(
        &self,
        request: GovernedReasoningRequest,
    ) -> anyhow::Result<GovernedReasoningResponse> {
        Ok(GovernedReasoningResponse {
            proposals: Vec::new(),
            trace_steps: vec![ReasoningStep {
                description: format!("reasoned: {}", request.problem_statement),
                used_events: request.context_event_ids,
                produced_events: Vec::new(),
                invariants_checked: request.invariants,
                violations: Vec::new(),
            }],
            evidence_refs: Vec::new(),
            invariants_checked: vec!["inv:evidence-binding".to_string()],
            violations: Vec::new(),
        })
    }
}

#[test]
fn darz_orchestrator_runs_reasoner_and_records_decision() {
    let continuity = Arc::new(ContinuityEngine::new(InMemoryContinuityStore::default()));
    let thread = continuity.create_thread(None, Some("darz-fos".to_string())).unwrap();
    let orchestrator = DARZOrchestrator::new(continuity.clone(), Arc::new(EchoReasoner));

    let response = orchestrator
        .run(GovernedReasoningRequest {
            thread_id: thread.id,
            problem_statement: "Should DAR-Z emit typed traces?".to_string(),
            scope: "architecture".to_string(),
            time_horizon: Some("v1".to_string()),
            invariants: vec!["inv:evidence-binding".to_string()],
            constraints: Vec::new(),
            evidence_requirements: Vec::new(),
            context_event_ids: Vec::new(),
        })
        .unwrap();

    assert_eq!(response.trace_steps.len(), 1);

    let decision = orchestrator
        .record_decision_from_proposal(
            thread.id,
            "Record typed trace".to_string(),
            "FOS needs evidence-bearing continuity events.".to_string(),
            None,
            Vec::new(),
            Vec::new(),
            Vec::new(),
            Vec::new(),
        )
        .unwrap();

    assert_eq!(decision.event_type, EventType::Decision);
}
