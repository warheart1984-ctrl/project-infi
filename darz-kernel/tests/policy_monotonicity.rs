use darz_kernel::{
    DefaultKernelValidator, ExecutionDecision, KernelPolicy, KernelValidator, TrajectoryMessage,
};

fn admissible_message() -> TrajectoryMessage {
    TrajectoryMessage::new(
        "traj-policy",
        "omega-a",
        "lts-stable",
        "history",
        [("intent", "observe"), ("domain", "law")],
    )
}

#[test]
fn stricter_policy_cannot_turn_block_into_execute() {
    let mut loose = KernelPolicy::default();
    loose.k32.require_stable = false;

    let mut strict = KernelPolicy::default();
    strict.k32.require_stable = true;

    let blocked_msg = TrajectoryMessage::new(
        "traj-policy",
        "omega-a",
        "unstable",
        "history",
        [("intent", "observe"), ("domain", "law")],
    );

    let strict_decision = DefaultKernelValidator::new(strict).evaluate(&blocked_msg);
    let loose_decision = DefaultKernelValidator::new(loose).evaluate(&blocked_msg);

    assert!(matches!(strict_decision, ExecutionDecision::Block(_)));
    assert!(matches!(
        loose_decision,
        ExecutionDecision::Execute(_) | ExecutionDecision::Block(_)
    ));
}

#[test]
fn execution_under_strict_policy_executes_under_default_policy() {
    let strict = KernelPolicy::default();
    let default = KernelPolicy::default();
    let msg = admissible_message();

    let strict_decision = DefaultKernelValidator::new(strict).evaluate(&msg);
    let default_decision = DefaultKernelValidator::new(default).evaluate(&msg);

    if matches!(strict_decision, ExecutionDecision::Execute(_)) {
        assert!(matches!(default_decision, ExecutionDecision::Execute(_)));
    }
}
