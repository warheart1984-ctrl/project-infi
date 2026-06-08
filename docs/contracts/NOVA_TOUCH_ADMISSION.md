# Nova Touch Admission Contract

Status: **active contract** (Release 34)

## Purpose

Admit touch/gesture events as **keystroke-equivalent** turns without new authority or persistent biometric storage.

## Rules

1. Touch events are ephemeral by default
2. `logs_biometric_traces` remains false
3. No memory board writes without explicit operator MP-X opt-in
4. Jarvis retains execution authority

## API

- `POST /api/jarvis/nova/touch`
- `GET /api/jarvis/nova/touch/status`

Schema: [schemas/nova_touch_event.v1.json](../../schemas/nova_touch_event.v1.json)
