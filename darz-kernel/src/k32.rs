use crate::types::InvariantObject;

pub fn stable(ig: &InvariantObject) -> bool {
    !ig.annotations
        .get("lts_state")
        .map(|state| state.to_lowercase().contains("unstable"))
        .unwrap_or(false)
}
