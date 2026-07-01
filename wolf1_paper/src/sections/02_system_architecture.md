# 2. System Architecture Overview

WOLF‑1 is structured as a four‑layer stack:

| Layer | Components | Key Property |
|-------|------------|--------------|
| **Physical Layer** | Radiation‑tolerant compute, power subsystem (solar + nuclear + thermoelectric), thermal management, comms | Survives the environment |
| **Platform Layer** | OS, container isolation, storage, telemetry | Software substrate |
| **Cognitive Governance Layer** | CRK‑1, CAS API, invariant engine, RunLedger, FaultJournal | Constitutional substrate |
| **Cognitive Tenant Layer** | LLMs, tooling adapters, sandbox | Intelligence substrate (proposals only) |

---
