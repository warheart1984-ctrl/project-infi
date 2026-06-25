//! DAR-Z sovereign deterministic execution kernel.
//!
//! The crate exposes one enforcement surface: [`KernelValidator::evaluate`].

pub mod axes;
pub mod darz_contract;
pub mod darz_orchestrator;
mod hash;
pub mod k32;
pub mod ledger;
pub mod payload;
pub mod policy;
pub mod runtime;
pub mod scil;
pub mod scol;
pub mod storage;
#[cfg(feature = "sled-store")]
pub mod storage_sled;
#[cfg(feature = "sqlite-store")]
pub mod storage_sqlite;
pub mod types;
pub mod validator;
pub mod query;

pub mod integration {
    pub mod aais;
    pub mod infinity;
}

pub use integration::aais;
pub use ledger::{AuditSink, InMemoryAuditSink};
pub use payload::{
    ArchitecturePayload, ConceptPayload, DecisionPayload, EventPayload, EvidencePayload,
    GovernancePayload, InvariantPayload, NotePayload,
};
pub use policy::{AxisPolicy, KernelPolicy, OiwlPolicy};
pub use query::ContinuityEngine;
pub use storage::{ContinuityStore, InMemoryContinuityStore};
pub use types::{
    AxisName, AxisResult, BlockReceipt, ContinuityEvent, ContinuityThread, EventId, EventType,
    ExecutionAudit, ExecutionDecision, ExecutionReceipt, ForgeProof, InvariantObject, OiwlReport,
    ThreadId, TrajectoryMessage,
};
pub use validator::{DefaultKernelValidator, KernelValidator};
