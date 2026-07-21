# Policy DSL

Policies define routing rules and guardrails for governed requests.

## Structure

```yaml
- id: "coding.general.prefers_groq"
  when:
    domain: "coding"
    risk: "low"
  then:
    routing:
      preferred_backends: ["groq-llama3-70b"]
    guardrails:
      max_tokens_out: 4096
```

## Matching Rules

- `domain` — exact match on governance domain
- `risk` — exact match on risk level
- `tags` — all specified tags must be present (AND semantics)

## Compilation

Policies are compiled to `CompiledPolicy` objects with a `matches(governance)` predicate:

```ts
import { loadCodingPolicyPack } from '@aaes-os/governed-runtime';
const policies = loadCodingPolicyPack();
```
