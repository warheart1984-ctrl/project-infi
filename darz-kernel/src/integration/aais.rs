use crate::types::{ExecutionDecision, TrajectoryMessage};

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct AaisProposal {
    pub proposal_id: String,
    pub origin: String,
    pub lts_state: String,
    pub history: String,
    pub intent: String,
    pub domain: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct AaisMutationGate {
    pub proposal_id: String,
    pub allowed: bool,
    pub reason: String,
}

pub fn proposal_to_trajectory_message(proposal: &AaisProposal) -> TrajectoryMessage {
    TrajectoryMessage::new(
        proposal.proposal_id.clone(),
        proposal.origin.clone(),
        proposal.lts_state.clone(),
        proposal.history.clone(),
        [
            ("intent", proposal.intent.as_str()),
            ("domain", proposal.domain.as_str()),
        ],
    )
}

pub fn decision_to_mutation_gate(decision: &ExecutionDecision) -> AaisMutationGate {
    match decision {
        ExecutionDecision::Execute(receipt) => AaisMutationGate {
            proposal_id: receipt.source_message_id.clone(),
            allowed: true,
            reason: "kernel execution admitted".to_string(),
        },
        ExecutionDecision::Block(receipt) => AaisMutationGate {
            proposal_id: receipt.source_message_id.clone(),
            allowed: false,
            reason: receipt.reasons.join("; "),
        },
    }
}
