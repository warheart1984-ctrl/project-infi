# Continuity OS — Reality Interface Specification

**Version:** 1.0  
**Status:** Normative

---

## 1. Reality channel abstraction

### Interface: `RealityChannel`

| Method | Returns |
|--------|---------|
| `observe()` | `EvidencePayload` |
| `describe_consequences()` | `ConsequenceProfile` |
| `verify_source(EvidencePayload)` | `VerificationResult` |

### Properties

| Property | Description |
|----------|-------------|
| `channel_id` | Stable identifier |
| `independence_score` | Degree of steward control (lower = more independent) |
| `consequence_weight` | Impact on judgment if contradicted |

---

## 2. Reality Interface Adapter (RIA)

**Responsibilities:**

- Bind concrete sources (markets, sensors, failures, adversaries, ecosystems) into `RealityChannel`
- Enforce constitutional constraints:

| Constraint | Rule |
|------------|------|
| **Non-spoofability** | Cryptographic verification where possible |
| **Non-silencing** | Channels cannot be disabled without constitutional procedure |
| **Non-monopolization** | No single steward controls all channels |

RIA implements **K-∞.2** (reality access guarantee).

---

## 3. Evidence pipeline

```
RealityChannel.observe()
    → raw payload
    → ECE: normalize → Evidence (timestamp, hash, sign)
    → CD: match Evidence to Expectation
    → Contradiction (if delta > threshold)
    → CRR-1 (on correction)
```

### Evidence Capture Engine (ECE)

1. Normalize payload to wire schema
2. Assign `evidence_id`, `timestamp`, `channel_id`
3. Compute content hash
4. Sign if channel supports verification

### Contradiction Detector (CD)

1. Load active Expectations for steward/model
2. Compare observed Evidence
3. Emit Contradiction with `surprise_intensity`
4. Trigger Judgment Engine update path (Loop B)

---

## 4. Reality Access Monitor

Tracks:

- **RAI** — Reality Access Index (fraction of judgment exposed to independent channels)
- **RDI** — Reality Deprivation Index
- **CE / SE** — Consequence / Semantic exposure

CFM uses RAI collapse as Type I insulation precursor.

---

## 5. CRK-1 v1.0 implementation status

| Component | Status |
|-----------|--------|
| Evidence object + schema | Implemented |
| Consequence lattice (CE/SE) | Implemented |
| Full RIA registry | Specified; partial in runtime |
| CD → CRR-1 automation | Schema normative; builder TBD |

See: [CONTINUITY_OS_RUNTIME_SPEC.md](CONTINUITY_OS_RUNTIME_SPEC.md)
