use crate::error::{not_implemented, AaesResult};
use crate::governed_span::GovernedSpan;
use crate::trace_bus::TraceBusStub;
use crate::types::{AAESContext, AAESRequest, StepType};

#[derive(Debug)]
pub struct CognitiveOrchestratorStub {
    pub bus: TraceBusStub,
}

impl Default for CognitiveOrchestratorStub {
    fn default() -> Self {
        Self {
            bus: TraceBusStub::new(),
        }
    }
}

impl CognitiveOrchestratorStub {
    pub fn execute(&self, request: &AAESRequest) -> AaesResult<AAESContext> {
        let _ = request;
        Err(not_implemented("CognitiveOrchestrator.execute"))
    }
}

#[derive(Debug)]
pub struct AAESContext {
    pub request: AAESRequest,
    pub span: GovernedSpan,
    pub bus: TraceBusStub,
    pub steps_completed: Vec<StepType>,
}
