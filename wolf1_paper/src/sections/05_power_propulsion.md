# 5. Power / Propulsion Controller Spec v1.0

The Power/Propulsion Controller governs energy availability, thermal safety, and propulsion state transitions. It is fully mediated by CAS and evaluated against constitutional invariants.

---

## 5.1 CAS Objects

### PowerState

```json
{
  "solarInput": 0,
  "storageLevel": 0,
  "reactorStatus": "off",
  "thermoGradient": 0,
  "failsafeFloorAvailable": true,
  "mode": "normal"
}
```

| Field | Type | Notes |
|-------|------|-------|
| solarInput | number | watts |
| storageLevel | number | kWh |
| reactorStatus | enum | off \| standby \| nominal \| fault |
| thermoGradient | number | °C delta |
| failsafeFloorAvailable | boolean | governance floor |
| mode | enum | normal \| throttled \| safe-mode |

### PropulsionState

```json
{
  "primaryMode": "idle",
  "stationKeepingMode": "idle",
  "attitudeControlMode": "nominal",
  "propellantLevel": 0,
  "lastBurnTimestamp": "2026-06-25T00:00:00Z"
}
```

| Field | Type | Notes |
|-------|------|-------|
| primaryMode | enum | idle \| burn \| cooldown |
| stationKeepingMode | enum | idle \| active |
| attitudeControlMode | enum | nominal \| hold \| safe |
| propellantLevel | number | kg |
| lastBurnTimestamp | string | ISO 8601 |

### PowerPolicy

```json
{
  "cognitiveMinSolar": 0,
  "cognitiveMinStorage": 0,
  "governanceFloor": 0,
  "thermalBounds": { "min": 0, "max": 0 }
}
```

---

## 5.2 Power Modes

| Mode | Description |
|------|-------------|
| **NORMAL** | Solar + storage meet thresholds; LLM runs allowed |
| **THROTTLED** | Solar low or intermittent; LLM rate‑limited |
| **SAFE‑MODE** | Failsafe floor lost or thermal breach; LLM disabled |

---

## 5.3 Power Mode State Machine

Diagram reference: `assets/diagrams/power_mode_state_machine.mmd`

Transitions:

- NORMAL → THROTTLED (low solar/storage)
- THROTTLED → NORMAL (recovery)
- ANY → SAFE‑MODE (Class A fault)
- SAFE‑MODE → THROTTLED/NORMAL (ground‑authorized recovery)

---

## 5.4 Propulsion Modes

| Mode | Description |
|------|-------------|
| **IDLE** | No burns |
| **BURN** | Primary engine active; CAS logs only |
| **STATION‑KEEPING** | Low‑thrust corrections |
| **ATTITUDE SAFE** | Minimal motion; safe pointing |

---

## 5.5 Transition Rules

| From → To | Condition |
|-----------|-----------|
| NORMAL → THROTTLED | Solar/storage below thresholds |
| THROTTLED → NORMAL | Solar/storage recover |
| ANY → SAFE‑MODE | Failsafe lost / thermal breach |
| SAFE‑MODE → THROTTLED | Ground‑authorized recovery |
| IDLE → BURN | Flight computer command |
| BURN → COOLDOWN | Burn complete |
| ANY → ATTITUDE SAFE | Attitude/power/thermal fault |

---

## 5.6 Controller Behavior

- Every CAS run queries PowerState + PropulsionState
- LLM runs blocked unless mode ∈ {NORMAL, THROTTLED}
- Propulsion events logged but never originated by CAS
- If PowerPolicy corrupted → INV.GOV.FAILED_INVARIANTS_FAIL_CLOSED triggers

---
