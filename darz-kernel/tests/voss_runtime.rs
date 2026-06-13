use darz_kernel::{
    runtime::voss::{VossBinaryRuntime, VossCapabilityRequest},
    DefaultKernelValidator, KernelPolicy, KernelValidator, TrajectoryMessage,
};

#[test]
fn voss_runtime_executes_only_after_kernel_execute() {
    let validator = DefaultKernelValidator::new(KernelPolicy::default());
    let msg = TrajectoryMessage::new(
        "traj-voss",
        "omega-a",
        "lts-stable",
        "history",
        [("intent", "mutate"), ("domain", "binary-runtime")],
    );
    let decision = validator.evaluate(&msg);
    let runtime = VossBinaryRuntime::default();

    let receipt = runtime.dispatch(
        &decision,
        VossCapabilityRequest {
            binary_id: "bin:demo".to_string(),
            capability_id: "fs.write".to_string(),
            pre_state_hash: [1; 32],
            post_state_hash: [2; 32],
            cycle_id: "cycle-1".to_string(),
            lane_id: "lane:substrate".to_string(),
        },
    );

    assert!(receipt.executed);
    assert_eq!(receipt.disposition, "BOUND");
    assert_ne!(receipt.lambda_coupling_id, [0; 32]);
    assert_eq!(receipt.kernel_replay_hash, decision.replay_hash());
}

#[test]
fn voss_runtime_blocks_when_kernel_blocks() {
    let mut policy = KernelPolicy::default();
    policy.k32.require_stable = true;
    let validator = DefaultKernelValidator::new(policy);
    let msg = TrajectoryMessage::new(
        "traj-voss-block",
        "omega-a",
        "unstable",
        "history",
        std::iter::empty::<(&str, &str)>(),
    );
    let decision = validator.evaluate(&msg);

    let receipt = VossBinaryRuntime::default().dispatch(
        &decision,
        VossCapabilityRequest {
            binary_id: "bin:demo".to_string(),
            capability_id: "fs.write".to_string(),
            pre_state_hash: [1; 32],
            post_state_hash: [2; 32],
            cycle_id: "cycle-1".to_string(),
            lane_id: "lane:substrate".to_string(),
        },
    );

    assert!(!receipt.executed);
    assert_eq!(receipt.disposition, "REJECTED");
}
