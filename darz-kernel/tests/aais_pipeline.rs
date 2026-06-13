use darz_kernel::{
    aais::{decision_to_mutation_gate, proposal_to_trajectory_message, AaisProposal},
    DefaultKernelValidator, ExecutionDecision, KernelPolicy, KernelValidator,
};

#[test]
fn aais_proposal_can_be_evaluated_and_mapped_to_mutation_gate() {
    let proposal = AaisProposal {
        proposal_id: "proposal-001".to_string(),
        origin: "aais".to_string(),
        lts_state: "stable".to_string(),
        history: "proposal history".to_string(),
        intent: "observe".to_string(),
        domain: "ai".to_string(),
    };

    let msg = proposal_to_trajectory_message(&proposal);
    let decision = DefaultKernelValidator::new(KernelPolicy::default()).evaluate(&msg);
    let gate = decision_to_mutation_gate(&decision);

    assert_eq!(msg.id, "proposal-001");
    assert_eq!(gate.proposal_id, "proposal-001");
    assert_eq!(gate.allowed, matches!(decision, ExecutionDecision::Execute(_)));
}
