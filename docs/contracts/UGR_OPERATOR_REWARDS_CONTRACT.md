# UGR Operator Rewards Contract (v1.1)

Governed incentive layer for Proof-of-Subsystem. This is **not** an agent marketplace currency — it extends the **chain of custody** one step further so verified contribution earns durable status, and spendable credits remain bounded utility.

## Lifecycle chain of custody

```
Discovery → Proof → Receipt → Governance → Promotion → Adoption → Attribution → Reward
```

| Stage | UGR artifact |
|-------|----------------|
| Discovery | Valid `SubsystemSpec` + `subsystem_id` hash |
| Proof | Invariant + rail validity checks |
| Receipt | `subsystem_discovery_receipt` (signed) |
| Governance | `governance_mutation` mission (optional `promote`) |
| Promotion | Provider organ overlay `discovered-*` |
| Adoption | Mission step executes on promoted organ |
| Attribution | `attribution` block on reward events |
| Reward | `operator_reward_receipt` (signed) |

## Reputation-primary economy

**Reputation is dominant.** It is permanent, non-spendable, and tied to verified receipts. **Rail credits** are utility-only (scheduling boost) and are:

- Capped at earn time relative to reputation delta (`reputation_to_credit_ratio_min`)
- Capped by standing (`credit_earn_cap_fraction_of_reputation`)
- Not earnable on adoption events (value flows back as reputation + multiplier)
- Spendable only above `min_reputation_to_spend_credits`
- Bounded per spend by `max_spend_per_reputation_point × reputation_score`

**Adoption multipliers** scale reputation rewards on adoption (long-term attribution), not credit payouts.

## Reward types

| Type | Role | Spendable |
|------|------|-----------|
| Reputation | Primary status / standing | No |
| Rail credits | EXPRESS scheduling utility | Yes (bounded) |
| Adoption multiplier | Scales future reputation on adoption | No |

## Events

| event_type | Trigger | Typical reputation | Typical credits |
|------------|---------|-------------------|-----------------|
| `subsystem_discovered` | First valid discovery receipt | +15 (+3 search bonus) | +3 (capped) |
| `subsystem_promoted` | Governance `status: ok` | +40 | +8 (capped) |
| `subsystem_adopted` | Mission uses `discovered-*` organ | +10 × multiplier | 0 |

Events are idempotent by `event_id = SHA256(canonical anchors)`. Each record includes an `attribution` block with `lifecycle_chain` and `contributor_attribution`.

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/ugr/rewards/operator/<operator_id>?tenant_id=` | Profile snapshot |
| GET | `/api/ugr/rewards/ledger?tenant_id=&operator_id=&subsystem_id=&limit=` | Reward events |
| POST | `/api/ugr/rewards/spend` | Debit credits (reputation-gated); return `forge_boost` |
| POST | `/api/ugr/discover/subsystem` | Includes `operator_rewards` on discovery / promotion |

## Policy

[`deploy/ugr/reward-policy.json`](../../deploy/ugr/reward-policy.json) — `economy.reputation_primary` must remain true for production tenants.

## Environment

| Variable | Default | Purpose |
|----------|---------|---------|
| `UGR_OPERATOR_REWARDS_ENABLED` | `1` | Kill switch |
| `UGR_RAIL_CREDIT_SPEND_ENABLED` | `1` | Allow spend + forge hook |
| `UGR_REWARD_POLICY_PATH` | `deploy/ugr/reward-policy.json` | Policy file |

## Related

- [UGR_SUBSYSTEM_DISCOVERY_CONTRACT.md](UGR_SUBSYSTEM_DISCOVERY_CONTRACT.md)
- [URG_CLOUD_PLATFORM.md](../URG_CLOUD_PLATFORM.md)

## Implementation

- `src/ugr/rewards/`
- Hooks: `subsystem_discovery.py`, `mission_runtime.py`, `cloud_forge_bridge.py`
