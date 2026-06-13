use std::sync::{Arc, Mutex};

use crate::hash::{hash_parts, zero_hash};
use crate::types::{ExecutionAudit, ExecutionDecision, Hash256};

pub trait AuditSink: Send + Sync {
    fn record(&self, audit: ExecutionAudit);
}

#[derive(Clone, Default)]
pub struct InMemoryAuditSink {
    records: Arc<Mutex<Vec<ExecutionAudit>>>,
}

impl InMemoryAuditSink {
    pub fn records(&self) -> Vec<ExecutionAudit> {
        self.records.lock().expect("audit lock poisoned").clone()
    }

    pub fn next_sequence_and_previous_hash(&self) -> (u64, Hash256) {
        let records = self.records.lock().expect("audit lock poisoned");
        let sequence = records.len() as u64;
        let previous_hash = records
            .last()
            .map(|record| record.audit_hash)
            .unwrap_or_else(zero_hash);
        (sequence, previous_hash)
    }

    pub fn verify_chain(&self) -> bool {
        let records = self.records();
        let mut previous_hash = zero_hash();
        for (sequence, record) in records.iter().enumerate() {
            if record.sequence != sequence as u64 || record.previous_hash != previous_hash {
                return false;
            }
            previous_hash = record.audit_hash;
        }
        true
    }
}

impl AuditSink for InMemoryAuditSink {
    fn record(&self, audit: ExecutionAudit) {
        self.records
            .lock()
            .expect("audit lock poisoned")
            .push(audit);
    }
}

pub fn audit_hash(
    sequence: u64,
    previous_hash: Hash256,
    decision: &ExecutionDecision,
    regime_id: &str,
) -> Hash256 {
    hash_parts(&[
        "audit",
        &sequence.to_string(),
        &format!("{previous_hash:?}"),
        &format!("{decision:?}"),
        regime_id,
    ])
}
