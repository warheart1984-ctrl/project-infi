# Kernel Sentinel Design (Stage 4)

## Status

`asserted` — design only; no native code in repository yet.

## Boundary

- Kernel/native adapter emits **only** `scorpion.event.v1` normalized events.
- No direct ledger writes from kernel space.
- Python `scorpion` package owns classify, extract, reconstruct, historize.

## Proposed Layout

```
scorpion/sentinel/kernel/
  README.md           # build instructions (out-of-tree)
  event_schema.json   # mirror os_invariants event shape
```

## Linux v1 Adapter Options

| Adapter | Pros | Cons |
|---------|------|------|
| eBPF tracepoints | Low overhead, rich syscall data | Requires kernel headers, signing on secure boot |
| auditd | Policy-driven, no custom kernel module | Higher noise, coarser timing |
| ftrace/perf | Scheduler/timing friendly | Heavier export pipeline |

Recommended path: eBPF for syscall/fd/privilege; perf for scheduler/timing.

## Promotion Criteria (`proven`)

1. VM or hardware replay captures boot + workload trace.
2. Scorpion `ingest` + `scan` flags known seeded drift in VM trace.
3. Proof bundle under `docs/proof/scorpion/kernel_sentinel/` with hashes and commands.
4. Cross-machine replay manifest completed (optional second machine).

## Platform Adapters

Follow Wolf `substrate-invariants.json` platform table:

- `linux` — eBPF/auditd first
- `windows` — ETW session adapter (future)
- `macos` — endpoint security export adapter (future)
- `android` — logd/selinux-aware adapter (future)

## Stub

`scorpion/sentinel/kernel_stub.py` returns `not_implemented` with contract-stable error.
