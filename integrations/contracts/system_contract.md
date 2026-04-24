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
- Runtime routes exposed by `src/api.py` are mounted under `/legacy_api`.

The UI should not bypass the shell and call the runtime directly when the shell
is present.

## Raw Endpoints

- `GET /health`
- `POST /legacy_api/api/chat/sessions`
- `POST /legacy_api/api/chat/sessions/{session_id}/message`
- `POST /legacy_api/api/jarvis/memory`

## Raw Request: Create Session

```json
{
  "system_prompt": "string",
  "persona_mode": "builder",
  "response_mode": "fast",
  "provider": "auto",
  "provider_mode": "auto_best",
  "requested_specialists": [],
  "requested_specialist_preset": null
}
```

## Raw Request: Chat Message

```json
{
  "message": "string",
  "response_mode": "fast | think",
  "use_research": false,
  "persona_mode": "builder",
  "provider": "auto",
  "provider_mode": "auto_best",
  "requested_specialists": [],
  "requested_specialist_preset": null
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

## Raw Response: Chat Message

```json
{
  "response": "string",
  "response_trace": {},
  "session_id": "string",
  "session_state": {},
  "policy_status": {},
  "provider_notice": null
}
```

## Normalized Adapter Request

This is the UI contract exposed by `integrations/adapters/ui_to_jarvis.ts`.

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

- `ok` -> backend completed normally with no visible degradation signal
- `degraded` -> backend completed, but exposed fallback, truncation, or prompt-pressure evidence
- `blocked` -> backend rejected the request or returned an error posture

## Law

- UI code should prefer the adapter contract over direct hardcoded route strings for new integration work.
- Route ownership lives in `integrations/routing/map.json`.
- If raw backend endpoints change, this contract and the route map must be updated together.
