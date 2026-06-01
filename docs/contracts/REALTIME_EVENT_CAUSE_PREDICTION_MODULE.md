# Real-Time Event-and-Cause Prediction Module

Version: `0.1`  
Module ID: `aais.realtime_event_cause_predictor`

## Purpose

Predict the next bounded event and its likely causes from local realtime deltas,
then emit compact advisory packets on the governed `rt` channel.

## Scope

- No new lane is introduced.
- The module uses the governed direct lane with compact channel override `rt`.
- No tool calls or external providers are allowed on this path.
- All predictions remain advisory until routed through God Brain and approved by Jarvis.

## Compact Operation Codes

- `predict_event` → `22`
- `predict_cause` → `23`

## Compact Payload Keys

- `ev`: predicted event code
- `ca`: causal factor codes
- `horiz`: horizon in milliseconds
- `conf`: confidence from `0` to `100`
- `ev_ref`: stable event reference

## Validation Rules

- God Brain appears in the packet path
- Jarvis remains the approval authority
- Every prediction packet carries `conf` and `horiz`
- No `tool_call` or `tool_result` intents appear on the realtime trace
- Compact packet payloads stay under `400` bytes
