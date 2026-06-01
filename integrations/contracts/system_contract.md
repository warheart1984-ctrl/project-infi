# System Contract v1

This file defines the UI-to-AAIS integration law for the primary operator-facing
chat and memory surfaces.

It separates:

- raw backend endpoints
- normalized adapter request/response shape

The backend remains session-oriented.
The adapter provides the simplified UI contract.

## Single Ingress Rule

- `app/main.py` is the public UI-facing API shell.
- `src/api.py` is the canonical Jarvis runtime.
- UI traffic must enter through the shell surface.
- `POST /api/jarvis` is the shell-owned Jarvis ingress exposed in FastAPI docs.
- The shell forwards Jarvis chat traffic into the mounted runtime lane.

The UI should not bypass the shell and call the runtime directly when the shell
is present.

## Primary Endpoint

- `GET /health`
- `POST /api/jarvis`
- `POST /api/memory/write`

## Lower-Level Runtime Endpoints

- `POST /legacy_api/api/jarvis`
- `POST /legacy_api/api/chat/sessions`
- `POST /legacy_api/api/chat/sessions/{session_id}/message`
- `POST /legacy_api/api/jarvis/memory`

## Raw Request: Jarvis Chat

```json
{
  "input": "string",
  "context": {
    "session_id": "string",
    "system_prompt": "string",
    "persona_mode": "builder",
    "provider": "auto",
    "provider_mode": "auto_best",
    "requested_specialists": [],
    "requested_specialist_preset": null
  },
  "mode": "normal | think | research"
}
```

## Raw Request: Memory Write

```json
{
  "text": "string",
  "tags": [],
  "source": "manual",
  "category": "memory",
  "kind": "memory",
  "why": "string"
}
```

## Raw Response: Jarvis Chat

```json
{
  "output": "string",
  "trace": {},
  "status": "ok | degraded | blocked",
  "session_id": "string",
  "runtime": {}
}
```

## Normalized Adapter Request

This is the UI contract exposed by `integrations/adapters/ui_to_jarvis.ts` and it
now matches the compatibility endpoint directly.

```json
{
  "input": "string",
  "context": {
    "session_id": "string",
    "system_prompt": "string",
    "persona_mode": "builder",
    "provider": "auto",
    "provider_mode": "auto_best",
    "requested_specialists": [],
    "requested_specialist_preset": null
  },
  "mode": "normal | think | research"
}
```

## Normalized Adapter Response

```json
{
  "output": "string",
  "trace": {},
  "status": "ok | degraded | blocked",
  "session_id": "string",
  "runtime": {}
}
```

## Mode Mapping

- `normal` -> default chat path with no forced research
- `think` -> `response_mode = "think"`
- `research` -> `use_research = true`

## Status Mapping

- `ok` -> Jarvis completed normally with no visible degradation signal
- `degraded` -> Jarvis completed, but exposed fallback, truncation, or prompt-pressure evidence
- `blocked` -> Jarvis rejected the request or returned an error posture

## Law

- UI code should prefer the adapter contract over direct hardcoded route strings for new integration work.
- Route ownership lives in `integrations/routing/map.json`.
- `POST /api/jarvis` is the public compatibility chat ingress for UI callers.
- `POST /api/memory/write` is the public compatibility memory-write ingress for UI callers.
- If raw backend endpoints change, this contract and the route map must be updated together.
