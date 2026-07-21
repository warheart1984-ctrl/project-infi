pub const MAGIC: [u8; 2] = [0xC0, 0xDA];
pub const VERSION: u8 = 1;

#[repr(u8)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum MessageType {
    Ping = 0x01,
    Pong = 0x02,
    AllocArena = 0x10,
    ArenaHandle = 0x11,
    SpawnFiber = 0x20,
    FiberReady = 0x21,
    InferRequest = 0x30,
    InferToken = 0x31,
    InferDone = 0x32,
    SyscallRequest = 0x40,
    SyscallResult = 0x41,
    PluginLoad = 0x50,
    ConstitutionalCheck = 0x60,
    CenDecision = 0x61,
    IveResult = 0x62,
}

impl MessageType {
    pub fn from_u8(value: u8) -> Option<Self> {
        match value {
            0x01 => Some(Self::Ping),
            0x02 => Some(Self::Pong),
            0x10 => Some(Self::AllocArena),
            0x11 => Some(Self::ArenaHandle),
            0x20 => Some(Self::SpawnFiber),
            0x21 => Some(Self::FiberReady),
            0x30 => Some(Self::InferRequest),
            0x31 => Some(Self::InferToken),
            0x32 => Some(Self::InferDone),
            0x40 => Some(Self::SyscallRequest),
            0x41 => Some(Self::SyscallResult),
            0x50 => Some(Self::PluginLoad),
            0x60 => Some(Self::ConstitutionalCheck),
            0x61 => Some(Self::CenDecision),
            0x62 => Some(Self::IveResult),
            _ => None,
        }
    }
}

pub fn encode_header(msg_type: MessageType, body: &[u8]) -> [u8; 12] {
    let mut header = [0u8; 12];
    header[0] = MAGIC[0];
    header[1] = MAGIC[1];
    header[2] = VERSION;
    header[3] = msg_type as u8;
    let len = (body.len() as u32).to_be_bytes();
    header[4..8].copy_from_slice(&len);
    let crc = crc32fast::hash(body).to_be_bytes();
    header[8..12].copy_from_slice(&crc);
    header
}

pub fn decode_header(buf: &[u8; 12]) -> Result<(MessageType, u32, u32), String> {
    if buf[0] != MAGIC[0] || buf[1] != MAGIC[1] {
        return Err("invalid magic bytes".into());
    }
    if buf[2] != VERSION {
        return Err("unsupported protocol version".into());
    }
    let body_len = u32::from_be_bytes(buf[4..8].try_into().unwrap());
    let crc = u32::from_be_bytes(buf[8..12].try_into().unwrap());
    let msg_type = MessageType::from_u8(buf[3]).ok_or_else(|| "unknown message type".to_string())?;
    Ok((msg_type, body_len, crc))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn encode_decode_header_roundtrip() {
        let body = b"hello";
        let header = encode_header(MessageType::Ping, body);
        let (msg_type, body_len, crc) = decode_header(&header).expect("decode header");
        assert_eq!(msg_type, MessageType::Ping);
        assert_eq!(body_len, body.len() as u32);
        assert_eq!(crc, crc32fast::hash(body));
    }

    #[test]
    fn rejects_invalid_magic() {
        let mut header = encode_header(MessageType::Ping, b"");
        header[0] = 0x00;
        assert!(decode_header(&header).is_err());
    }
}
