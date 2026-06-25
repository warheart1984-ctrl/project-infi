# H_CORRIDORS Boot Manifest Line (v0.1)

**Engineering module:** `src/ucr/corridor_serialize.py`  
**Related:** `CORRIDOR_LOADER_SPEC_v0.1.md`, `TRUST_ROOT_MEASUREMENT_CHAIN.md`

## Manifest line

```text
H_CORRIDORS=sha3-256:<hex>
```

Emitted during early boot after `CorridorLoader` seals `TrustedCorridorSet`.

## Canonical JSON payload

Keys only (no extra fields):

```json
{
  "corridors": [
    {
      "corridor_id": "<uuid>",
      "default_law": "0x<hex>",
      "max_risk": "<low|medium|high|critical>",
      "name": "<string>",
      "owner_id": "<uuid>",
      "version": <int>
    }
  ],
  "law_keys": ["0x...", "..."],
  "registry_version": <int>,
  "timestamp": "<ISO8601>"
}
```

Serialization rules:

1. `corridors` sorted ascending by `corridor_id` string
2. `law_keys` sorted ascending (hex strings)
3. `json.dumps(sort_keys=True, separators=(",", ":"))`
4. UTF-8 encode → `sha3-256` → `sha3-256:<hex>`

## Fixture snapshot (Nova-Dev + Prod-Ops)

| Field | Value |
|-------|-------|
| `registry_version` | `1` |
| `timestamp` | `2026-06-18T10:00:00Z` |
| **H_CORRIDORS** | `sha3-256:732b66373c6d66281ff95fa69fe3ff1a0d8c8fa70cc2ae13245e6d1890372cda` |

Corridor IDs:

- Nova-Dev: `11111111-1111-4111-8111-111111111101`
- Prod-Ops: `22222222-2222-4222-8222-222222222201`

## Trust root binding

`H_CORRIDORS` is the third of four raw 32-byte digests concatenated (after domain separator) into `H_TRUST_ROOT`. Any corridor registry change invalidates trust root and governed-mode admission.

## Verification

At commit time, `cog_act_commit` uses the **sealed** `get_trusted_corridors()` set, not live filesystem reads. `require_governed_mode` compares UCR corridor view to kernel `h_corridors`.
