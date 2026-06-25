use std::collections::BTreeMap;
use std::fmt::Debug;

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::payload::EventPayload;

pub type Hash256 = [u8; 32];
pub type MetaMap = BTreeMap<String, String>;
pub type ThreadId = Uuid;
pub type EventId = Uuid;

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq, Serialize, Deserialize)]
pub enum EventType {
    Concept,
    Invariant,
    Architecture,
    Governance,
    Decision,
    Evidence,
    Note,
    Custom,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct ContinuityThread {
    pub id: ThreadId,
    pub parent: Option<ThreadId>,
    pub label: Option<String>,
    pub created_at: DateTime<Utc>,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct ContinuityEvent {
    pub id: EventId,
    pub thread_id: ThreadId,
    pub event_type: EventType,
    pub payload: EventPayload,
    pub timestamp: DateTime<Utc>,
    pub lineage: Vec<EventId>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct TrajectoryMessage {
    pub id: String,
    pub origin: String,
    pub lts_state: String,
    pub history: String,
    pub metadata: MetaMap,
}

impl TrajectoryMessage {
    pub fn new<K, V, I>(
        id: impl Into<String>,
        origin: impl Into<String>,
        lts_state: impl Into<String>,
        history: impl Into<String>,
        metadata: I,
    ) -> Self
    where
        K: Into<String>,
        V: Into<String>,
        I: IntoIterator<Item = (K, V)>,
    {
        Self {
            id: id.into(),
            origin: origin.into(),
            lts_state: lts_state.into(),
            history: history.into(),
            metadata: metadata
                .into_iter()
                .map(|(key, value)| (key.into(), value.into()))
                .collect(),
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct OiwlReport {
    pub drift_score: u32,
    pub entropy_delta: u32,
    pub contamination_flags: Vec<String>,
    pub annotations: MetaMap,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ForgeProof {
    pub algorithm: String,
    pub input_hash: Hash256,
    pub oiwl_hash: Hash256,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct InvariantObject {
    pub id: Hash256,
    pub class_name: String,
    pub payload_hash: Hash256,
    pub forge_proof: ForgeProof,
    pub annotations: MetaMap,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum AxisName {
    OIWL,
    Forge,
    K32,
    LiSCAL,
    EGL,
    SDAF,
    SSAGL,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum AxisResult {
    Pass(AxisName),
    Fail {
        axis: AxisName,
        reasons: Vec<String>,
    },
}

impl AxisResult {
    pub fn pass(axis: AxisName) -> Self {
        Self::Pass(axis)
    }

    pub fn fail(axis: AxisName, reason: impl Into<String>) -> Self {
        Self::Fail {
            axis,
            reasons: vec![reason.into()],
        }
    }

    pub fn axis(&self) -> AxisName {
        match self {
            Self::Pass(axis) => *axis,
            Self::Fail { axis, .. } => *axis,
        }
    }

    pub fn is_pass(&self) -> bool {
        matches!(self, Self::Pass(_))
    }

    pub fn reasons(&self) -> Vec<String> {
        match self {
            Self::Pass(_) => Vec::new(),
            Self::Fail { reasons, .. } => reasons.clone(),
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ExecutionReceipt {
    pub source_message_id: String,
    pub invariant_id: Hash256,
    pub axis_results: Vec<AxisResult>,
    pub replay_hash: Hash256,
    pub audit_hash: Hash256,
    pub regime_id: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BlockReceipt {
    pub source_message_id: String,
    pub invariant_id: Hash256,
    pub failed_axes: Vec<AxisName>,
    pub reasons: Vec<String>,
    pub axis_results: Vec<AxisResult>,
    pub replay_hash: Hash256,
    pub audit_hash: Hash256,
    pub regime_id: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum ExecutionDecision {
    Execute(ExecutionReceipt),
    Block(BlockReceipt),
}

impl ExecutionDecision {
    pub fn replay_hash(&self) -> Hash256 {
        match self {
            Self::Execute(receipt) => receipt.replay_hash,
            Self::Block(receipt) => receipt.replay_hash,
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ExecutionAudit {
    pub sequence: u64,
    pub ig_id: Hash256,
    pub stability: bool,
    pub axis_results: Vec<AxisResult>,
    pub decision: ExecutionDecision,
    pub replay_hash: Hash256,
    pub regime_id: String,
    pub previous_hash: Hash256,
    pub audit_hash: Hash256,
}
