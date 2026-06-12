# Universal Substrate Loader (USL) — Nova NorthStar CoG OS

## Purpose

USL is the governed execution layer for Nova NorthStar CoG OS. Foreign binaries (PE, ELF,
Mach-O, DEX, WASM) become **guests** under one invariant **capability lattice**. Every state
change passes **Voss Binding** before touching the substrate.

USL is **not**:

- Wine-style Win32 emulation or API translation
- P15 Forge Universal Substrate (image extract/inject/replay — see `docs/forge-universal-substrate-program.md`)
- AAIS-UL governed command verbs (see `aris/ul_substrate.py`)
- OTEM capability bands 1–20 (see `docs/contracts/GOVERNANCE_TAXONOMY.md`)

USL uses `usl_capability_id` strings (`fs.write`, `net.connect`, …) distinct from OTEM bands.

## Architecture

```
Layer 0: UL Lift (Exokernel courier → ULLiftedModel → Forge emit)
Binary ingestion (PE/ELF/…) → UBO
Link & bind → capability lattice
Voss Binding gate → append-only ledger
Substrate dispatch (FS, net, scheduler, compositor)
```

### Layer 0: UL Lift (above UBO)

Substrate transmutation pipeline — **not** a traditional compiler:

```
RawBinary → ExokernelCourier → UBO → ULLifter → ULLiftedModel
  → AAIS registry → ForgeCompiler (dynamic | static)
```

| Role | Package / doc |
|------|----------------|
| Exokernel courier (thin mux, no interpretation) | `src/usl/exo/`, `EXOKERNEL_COURIER_SPEC.md` |
| UL semantic lifter | `src/usl/lift/`, `UL_LIFT_SPEC.md` |
| Forge dual-mode emitter | `src/usl/forge/`, `FORGE_LIFT_COMPILER_SPEC.md` |
| Lifted model schema | `schemas/ul_lifted_model.v1.json` |

**Naming:** UL Lifter (`src/usl/lift/`) is distinct from AAIS-UL (`src/aais_ul_substrate.py`).
Dynamic Forge output tightens USLGate + broker policy from static analysis; static Forge
emits governed images via cog-os profile `usl-lifted-guest`.

### Five layers

0. **UL Lift** — machine-code semantic model for registration and Forge (Layer 0)
1. **Binary ingestion** — family parsers normalize to Unified Binary Object (UBO)
2. **Link & bind** — imports → abstract service slots / capability endpoints
3. **Capability lattice** — invariant primitives: `fs.*`, `net.*`, `proc.*`, `mem.*`, `ui.*`, `ipc.*`, `time.*`, `crypto.*`
4. **Memory & threading** — unified guest address spaces and scheduler (Phase 2+ hardware execution)
5. **Governance** — law engine + Voss scars + cryptographic ledger

## Contracts

| Artifact | Path |
|----------|------|
| Voss transition record | `schemas/voss_transition.v1.json` |
| Unified Binary Object | `schemas/ubo.v1.json` |
| UL Lifted Model | `schemas/ul_lifted_model.v1.json` |
| Capability lattice | `schemas/usl_capability_lattice.v1.json` |

## Canonical serialization

`event_hash = SHA256(canonical_bytes)` over 39 fields in fixed order (see schema docstring in
`src/usl/canonical_serialize.py`). Rules:

- UTF-8, no whitespace
- Omit null/missing keys
- Lowercase enums; hashes as lowercase hex (no `sha256:` prefix in canonical form)

## Ledger

USL maintains a **separate** append-only chain per `usl_node_id`:

```
ledger_root_{n+1} = SHA256(prev_ledger_root_n || event_hash)
```

This is independent of UGR Merkle ledger (`src/ugr/mission/ledger_merkle.py`). An export bridge
may be added later.

## Voss Δ → scar

- `lambda_coupling_id = SHA256(pre_state_hash || capability_id || post_state_hash || actor_blob)`
- `scar_id = SHA256(lambda_coupling_id || decision || cycle_id)`
- `debt_id` — hash of pending obligations; empty sentinel `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` when none

Cycle-boundary Λ from `voss_binding.py` applies to constitutional transitions; per-transition
scars extend that model for syscall-level changes.

## Phase 1 (current)

Host-side Python runtime (`src/usl/`) proving:

- Canonical serializer + golden `fs.write` vector
- Ledger chaining + ed25519 signing
- PE parser + Windows `fs.write` adapter (simulated guest)
- ELF64 parser + syscall binder stub (`fs.write` wired)
- CoG substrate registry entry `usl-guest`

Execution is **interpreted dispatch** through adapters — not hardware guest execution.

## Phase 2 (Slice 2 — guest broker IPC)

Guest syscalls from fixture ELF `write` reach `USLGate.dispatch` through a **Unix domain
socket** broker (not only in-process `GuestBroker`).

