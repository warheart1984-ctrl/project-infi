use std::path::Path;
use std::sync::Arc;

use anyhow::Result;
use sled::{Db, Tree};

use crate::storage::ContinuityStore;
use crate::types::{ContinuityEvent, ContinuityThread, EventId, ThreadId};

pub struct SledStore {
    db: Arc<Db>,
}

impl SledStore {
    pub fn open(path: impl AsRef<Path>) -> Result<Self> {
        let db = sled::open(path)?;
        Ok(Self { db: Arc::new(db) })
    }

    fn threads_tree(&self) -> Result<Tree> {
        Ok(self.db.open_tree("threads")?)
    }

    fn events_tree(&self) -> Result<Tree> {
        Ok(self.db.open_tree("events")?)
    }
}

impl ContinuityStore for SledStore {
    fn create_thread(&self, thread: ContinuityThread) -> Result<()> {
        self.threads_tree()?
            .insert(thread.id.as_bytes(), bincode::serialize(&thread)?)?;
        Ok(())
    }

    fn get_thread(&self, id: ThreadId) -> Result<Option<ContinuityThread>> {
        Ok(self
            .threads_tree()?
            .get(id.as_bytes())?
            .map(|value| bincode::deserialize(&value))
            .transpose()?)
    }

    fn list_threads(&self) -> Result<Vec<ContinuityThread>> {
        let mut out = Vec::new();
        for item in self.threads_tree()?.iter() {
            let (_, value) = item?;
            out.push(bincode::deserialize(&value)?);
        }
        Ok(out)
    }

    fn append_event(&self, event: ContinuityEvent) -> Result<()> {
        self.events_tree()?
            .insert(event.id.as_bytes(), bincode::serialize(&event)?)?;
        Ok(())
    }

    fn get_event(&self, id: EventId) -> Result<Option<ContinuityEvent>> {
        Ok(self
            .events_tree()?
            .get(id.as_bytes())?
            .map(|value| bincode::deserialize(&value))
            .transpose()?)
    }

    fn list_events_for_thread(&self, thread_id: ThreadId) -> Result<Vec<ContinuityEvent>> {
        let mut out = Vec::new();
        for item in self.events_tree()?.iter() {
            let (_, value) = item?;
            let event: ContinuityEvent = bincode::deserialize(&value)?;
            if event.thread_id == thread_id {
                out.push(event);
            }
        }
        Ok(out)
    }
}
