use crate::error::{not_implemented, AaesResult};
use crate::orchestrator::AAESContext;
use crate::types::{AAESDecision, AAESRequest};

#[derive(Debug, Default)]
pub struct PolicyEngineStub;

impl PolicyEngineStub {
    pub fn evaluate(
        &self,
        _request: &AAESRequest,
        _context: &AAESContext,
    ) -> AaesResult<AAESDecision> {
        Err(not_implemented("PolicyEngine.evaluate"))
    }
}
