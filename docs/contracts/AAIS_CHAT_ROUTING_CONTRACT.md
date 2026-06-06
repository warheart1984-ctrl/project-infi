# AAIS Chat Routing Contract

Authority: [SEAM_LAW.md](./SEAM_LAW.md), [SEAM-TRANSITION-002-dual-path-chat.md](./seams/SEAM-TRANSITION-002-dual-path-chat.md)

## Canonical operator path

| Surface | Path | Authority |
|---------|------|-----------|
| Jarvis chat (canonical) | `/legacy_api/api/chat/sessions/*` | Governed pipeline + OTEM |
| Workflow shell compat | `POST /chat`, `POST /chat/stream` | Token-gated shell; no extra execute authority |
| Jarvis compat forward | `POST /api/jarvis` | Forwards to legacy Flask |

## Invariants

1. Operator documentation and stress harness use the canonical Jarvis path.
2. Shell `/chat` does not bypass Brain `proposal_only` or OTEM approval gates.
3. Dual-path coexistence is a **governed transition** — not a seam failure while invariants hold.

## Verification

```bash
make wave6-transition-gate
```
