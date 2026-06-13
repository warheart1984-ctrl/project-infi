use crate::axes::{egl, forge, liscal, oiwl, sdaf, ssagl};
use crate::hash::hash_parts;
use crate::k32;
use crate::ledger::{audit_hash, AuditSink, InMemoryAuditSink};
use crate::policy::KernelPolicy;
use crate::types::{
    AxisName, AxisResult, BlockReceipt, ExecutionAudit, ExecutionDecision, ExecutionReceipt,
    InvariantObject, TrajectoryMessage,
};

pub trait KernelValidator {
    fn evaluate(&self, msg: &TrajectoryMessage) -> ExecutionDecision;
}

#[derive(Clone)]
pub struct DefaultKernelValidator {
    pub policy: KernelPolicy,
    audit_sink: InMemoryAuditSink,
}

impl DefaultKernelValidator {
    pub fn new(policy: KernelPolicy) -> Self {
        Self::with_audit_sink(policy, InMemoryAuditSink::default())
    }

    pub fn with_audit_sink(policy: KernelPolicy, audit_sink: InMemoryAuditSink) -> Self {
        Self { policy, audit_sink }
    }

    fn replay_hash(&self, msg: &TrajectoryMessage, ig: &InvariantObject) -> [u8; 32] {
        hash_parts(&[
            "replay",
            &msg.id,
            &format!("{:?}", msg),
            &format!("{:?}", ig),
            &format!("{:?}", self.policy),
        ])
    }
}

impl KernelValidator for DefaultKernelValidator {
    fn evaluate(&self, msg: &TrajectoryMessage) -> ExecutionDecision {
        let oiwl_report = oiwl::sense(msg, &self.policy.oiwl);
        let ig = forge::project(msg, &oiwl_report);
        let stable = k32::stable(&ig) || !self.policy.k32.require_stable;

        let mut axis_results = vec![
            if stable {
                AxisResult::pass(AxisName::K32)
            } else {
                AxisResult::fail(AxisName::K32, "invariant object is not replay stable")
            },
            liscal::eval(&ig, &self.policy.liscal),
            egl::eval(&ig, &self.policy.egl),
            sdaf::eval(&ig, &self.policy.sdaf),
            ssagl::eval(&ig, &self.policy.ssagl),
        ];
        axis_results.sort_by_key(AxisResult::axis);

        let replay_hash = self.replay_hash(msg, &ig);
        let failed_axes: Vec<AxisName> = axis_results
            .iter()
            .filter(|result| !result.is_pass())
            .map(AxisResult::axis)
            .collect();
        let reasons: Vec<String> = axis_results
            .iter()
            .flat_map(AxisResult::reasons)
            .collect();

        let (sequence, previous_hash) = self.audit_sink.next_sequence_and_previous_hash();
        let provisional_hash = hash_parts(&["receipt", &format!("{ig:?}"), &format!("{axis_results:?}")]);

        let mut decision = if failed_axes.is_empty() {
            ExecutionDecision::Execute(ExecutionReceipt {
                source_message_id: msg.id.clone(),
                invariant_id: ig.id,
                axis_results: axis_results.clone(),
                replay_hash,
                audit_hash: provisional_hash,
                regime_id: self.policy.regime_id.clone(),
            })
        } else {
            ExecutionDecision::Block(BlockReceipt {
                source_message_id: msg.id.clone(),
                invariant_id: ig.id,
                failed_axes,
                reasons,
                axis_results: axis_results.clone(),
                replay_hash,
                audit_hash: provisional_hash,
                regime_id: self.policy.regime_id.clone(),
            })
        };

        let final_audit_hash = audit_hash(sequence, previous_hash, &decision, &self.policy.regime_id);

        self.audit_sink.record(ExecutionAudit {
            sequence,
            ig_id: ig.id,
            stability: stable,
            axis_results,
            decision: decision.clone(),
            replay_hash,
            regime_id: self.policy.regime_id.clone(),
            previous_hash,
            audit_hash: final_audit_hash,
        });

        decision
    }
}
