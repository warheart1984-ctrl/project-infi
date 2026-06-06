# Plugin Governance Contract

Status: **active contract**

CISIV stage: **structure**

## Purpose

Normative contract for governed plug admission, execution, and operator control in AAIS.
Every MCP tool, native capability route, and Cursor skill admitted through the plug adapter
runtime must satisfy this contract and [`plug_adapter.v1.json`](../../schemas/plug_adapter.v1.json).

## Ecosystem doctrine

AAIS does not replace agent ecosystems; it governs their admission, authority, execution,
receipts, replay, and operator trust boundaries.

## Admission law

- **Existence is not activation.** Discovered plugs start at CISIV `concept`, `enabled: false`.
- **No plug enters `live_runtime` without:** a valid `plug_adapter.v1` contract, a genome record
  (`plugin_<name>.genome.v1.json`), and operator explicit enable (or gate-promoted default for
  `observe`-only plugs after verification).

## Authority ladder

| Level | Jarvis may | Operator UI | OTEM |
|-------|-----------|-------------|------|
| `observe` | read/query | toggle on/off | none |
| `assist` | suggest + sandbox invoke | toggle + context lock | none |
| `execute` | invoke in operator_runtime | toggle + approval policy | checkpoint if medium+ blast |
| `admin` | config/auth flows | dual-control enable | always checkpoint |

## Invariants

1. Every executed plug call emits a UL-wrapped receipt with `trace_id` and `provenance`.
2. Disabled plugs return `blocked` outcome — never silent fallback.
3. Blast radius is bounded before ledger write; high risk blocks without OTEM approval.
4. MCP auth state is visible in operator snapshot; no credential values in receipts.
5. Native capability plugs cannot exceed parent bridge `governance_mode`.

## CISIV path (per plug)

`concept → identity → structure → implementation → verification`

| Stage | Plug state |
|-------|------------|
| concept | cataloged, disabled, descriptor only |
| identity | `plug_id` + provenance frozen |
| structure | `plug_adapter.v1` validated, genome written |
| implementation | native MCP client wired, sandbox execution proven |
| verification | operator UI + ledger receipts + gate proof bundle |

## Receipt extension

Plug execution events use `decision_kind: plug_execution` and optional `event_context` fields:
`plug_id`, `source_kind`, `authority_level`, `mcp_server`.

## Related

- [AAIS_SUBSYSTEM_GENOME.md](./AAIS_SUBSYSTEM_GENOME.md)
- [AAIS_AGENT_WORKFLOW_CAPABILITY_MAP.md](../runtime/AAIS_AGENT_WORKFLOW_CAPABILITY_MAP.md)
- [schemas/plug_adapter.v1.json](../../schemas/plug_adapter.v1.json)
- [src/plug_adapter_runtime.py](../../src/plug_adapter_runtime.py)
- [src/mcp_bridge.py](../../src/mcp_bridge.py)
