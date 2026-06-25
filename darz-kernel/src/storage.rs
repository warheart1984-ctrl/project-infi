use std::collections::BTreeMap;
use std::sync::{Arc, Mutex};

use anyhow::Result;

use crate::types::{ContinuityEvent, ContinuityThread, EventId, ThreadId};

pub trait ContinuityStore: Send + Sync {
    fn create_thread(&self, thread: ContinuityThread) -> Result<()>;
    fn get_thread(&self, id: ThreadId) -> Result<Option<ContinuityThread>>;
    fn list_threads(&self) -> Result<Vec<ContinuityThread>>;
    fn append_event(&self, event: ContinuityEvent) -> Result<()>;
    fn get_event(&self, id: EventId) -> Result<Option<ContinuityEvent>>;
    fn list_events_for_thread(&self, thread_id: ThreadId) -> Result<Vec<ContinuityEvent>>;
}

#[derive(Clone, Default)]
pub struct InMemoryContinuityStore {
    threads: Arc<Mutex<BTreeMap<ThreadId, ContinuityThread>>>,
    events: Arc<Mutex<BTreeMap<EventId, ContinuityEvent>>>,
}

impl ContinuityStore for InMemoryContinuityStore {
    fn create_thread(&self, thread: ContinuityThread) -> Result<()> {
        self.threads
            .lock()
            .expect("continuity thread lock poisoned")
            .insert(thread.id, thread);
        Ok(())
    }

    fn get_thread(&self, id: ThreadId) -> Result<Option<ContinuityThread>> {
        Ok(self
            .threads
            .lock()
            .expect("continuity thread lock poisoned")
            .get(&id)
            .cloned())
    }

    fn list_threads(&self) -> Result<Vec<ContinuityThread>> {
        Ok(self
            .threads
            .lock()
            .expect("continuity thread lock poisoned")
            .values()
            .cloned()
            .collect())
    }

    fn append_event(&self, event: ContinuityEvent) -> Result<()> {
        self.events
            .lock()
            .expect("continuity event lock poisoned")
            .insert(event.id, event);
        Ok(())
    }

    fn get_event(&self, id: EventId) -> Result<Option<ContinuityEvent>> {
        Ok(self
            .events
            .lock()
            .expect("continuity event lock poisoned")
            .get(&id)
            .cloned())
    }

    fn list_events_for_thread(&self, thread_id: ThreadId) -> Result<Vec<ContinuityEvent>> {
        Ok(self
            .events
            .lock()
            .expect("continuity event lock poisoned")
            .values()
            .filter(|event| event.thread_id == thread_id)
            .cloned()
            .collect())
    }
}
