use crate::types::{Hash256, MetaMap};

pub fn hash_parts(parts: &[&str]) -> Hash256 {
    let mut state = [
        0x243f_6a88_85a3_08d3u64,
        0x1319_8a2e_0370_7344u64,
        0xa409_3822_299f_31d0u64,
        0x082e_fa98_ec4e_6c89u64,
    ];
    for part in parts {
        for byte in part.as_bytes() {
            for (idx, lane) in state.iter_mut().enumerate() {
                *lane ^= (*byte as u64).wrapping_add((idx as u64) << 8);
                *lane = lane
                    .wrapping_mul(0x1000_0000_01b3)
                    .rotate_left(5 + idx as u32);
            }
        }
    }
    let mut out = [0u8; 32];
    for (idx, lane) in state.into_iter().enumerate() {
        out[idx * 8..(idx + 1) * 8].copy_from_slice(&lane.to_be_bytes());
    }
    out
}

pub fn hash_metadata(prefix: &str, metadata: &MetaMap) -> Hash256 {
    let canonical = metadata
        .iter()
        .map(|(key, value)| format!("{key}={value}"))
        .collect::<Vec<_>>()
        .join("|");
    hash_parts(&[prefix, &canonical])
}

pub fn zero_hash() -> Hash256 {
    [0; 32]
}
