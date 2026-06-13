use crate::hash::hash_parts;
use crate::types::{ExecutionDecision, Hash256};

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct VossCapabilityRequest {
    pub binary_id: String,
    pub capability_id: String,
    pub pre_state_hash: Hash256,
    pub post_state_hash: Hash256,
    pub cycle_id: String,
    pub lane_id: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct VossRuntimeReceipt {
    pub executed: bool,
    pub disposition: String,
    pub binary_id: String,
    pub capability_id: String,
    pub lambda_coupling_id: Hash256,
    pub debt_id: Hash256,
    pub scar_id: Hash256,
    pub cycle_id: String,
    pub lane_id: String,
    pub kernel_replay_hash: Hash256,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct VossBinaryRuntime {
    pub empty_debt_sentinel: Hash256,
}

impl Default for VossBinaryRuntime {
    fn default() -> Self {
        Self {
            empty_debt_sentinel: hash_parts(&["voss", "empty-debt"]),
        }
    }
}

impl VossBinaryRuntime {
    pub fn dispatch(
        &self,
        decision: &ExecutionDecision,
        request: VossCapabilityRequest,
    ) -> VossRuntimeReceipt {
        let kernel_replay_hash = decision.replay_hash();
        let allowed = matches!(decision, ExecutionDecision::Execute(_));
        let disposition = if allowed { "BOUND" } else { "REJECTED" }.to_string();
        let lambda_coupling_id = if allowed {
            derive_lambda_coupling_id(&request, kernel_replay_hash)
        } else {
            [0; 32]
        };
        let scar_id = if allowed {
            hash_parts(&[
                "scar",
                &format!("{lambda_coupling_id:?}"),
                &disposition,
                &request.cycle_id,
            ])
        } else {
            [0; 32]
        };

        VossRuntimeReceipt {
            executed: allowed,
            disposition,
            binary_id: request.binary_id,
            capability_id: request.capability_id,
            lambda_coupling_id,
            debt_id: self.empty_debt_sentinel,
            scar_id,
            cycle_id: request.cycle_id,
            lane_id: request.lane_id,
            kernel_replay_hash,
        }
    }
}

fn derive_lambda_coupling_id(request: &VossCapabilityRequest, kernel_replay_hash: Hash256) -> Hash256 {
    hash_parts(&[
        "lambda",
        &request.binary_id,
        &request.capability_id,
        &format!("{:?}", request.pre_state_hash),
        &format!("{:?}", request.post_state_hash),
        &format!("{kernel_replay_hash:?}"),
    ])
}
