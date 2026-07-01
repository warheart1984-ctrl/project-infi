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
