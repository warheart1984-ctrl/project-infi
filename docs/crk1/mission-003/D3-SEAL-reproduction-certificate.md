# D-3 Seal — Reproduction Seal Format (v1.0)

**Status:** Normative (final wire form)  
**Schema:** `fixtures/crk1/reproduction_seal.schema.json`  
**Sample:** `fixtures/crk1/sample_reproduction_seal.json`

A D-3 Seal is **not a badge**. It is a receipt proving CRK-1 is a scientific object that can be rebuilt by non-founders.

---

## Canonical JSON shape

```json
{
  "id": "D3-XXXX",
  "type": "ReproductionSeal",
  "created_at": "ISO-8601 timestamp",
  "created_by": "ExternalSteward-ID",
  "epoch": 3,
  "payload": {
    "runtime_rebuilt": true,
    "source_of_truth": "RP-CRK1-v1.0",
    "oral_tradition_used": false,
    "tests_executed": {
      "invariant_enforcement": "PASS",
      "governance_refusal": "PASS",
      "semantic_capture_resistance": "PASS",
      "governance_bypass_resistance": "PASS",
      "continuity_graph_reconstruction": "PASS",
      "kernel_challenge_path": "PASS"
    },
    "results": {
      "all_passed": true,
      "notes": "Optional free-text summary"
    }
  },
  "links": {
    "reproduction_packet_id": "RP-CRK1-v1.0",
    "test_harness_ids": ["TH-0001", "TH-0002", "TH-0003"],
    "external_steward_id": "ExternalSteward-ID",
    "governance_receipt_ids": ["R-XXXX", "R-YYYY"]
  }
}
```

---

## Field semantics

| Field | Requirement |
|-------|-------------|
| `oral_tradition_used` | MUST be `false` for founder-independent certification |
| `tests_executed.*` | Each MUST be `PASS` or `FAIL` |
| `results.all_passed` | `true` only if all six tests are `PASS` |
| `source_of_truth` | Reproduction packet ID used for rebuild |

---

## Test harness mapping

| `tests_executed` key | Harness |
|----------------------|---------|
| `invariant_enforcement` | K0–K12 invariant suite |
| `governance_refusal` | Commit-refusing governance gate |
| `semantic_capture_resistance` | Semantic reproduction / K7–K12 |
| `governance_bypass_resistance` | Red-team B1–B4 |
| `continuity_graph_reconstruction` | Wire v01 + continuity graph |
| `kernel_challenge_path` | Mission #004 / KΩ / IDC |

---

## Programmatic issuance

```python
from src.crk1.reproduction_packet import ReproductionPacket, ReproductionSeal
from src.crk1.schema_validator import CRK1SchemaValidator

packet = ReproductionPacket.build()
seal = ReproductionSeal.from_d3_certificate(
    seal_id="D3-0001",
    created_by="ExternalSteward-001",
    epoch=packet.epoch,
    runtime_rebuilt=True,
    oral_tradition_used=False,
    tests_executed={k: "PASS" for k in [
        "invariant_enforcement", "governance_refusal",
        "semantic_capture_resistance", "governance_bypass_resistance",
        "continuity_graph_reconstruction", "kernel_challenge_path",
    ]},
    all_passed=True,
    reproduction_packet_id=packet.id,
    test_harness_ids=["TH-0001", "TH-0002", "TH-0003"],
    external_steward_id="ExternalSteward-001",
)
CRK1SchemaValidator().validate("ReproductionSeal", seal.to_dict())
```

---

## Legacy markdown certificate

Human-readable D-3 certificate (pre-wire): `src/crk1/d3_reproduction_certificate.py`

```bash
python tools/run_mission_003_certification.py --d3-seal
```

Both forms may coexist; the **wire `ReproductionSeal`** is authoritative for Mission #003.

---

## Operator procedure

- [MISSION-003-OPERATOR-MANUAL.md](MISSION-003-OPERATOR-MANUAL.md)
- [MISSION-003-REPRODUCTION-CHECKLIST.md](MISSION-003-REPRODUCTION-CHECKLIST.md)
