# Live evidence pack — Production Baseline v1.0

Artifacts from **one** cluster reproduction run. Until captured, `STATUS.json` remains `pending-cluster-execution`.

## Expected layout

```text
live/
  STATUS.json                 # machine-readable gate status
  probes/                     # kubectl get / curl probe outputs
  trivy/                      # SARIF or JSON scan attach (from CI or cluster images)
  hpa/                        # HPA describe + scale notes
  recovery/                   # rollback / failure drill notes
```

## Capture

From repo root (PowerShell):

```powershell
pwsh -File scripts/capture-baseline-live-evidence.ps1
```

Requires `kubectl` context targeting a cluster where baseline manifests are applied.

## Honesty

Live capture is **optional backlog**. Current ESFR (2026-07-31) waived independent reproduction as a gate requirement; DRAFT/HOLD certificate is accepted.

If you later want an ACTIVE certificate, pin digests and fill this pack first — that is stewardship beyond the waived ESFR gate.
