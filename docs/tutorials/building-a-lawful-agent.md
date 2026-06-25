# Building a Lawful Agent

End-to-end pattern for a constitutional agent.

## Architecture

```
User prompt
    ↓
LawfulLLMAdapter.ask()     → GRR header
    ↓
LawfulLLMAdapter.predict() → ExpectationObject
    ↓
Reality channel            → EvidenceObject
    ↓
LawfulLLMAdapter.correct() → CRR-1 + CLG-1
```

## Step 1 — Define your model

```python
class TradingAgentModel:
    def __call__(self, prompt: str) -> dict:
        return {
            "outcome": 100.0,  # predicted price
            "confidence": 0.75,
            "assumptions": ["mean_reversion"],
        }

    def on_correction(self, correction) -> None:
        # optional: update internal state
        pass
```

## Step 2 — Wrap in LawfulLLMAdapter

```python
from continuity_sdk import LawfulLLMAdapter

agent = LawfulLLMAdapter(
    TradingAgentModel(),
    steward_id="agent_alpha",
    channel_id="market.feed.primary",
    decision_cluster_id="strategy:momentum_v1",
)
```

## Step 3 — Governed action loop

```python
def act(prompt: str, market_price: float) -> dict:
    raw, grr = agent.ask(prompt)
    exp = agent.predict(prompt)
    evidence = agent.observe({"value": market_price, "strength": 1.0})

    if abs(float(exp.expected_outcome) - market_price) > 0.01:
        correction, crr1 = agent.correct(exp, evidence)
        return {"action": raw, "corrected": True, "crr_id": crr1["crr_id"]}

    return {"action": raw, "corrected": False}
```

## Step 4 — Verify lineage

Run Mission #005 pattern with multiple agent instances sharing one CLG-1.

## Rules

1. Never skip GRR on decisions
2. Never hide contradiction
3. Always emit CRR-1 on correction
4. Use independent reality channels (see [Designing Reality Channels](designing-reality-channels.md))

## Related

[LawfulLLMAdapter](../continuity-sdk/lawful-llm-adapter.md) · [Book of Invariants](../continuity-os/invariants/book-of-invariants.md)
