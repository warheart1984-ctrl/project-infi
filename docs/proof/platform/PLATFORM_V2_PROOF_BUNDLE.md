# Platform Membrane v2 Proof Bundle

Policy engine, OIDC scaffold, quotas — **asserted** single-machine.

```bash
pytest tests/test_platform_v11.py -q
```

Cross-machine **proven** claim remains tied to `platform-cross-machine-gate` when manifest is active.

v19–v28 adds k-of-n attestation quorum via [`REPLAY_MANIFEST.v2.template.json`](cross_machine/REPLAY_MANIFEST.v2.template.json) and `POST /v1/jobs/{id}/attestations` — **proven** when CI tertiary hash quorum matches (`platform-cross-machine-gate`).

v35–v36 adds replay v3 + attestation bundles — see [`PLATFORM_V35_V36_PROOF_BUNDLE.md`](PLATFORM_V35_V36_PROOF_BUNDLE.md).
