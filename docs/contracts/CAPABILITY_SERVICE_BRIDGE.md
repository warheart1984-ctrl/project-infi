# Capability Service-Lane Bridge

## Purpose

The Capability Service-Lane Bridge routes eligible direct-tool requests through governed AAIS capability modules instead of ad hoc operator logic.

It currently covers:

- `spatial_reason`
- `mystic_reading`
- `v9_core`
- `v10_core`

## Runtime Role

AAIS runtime -> `JarvisOperator` -> `CapabilityServiceBridge` -> capability module -> provider/runtime

The bridge keeps service-lane traffic bounded while preserving the existing direct-tool response contract.

## Guarantees

- Registered tool requests are translated into AAIS capability-module executions.
- Success and failure both return deterministic `tool_result` objects.
- Capability metadata is attached to the tool result for governance visibility.
- Service-lane packet traces surface capability module and provider metadata.
- The bridge keeps a small in-memory audit trail of recent routed executions.

## Capability Metadata

Bridged tool results expose:

- `bridge_id`
- `bridge_version`
- `tool_type`
- `module`
- `action`
- `provider`
- `model` when available
- `timestamp`
- `trace_id`
- `result_size`
- `error_type` on failure
- `audit_sequence`

## Initial Scope

This bridge is intentionally narrow. It does not yet replace:

- memory governance tools
- workspace inspection tools
- approval/action lifecycle tools
- Forge routing

Those remain on their existing governed paths until they are refactored into capability-style adapters.
