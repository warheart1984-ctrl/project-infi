# Mission #003 — Founder-Independent Reproduction (D-3 Seal)

## Success condition

At least one **non-founder steward**:

1. Reconstructs CRK-1 from `ReproductionPacket` (`RP-CRK1-v1.0`)
2. Passes all test harness suites
3. Issues a `ReproductionSeal` (D-3) with `oral_tradition_used: false`
4. May file Kernel Challenges if reality exposes gaps (KΩ path)

## Wire objects

| Object | Schema | Builder |
|--------|--------|---------|
| `ReproductionPacket` | `fixtures/crk1/reproduction_packet.schema.json` | `ReproductionPacket.build()` |
| `ReproductionSeal` | `fixtures/crk1/reproduction_seal.schema.json` | `ReproductionSeal.from_d3_certificate()` |
| `D3ReproductionCertificate` | (legacy markdown cert) | `issue_d3_certificate()` |

## Packet contents

- **Spec docs:** Kernel Codex, minimap, runtime diagram
- **Reference implementation:** minimal runtime, governance engine, ledgers
- **Test harness:** pytest suites + semantic/external reproduction harnesses
- **Fingerprint:** `compute_packet_fingerprint()` embedded in packet payload

## Related constitutional mechanisms

- **KΩ + KCR:** kernel remains consequence-exposed post-reproduction
- **IDC:** drift / silent CF-events open invariant discovery when reproduction reveals gaps

See also: `docs/crk1/mission-003/D3-SEAL-reproduction-certificate.md`, `docs/crk1/mission-003/MISSION-003-OPERATOR-MANUAL.md`
