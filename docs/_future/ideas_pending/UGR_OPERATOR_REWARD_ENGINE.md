# UGR Operator Reward Engine

CISIV stage: **concept**

Status: pending — not yet integrated into active AAIS doc tree or backed by runtime.

## 1. Purpose

**Mythic:** UGR Operator Reward Engine — Proof-of-Subsystem incentive layer that turns verified subsystem discovery, promotion, and adoption into durable operator reputation and bounded rail credits.

**Engineering:** `OperatorRewardEngine` (`UgrOperatorRewardEngine`) — governed reward issuance, attribution, ledger, and policy engine for the UGR membrane.

Naming protocol: [docs/contracts/AAIS_CODEX_CURSOR_NAMING_PROTOCOL.md](../../../docs/contracts/AAIS_CODEX_CURSOR_NAMING_PROTOCOL.md)

Extends the chain of custody (Discovery → Proof → Receipt → Governance → Promotion → Adoption → Attribution → Reward) so contribution earns status.

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation > Pipeline > Tool

Primary contract: [docs/contracts/UGR_OPERATOR_REWARDS_CONTRACT.md](../../../docs/contracts/UGR_OPERATOR_REWARDS_CONTRACT.md) (reputation primary; rail credits utility with caps; no bypass without valid discovery receipt).

## 3. Non-Goals

- Not a general cryptocurrency or agent marketplace currency.
- Rewards are not issued for unverified or non-governed contributions.
- Does not own core Jarvis cognition or Project Infi final-truth admission (defers to AAIS law where required).

## 4. Core Contract

Schema: [schemas/ugr_operator_reward_engine.v1.json](./schemas/ugr_operator_reward_engine.v1.json)

See [docs/contracts/UGR_OPERATOR_REWARDS_CONTRACT.md](../../../docs/contracts/UGR_OPERATOR_REWARDS_CONTRACT.md) for lifecycle, event types, caps, and attribution rules. The engine implements `issue_reward` gated on discovery receipt resolution.

## 5. Reward Issuance And Attribution

- Idempotent by event_id = SHA256 anchors.
- Attribution block carries lifecycle_chain and contributor attribution.
- Adoption events scale future reputation (no direct credits).

## 6. Integration With UGR Membrane

Wired via api routes (/api/ugr/reward/*), discovery service, mission runtime for promotion/adoption steps, and operator console surfaces.

## 7. Failsafe

- All issuance requires valid `subsystem_id` + discovery receipt (enforced in reward_attribution + issuer).
- Shadow / audit modes via env for safe rollout.
- Fail closed on missing receipt or disabled.

## 8. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers required fields and invariants | `asserted` | Schema + this document |
| Runtime module + issuer present and gated on receipts | `proven` | src/ugr/rewards/* + tests |
| API surface + routes wired in main Jarvis | `proven` | src/api.py ugr reward handlers |
| Contract + attribution + policy implemented | `proven` | UGR_OPERATOR_REWARDS_CONTRACT + code |

Target proof packet: `docs/proof/ugr/UGR_OPERATOR_REWARD_ENGINE_V1_PROOF.md` (exists per current tree).

## 9. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan + genome |
| Identity | Genome registration + subsystem spec entry |
| Structure | Full engine + receipt + ledger + policy modules (done) |
| Implementation | API routes, tests, operator console integration (done) |
| Verification | ugr-rewards-gate + integration in flagship audit + proof packet |

## 10. Related

- Contract: [UGR_OPERATOR_REWARDS_CONTRACT.md](../../../docs/contracts/UGR_OPERATOR_REWARDS_CONTRACT.md)
- Sibling: UGR Subsystem Discovery, UGR Mission Runtime
- Genome: governance/subsystem_genomes/ugr_operator_reward_engine.genome.v1.json
- Subsystem doc: docs/subsystems/ugr/UGR_OPERATOR_REWARD_ENGINE.md

## 11. Activation Order Notes And Minimal Invariants

**Recommended activation order (batch):** After core UGR discovery + mission (foundational for receipts and adoption).

**Depends on:** UGR Subsystem Discovery (for receipt validation), Mission Runtime (for promotion/adoption attribution), Project Infi law (for any outer governed action records).

**Minimal invariants:**
- No reward without resolved discovery receipt for the subsystem_id.
- Reputation is permanent/non-spendable; credits are capped utility only.
- All events carry attribution for long-term multiplier on adoption.
