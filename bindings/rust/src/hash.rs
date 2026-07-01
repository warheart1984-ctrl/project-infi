use crate::cas::Receipt;
use serde_json::Value;
use sha2::{Digest, Sha256};

/// Recursively sort object keys for language-agnostic canonical JSON.
pub fn sort_json_keys(value: &Value) -> Value {
    match value {
        Value::Object(map) => {
            let mut keys: Vec<&String> = map.keys().collect();
            keys.sort();
            let mut sorted = serde_json::Map::new();
            for key in keys {
                sorted.insert(key.clone(), sort_json_keys(&map[key]));
            }
            Value::Object(sorted)
        }
        Value::Array(items) => Value::Array(items.iter().map(sort_json_keys).collect()),
        _ => value.clone(),
    }
}

/// Canonical form: JSON with sorted keys, compact separators, UTF-8.
pub fn canonical_json(value: &Value) -> String {
    let sorted = sort_json_keys(value);
    serde_json::to_string(&sorted).expect("canonical json")
}

/// SHA-256(canonical_json_bytes). The `hash` field is always cleared before hashing.
pub fn hash_receipt(receipt: &Receipt) -> String {
    let mut value = serde_json::to_value(receipt).expect("to_value");
    if let Value::Object(ref mut map) = value {
        map.insert("hash".into(), Value::String(String::new()));
    }
    let canonical = canonical_json(&value);
    let mut hasher = Sha256::new();
    hasher.update(canonical.as_bytes());
    format!("{:x}", hasher.finalize())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cas::{Identity, IdentityType, Receipt, Span};
    use serde_json::json;

    #[test]
    fn hash_is_stable_with_sorted_keys() {
        let receipt = Receipt {
            run_id: "run-1".into(),
            hash: "ignored".into(),
            spans: vec![Span {
                id: "span-1".into(),
                run_id: "run-1".into(),
                r#type: "execute".into(),
                timestamp: 1735689600,
                data: Default::default(),
            }],
            result: json!({ "echo": "hello" }),
            created_at: "2025-01-01T00:00:00Z".into(),
        };

        let h1 = hash_receipt(&receipt);
        let h2 = hash_receipt(&receipt);
        assert_eq!(h1, h2);
        assert_eq!(h1.len(), 64);
    }
}
