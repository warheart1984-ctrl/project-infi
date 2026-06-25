# Mission #003

**External Reproduction & Red-Team Certification**

## Objective

Prove CRK-1 can be rebuilt and defended by an external steward without founder dependence.

## Levels

| Level | Requirement |
|-------|-------------|
| R1 | Substrate reproducible |
| R2 | Invariants verified |
| R3 | Semantic reproduction (K7–K12) |
| R4 | Red-team suite B1–B4 blocked |
| R5 | Drift envelope stress (9/9) |

## Artifacts

- External reproduction packet (M3-A)
- Red-team protocol (M3-B)
- Drift stress (M3-C)
- Failure catalog (M3-D)
- D-3 Reproduction Seal (M3-E)

## Run

```bash
python tools/run_mission_003_certification.py --json
python tools/run_mission_003_certification.py --d3-seal
```

## Docs

- [Operator Manual](../crk1/mission-003/MISSION-003-OPERATOR-MANUAL.md)
- [Reproduction Checklist](../crk1/mission-003/MISSION-003-REPRODUCTION-CHECKLIST.md)
- [D-3 Seal](../crk1/mission-003/D3-SEAL-reproduction-certificate.md)
