use crate::error::{aaes_err, AaesResult};
use crate::types::{RuntimeContext, SpanState};

#[derive(Debug, Clone)]
pub struct GovernedSpan {
    pub span_id: String,
    pub parent_span_id: Option<String>,
    pub state: SpanState,
    pub runtime_context: Option<RuntimeContext>,
}

impl GovernedSpan {
    pub fn new(span_id: impl Into<String>, parent_span_id: Option<String>) -> Self {
        Self {
            span_id: span_id.into(),
            parent_span_id,
            state: SpanState::Init,
            runtime_context: None,
        }
    }

    pub fn close(&mut self) -> AaesResult<()> {
        if self.state != SpanState::Resulted && self.state != SpanState::Closed {
            return Err(aaes_err(
                "AAES_SPAN_STATE_INVALID",
                format!("cannot close span in state {:?}", self.state),
            ));
        }
        self.state = SpanState::Closed;
        Ok(())
    }
}
