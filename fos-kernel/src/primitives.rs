use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

pub type ThreadId = Uuid;
pub type EventId = Uuid;

#[derive(Clone, Debug, Eq, Hash, PartialEq, Serialize, Deserialize)]
pub enum EventType {
    Concept,
    Invariant,
    Architecture,
    Governance,
    Decision,
    Evidence,
    Note,
    Custom(String),
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
    pub payload: serde_json::Value,
    pub timestamp: DateTime<Utc>,
    pub lineage: Vec<EventId>,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct MemoryObjectRef {
    pub event_id: EventId,
    pub event_type: EventType,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct FOSMemoryObject {
    pub id: EventId,
    pub object_type: EventType,
    pub definition: String,
    pub evidence_refs: Vec<EventId>,
    pub lineage: Vec<EventId>,
    pub version: String,
    pub continuity_thread: ThreadId,
}