| Item | Value |
|------|--------|
| Socket path (default) | `/run/cog/usl-broker.sock` |
| PID file | `/run/cog/usl-broker.pid` |
| Framing | One JSON object per line (NDJSON) |
| Request type | `BrokerMessage` (`src/usl/broker/ipc.py`) |
| Response type | `BrokerResponse` |
| Env: broker socket | `USL_BROKER_SOCKET` |
| Env: health HTTP port | `COG_USL_PORT` (default `8766`) |
| Env: staged ELF for broker | `USL_BROKER_ELF` |

**Health JSON (phase 2):** `$COG_RUN_DIR/usl.health` and HTTP `GET /health` include
`"phase": 2`, `"broker": "ok"`, and `"socket": "<path>"` when broker-smoke succeeds.

**Serial boot event:** `{"event":"usl","status":"ok","phase":2,"broker":"ok"}` on metal when
phase ≥ 2.

**CLI:**

```bash
python -m src.usl.cli broker-serve
python -m src.usl.cli broker-smoke
```

**Megaton / admission:** `USL_BROKER_SOCKET` or `--broker-socket` routes `p2_elf_broker_write`
through `RemoteBroker`; `--require-live` on phase 2 checks guest `/health` for
`phase==2` and `broker==ok` (QEMU forwards `:8766`, not the guest Unix socket).

**Admission artifact:** `ci-artifacts/usl-slice2-admit.json` (`schema: usl-slice2-admit.v1`).
Tiers: A = attestation `usl_broker_ready` + pytest + Megaton phase 2 in-process; B = QEMU
`--usl-slice2` contract-boot; C = Megaton phase 2 `--require-live`.

**CI profiles:**

| Profile | Gate | QEMU |
|---------|------|------|
| `metal` | PR `linux-broker-governance` (full Tier A/B/C) | yes |
| `usl-lifted-guest` | PR `usl-lifted-guest-admit` + nightly `usl-lifted-guest-nightly` | no (Tier A) |

Set `USL_SLICE2_REQUIRE_FORGE_INTEGRATION=1` on metal and guest gates to run forge
integration pytest. WSL dev notes: `docs/operations/USL_WSL_DEV.md`.

### Slice 2.1 — supervision (ptrace / seccomp)

Supervision is **opt-in** via `USL_SUPERVISION_MODE` (default `ipc` preserves Slice 2
NDJSON broker IPC).

| Mode | Behavior |
|------|----------|
| `ipc` | Guest connects to `BrokerServer` over AF_UNIX (default) |
| `ptrace` | `SupervisionRunner` traps syscalls and forwards `BrokerMessage` to the broker |

Env: `USL_SUPERVISION_GUEST_ELF`, `USL_SUPERVISION_GUEST_ID`. Seccomp policy is
deny-by-default with broker-connect allowlist (`src/usl/supervision/seccomp.py`).
Tier A admit runs supervision pytest; optional ptrace smoke when
`USL_SUPERVISION_MODE=ptrace`.

**Failure modes:** unknown guest id → `unknown_guest:*`; guest not admitted →
`guest_not_admitted:*`; ptrace unavailable on non-Linux → runner refuses `start_guest`.

### Multi-guest broker routing

`BrokerServer` registers multiple guests via IPC `register_guest` (`guest_process_id`,
`elf_path`, `admitted`). Each `BrokerMessage.guest_process_id` routes to a per-guest
`GuestBroker`. Set `USL_REGISTRY_DB` for SQLite artifact persistence under
`/opt/cogos/usl-lifted/registry.db` on lifted guest profiles.

## Phase 2+ (beyond Slice 2)

- Mach-O, DEX/ART, WASM loaders
- Real guest execution (ptrace / user-mode VM / cog-os seccomp broker)
- UI compositor bridge, mesh network capability
- Policy signed under Λ-sigil root of trust
- Kernel syscall interception on `metal` profile

## CoG OS integration

- Registry: `cog-os/forge/substrates/registry.json` → `usl-guest`
- Service: `cog-os/payload/opt/cogos/bin/start-usl` (metal / daily-driver profiles)
- Slice 1 spine: `usl` in profile service table → `rc.sh` `wait_for_usl_health` → serial `{"event":"usl","status":"ok"}`; HTTP `/health` on `:8766`
- Phase 2+: broker IPC, Mach-O/DEX loaders, kernel syscall interception on `metal`

## CLI smoke

```bash
python -m src.usl.cli replay-transition
python -m src.usl.cli load-elf --path tests/fixtures/usl/minimal.elf
python -m src.usl.cli simulate-win-write --path tests/fixtures/usl/minimal.pe
```

## Tests

```bash
python -m unittest discover -s tests -p 'test_usl_*'
```
