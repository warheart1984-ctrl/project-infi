use crate::error::{not_implemented, AaesResult};

#[derive(Debug)]
pub struct UlsStub {
    pub surface_id: String,
}

impl Default for UlsStub {
    fn default() -> Self {
        Self {
            surface_id: "uls.v1.stub".to_string(),
        }
    }
}

impl UlsStub {
    pub fn normalize(&self, _raw: &serde_json::Value) -> AaesResult<serde_json::Value> {
        Err(not_implemented("ULS.normalize"))
    }
}
