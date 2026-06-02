# Imagine Generator v1 Proof Packet

Claim: Governed imagine patterns emit with constraint checks, admit to Story Forge, register on the capability bridge, emit UL lineage, and optionally render via xAI Grok when env keys are set.

Claim status: **proven** on fixtures and mock transport. Live Grok network calls are operator-only when keys are configured.

## Verification

```bash
make imagine-generator-gate
python -m pytest tests/test_imagine_generator.py tests/test_imagine_grok.py tests/test_capability_bridge_alt3.py tests/test_alt3_lineage.py -q
```

| Claim | Label |
|---|---|
| Fixture pattern emits with asserted claim | proven |
| Forbidden term rejects pattern | proven |
| Story Forge admission file written on handoff | proven |
| Capability bridge catalog (emit, handoff, grok_render) | proven |
| UL lineage capability_call for Alt-3 actions | proven |
| Grok render with env key + mock transport | proven |
| Grok blocked without env key (keys_required) | proven |
| Capability bridge catalog UI registration only | none_yet |

- claim_label: proven
- override_command: make imagine-generator-gate
