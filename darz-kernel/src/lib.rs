//! DAR-Z sovereign deterministic execution kernel.
//!
//! The crate exposes one enforcement surface: [`KernelValidator::evaluate`].

pub mod axes;
mod hash;
pub mod k32;
pub mod ledger;
pub mod policy;
pub mod runtime;
pub mod scil;
pub mod scol;
pub mod types;
pub mod validator;

pub mod integration {
    pub mod aais;
    pub mod infinity;
}

pub use integration::aais;
pub use ledger::{AuditSink, InMemoryAuditSink};
pub use policy::{AxisPolicy, KernelPolicy, OiwlPolicy};
pub use types::{
    AxisName, AxisResult, BlockReceipt, ExecutionAudit, ExecutionDecision,
    ExecutionReceipt, ForgeProof, InvariantObject, OiwlReport, TrajectoryMessage,
};
pub use validator::{DefaultKernelValidator, KernelValidator};
