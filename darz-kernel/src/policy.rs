use crate::types::{AxisName, AxisResult};

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct OiwlPolicy {
    pub max_drift_score: u32,
    pub max_entropy_delta: u32,
}

impl Default for OiwlPolicy {
    fn default() -> Self {
        Self {
            max_drift_score: 100,
            max_entropy_delta: 100,
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct AxisPolicy {
    pub allowed: Vec<AxisResult>,
}

impl AxisPolicy {
    pub fn pass(axis: AxisName) -> Self {
        Self {
            allowed: vec![AxisResult::pass(axis)],
        }
    }

    pub fn first_result(&self, axis: AxisName) -> AxisResult {
        self.allowed
            .first()
            .cloned()
            .unwrap_or_else(|| AxisResult::fail(axis, "axis policy has no admissible state"))
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct K32Policy {
    pub require_stable: bool,
}

impl Default for K32Policy {
    fn default() -> Self {
        Self {
            require_stable: true,
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct KernelPolicy {
    pub regime_id: String,
    pub oiwl: OiwlPolicy,
    pub k32: K32Policy,
    pub liscal: AxisPolicy,
    pub egl: AxisPolicy,
    pub sdaf: AxisPolicy,
    pub ssagl: AxisPolicy,
}

impl Default for KernelPolicy {
    fn default() -> Self {
        Self {
            regime_id: "darz-default-regime-v1".to_string(),
            oiwl: OiwlPolicy::default(),
            k32: K32Policy::default(),
            liscal: AxisPolicy::pass(AxisName::LiSCAL),
            egl: AxisPolicy::pass(AxisName::EGL),
            sdaf: AxisPolicy::pass(AxisName::SDAF),
            ssagl: AxisPolicy::pass(AxisName::SSAGL),
        }
    }
}
