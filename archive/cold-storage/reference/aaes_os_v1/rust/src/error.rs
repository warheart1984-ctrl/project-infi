use serde::{Deserialize, Serialize};
use std::fmt::{Display, Formatter};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AaesError {
    pub code: String,
    pub message: String,
}

impl Display for AaesError {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}: {}", self.code, self.message)
    }
}

impl std::error::Error for AaesError {}

pub type AaesResult<T> = Result<T, AaesError>;

pub fn aaes_err(code: &str, message: impl Into<String>) -> AaesError {
    AaesError {
        code: code.to_string(),
        message: message.into(),
    }
}

pub fn not_implemented(surface: &str) -> AaesError {
    aaes_err("AAES_NOT_IMPLEMENTED", format!("{surface} is not implemented in stub"))
}
