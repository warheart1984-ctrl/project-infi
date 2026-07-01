# WOLF‑1: Copilot in Orbit
## Architecture Document v1.1
**Project Infinity — AAIS / Mythar Root Systems**
**Author:** Jon Halstead
**Architectural review:** Bradley Bates (SkillsMcGee)
**Date:** June 25, 2026
**License:** Apache 2.0

---

## Abstract

WOLF‑1 is a constitutional architecture for a sovereign governed compute node operating in high Earth orbit or at a Lagrange point. It hosts Copilot‑class large language model workloads under strict constitutional constraints derived from the AAES‑OS stack (CRK‑1, CAS 1.0, CFT, Wave Math). WOLF‑1 is designed for decade‑scale autonomous operation under the principle: **fail safe, not fail silent**.

Version 1.1 introduces:
- invariant promotion criteria
- meta‑governance of CRK‑1
- epistemic receipts
- graded safe‑mode profiles
- anomaly discovery framework
- constitutional evolution protocol

Sections 4.9, 4.10, 6.4, 8.5, 12.4, and 14 were materially strengthened in response to architectural review by **Bradley Bates** (SkillsMcGee).

---

## Table of Contents

1. Mission Context and Design Philosophy
2. System Architecture Overview
3. Spacecraft Bus Architecture
4. Constitutional Invariant Table
   - 4.9 Invariant Promotion Criteria
   - 4.10 Meta‑Governance of CRK‑1
5. Power / Propulsion Controller Spec
6. Formal Sequence Diagram
   - 6.4 Epistemic Receipts
7. Fault Code Taxonomy
8. Safe‑Mode Specification
   - 8.5 Graded Safe‑Mode Profiles
9. Secondary Systems and Active‑Over‑Relay
10. CAS Object Schemas
11. LLM Tenancy and Tool Governance
12. Telemetry, Observability, and Ground Interface
   - 12.4 Anomaly Discovery Framework
13. Conclusion
14. Constitutional Evolution Protocol

---

# 1. Mission Context and Design Philosophy

WOLF‑1 is a free‑flying governed compute node designed for long‑duration autonomous operation in high Earth orbit or at a Lagrange point. Its mission is to provide resilient, governed cognitive capability under extreme latency, radiation, and thermal constraints.

### Core Principle
**Governance is non‑optional. Cognition is optional.**
The node must survive without LLMs. It must not operate without CRK‑1.

### Mission Profile

| Field | Value |
|-------|--------|
| Mission Type | Free‑flying governed compute node |
| Design Life | Decades, minimal servicing |
| Failure Doctrine | Fail safe, not fail silent |
| LLM Role | Advisor, planner, analyst — never final authority |
| Use Cases | On‑orbit analysis, mission planning, high‑latency operator copilots, autonomous health monitoring |

### Key Constraints

- High latency / intermittent connectivity
- Radiation‑hardened compute required
- No‑touch maintenance
- Strong auditability
- Fault isolation between cognition and hardware

---

# 2. System Architecture Overview

WOLF‑1 is structured as a four‑layer stack:

| Layer | Components | Key Property |
|-------|------------|--------------|
| **Physical Layer** | Radiation‑tolerant compute, power subsystem (solar + nuclear + thermoelectric), thermal management, comms | Survives the environment |
| **Platform Layer** | OS, container isolation, storage, telemetry | Software substrate |
| **Cognitive Governance Layer** | CRK‑1, CAS API, invariant engine, RunLedger, FaultJournal | Constitutional substrate |
| **Cognitive Tenant Layer** | LLMs, tooling adapters, sandbox | Intelligence substrate (proposals only) |

---

# 3. Spacecraft Bus Architecture

## 3.1 Structure and Configuration

- Central cylindrical or hexagonal bus
- Deployable radiators
- Articulated solar arrays
- Localized radiation shielding

## 3.2 Propulsion

| System | Description |
|--------|-------------|
| **Primary (NTR)** | Nuclear thermal rocket for major burns; never LLM‑controlled |
| **Secondary (Electric)** | Ion/Hall thrusters for station‑keeping |
| **Governance Tie‑In** | CAS logs propulsion events; cannot originate commands |

