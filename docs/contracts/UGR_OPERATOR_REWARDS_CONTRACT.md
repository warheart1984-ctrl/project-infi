# UGR Operator Rewards Contract (v1.2)

Governed dual-token economy: reputation (standing) + rail credits (Cloud Forge utility).

## Tokens

| Token | Spendable | Source |
|-------|-----------|--------|
| Reputation | No | Proof of Discovery |
| Rail credits (earned) | Yes | Verified contribution rewards |
| Rail credits (purchased) | Yes | Ledger-only purchase after off-platform payment |

## Lifecycle

`Discovery → Proof → Receipt → Governance → Promotion → Adoption → Attribution → Reward`

## Spend

`POST /api/ugr/rewards/spend` debits credits and returns `forge_boost` for Cloud Forge EXPRESS scheduling.

Purchased credits spend without reputation floor; earned credits require `min_reputation_to_spend_credits`.

## Policy

`deploy/ugr/reward-policy.json`

## Implementation

- `src/ugr/rewards/`
