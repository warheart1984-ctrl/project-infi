# Narrative Trust Pack v1 Proof Packet

Claim: Story Forge → Beatbox → Speakers outputs can be wrapped in a governed `narrative_trust_pack.v1` with hash verification and human signoff before `proven` export.

Claim status: **proven** on single-machine E2E fixture. Jarvis capability registration: **proven**.

## 1) Incident / Issue ID

- ID: `NTP-V1`
- Title: Narrative Trust Pack MVP
- Scope: `src/capabilities/narrative_trust_pack.py`, capability bridge, API routes, `tools/narrative/`, tests

## 2) Verification Evidence

### One-click override command

```bash
make narrative-gate
python -m pytest tests/test_narrative_trust_pack.py tests/test_capability_bridge_alt3.py -q
```

### Claim posture

| Claim | Label |
|---|---|
| E2E pack + signoff → proven | proven |
| Tampered artifact → rejected | proven |
| Jarvis capability route | proven |
| Bridge pack / verify / signoff | proven |

## 3) Sign-Off

- claim_label: proven
- why_short: E2E test builds pack from story_forge_audio output; bridge pack→verify→signoff chain proven; signoff promotes to proven.
- proof_links:
  - docs/proof/storyforge/NARRATIVE_TRUST_PACK_V1_PROOF.md
  - tests/test_narrative_trust_pack.py
  - tests/test_capability_bridge_alt3.py
- override_command: make narrative-gate
