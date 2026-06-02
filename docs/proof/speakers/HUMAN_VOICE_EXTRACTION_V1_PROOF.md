# Human Voice Extraction v1 Proof Packet

Claim: Voice profiles extract from notes without persisting raw source; Speakers handoff requires signoff; capability bridge and UL lineage wired.

Claim status: **proven** on fixture `notes-demo-redacted`.

## Verification

```bash
make human-voice-extraction-gate
python -m pytest tests/test_human_voice_extraction.py tests/test_capability_bridge_alt3.py tests/test_alt3_lineage.py -q
```

| Claim | Label |
|---|---|
| No raw notes in persisted pack | proven |
| Handoff blocked without signoff | proven |
| Speakers constraints file after signoff | proven |
| Capability bridge extract / signoff / handoff | proven |
| UL lineage on extract and handoff | proven |
| Lumen archive explicitly out of scope | asserted |

- claim_label: proven
- override_command: make human-voice-extraction-gate
