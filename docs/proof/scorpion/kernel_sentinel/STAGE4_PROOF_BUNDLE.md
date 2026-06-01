# Scorpion Stage 4 Proof Bundle

Claim: **asserted** (audit-export adapter proven; native eBPF not in tree).

## Proven Locally

- `AuditExportSentinel` on NDJSON fixtures
- `KernelSentinelStub` NDJSON bridge
- `scorpion/sentinel/kernel/event_schema.json`

## Commands

```bash
py -3.12 -m scorpion.scorpion --mode scan --case-id sc-s4 --sentinel audit --trace-path scorpion/fixtures/traces/fd_leak.ndjson
py -3.12 -m scorpion.scorpion --mode scan --case-id sc-s4-kernel --sentinel kernel --trace-path scorpion/fixtures/traces/syscall_misuse.ndjson
```

## Promotion to `proven` (native kernel)

VM replay with eBPF export matching `event_schema.json` and cross-machine manifest in `docs/proof/scorpion/cross_machine/`.
