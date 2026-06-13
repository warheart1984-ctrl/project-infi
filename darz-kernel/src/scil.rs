use crate::types::InvariantObject;

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct NormalizedInvariantObject {
    pub ig: InvariantObject,
    pub normalized: bool,
}

pub fn normalize(ig: &InvariantObject) -> NormalizedInvariantObject {
    NormalizedInvariantObject {
        ig: ig.clone(),
        normalized: true,
    }
}
