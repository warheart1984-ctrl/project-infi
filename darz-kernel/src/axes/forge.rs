use crate::hash::{hash_metadata, hash_parts};
use crate::types::{ForgeProof, InvariantObject, MetaMap, OiwlReport, TrajectoryMessage};

pub fn project(msg: &TrajectoryMessage, oiwl: &OiwlReport) -> InvariantObject {
    let mut annotations: MetaMap = msg.metadata.clone();
    annotations.insert("trajectory_id".to_string(), msg.id.clone());
    annotations.insert("origin".to_string(), msg.origin.clone());
    annotations.insert("lts_state".to_string(), msg.lts_state.clone());
    annotations.extend(oiwl.annotations.clone());

    let input_hash = hash_parts(&[
        &msg.id,
        &msg.origin,
        &msg.lts_state,
        &msg.history,
        &format!("{:?}", msg.metadata),
    ]);
    let oiwl_hash = hash_parts(&[
        &oiwl.drift_score.to_string(),
        &oiwl.entropy_delta.to_string(),
        &oiwl.contamination_flags.join("|"),
    ]);
    let payload_hash = hash_metadata("forge.payload", &annotations);
    let id = hash_parts(&[
        "ig",
        &msg.id,
        &hexish(&input_hash),
        &hexish(&oiwl_hash),
        &hexish(&payload_hash),
    ]);

    InvariantObject {
        id,
        class_name: annotations
            .get("domain")
            .cloned()
            .unwrap_or_else(|| "general".to_string()),
        payload_hash,
        forge_proof: ForgeProof {
            algorithm: "darz-forge-k-v1".to_string(),
            input_hash,
            oiwl_hash,
        },
        annotations,
    }
}

fn hexish(hash: &[u8; 32]) -> String {
    hash.iter().map(|byte| format!("{byte:02x}")).collect()
}
