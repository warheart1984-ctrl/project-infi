use std::sync::{Arc, Mutex};

use anyhow::Result;
use rusqlite::{params, Connection};

use crate::payload::EventPayload;
use crate::storage::ContinuityStore;
use crate::types::{ContinuityEvent, ContinuityThread, EventId, EventType, ThreadId};

pub struct SqliteStore {
    conn: Arc<Mutex<Connection>>,
}

impl SqliteStore {
    pub fn open(path: &str) -> Result<Self> {
        let conn = Connection::open(path)?;
        let store = Self {
            conn: Arc::new(Mutex::new(conn)),
        };
        store.init_schema()?;
        Ok(store)
    }

    fn init_schema(&self) -> Result<()> {
        self.conn.lock().expect("sqlite lock poisoned").execute_batch(
            r#"
            CREATE TABLE IF NOT EXISTS threads (
                id BLOB PRIMARY KEY,
                parent BLOB NULL,
                label TEXT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS events (
                id BLOB PRIMARY KEY,
                thread_id BLOB NOT NULL,
                event_type TEXT NOT NULL,
                payload BLOB NOT NULL,
                timestamp TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS lineage (
                event_id BLOB NOT NULL,
                parent_id BLOB NOT NULL
            );
            "#,
        )?;
        Ok(())
    }
}

impl ContinuityStore for SqliteStore {
    fn create_thread(&self, thread: ContinuityThread) -> Result<()> {
        self.conn.lock().expect("sqlite lock poisoned").execute(
            "INSERT INTO threads (id, parent, label, created_at) VALUES (?1, ?2, ?3, ?4)",
            params![
                thread.id.as_bytes().to_vec(),
                thread.parent.map(|parent| parent.as_bytes().to_vec()),
                thread.label,
                thread.created_at.to_rfc3339(),
            ],
        )?;
        Ok(())
    }

    fn get_thread(&self, id: ThreadId) -> Result<Option<ContinuityThread>> {
        let conn = self.conn.lock().expect("sqlite lock poisoned");
        let mut stmt = conn.prepare("SELECT id, parent, label, created_at FROM threads WHERE id = ?1")?;
        let mut rows = stmt.query(params![id.as_bytes().to_vec()])?;
        if let Some(row) = rows.next()? {
            let id_bytes: Vec<u8> = row.get(0)?;
            let parent_bytes: Option<Vec<u8>> = row.get(1)?;
            let label: Option<String> = row.get(2)?;
            let created_at: String = row.get(3)?;
            Ok(Some(ContinuityThread {
                id: uuid::Uuid::from_slice(&id_bytes)?,
                parent: parent_bytes
                    .map(|bytes| uuid::Uuid::from_slice(&bytes))
                    .transpose()?,
                label,
                created_at: created_at.parse()?,
            }))
        } else {
            Ok(None)
        }
    }

    fn list_threads(&self) -> Result<Vec<ContinuityThread>> {
        let conn = self.conn.lock().expect("sqlite lock poisoned");
        let mut stmt = conn.prepare("SELECT id, parent, label, created_at FROM threads")?;
        let rows = stmt.query_map([], |row| {
            let id_bytes: Vec<u8> = row.get(0)?;
            let parent_bytes: Option<Vec<u8>> = row.get(1)?;
            let label: Option<String> = row.get(2)?;
            let created_at: String = row.get(3)?;
            Ok((id_bytes, parent_bytes, label, created_at))
        })?;

        let mut out = Vec::new();
        for row in rows {
            let (id_bytes, parent_bytes, label, created_at) = row?;
            out.push(ContinuityThread {
                id: uuid::Uuid::from_slice(&id_bytes)?,
                parent: parent_bytes
                    .map(|bytes| uuid::Uuid::from_slice(&bytes))
                    .transpose()?,
                label,
                created_at: created_at.parse()?,
            });
        }
        Ok(out)
    }

    fn append_event(&self, event: ContinuityEvent) -> Result<()> {
        let conn = self.conn.lock().expect("sqlite lock poisoned");
        conn.execute(
            "INSERT INTO events (id, thread_id, event_type, payload, timestamp) VALUES (?1, ?2, ?3, ?4, ?5)",
            params![
                event.id.as_bytes().to_vec(),
                event.thread_id.as_bytes().to_vec(),
                format!("{:?}", event.event_type),
                bincode::serialize(&event.payload)?,
                event.timestamp.to_rfc3339(),
            ],
        )?;
        for parent in &event.lineage {
            conn.execute(
                "INSERT INTO lineage (event_id, parent_id) VALUES (?1, ?2)",
                params![event.id.as_bytes().to_vec(), parent.as_bytes().to_vec()],
            )?;
        }
        Ok(())
    }

    fn get_event(&self, id: EventId) -> Result<Option<ContinuityEvent>> {
        let conn = self.conn.lock().expect("sqlite lock poisoned");
        let mut stmt = conn.prepare(
            "SELECT id, thread_id, event_type, payload, timestamp FROM events WHERE id = ?1",
        )?;
        let mut rows = stmt.query(params![id.as_bytes().to_vec()])?;
        if let Some(row) = rows.next()? {
            let id_bytes: Vec<u8> = row.get(0)?;
            let thread_bytes: Vec<u8> = row.get(1)?;
            let event_type_str: String = row.get(2)?;
            let payload_bytes: Vec<u8> = row.get(3)?;
            let timestamp: String = row.get(4)?;
            let payload: EventPayload = bincode::deserialize(&payload_bytes)?;
            let event_type = match event_type_str.as_str() {
                "Concept" => EventType::Concept,
                "Invariant" => EventType::Invariant,
                "Architecture" => EventType::Architecture,
                "Governance" => EventType::Governance,
                "Decision" => EventType::Decision,
                "Evidence" => EventType::Evidence,
                "Note" => EventType::Note,
                _ => EventType::Custom,
            };
            let mut lineage_stmt = conn.prepare("SELECT parent_id FROM lineage WHERE event_id = ?1")?;
            let lineage_rows = lineage_stmt.query_map(params![id.as_bytes().to_vec()], |row| {
                let parent_bytes: Vec<u8> = row.get(0)?;
                Ok(parent_bytes)
            })?;
            let mut lineage = Vec::new();
            for parent in lineage_rows {
                lineage.push(uuid::Uuid::from_slice(&parent?)?);
            }
            Ok(Some(ContinuityEvent {
                id: uuid::Uuid::from_slice(&id_bytes)?,
                thread_id: uuid::Uuid::from_slice(&thread_bytes)?,
                event_type,
                payload,
                timestamp: timestamp.parse()?,
                lineage,
            }))
        } else {
            Ok(None)
        }
    }

    fn list_events_for_thread(&self, thread_id: ThreadId) -> Result<Vec<ContinuityEvent>> {
        let ids = {
            let conn = self.conn.lock().expect("sqlite lock poisoned");
            let mut stmt = conn.prepare("SELECT id FROM events WHERE thread_id = ?1")?;
            let rows = stmt.query_map(params![thread_id.as_bytes().to_vec()], |row| {
                let id_bytes: Vec<u8> = row.get(0)?;
                Ok(id_bytes)
            })?;
            let mut ids = Vec::new();
            for row in rows {
                ids.push(uuid::Uuid::from_slice(&row?)?);
            }
            ids
        };

        let mut out = Vec::new();
        for id in ids {
            if let Some(event) = self.get_event(id)? {
                out.push(event);
            }
        }
        Ok(out)
    }
}
