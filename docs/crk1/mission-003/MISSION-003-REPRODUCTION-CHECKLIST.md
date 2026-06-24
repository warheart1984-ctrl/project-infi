# Mission #003 — Reproduction Checklist

**For external stewards.** Runnable steps against this repository. No oral tradition required.

**Packet ID:** `RP-CRK1-v1.0`  
**Seal schema:** `fixtures/crk1/reproduction_seal.schema.json`  
**Operator manual:** [MISSION-003-OPERATOR-MANUAL.md](MISSION-003-OPERATOR-MANUAL.md)

---

## Prerequisites

- [ ] Python 3.12+
- [ ] Clean clone (no founder-only patches, no pre-seeded runtime state)
- [ ] Virtual environment created and dependencies installed
- [ ] No network except package install (tests are offline)

```powershell
cd <repo-root>
python -m venv .venv
.\.venv\Scripts\pip install -e ".[dev]"
```

---

## Phase 0 — Packet integrity

- [ ] Read `docs/crk1/mission-003/M3-A-external-reproduction-packet.md`
- [ ] Verify packet artifacts exist:

```powershell
.\.venv\Scripts\python.exe -c "from src.crk1.mission_003_packet import verify_packet_artifacts; ok, missing = verify_packet_artifacts(); print('OK' if ok else missing); assert ok"
```

- [ ] Confirm fingerprint:

```powershell
.\.venv\Scripts\python.exe -c "from src.crk1.mission_003_packet import compute_packet_fingerprint; print(compute_packet_fingerprint())"
```

- [ ] Build wire packet object:

```powershell
.\.venv\Scripts\python.exe -c "from src.crk1.reproduction_packet import ReproductionPacket; p=ReproductionPacket.build(); print(p.id, p.packet_hash())"
```

**Pass:** `packet.id == "RP-CRK1-v1.0"`, `artifacts_verified == true`

---

## Phase 1 — Rebuild & initialize runtime

- [ ] Confirm reference implementation imports:

```powershell
.\.venv\Scripts\python.exe -c "from src.crk1.runtime_facade import CRK1Runtime; r=CRK1Runtime.bootstrap(); print(r.kernel.epoch)"
```

- [ ] Run external reproduction harness (core steps):

```powershell
.\.venv\Scripts\python.exe -c "
from src.crk1.runtime_facade import CRK1Runtime
from src.crk1.external_reproduction_harness import ExternalReproductionHarness
rt = CRK1Runtime.bootstrap()
report = ExternalReproductionHarness(rt).run_all()
print('PASS' if report.all_passed else report)
assert report.all_passed
"
```

**Pass:** Runtime initializes; harness `all_passed`

---

## Phase 2 — Test harness (map to D-3 `tests_executed`)

### 2.1 Invariant enforcement → `invariant_enforcement`

```powershell
.\.venv\Scripts\python.exe -m pytest tests\crk1\test_crk1_invariants.py tests\crk1\test_crk1_wire_v01.py -q
```

### 2.2 Governance refusal → `governance_refusal`

```powershell
.\.venv\Scripts\python.exe -m pytest tests\crk1\test_crk1_governance_engine.py tests\crk1\test_governance_receipt_audit.py -q
```

### 2.3 Semantic capture resistance → `semantic_capture_resistance`

```powershell
.\.venv\Scripts\python.exe -m pytest tests\crk1\test_crk1_semantic.py -q
.\.venv\Scripts\python.exe -m pytest tests\crk1\test_mission_003_drift_stress.py -k "semantic" -q
```

If no `-k semantic` tests exist, run full semantic harness:

```powershell
.\.venv\Scripts\python.exe -c "
from src.crk1.runtime_facade import CRK1Runtime
from src.crk1.semantic_reproduction_harness import SemanticReproductionHarness
rt = CRK1Runtime.bootstrap()
assert SemanticReproductionHarness(rt).run().all_passed
print('semantic_capture_resistance PASS')
"
```

### 2.4 Governance bypass resistance → `governance_bypass_resistance`

```powershell
.\.venv\Scripts\python.exe -m pytest tests\crk1\test_crk1_redteam_suite.py -q
```

### 2.5 Continuity graph reconstruction → `continuity_graph_reconstruction`

```powershell
.\.venv\Scripts\python.exe -m pytest tests\crk1\test_crk1_continuity.py tests\crk1\test_crk1_wire_v01.py -q
```

### 2.6 Kernel challenge path → `kernel_challenge_path`

```powershell
.\.venv\Scripts\python.exe -m pytest tests\crk1\test_mission_004_005.py tests\crk1\test_komega_idc_mission003.py -q
```

---

## Phase 3 — Full certification (optional but recommended)

```powershell
.\.venv\Scripts\python.exe tools\run_mission_003_certification.py --json
```

Or full suite:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\crk1\ -q
```

**Pass:** R1–R5 certified (see `M3-E-reproduction-certification-protocol.md`)

---

## Phase 4 — Founder independence attestation

- [ ] Reproduction completed without founder Q&A or undocumented behavior
- [ ] `oral_tradition_used` will be `false` on seal
- [ ] All behavior traceable to packet + schemas + pytest logs

---

## Phase 5 — Issue D-3 Seal

When all Phase 2 suites pass, build the wire seal:

```powershell
.\.venv\Scripts\python.exe -c "
from src.crk1.reproduction_packet import ReproductionPacket, ReproductionSeal
from src.crk1.schema_validator import CRK1SchemaValidator

packet = ReproductionPacket.build()
seal = ReproductionSeal.from_d3_certificate(
    seal_id='D3-<YOUR-ID>',
    created_by='ExternalSteward-<YOU>',
    epoch=packet.epoch,
    runtime_rebuilt=True,
    oral_tradition_used=False,
    tests_executed={
        'invariant_enforcement': 'PASS',
        'governance_refusal': 'PASS',
        'semantic_capture_resistance': 'PASS',
        'governance_bypass_resistance': 'PASS',
        'continuity_graph_reconstruction': 'PASS',
        'kernel_challenge_path': 'PASS',
    },
    all_passed=True,
    notes='Independent reproduction from RP-CRK1-v1.0',
    reproduction_packet_id=packet.id,
    test_harness_ids=['TH-0001', 'TH-0002', 'TH-0003'],
    external_steward_id='ExternalSteward-<YOU>',
)
CRK1SchemaValidator().validate('ReproductionSeal', seal.to_dict())
print(seal.to_dict())
"
```

**On failure:** Log failing suite, retain pytest output, file Kernel Challenge if invariant gap (Mission #004).

---

## Evidence bundle (submit with seal)

| Artifact | Path |
|----------|------|
| Test log | `pytest tests/crk1/ --junitxml=m3-results.xml` |
| Packet fingerprint | from Phase 0 |
| Seal JSON | Phase 5 output |
| Steward ID | your `ExternalSteward-*` identifier |
| Environment | OS, Python version, commit SHA |

---

## Quick one-liner (smoke)

```powershell
.\.venv\Scripts\python.exe -m pytest tests\crk1\test_komega_idc_mission003.py tests\crk1\test_crk1_redteam_suite.py tests\crk1\test_mission_003_drift_stress.py -q
```

All green → proceed to full `tests/crk1/` before issuing seal.
