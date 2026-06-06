# OpenRouter Key Rotation Runbook

AAIS cannot revoke OpenRouter keys from code. Rotation is an operator checklist.

## Prerequisites

- OpenRouter dashboard access
- Local `.env` with `OPENROUTER_API_KEY`
- Backend restart authority

## Rotation steps

1. Create a new key in the [OpenRouter dashboard](https://openrouter.ai/keys).
2. Update `.env` with the new `OPENROUTER_API_KEY`.
3. Restart the AAIS backend (`make run` or your deployment process).
4. Verify health and one OpenRouter turn:

```powershell
cd e:\project-infi
.\tools\ops\rotate-openrouter-key.ps1 -VerifyOnly
```

5. Revoke the old key in the OpenRouter dashboard after verification succeeds.

## Apply new key locally

```powershell
.\tools\ops\rotate-openrouter-key.ps1 -NewKey "sk-or-v1-..."
```

## Rule

Helper scripts may update local config only. Dashboard revocation remains manual.
