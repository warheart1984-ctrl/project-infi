use darz_kernel::{
    DefaultKernelValidator, ExecutionDecision, InMemoryAuditSink, KernelPolicy, KernelValidator,
    TrajectoryMessage,
};

#[test]
fn audit_records_are_append_only_and_replay_verifiable() {
    let sink = InMemoryAuditSink::default();
    let validator = DefaultKernelValidator::with_audit_sink(KernelPolicy::default(), sink.clone());
    let msg = TrajectoryMessage::new(
        "traj-replay",
        "omega-a",
        "lts-stable",
        "history",
        [("intent", "observe")],
    );

    let first = validator.evaluate(&msg);
    let second = validator.evaluate(&msg);
    let records = sink.records();

    assert_eq!(records.len(), 2);
    assert_eq!(records[0].sequence, 0);
    assert_eq!(records[1].sequence, 1);
    assert!(sink.verify_chain());

    match (first, second) {
        (ExecutionDecision::Execute(a), ExecutionDecision::Execute(b)) => {
            assert_eq!(a.replay_hash, b.replay_hash);
        }
        (ExecutionDecision::Block(a), ExecutionDecision::Block(b)) => {
            assert_eq!(a.replay_hash, b.replay_hash);
        }
        _ => panic!("same input and policy must not diverge"),
    }
}