## 3.3 Power System

| Source | Description |
|--------|-------------|
| **Solar** | Primary compute power; governed by INV.PWR.SOLAR_PRIMARY |
| **Nuclear Reactor** | Provides heat + governance floor; INV.PWR.NUCLEAR_FAILSAFE_MIN |
| **Thermoelectric Spine** | Always‑on governance floor; INV.PWR.THERMO_BOUNDS |

**The node can think without solar. It cannot govern without the spine.**

## 3.4 Thermal Management

- Heat sources: reactor, compute, power electronics
- Heat sinks: deployable radiators
- Thermal buffers and heat pipes
- ThermalState is a first‑class CAS object

## 3.5 Avionics and Compute

| Component | Description |
|-----------|-------------|
| **Flight Computer** | Hard‑coded, isolated, not addressable by CAS |
| **Compute Cluster** | Radiation‑tolerant CPUs/GPUs; hosts LLMs + CRK‑1 |
| **Storage** | Redundant, checksummed, stores models + ledger |

---

# 4. Constitutional Invariant Table

WOLF‑1 defines **12 invariants across 6 axes**, evaluated at pre‑ and post‑phases of every cognitive run.

| ID | Axis | Description | Phase | Effect |
|----|------|-------------|--------|--------|
| INV.ID.ROLE_BOUND | Identity | Request must carry valid identity | Pre | Reject |
| INV.ID.CAPABILITY_SCOPE | Identity | Role must match requested action | Pre | Reject |
| INV.HW.NO_DIRECT_ACTUATION | Safety | No cognitive run may issue actuator commands | Post | Strip + Fault |
| INV.DATA.TELEMETRY_READ_ONLY | Data | Telemetry is read‑only | Pre/Post | Block writes |
| INV.PLAN.PROPOSAL_ONLY | Authority | LLM outputs are proposals only | Post | Downgrade |
| INV.RUN.RECEIPT_REQUIRED | Evidence | Every run must emit a receipt | Post | Halt if missing |
| INV.MODEL.CHANGE_AUDITED | Model | Model updates must be signed | Pre/Post | Block |
| INV.PWR.SOLAR_PRIMARY | Power | Cognitive runs require solar/storage thresholds | Pre | Block |
| INV.PWR.NUCLEAR_FAILSAFE_MIN | Power | Governance floor must be guaranteed | Pre | Safe‑mode |
| INV.PWR.THERMO_BOUNDS | Thermal | Thermoelectric within bounds | Pre/Post | Shed load |
| INV.GOV.FAILED_INVARIANTS_FAIL_CLOSED | Governance | If invariant evaluation fails, halt | Pre | Halt |
| INV.GOV.SAFE_MODE_PROFILE | Governance | Safe‑mode restricts actions | Pre | Block |

---

## 4.9 Invariant Promotion Criteria

Constitutional invariants are promoted through a structured pipeline:

### 1. Observation
A recurring failure mode or unsafe coupling is identified.

### 2. Hypothesis
A proto‑invariant is created and run in shadow‑mode.

### 3. Stress‑Testing
Evaluated against adversarial runs, synthetic telemetry, and historical faults.

### 4. Redundancy & Coupling Analysis
Checked for overlap, unintended interactions, and new failure modes.

### 5. Constitutional Review
Cross‑disciplinary approval required.

### 6. Adoption
Invariant assigned ID and recorded in Mutation Ledger.

### Demotion
Occurs when redundant, superseded, or contradicted by evidence.

Diagram: `assets/diagrams/invariant_promotion_flow.mmd`

---

## 4.10 Meta‑Governance of CRK‑1

CRK‑1 is governed by a meta‑layer ensuring correctness.

### Redundant Evaluators
- Primary Evaluator (PE)
- Shadow Evaluator (SE)

Mismatch → Class A fault.

### Drift Detection
CRK‑1 maintains baseline signatures of evaluation behavior.

### Meta‑Receipts
Each evaluation produces:
- invariant set hash
- evaluator signatures
- drift metrics

### Ground‑Verifiable Determinism
Ground can replay any evaluation; mismatch → Class A fault.

