# Wonder → RLS → OTEM Stack

Three layers govern imagination, reasoning, and action in AAIS:

1. **Gate of Wonder** — pre-logical imagination filter on unstructured text (`permit` / `sandbox` / `forbid`)
2. **Reasoning & Logic Substrate (RLS)** — epistemic firewall on reasoning graphs (`admit` / `downgrade` / `reject`)
3. **OTEM** — execution approval and escalation justification

## Ingress order

```
Packet → Detachment Guard → Wonder → RLS → Bridge Invariant → ARIS → Governed LLM → OTEM
```

Wonder applies to `generation_request`, `deliberation_request`, and `reasoning_packet_ingress`.

## Operator visibility

- `/api/wonder/status` — Wonder mode and contract reference
- `/api/rls/status` — RLS mode and quarantine summary
- Bridge and OTEM turn metadata include `wonder_verdict` and `rls_verdict` when present
