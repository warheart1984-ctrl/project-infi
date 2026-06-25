use anyhow::Result;
use chrono::Utc;
use uuid::Uuid;

use crate::payload::{ArchitecturePayload, DecisionPayload, EventPayload};
use crate::storage::ContinuityStore;
use crate::types::{ContinuityEvent, ContinuityThread, EventId, EventType, ThreadId};

pub struct ContinuityEngine<S: ContinuityStore> {
    store: S,
}

impl<S: ContinuityStore> ContinuityEngine<S> {
    pub fn new(store: S) -> Self {
        Self { store }
    }

    pub fn create_thread(
        &self,
        parent: Option<ThreadId>,
        label: Option<String>,
    ) -> Result<ContinuityThread> {
        let thread = ContinuityThread {
            id: Uuid::new_v4(),
            parent,
            label,
            created_at: Utc::now(),
        };
        self.store.create_thread(thread.clone())?;
        Ok(thread)
    }

    pub fn get_event(&self, id: EventId) -> Result<Option<ContinuityEvent>> {
        self.store.get_event(id)
    }

    pub fn list_events_for_thread(&self, thread_id: ThreadId) -> Result<Vec<ContinuityEvent>> {
        self.store.list_events_for_thread(thread_id)
    }

    pub fn append_decision(
        &self,
        thread_id: ThreadId,
        payload: DecisionPayload,
        lineage: Vec<EventId>,
    ) -> Result<ContinuityEvent> {
        self.append_event_typed(
            thread_id,
            EventType::Decision,
            EventPayload::Decision(payload),
            lineage,
        )
    }

    pub fn append_architecture(
        &self,
        thread_id: ThreadId,
        payload: ArchitecturePayload,
        lineage: Vec<EventId>,
    ) -> Result<ContinuityEvent> {
        self.append_event_typed(
            thread_id,
            EventType::Architecture,
            EventPayload::Architecture(payload),
            lineage,
        )
    }

    pub fn append_event_typed(
        &self,
        thread_id: ThreadId,
        event_type: EventType,
        payload: EventPayload,
        lineage: Vec<EventId>,
    ) -> Result<ContinuityEvent> {
        let event = ContinuityEvent {
            id: Uuid::new_v4(),
            thread_id,
            event_type,
            payload,
            timestamp: Utc::now(),
            lineage,
        };
        self.store.append_event(event.clone())?;
        Ok(event)
    }
}
