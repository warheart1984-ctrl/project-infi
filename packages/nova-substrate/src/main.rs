mod arena;
mod protocol;

use arena::Arena;
use protocol::{decode_header, encode_header, MessageType};
use serde_json::{json, Value};
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::UnixListener;

const SOCKET_PATH: &str = "/tmp/nova.sock";

struct ConnectionState {
    arena: Arena,
    next_arena_id: u64,
    next_fiber_id: u64,
    next_inference_id: u64,
    next_plugin_id: u64,
}

impl Default for ConnectionState {
    fn default() -> Self {
        Self {
            arena: Arena::new(),
            next_arena_id: 1,
            next_fiber_id: 1,
            next_inference_id: 1,
            next_plugin_id: 1,
        }
    }
}

#[tokio::main]
async fn main() {
    let _ = std::fs::remove_file(SOCKET_PATH);
    let listener = UnixListener::bind(SOCKET_PATH).expect("bind failed");
    println!("NovaCoda substrate listening at {}", SOCKET_PATH);

    loop {
        let (stream, _) = listener.accept().await.unwrap();
        tokio::spawn(handle_connection(stream));
    }
}

async fn handle_connection(mut stream: tokio::net::UnixStream) {
    let mut header_buf = [0u8; 12];
    let mut state = ConnectionState::default();

    loop {
        if stream.read_exact(&mut header_buf).await.is_err() {
            break;
        }

        let Ok((msg_type, body_len, expected_crc)) = decode_header(&header_buf) else {
            break;
        };

        let mut body = vec![0u8; body_len as usize];
        if stream.read_exact(&mut body).await.is_err() {
            break;
        }

        if crc32fast::hash(&body) != expected_crc {
            break;
        }

        let payload: Value = serde_json::from_slice(&body).unwrap_or(Value::Null);
        let (response_type, response_payload) = match msg_type {
            MessageType::Ping => (
                MessageType::Pong,
                json!({
                    "ok": true,
                    "message": "pong",
                    "protocol": "NovaCoda",
                    "arenaCapacity": state.arena.capacity(),
                }),
            ),
            MessageType::AllocArena => {
                let requested_capacity = payload
                    .get("capacity")
                    .and_then(Value::as_u64)
                    .unwrap_or(0) as usize;
                let label = payload
                    .get("label")
                    .and_then(Value::as_str)
                    .map(|value| value.trim().to_string())
                    .filter(|value| !value.is_empty());
                let granted_capacity = requested_capacity.min(state.arena.capacity());
                if granted_capacity > 0 {
                    let _ = state.arena.alloc(granted_capacity);
                }
                let arena_id = format!("arena-{:04}", state.next_arena_id);
                state.next_arena_id += 1;
                (
                    MessageType::ArenaHandle,
                    json!({
                        "protocol": "NovaCoda",
                        "arenaId": arena_id,
                        "requestedCapacity": requested_capacity,
                        "grantedCapacity": granted_capacity,
                        "remainingCapacity": state.arena.capacity(),
                        "label": label,
                    }),
                )
            }
            MessageType::SpawnFiber => {
                let entry_point = payload
                    .get("entryPoint")
                    .and_then(Value::as_str)
                    .unwrap_or("entryPoint")
                    .trim()
                    .to_string();
                let label = payload
                    .get("label")
                    .and_then(Value::as_str)
                    .map(|value| value.trim().to_string())
                    .filter(|value| !value.is_empty());
                let fiber_id = format!("fiber-{:04}", state.next_fiber_id);
                state.next_fiber_id += 1;
                (
                    MessageType::FiberReady,
                    json!({
                        "protocol": "NovaCoda",
                        "fiberId": fiber_id,
                        "entryPoint": entry_point,
                        "ready": true,
                        "scheduledAt": format!("fiber-seq-{}", state.next_fiber_id - 1),
                        "label": label,
                    }),
                )
            }
            MessageType::InferRequest => {
                let prompt = payload
                    .get("prompt")
                    .and_then(Value::as_str)
                    .unwrap_or("")
                    .trim()
                    .to_string();
                let mode = payload
                    .get("mode")
                    .and_then(Value::as_str)
                    .map(|value| value.trim().to_string())
                    .filter(|value| !value.is_empty());
                let words: Vec<String> = prompt.split_whitespace().map(|word| word.to_string()).collect();
                let inference_id = format!("infer-{:04}", state.next_inference_id);
                state.next_inference_id += 1;
                (
                    MessageType::InferDone,
                    json!({
                        "protocol": "NovaCoda",
                        "inferenceId": inference_id,
                        "prompt": prompt,
                        "completion": words.join(" "),
                        "tokens": words,
                        "done": true,
                        "mode": mode,
                    }),
                )
            }
            MessageType::SyscallRequest => {
                let syscall = payload
                    .get("syscall")
                    .and_then(Value::as_str)
                    .unwrap_or("")
                    .trim()
                    .to_string();
                let result = payload.get("args").cloned().unwrap_or(Value::Null);
                (
                    MessageType::SyscallResult,
                    json!({
                        "protocol": "NovaCoda",
                        "syscall": syscall,
                        "status": "ok",
                        "result": result,
                    }),
                )
            }
            MessageType::PluginLoad => {
                let plugin = payload
                    .get("plugin")
                    .and_then(Value::as_str)
                    .unwrap_or("")
                    .trim()
                    .to_string();
                let loaded = !plugin.is_empty();
                let plugin_sequence = state.next_plugin_id;
                state.next_plugin_id += 1;
                (
                    MessageType::PluginLoad,
                    json!({
                        "protocol": "NovaCoda",
                        "plugin": plugin,
                        "loaded": loaded,
                        "pluginSequence": plugin_sequence,
                    }),
                )
            }
            MessageType::ConstitutionalCheck => {
                let intent_id = payload
                    .get("intentId")
                    .and_then(Value::as_str)
                    .unwrap_or("")
                    .trim()
                    .to_string();
                let authority = payload
                    .get("authority")
                    .and_then(Value::as_str)
                    .unwrap_or("")
                    .trim()
                    .to_string();
                let evidence_count = payload
                    .get("evidence")
                    .and_then(Value::as_array)
                    .map(|values| values.len())
                    .unwrap_or(0);
                let allowed = !intent_id.is_empty() && !authority.is_empty() && evidence_count > 0;
                (
                    MessageType::CenDecision,
                    json!({
                        "protocol": "NovaCoda",
                        "intentId": intent_id,
                        "decision": if allowed { "allow" } else { "deny" },
                        "reason": if allowed { "constitutional check passed" } else { "missing authority or evidence" },
                    }),
                )
            }
            _ => (
                MessageType::Pong,
                json!({
                    "ok": false,
                    "message": "unsupported request",
                    "protocol": "NovaCoda",
                    "arenaCapacity": state.arena.capacity(),
                }),
            ),
        };

        let response_body = serde_json::to_vec(&response_payload).expect("serialize response");
        let response_header = encode_header(response_type, &response_body);
        if stream.write_all(&response_header).await.is_err() {
            break;
        }
        if stream.write_all(&response_body).await.is_err() {
            break;
        }
    }
}
