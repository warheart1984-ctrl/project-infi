# OpenRouter Key Rotation

AAIS cannot rotate the OpenRouter key from code alone.

The account-side revocation step still has to happen in the OpenRouter
dashboard.

This repo now includes a local helper:

- `rotate-openrouter-key.ps1`

## Safe Rotation Order

1. create a new key in the OpenRouter dashboard
2. update `.env` locally with the new key
3. restart the AAIS backend
4. verify `/health` and one OpenRouter turn
5. revoke the old key in the OpenRouter dashboard

## Verify Before And After

From repo root:

```powershell
.\rotate-openrouter-key.ps1 -VerifyOnly
```

If you already have the new key:

```powershell
.\rotate-openrouter-key.ps1 -NewKey "sk-or-v1-..."
```

## Important Rule

Local helper scripts may update local config.

They do not revoke the old dashboard key for you.

That final revocation is still manual and should remain on the operator
checklist until confirmed.
