use aaes_cas::cas::{Identity, IdentityType, Receipt, Span};
use aaes_cas::hash::hash_receipt;
use serde_json::json;
use std::collections::HashMap;

const FIXED_TIMESTAMP: i64 = 1735689600;

pub fn build_sample_receipt() -> Receipt {
    let identity = Identity {
        id: "agent-123".into(),
        r#type: IdentityType::Agent,
        metadata: HashMap::new(),
    };

    let span = Span {
        id: "span-1".into(),
        run_id: "run-1".into(),
        r#type: "execute".into(),
        timestamp: FIXED_TIMESTAMP,
        data: HashMap::new(),
    };

    Receipt {
        run_id: "run-1".into(),
        hash: String::new(),
        spans: vec![span],
        result: json!({ "echo": "hello" }),
        created_at: "2025-01-01T00:00:00Z".into(),
    }
}

pub fn main_evidence() {
    let mut receipt = build_sample_receipt();
    let h = hash_receipt(&receipt);
    receipt.hash = h.clone();

    let json = serde_json::to_string(&receipt).expect("serialize receipt");
    println!("{json}");
    eprintln!("RUST_HASH={h}");
}

fn main() {
    main_evidence();
}
