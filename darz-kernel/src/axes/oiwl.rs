use crate::policy::OiwlPolicy;
use crate::types::{MetaMap, OiwlReport, TrajectoryMessage};

pub fn sense(msg: &TrajectoryMessage, policy: &OiwlPolicy) -> OiwlReport {
    let drift_score = score(&msg.history, "drift") % (policy.max_drift_score + 1);
    let entropy_delta = score(&msg.lts_state, "entropy") % (policy.max_entropy_delta + 1);
    let contamination_flags = contamination_flags(msg);
    let mut annotations = MetaMap::new();
    annotations.insert("oiwl.drift_score".to_string(), drift_score.to_string());
    annotations.insert("oiwl.entropy_delta".to_string(), entropy_delta.to_string());
    annotations.insert(
        "oiwl.contamination_count".to_string(),
        contamination_flags.len().to_string(),
    );

    OiwlReport {
        drift_score,
        entropy_delta,
        contamination_flags,
        annotations,
    }
}

fn score(value: &str, salt: &str) -> u32 {
    value
        .bytes()
        .chain(salt.bytes())
        .fold(0u32, |acc, byte| acc.wrapping_mul(31).wrapping_add(byte as u32))
}

fn contamination_flags(msg: &TrajectoryMessage) -> Vec<String> {
    let haystack = format!("{} {} {}", msg.id, msg.lts_state, msg.history).to_lowercase();
    ["contaminated", "poison", "tainted"]
        .into_iter()
        .filter(|needle| haystack.contains(needle))
        .map(str::to_string)
        .collect()
}
