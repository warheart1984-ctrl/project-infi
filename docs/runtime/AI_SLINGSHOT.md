# AI Slingshot

**Governed kinetic accelerator** for customer AI workflows — not a weapon, not a hack.

| Field | Value |
|-------|-------|
| **Slingshot ID** | `slingshot.v1` |
| **Authority** | Meta Architect Lawbook · Stage 2 Copilot Doctrine (MA-13) |
| **Claim posture (v1)** | `asserted` — single-machine pytest + preload gate |

## Four phases

| Phase | Name | What happens |
|-------|------|--------------|
| 1 | **Pullback** | Mechanic scan → diagnose → rebuild; emit `SLINGSHOT_FRAME.v1` |
| 2 | **Tension** | Compress `SLINGSHOT_PACKET.v1` (goals, constraints, cost envelope) |
| 3 | **Launch** | Nova/Jarvis `fast` compose + mid-flight drift monitors |
| 4 | **Impact** | `SLINGSHOT_IMPACT_RECEIPT.v1` + ledger + optional human signoff |

## Operator commands

```bash
python -m slingshot preload --repo mechanic/fixtures/sample-customer-repo-v2 --case-id demo \
  --trace-path mechanic/fixtures/sample-customer-repo-v2/traces/session.ndjson
python -m slingshot status --case-id demo
python -m slingshot verify --case-id demo --repo mechanic/fixtures/sample-customer-repo-v2
make slingshot-gate
```

Artifacts: `.runtime/slingshot/<case_id>/` (frame, packet, receipts, ledger).  
Mechanic forensics: `.runtime/mechanic/<case_id>/`.

## Chat API (Launch)

```json
{
  "message": "Analyze deploy-ai workflow drift and propose safe remediation",
  "slingshot": {
    "case_id": "customer-acme-001",
    "authorized_goals": ["propose remediation only"],
    "required_constraints": ["no apply", "no repo writes"]
  }
}
```

Admission requires a valid non-expired packet and non-blocked frame. Slingshot sessions **always** enforce `MECHANIC_RUNTIME_PROFILE` for the case (no env var required).

## MA-13 guards

| Class | Guard |
|-------|-------|
| I — Usurpation | `authorized_goals` + `detect_smuggled_goal()` |
| II — Distortion | `required_constraints` + invariant-derived constraints |
| III — Leakage | Class III drifts block preload; runtime profile blocks `apply` |

## v1 exclusions

- Cross-machine replay manifests
- Cloud Forge EXPRESS rail coupling
- Jarvis Console UI panel

## Related

- [Mechanic blueprint](../subsystems/mechanic/MECHANIC_BLUEPRINT.md)
- [Composed turn proof](../proof/cognitive_runtime/COMPOSED_TURN_V1_PROOF_BUNDLE.md)
- [STAGE2_COPILOT_DOCTRINE.md](./STAGE2_COPILOT_DOCTRINE.md)