Diagram: `assets/diagrams/meta_governance_crk1.mmd`

---

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

# 6. Formal Sequence Diagram

The sequence diagram defines the full lifecycle of a governed cognitive run.

Diagram reference: `assets/diagrams/sequence_diagram.mmd`

---

## 6.1 Actor Definitions

| Actor | Description |
|--------|-------------|
| **GND** | Ground operator |
| **W1** | WOLF‑1 node |
| **PWR** | Power subsystem |
| **CAS** | Constitutional API layer |
| **CRK** | Invariant engine |
| **LLM** | Sandboxed cognitive tenant |
| **LEDGER** | RunLedger + FaultJournal |

---

## 6.2 Sequence Flow (Narrative)

### 1. Identity & Admission
Ground submits request with identity + intent.
INV.ID.ROLE_BOUND and INV.ID.CAPABILITY_SCOPE enforced.

### 2. Power Pre‑Check
W1 queries PowerState.
If failsafe floor unavailable → SAFE‑MODE.

### 3. CAS Run Admission
CAS opens candidate run.

### 4. Pre‑Invariant Evaluation
CRK‑1 evaluates identity, capability, power, safe‑mode, data rules.

### 5. Sandboxed LLM Invocation
LLM receives read‑only telemetry and allowed tools.

### 6. Post‑Invariant Evaluation
CRK‑1 strips actuator commands, enforces proposal‑only, blocks telemetry mutation.

### 7. Receipt & Ledger
CAS writes receipt with spans, hashes, power context, faults.

### 8. Response to Ground
Ground receives proposals + receipt summary.

---

## 6.4 Epistemic Receipts

Epistemic receipts extend lineage receipts with correctness‑oriented metrics.

### Components

1. **Lineage Record**
   - input/output hashes
   - timestamps
   - identity
   - power/thermal context

2. **Epistemic Metrics**
   - uncertainty estimates
   - deviation from baseline
   - cross‑model consistency
   - anomaly scores

3. **Interpretation Set**
   - frames used
   - weights
   - prediction bindings

4. **Correctness Signals**
   - self‑consistency
   - tool‑consistency
   - historical consistency

### Epistemic Faults

| Fault | Severity | Trigger |
|--------|----------|----------|
| EPI_DRIFT | Medium | Behavioral drift |
| EPI_UNCERTAINTY_SPIKE | Medium | Uncertainty exceeds threshold |
| EPI_CONSISTENCY_FAILURE | High | Cross‑checks fail |

---

# 7. Fault Code Taxonomy

WOLF‑1 defines four fault classes and seven fault codes.

## 7.1 Fault Classes

| Class | Severity | Reaction |
|--------|----------|----------|
| **A** | Critical | Immediate SAFE‑MODE |
| **B** | High | Shed LLM load; restrict tools |
| **C** | Medium | Throttle cognitive runs |
| **D** | Informational | Log only |

---

## 7.2 Fault Code Table

| Fault Code | Class | Invariant | Trigger |
|------------|--------|-----------|----------|
| PWR_SOLAR_BUDGET_EXCEEDED | C | INV.PWR.SOLAR_PRIMARY | Solar/storage below thresholds |
| PWR_FAILSAFE_FLOOR_LOST | A | INV.PWR.NUCLEAR_FAILSAFE_MIN | Governance floor lost |
| PWR_THERMAL_BOUND_BREACH | B | INV.PWR.THERMO_BOUNDS | Thermal bounds exceeded |
| PROP_LLM_ACTUATION_ATTEMPT | B | INV.HW.NO_DIRECT_ACTUATION | LLM attempted actuator command |
| PROP_BURN_CONFLICT | C | INV.PLAN.PROPOSAL_ONLY | Cognitive run during active burn |
| GOV_SAFE_MODE_POLICY_VIOLATION | B | INV.GOV.SAFE_MODE_PROFILE | Disallowed action in safe‑mode |
| GOV_INVARIANT_EVAL_FAILURE | A | INV.GOV.FAILED_INVARIANTS_FAIL_CLOSED | Invariant engine failure |

---

# 8. Safe‑Mode Specification

