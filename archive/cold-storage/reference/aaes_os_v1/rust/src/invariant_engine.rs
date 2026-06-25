use crate::error::{not_implemented, AaesResult};
use crate::governed_span::GovernedSpan;
use crate::types::{InvariantId, TraceEvent};

#[derive(Debug, Default)]
pub struct InvariantEngineStub;

impl InvariantEngineStub {
    pub fn check(
        &self,
        _event: &TraceEvent,
        _span: &GovernedSpan,
        _prior: &[TraceEvent],
    ) -> AaesResult<()> {
        Err(not_implemented("InvariantEngine.check"))
    }

    pub fn check_ids(
        &self,
        _ids: &[InvariantId],
        _event: &TraceEvent,
        _span: &GovernedSpan,
        _prior: &[TraceEvent],
    ) -> AaesResult<()> {
        Err(not_implemented("InvariantEngine.check_ids"))
    }
}
