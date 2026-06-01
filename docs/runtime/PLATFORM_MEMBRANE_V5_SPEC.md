# Platform Membrane v5 Specification

| Field | Value |
|-------|-------|
| **Service ID** | `platform.membrane.v5` |
| **Port** | 8090 (default) |
| **Authority** | `META_ARCHITECT_LAWBOOK.md`, MA-13 |

Historical: [PLATFORM_MEMBRANE_V4_SPEC.md](./PLATFORM_MEMBRANE_V4_SPEC.md).

## Layer map

| Layer | Versions | Capability |
|-------|----------|------------|
| Substrate | v1–v7 | Orgs, jobs, artifacts |
| Commercial | v8–v14 | OIDC, billing, drift, workflows |
| Civilization | v15–v20 | Mesh, Marketplace, Proof Federation |
| Fourth arc | v21–v30 | Mesh v2, Marketplace v2, Proof v2, Sovereign v1 |
| Fifth arc | v31–v40 | Events, Proof v3, Mesh v3, Sovereign v2 |
| **Sixth arc** | **v41–v50** | See pillars below |

## Sixth arc pillars

| Versions | Pillar | Capability |
|----------|--------|------------|
| v41–v42 | Autonomous Org Mesh | Policy-bound routing autopilot (dry-run / apply) |
| v43–v44 | Global Proof Network | Witness registry + attestation graph |
| v45–v46 | Inter-Membrane Exchange | Intra-tenant transfer + peer federation (IMXP) |
| v47–v48 | Platform Ledger v2 | Hash-chained operational ledger |
| v49–v50 | Sovereign Runtime | `sovereign_profile`, signed export packs |

## Primitives (v5)

| Primitive | Schema |
|-----------|--------|
| routing_policy | `platform.routing_policy.v1.json` |
| proof_witness | `platform.proof_witness.v1.json` |
| membrane_envelope | `platform.membrane_envelope.v1.json` |
| platform_ledger_entry | `platform.platform_ledger_entry.v1.json` |
| sovereign_profile | `platform.sovereign_profile.v1.json` |

## MA-13

- **Autonomous mesh:** routing only; no Stage 3 actuation without consent.
- **IMXP:** dual consent for cross-tenant peer exchange.
- **Ledger:** operational evidence; not Nova cognition.

## Verification

```bash
python .github/scripts/check-platform-v5-spec-governance.py
make platform-v6-gate
make platform-v6-smoke
```