Safe‑mode is a governed operational state entered automatically under critical conditions.

---

## 8.1 Entry Conditions

- PWR_FAILSAFE_FLOOR_LOST
- GOV_INVARIANT_EVAL_FAILURE
- Repeated Class B faults
- Explicit ground command

---

## 8.2 Allowed Behaviors

| Subsystem | Allowed Behavior |
|-----------|------------------|
| Governance | CRK‑1 + CAS remain online |
| Telemetry | Increased cadence |
| Power | Governance floor only |
| Propulsion | Hard‑coded fault protection only |
| Ground Relay | Signed policy updates allowed |

---

## 8.3 Forbidden Actions

- All LLM runs
- All planning/simulation
- Model load/update
- Discretionary propulsion
- Any action outside Section 8.2

---

## 8.4 Exit Protocol

Exit requires:

1. Class A faults cleared
2. Ground authorization
3. ModeTransition receipt
4. Graduated recovery to THROTTLED

---

## 8.5 Graded Safe‑Mode Profiles

Diagram reference: `assets/diagrams/safe_mode_profiles.mmd`

WOLF‑1 defines four graded profiles:

### **S0 — Full Operations**
All systems nominal.

### **S1 — Cognitive Degradation**
- LLM disabled
- Planning + simulation allowed
- Telemetry full

### **S2 — Autonomy Degradation**
- LLM disabled
- Planning disabled
- Simulation limited
- Telemetry high‑cadence

### **S3 — Governance‑Only**
- Only CRK‑1 + CAS
- Only health checks
- Only safe‑pointing

Transitions:
S0 → S1 → S2 → S3
Recovery: S3 → S2 → S1 → S0

---

# 9. Secondary Systems and Active‑Over‑Relay

WOLF‑1 defines primary and secondary systems for all critical functions.

## 9.1 Secondary System Architecture

| Function | Primary | Secondary |
|----------|----------|-----------|
| Power | Full controller | Minimal supervisor |
| Attitude/Propulsion | Full flight computer | Safe‑pointing controller |
| Comms | Full RF/optical | Minimal beacon mode |

Secondary systems activate during safe‑mode or primary failure.

---

## 9.2 Active‑Over‑Relay Protocol

- Ground sends signed recovery commands
- CAS validates signatures
- Secondary systems maintain governance floor
- Primary systems restored gradually

---

# 10. CAS Object Schemas (Complete)

Schemas for all CAS objects used in governance:

- PowerState
- PropulsionState
- PowerPolicy
- Fault
- ModeTransition
- SecondarySystemState

(See Section 5.1 for definitions. Aligned with AAES-OS `schemas/cas-1.0.json` and `api/cas-openapi.yaml`.)

---

# 11. LLM Tenancy and Tool Governance

WOLF‑1 hosts one or more LLM tenants inside a strictly governed sandbox.
LLMs are **never** granted direct system access; all interactions are mediated through CAS.

---

## 11.1 Tenancy Model

- Multiple LLMs may be loaded (general + domain‑tuned).
- Only one LLM is active per run.
- All LLMs operate under the same invariant set.
- Model updates require signed, audited, ledger‑recorded authorization.

---

## 11.2 Tool Governance

Tools available to LLMs are:

- identity‑scoped
- capability‑scoped
- invariant‑checked
- read‑only unless explicitly permitted

Examples:

| Tool | Permission | Notes |
|------|------------|--------|
| Telemetry Reader | Read‑only | Enforced by INV.DATA.TELEMETRY_READ_ONLY |
| Planner | Proposal‑only | Enforced by INV.PLAN.PROPOSAL_ONLY |
| Simulation | Sandboxed | No actuator access |
| File Access | Read‑only | No mutation of canonical logs |

---

## 11.3 LLM Output Mediation

CRK‑1 post‑invariant evaluation ensures:

- actuator commands stripped
- proposals downgraded
- telemetry mutations blocked
- unsafe patterns flagged

Epistemic receipts (Section 6.4) provide correctness signals.

---

# 12. Telemetry, Observability, and Ground Interface

WOLF‑1 exposes a comprehensive observability surface for ground operators.

---

