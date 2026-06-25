use crate::error::{not_implemented, AaesResult};
use crate::governed_span::GovernedSpan;
use crate::types::TraceEvent;

#[derive(Debug, Default)]
pub struct TraceBusStub {
    log: Vec<TraceEvent>,
    spans: std::collections::HashMap<String, GovernedSpan>,
}

impl TraceBusStub {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn validate(&self, event: &TraceEvent, span: &GovernedSpan) -> AaesResult<TraceEvent> {
        if event.span_id != span.span_id {
            return Err(crate::error::aaes_err(
                "AAES_SPAN_STATE_INVALID",
                "event.span_id does not match span",
            ));
        }
        Err(not_implemented("TraceBus.validate"))
    }

    pub fn append(&mut self, event: TraceEvent, span: &GovernedSpan) -> AaesResult<TraceEvent> {
        let _ = self.validate(&event, span)?;
        self.log.push(event.clone());
        self.spans.insert(span.span_id.clone(), span.clone());
        Ok(event)
    }

    pub fn get_events(&self, span_id: &str) -> Vec<TraceEvent> {
        self.log
            .iter()
            .filter(|event| event.span_id == span_id)
            .cloned()
            .collect()
    }

    pub fn validate_and_append(
        &mut self,
        event: TraceEvent,
        span: &GovernedSpan,
    ) -> AaesResult<TraceEvent> {
        self.append(event, span)
    }

    pub fn register_span(&mut self, span: GovernedSpan) {
        self.spans.insert(span.span_id.clone(), span);
    }
}
