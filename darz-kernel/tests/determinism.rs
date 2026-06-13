use darz_kernel::{
    AxisName, AxisResult, DefaultKernelValidator, ExecutionDecision, KernelPolicy,
    KernelValidator, TrajectoryMessage,
};

fn message() -> TrajectoryMessage {
    TrajectoryMessage::new(
        "traj-001",
        "omega-a",
        "lts-stable",
        "history-a",
        [("intent", "observe"), ("domain", "ai")],
    )
}

#[test]
fn same_message_and_policy_yield_same_decision() {
    let validator = DefaultKernelValidator::new(KernelPolicy::default());
    let first = validator.evaluate(&message());
    let second = validator.evaluate(&message());

    assert_eq!(first, second);
}

#[test]
fn oiwl_only_annotates_and_does_not_block() {
    let mut policy = KernelPolicy::default();
    policy.oiwl.max_drift_score = 0;
    policy.oiwl.max_entropy_delta = 0;

    let validator = DefaultKernelValidator::new(policy);
    let decision = validator.evaluate(&message());

    assert!(matches!(decision, ExecutionDecision::Execute(_)));
}

#[test]
fn failing_axis_blocks_with_axis_attribution() {
    let mut policy = KernelPolicy::default();
    policy.liscal.allowed = vec![AxisResult::fail(
        AxisName::LiSCAL,
        "forced ecological failure",
    )];

    let validator = DefaultKernelValidator::new(policy);
    let decision = validator.evaluate(&message());

    match decision {
        ExecutionDecision::Block(receipt) => {
            assert_eq!(receipt.failed_axes, vec![AxisName::LiSCAL]);
            assert_eq!(receipt.reasons, vec!["forced ecological failure"]);
        }
        ExecutionDecision::Execute(_) => panic!("LiSCAL failure must block execution"),
    }
}
