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

## Credit transfer (rail credits only)

Operators in the **same tenant** may transfer rail credits P2P or via atomic two-way exchange. **Reputation and adoption multipliers are not transferable.**

| Rule | Purpose |
|------|---------|
| `min_reputation_to_send` | Sender standing gate |
| `max_per_transfer` / `max_outbound_per_day` | Anti-farming caps |
| `transfer_fee_fraction` | Fee burn on send (discourages wash loops) |
| `cooldown_seconds` | Throttle rapid cycles |

Transfers move existing balance only (no minting). Signed `credit_transfer_receipt` + paired ledger events (`rail_credits_sent`, `rail_credits_received`).

## Fail-closed (discovery receipt gate)

**No reward may be issued unless `subsystem_id` resolves to a valid discovery receipt.**

Before any balance or ledger write, `resolve_valid_discovery_receipt` MUST:

1. Load the receipt from `SubsystemDiscoveryStore.get_by_subsystem_id`
2. Pass `verify_subsystem_discovery_receipt` (HMAC)
3. Match `receipt.subsystem_id` to the requested `subsystem_id`
4. Match normalized `receipt.tenant_id` to the request tenant
5. Match `discovery_receipt_id` when provided

Failure returns `status: rejected` with `reason: discovery_receipt_unresolved`. All issuance flows go through `reward_issuer.issue_reward()` — there is no bypass.

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/ugr/reward/transfer` | P2P rail credit transfer (`from_operator_id`, `to_operator_id`, `amount`, `trace_id`) |
| POST | `/api/ugr/reward/exchange` | Atomic two-way exchange (`operator_a`, `operator_b`, `amount_a`, `amount_b`) |
| GET | `/api/ugr/reward/transfers?tenant_id=&operator_id=` | Transfer ledger events |
| POST | `/api/ugr/rewards/transfer` | Legacy alias |
| POST | `/api/ugr/reward/issue` | Issue reward (gated); body: `tenant_id`, `operator_id`, `subsystem_id`, `event_type`, optional anchors |
| GET | `/api/ugr/reward/operator/<operator_id>?tenant_id=` | Balances from `operator_balances.json` |
| GET | `/api/ugr/reward/subsystem/<subsystem_id>?tenant_id=` | Tenant ledger rows + attributions for subsystem |
| GET | `/api/ugr/rewards/operator/<operator_id>?tenant_id=` | Legacy alias |
| GET | `/api/ugr/rewards/ledger?tenant_id=&operator_id=&subsystem_id=&limit=` | Legacy alias |
| POST | `/api/ugr/rewards/spend` | Debit credits (reputation-gated); return `forge_boost` |
| POST | `/api/ugr/discover/subsystem` | Includes `operator_rewards` on discovery / promotion |

## Policy

[`deploy/ugr/reward-policy.json`](../../deploy/ugr/reward-policy.json) — `economy.reputation_primary` must remain true for production tenants.

## Environment

| Variable | Default | Purpose |
|----------|---------|---------|
| `UGR_OPERATOR_REWARDS_ENABLED` | `1` | Kill switch |
| `UGR_REWARDS_SHADOW_ONLY` | `1` | Validate + compute; no balance writes (audit is stricter preview-only) |
| `UGR_REWARDS_AUDIT_ONLY` | `0` | Compute deltas + attribution preview; no ledger append |
| `UGR_RAIL_CREDIT_TRANSFER_ENABLED` | `1` | Allow operator P2P credit transfer |
| `UGR_RAIL_CREDIT_SPEND_ENABLED` | `1` | Allow spend + forge hook |
| `UGR_REWARD_POLICY_PATH` | `deploy/ugr/reward-policy.json` | Policy file |

## Related

- [UGR_SUBSYSTEM_DISCOVERY_CONTRACT.md](UGR_SUBSYSTEM_DISCOVERY_CONTRACT.md)
- [URG_CLOUD_PLATFORM.md](../URG_CLOUD_PLATFORM.md)

## Implementation

- `src/ugr/rewards/operator_reward_spec.py` — event types and anchor requirements
- `src/ugr/rewards/reward_attribution.py` — attribution chain + `resolve_valid_discovery_receipt`
- `src/ugr/rewards/reward_calculator.py` — policy v1.1 deltas
- `src/ugr/rewards/reward_ledger.py` — `rewards.jsonl` + `operator_balances.json`
- `src/ugr/rewards/reward_issuer.py` — `issue_reward()` single entry
- `src/ugr/rewards/rail_credit_transfer.py` — `transfer_rail_credits()` / `exchange_rail_credits()`
- `src/ugr/rewards/operator_credit_transfer_receipt.py` — signed transfer receipts
- `src/ugr/rewards/reward_governance.py` — `reward_policy_update` via governance missions
- `src/ugr/rewards/operator_reward_engine.py` — thin wrapper for discovery hooks
- Hooks: `subsystem_discovery.py`, `mission_runtime.py`, `cloud_forge_bridge.py`
