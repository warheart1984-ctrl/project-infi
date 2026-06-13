use crate::policy::AxisPolicy;
use crate::types::{AxisName, AxisResult, InvariantObject};

pub fn eval(_ig: &InvariantObject, policy: &AxisPolicy) -> AxisResult {
    policy.first_result(AxisName::LiSCAL)
}
