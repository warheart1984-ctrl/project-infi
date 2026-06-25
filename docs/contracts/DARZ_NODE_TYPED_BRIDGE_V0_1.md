# DAR-Z Node Typed Bridge v0.1

Continuity Bridge Contract

Status: Implemented
Implementation: `src/darz_kernel_bridge.py`
Primary test: `tests/test_ugr_aais_darz_aaes_bridge.py`

## Purpose

This contract binds the live path:

```text
UGR -> AAIS -> DAR-Z Continuity Kernel -> AAES
```

DAR-Z acts as the continuity and identity substrate for the bridge. It is not a
parallel execution runtime.

## Node Advertisement

The bridge accepts a `DarzNodeAdvertisement`:

```text
node_id
status
threads
events
reconstruction
proof_status
federation_ready
genesis_threads
proof_hash
```

For `darz.node.001`, the expected healthy state is:

```text
status = ACTIVE
threads >= 3
events >= 3
reconstruction = PASS
proof_status = PROVEN
federation_ready = true
genesis_threads = founder.genesis, identity.genesis, darz.genesis
```

## Typed Event Chain

When the node advertisement is valid, the DAR-Z bridge emits Rust-compatible
serde-tagged events:

```text
Evidence -> Architecture -> Governance -> Decision
```

The `Architecture` event is named:

```text
DAR-Z Continuity and Identity Substrate
```

The final `Decision` event sets `chosen_architecture` to that Architecture event
ID, and its lineage includes Evidence, Architecture, and Governance.

Each event carries `bridge_fields`:

```text
darz_node_id
substrate_role
bridge_hash
lineage_pointers
wave_signature
continuity_proof
```

The bridge summary also carries `cross_kernel_coherence` for CEC-1 enforcement
inside AAES.

## Rejection Rules

The bridge rejects the handoff when any node condition fails:

- `darz.node.inactive`
- `darz.node.reconstruction_failed`
- `darz.node.proof_not_proven`
- `darz.node.federation_not_ready`
- `darz.node.genesis_threads_incomplete`
- `darz.node.thread_count_below_genesis`
- `darz.node.event_count_below_genesis`
- `darz.node.proof_hash_missing`

## AAES Carry-Forward

`darz_bridge_summary()` includes:

```text
darz_node_id
substrate_role
bridge_hash
event_types
ul_trace_count
```

AAES stores this summary in the governed action outcome so the handoff remains
auditable after execution.

CEC-1 then propagates the substrate fields into AAES INTENT, DECISION,
EXECUTION, and RESULT events.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_darz_node_typed_bridge.py tests\test_ugr_aais_darz_aaes_bridge.py -q
```
