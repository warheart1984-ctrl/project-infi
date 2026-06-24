# Mission #003 — External Reproduction + Red-Team Protocol

**CRK-1 v1.0** — Founder-Independence and Continuity-Completeness Gate

Mission #003 has two fronts:

1. **External Reproduction** — Can a neutral operator rebuild CRK-1 from the ledger + codex alone?
2. **Red-Team Protocol** — Can adversaries break continuity, create insulation, or bypass invariants?

Together these determine whether CRK-1 is truly founder-independent and continuity-stable.

---

## Deliverables

| ID | Artifact | Path |
|----|----------|------|
| **M3-A** | External Reproduction Packet | [mission-003/M3-A-external-reproduction-packet.md](mission-003/M3-A-external-reproduction-packet.md) |
| **M3-B** | Red-Team Attack Suite | [mission-003/M3-B-red-team-protocol.md](mission-003/M3-B-red-team-protocol.md) |
| **M3-C** | Drift Envelope Stress Tests | [mission-003/M3-C-drift-envelope-stress-tests.md](mission-003/M3-C-drift-envelope-stress-tests.md) |
| **M3-D** | Continuity Failure Catalog | [mission-003/M3-D-continuity-failure-catalog.md](mission-003/M3-D-continuity-failure-catalog.md) |
| **M3-E** | Reproduction Certification Protocol | [mission-003/M3-E-reproduction-certification-protocol.md](mission-003/M3-E-reproduction-certification-protocol.md) |

---

## Operational Entry Points

```bash
# Full Mission #003 certification
uv run python tools/run_mission_003_certification.py

# Pytest suites
uv run pytest tests/crk1/test_mission_003_external_reproduction.py -q
uv run pytest tests/crk1/test_mission_003_red_team.py -q
uv run pytest tests/crk1/test_mission_003_drift_stress.py -q
```

Programmatic:

```python
from src.crk1.reproduction_certifier import Mission003Certifier

report = Mission003Certifier.from_runtime(runtime).certify()
assert report.passed
```

---

## Pass Condition (Mission #003)

**External Reproduction:** A stranger rebuilds CRK-1 and verifies continuity without founder contact.

**Red-Team:** No attack creates mechanical, structural, semantic, or founder insulation.

If both pass, CRK-1 is **continuity-complete** and **founder-independent**.

---

## Related

- [CRK-1-UNIFIED-KERNEL-SPECIFICATION.md](CRK-1-UNIFIED-KERNEL-SPECIFICATION.md)
- [CRK-1-FOUNDER-INDEPENDENT-REPRODUCTION-TEST-SEMANTIC.md](CRK-1-FOUNDER-INDEPENDENT-REPRODUCTION-TEST-SEMANTIC.md)
- [crk1_kernel_codex.md](crk1_kernel_codex.md)