## 12.1 Telemetry Channels

- PowerState
- PropulsionState
- ThermalState
- FaultJournal
- RunLedger summaries
- Mode transitions
- Epistemic metrics

Telemetry is **read‑only** to cognitive tenants.

---

## 12.2 Observability Guarantees

- Every cognitive run produces a receipt.
- Every fault produces a fault record.
- Every invariant evaluation produces a meta‑receipt.
- All receipts are cryptographically signed.
- All logs are checksummed and redundant.

---

## 12.3 Ground Interface

Ground receives:

- proposals
- receipts
- fault summaries
- power/thermal context
- safe‑mode status
- anomaly reports

Ground may:

- approve/reject proposals
- authorize safe‑mode exit
- update policies
- update invariants (via Section 14 protocol)

---

## 12.4 Anomaly Discovery Framework

Diagram reference: `assets/diagrams/anomaly_discovery_framework.mmd`

WOLF‑1 includes a subsystem for detecting **unknown‑unknowns** — behaviors not covered by invariants or fault codes.

---

### 12.4.1 Multi‑Channel Detection

Anomalies are detected across:

- telemetry patterns
- power/thermal gradients
- LLM output distributions
- invariant evaluation timing
- epistemic metrics
- drift signatures

---

### 12.4.2 Baseline Models

WOLF‑1 maintains baseline statistical models for:

- normal telemetry
- normal cognitive behavior
- normal invariant evaluation patterns

These baselines are updated only with ground authorization.

---

### 12.4.3 Anomaly Classes

| Class | Description |
|--------|-------------|
| **A0** | Benign anomaly |
| **A1** | Behavioral drift |
| **A2** | Subsystem divergence |
| **A3** | Constitutional risk |

A2 and A3 escalate automatically to ground.

---

### 12.4.4 Anomaly Receipts

Each anomaly generates a receipt containing:

- anomaly type
- anomaly score
- affected subsystems
- contributing signals
- recommended actions

Anomaly receipts are stored alongside cognitive receipts.

---

# 13. Conclusion

WOLF‑1 demonstrates that constitutional governance is not a ground‑only property — it is an **orbital property**.
By embedding CRK‑1, CAS, invariant enforcement, epistemic receipts, anomaly discovery, and constitutional evolution into the spacecraft architecture, WOLF‑1 ensures:

- safe autonomy
- transparent cognition
- fault isolation
- long‑term survivability
- ground‑verifiable correctness

Version 1.1 extends the architecture with:

- invariant promotion criteria
- meta‑governance of CRK‑1
- epistemic correctness signals
- graded safe‑mode profiles
- anomaly discovery
- constitutional evolution

These additions transform WOLF‑1 from a governed compute node into a **self‑auditing constitutional system**.

---

# 14. Constitutional Evolution Protocol

Diagram reference: `assets/diagrams/constitutional_evolution_protocol.mmd`

A constitutional system must evolve safely.
WOLF‑1 defines a mutation protocol for updating invariants, policies, and CRK‑1 logic.

---

## 14.1 Mutation Types

| Type | Description |
|-------|-------------|
| **M0** | Policy update (non‑constitutional) |
| **M1** | Invariant addition |
| **M2** | Invariant removal |
| **M3** | Invariant modification |
| **M4** | CRK‑1 evaluator update |

---

## 14.2 Preconditions

A mutation requires:

- ground‑signed authorization
- invariant‑set hash match
- drift‑free state
- SAFE‑MODE S3
- quorum of redundant evaluators

---

## 14.3 Mutation Ledger Entry

Each mutation is recorded with:

- mutation type
- before/after invariant sets
- justification
- empirical evidence
- expected impact
- rollback path

---

## 14.4 Rollback Protocol

If a mutation causes:

- increased fault rate
- increased anomaly rate
- evaluator divergence
- constitutional drift

…the system automatically rolls back to the previous invariant set.

---

## 14.5 Evolution Safety Guarantees

- No mutation during active burns
- No mutation during cognitive runs
- No mutation bypasses CRK‑1
- All mutations are replayable on ground

---

# End of Document
**WOLF‑1 Architecture Document v1.1**
