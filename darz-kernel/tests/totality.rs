use darz_kernel::{
    AxisName, AxisResult, DefaultKernelValidator, ExecutionDecision, KernelPolicy,
    KernelValidator, TrajectoryMessage,
};

#[test]
fn empty_or_sparse_messages_still_return_a_decision() {
    let validator = DefaultKernelValidator::new(KernelPolicy::default());
    let msg = TrajectoryMessage::new("", "", "", "", std::iter::empty::<(&str, &str)>());

    let decision = validator.evaluate(&msg);

    assert!(matches!(
        decision,
        ExecutionDecision::Execute(_) | ExecutionDecision::Block(_)
    ));
}

#[test]
fn quarantine_or_denial_states_are_total_blocks() {
    for axis in [
        AxisName::K32,
        AxisName::LiSCAL,
        AxisName::EGL,
        AxisName::SDAF,
        AxisName::SSAGL,
    ] {
        let mut policy = KernelPolicy::default();
        match axis {
            AxisName::K32 => policy.k32.require_stable = true,
            AxisName::LiSCAL => {
                policy.liscal.allowed = vec![AxisResult::fail(axis, "not aligned")]
            }
            AxisName::EGL => policy.egl.allowed = vec![AxisResult::fail(axis, "not green")],
            AxisName::SDAF => policy.sdaf.allowed = vec![AxisResult::fail(axis, "not coherent")],
            AxisName::SSAGL => policy.ssagl.allowed = vec![AxisResult::fail(axis, "denied")],
            AxisName::OIWL | AxisName::Forge => unreachable!(),
        }

        let validator = DefaultKernelValidator::new(policy);
        let msg = TrajectoryMessage::new(
            format!("traj-{axis:?}"),
            "omega-a",
            "unstable",
            "history",
            std::iter::empty::<(&str, &str)>(),
        );

        assert!(matches!(validator.evaluate(&msg), ExecutionDecision::Block(_)));
    }
}
