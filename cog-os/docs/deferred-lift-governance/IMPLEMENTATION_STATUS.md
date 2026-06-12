# Implementation status (completed)

Summary of work delivered for the Deferred Lift / Governance roadmap. Plan source: `deferred_lift_governance_7ca7fbaf.plan.md` (not edited in-repo).

## Phase 1 — Governance bridge

| Item | Location | Notes |
|------|----------|-------|
| Lift invariants → Governance IR | `src/usl/lift/governance_bridge.py` | `lift_invariants_to_governance_ir`, `compile_lift_governance`, `run_lift_admission` |
| `binary_lift` taxonomy | `src/governance_taxonomy.py` | Training source entry added |
| `lift_binary_invariant` validator | `src/invariant_compiler.py` | When `ir.pipeline == "binary_lift"`; `block` severity denies; `blocked_invariants` at **top level** of admission result |
| Decode bundle emission | `src/usl/forge/static_emitter.py`, `dynamic_emitter.py` | Writes `governance_decode_bundle.json` in forge output |
| Runtime admission | `src/usl/forge/runtime_policy.py`, `bootstrap.py` | Loads optional bundle; `check_admission()` compiler path first, severity-map fallback; env `USL_GOVERNANCE_ADMISSION=compiler\|severity` |
| Tests | `tests/test_usl_governance_bridge.py`, `tests/test_usl_forge.py`, `tests/test_usl_broker_forge_integration.py` | Linux broker deny on `block` (skipped on Windows where AF_UNIX broker unavailable) |

## Phase 2 — PE x86_64 Windows

| Item | Location | Notes |
|------|----------|-------|
| PE guest path | `src/usl/exo/courier.py` | `guest_from_pe_bytes()` |
| PE loader | `src/usl/loaders/pe.py` | |
| Windows syscall effect | `src/usl/lift/effects.py`, `src/usl/lift/disasm/x86_64.py` | `int 0x2e` treated as syscall |
| Fixtures | `tests/fixtures/usl/minimal.pe`, `syscall.pe` | Built via `tests/fixtures/usl/build_fixtures.py` |
| Tests | `tests/test_usl_lift_pe.py`, `tests/test_usl_exo_courier.py` | Includes `test_lift_and_register_pe_windows` |

## Phase 3 — aarch64 ELF Linux

| Item | Location | Notes |
|------|----------|-------|
| aarch64 disasm | `src/usl/lift/disasm/aarch64.py` | Linear sweep; SVC; movz/x8 syscall heuristic |
| ELF routing | loaders + control/effects | Architecture-aware |
| Fixtures | `tests/fixtures/usl/` | Little-endian SVC pattern corrected in `build_fixtures.py` |
| Tests | `tests/test_usl_lift_aarch64.py`, `tests/test_usl_disasm_backend.py` | |

## Phase 4 — Pluggable disasm

| Item | Location | Notes |
|------|----------|-------|
| Backend protocol | `src/usl/lift/disasm/backend.py` | `DisasmBackend`, `get_disasm_backend()` |
| Linear backend | `src/usl/lift/disasm/linear_x86_64.py` | Default |
| Capstone backend | `src/usl/lift/disasm/capstone_backend.py` | Optional; env `USL_DISASM_BACKEND=linear\|capstone` |
| Tests | `tests/test_usl_disasm_backend.py` | |

## Phase 5 — Persistent AAIS registry

| Item | Location | Notes |
|------|----------|-------|
| Registry API | `src/usl/exo/registry.py` | `ArtifactStore`, `FileArtifactStore` (JSON under `USL_AAIS_REGISTRY_DIR`) |
| Courier wiring | `src/usl/exo/courier.py` | `law_envelope` passed to `register_lifted_model`; persistent default registry |
| Tests | `tests/test_usl_registry_persist.py` | |

## cog-os (partial)

| Item | Location | Notes |
|------|----------|-------|
| USL lifted staging script | `cog-os/forge/scripts/lib/payload-stage-usl-lifted.sh` | Calls `payload-stage-usl.sh`; bakes `minimal.elf` lift into `/opt/cogos/usl-lifted` when fixture present |
| Forge profile | `cog-os/forge/profiles/usl-lifted-guest.yaml` | `payload_usl_lifted: true`; USL health + broker gates |
