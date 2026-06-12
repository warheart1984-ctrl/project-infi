# Remaining work (by phase)

What is **not** done yet or only partially done after the initial Deferred Lift / Governance delivery. Use this as a backlog; items are ordered roughly by dependency and cog-os impact.

---

## Phase 1 — Governance bridge

- [x] **Stage `governance_decode_bundle.json` on guest rootfs** under `/opt/cogos/usl-lifted/` — enforced in `payload-stage-usl-lifted.sh`.
- [ ] **Dual-path admission maintenance:** keep compiler and severity fallback aligned when taxonomy or IR shape changes; document env defaults per profile (`USL_GOVERNANCE_ADMISSION`).
- [ ] **Richer `binary_lift` taxonomy** entries if new lift pipelines or severities are added beyond current bridge mapping.
- [x] **Linux CI for broker admission:** `linux-broker-governance` job in `.github/workflows/cogos-forge-gate.yml` runs pytest + `usl-slice2-admit` for `usl-lifted-guest`.

---

## Phase 2 — PE x86_64 Windows

- [ ] **No full Windows syscall table** (by design for MVP); extend only when a concrete guest needs more than `int 0x2e` heuristic.
- [ ] **Limited PE depth:** imports, relocations, and multi-section CFG are not fully modeled.
- [ ] **PE fixture coverage:** add more representative PE samples if Windows guest profiles expand.

---

## Phase 3 — aarch64 ELF Linux

- [ ] **Heuristic aarch64 effects** (SVC + x8) may mis-classify; needs Capstone or table-driven syscall IDs for production guests.
- [ ] **Linear sweep CFG quality** on variable-length aarch64; no full decoder yet.
- [x] **Guest profile stub** `usl-lifted-guest-aarch64.yaml` (payload arch tag; full aarch64 guest image deferred).
- [x] **CI** `usl-lift-aarch64` job runs `pytest tests/test_usl_lift_aarch64.py` (no QEMU).

---

## Phase 4 — Pluggable disasm

- [x] **Capstone optional dependency** documented in `requirements.txt` (`pip install capstone`); disasm fails soft when absent.
- [ ] **CI matrix** exercising both `linear` and `capstone` backends where Capstone is installed.

---

## Phase 5 — Persistent AAIS registry

- [x] **SQLite `ArtifactStore`** (`SqliteArtifactStore`, env `USL_REGISTRY_DB`).
- [x] **Multi-guest broker routing** (`register_guest` IPC, per-guest `GuestBroker` dispatch).
- [ ] **Forge ↔ registry provenance** completeness (lineage from static/dynamic emit through courier register).
- [ ] **Concurrency:** SQLite WAL / file store locking, GC, and corruption recovery for multi-process forge/broker hosts.

---

## cog-os integration (global)

- [x] **`USL_LIFT_ELF` lift-at-boot** in guest init — `start-usl`, firstboot invariants; proof: `make usl-lift-at-boot-smoke`.
- [ ] **`elf.py` hardcoded caps cleanup** in loader (deferred).
- [x] **Linux CI** for AF_UNIX broker integration tests — see `linux-broker-governance` workflow job.
- [x] **Profile promotion:** `usl-lifted-guest` gates + `/etc/cog/policies/` via `payload-stage-policies.sh`; CI admit path for guest profile.
- [x] **Document operator flow** for refreshing lifted artifacts — see [COG_OS_INTEGRATION.md](./COG_OS_INTEGRATION.md#operator-refresh-installed-system).

---

## Suggested next priorities

1. SQLite registry backend if multi-artifact forge hosts need query semantics beyond JSON files.
2. Daily-driver metal sign-off on HP hardware using [../METAL_PROOF_CHECKLIST.md](../METAL_PROOF_CHECKLIST.md) daily-driver section.
3. Capstone backend CI matrix when guest profiles require richer disassembly.
