use crate::scil::NormalizedInvariantObject;
use crate::types::Hash256;

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ExecutionPlan {
    pub invariant_id: Hash256,
    pub steps: Vec<String>,
}

pub fn compose(normalized: &NormalizedInvariantObject) -> ExecutionPlan {
    ExecutionPlan {
        invariant_id: normalized.ig.id,
        steps: vec!["kernel-authorized-runtime-dispatch".to_string()],
    }
}
