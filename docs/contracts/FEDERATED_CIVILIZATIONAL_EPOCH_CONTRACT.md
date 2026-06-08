# Federated Civilizational Epoch Contract

Status: **active contract** (Mythic Stage 19 / Anatomical Layer 21 / Release 49)

## Purpose

Live **federated civilizational epochs** bind adopted GCV civilizations, ISD accords, NFD treaties, and CEV amendments into time-bounded epoch charters with external witness quorum — the transition from pilot-proven Stage 18 to multi-tenant, multi-operator federation.

## Coordination classes

| Class | Meaning |
|-------|---------|
| FCE-0 | Observe epoch drift (charter cardinality, peer desync, amendment window state) |
| FCE-1 | Federated epoch charter proposal |
| FCE-2 | Adopted epoch charter (operator + Jarvis + **external witness quorum**) |
| FCE-3 | Population-scale read-only coherence elevation |

## Invariants

1. Epoch rollover requires FCE-2 adopt; no auto-promotion across epochs
2. CEV amendments bind to `epoch_id`; rejected when epoch is `frozen`
3. FCE-2 adopt requires ≥1 external witness with distinct `witness_org_domain`
4. Upstream validation: GCV civilization + ISD + NFD + CEV posture must align
5. Nova interprets; Jarvis authorizes; Dreamspace proposal-only

## APIs

- `GET /api/operator/federated-epochs`
- `POST /api/operator/federated-epochs/observe`
- `GET /api/operator/federated-epochs/charters`
- `POST /api/operator/federated-epochs/charters/adopt`
- `GET /api/operator/federated-epochs/epochs`
- `GET /api/operator/federated-epochs/witnesses`

## Witness payload (FCE-2 adopt)

Adopt body must include `external_witnesses`: array of objects with:

- `witness_id` (string)
- `witness_org_domain` (string, must differ from operator org for quorum)
- `trust_bundle_ref` (string, optional)
- `signed_at` (ISO-8601 UTC)

## Verification

```bash
make federated-civilizational-epoch-body-gate
make stage19-federation-gate
```
