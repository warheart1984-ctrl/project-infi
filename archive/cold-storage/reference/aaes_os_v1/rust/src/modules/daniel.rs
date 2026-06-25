use crate::error::{not_implemented, AaesResult};
use crate::orchestrator::AAESContext;
use crate::types::AAESAction;

#[derive(Debug)]
pub struct DanielModuleStub {
    pub module_id: String,
}

impl Default for DanielModuleStub {
    fn default() -> Self {
        Self {
            module_id: "daniel.cinematic.v1".to_string(),
        }
    }
}

impl DanielModuleStub {
    pub fn plan(&self, _context: &AAESContext) -> AaesResult<serde_json::Value> {
        Err(not_implemented("DanielModule.plan"))
    }

    pub fn execute(
        &self,
        _action: &AAESAction,
        _context: &AAESContext,
    ) -> AaesResult<serde_json::Value> {
        Err(not_implemented("DanielModule.execute"))
    }
}
