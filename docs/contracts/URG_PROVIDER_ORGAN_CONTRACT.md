# URG Provider Organ Contract

Status: **v1**

Authority: `docs/contracts/URG_STACK_DOCTRINE.md`.

## Organ tuple

Each provider organ is documented as:

\[
O_i = (I_i, E_i, F_i, K_i)
\]

### Identity \(I_i\)

```json
{
  "organ_id": "organ-openrouter-mid",
  "organ_class": "llm_provider",
  "tier": "mid",
  "label": "OpenRouter Mid Relay"
}
```

### Envelope \(E_i\)

```json
{
  "execution_backend": "remote",
  "proposal_only": true,
  "response_mode": "think"
}
```

### Function \(F_i\)

```json
{
  "capabilities": ["general_qa", "explain", "governed_super_router_demo"],
  "max_tokens": 2048
}
```

### Contract \(K_i\)

```json
{
  "max_cost_units": 8,
  "risk_ceiling": "medium",
  "allowed_regions": ["local-primary", "tenant-us"],
  "allowed_domains": ["general_qa", "explain", "governed_super_router_demo"],
  "admissible_rails": ["SAFE", "NORMAL", "EXPRESS"]
}
```

## Routing law

URG selects an organ when:

1. Mission step names `organ_id` explicitly (v1 demo), or
2. Future: matcher scores organs by tier, cost remaining, and region (not in v1).

Organs do not self-route. URG switchboard is the only router.

## Config path

`deploy/ugr/provider-organs.json`

Registry code: `src/ugr/mission/provider_organ.py`
