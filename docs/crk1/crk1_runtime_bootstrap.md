# CRK-1 Runtime Bootstrap Guide
Version 1.0

This document describes how to initialize a fresh CRK-1 constitutional runtime.

**Core principle:** Immutable exposure, not immutable structure. Everything alive changes;
everything constitutional amends. But no change may create a consequence-free mutation.

---

## 1. Initialize Core Objects

Create the canonical objects:

- `IdentityObject`
- `EvidenceObject`
- `DecisionObject`
- `OutcomeObject`

All must conform to CRK-1 schemas under `fixtures/continuity/`.

---

## 2. Load Constitutional Artifacts

Load:

- `docs/crk1/crk1_state_machine.json`
- `docs/crk1/crk1_invariants.yaml`
- `src/crk1/runtime_validator.py`
- `src/crk1/integrity_monitor.py`
- `src/crk1/governance_engine.py`

These form the constitutional substrate.

---

## 3. Establish the Root Identity

Create the first steward:

```
Identity(Root)
parent_identity_id = null
```

This identity is the initial constitutional authority.

---

## 4. Seed Initial Evidence

Inject the first Evidence object:

```
Evidence(E0)
source_type = "reality"
admissible_for_decision = true
```

This anchors the system to external reality.

---

## 5. Create the First Decision

Root proposes the first constitutional decision:

```
Decision(D0)
identity = Root
input_evidence_ids = [E0]
```

Execute → Outcome → Replay → Evidence.

This establishes the first continuity loop.

---

## 6. Validate Continuity

Run:

- **Runtime Validator** — state machine + K0–K3 invariants
- **Integrity Monitor** — full-system insulation scan
- **Insulation Attack Suite** — automated attack vectors
- **Consequence Preservation gate** — any amendment must pass `GovernanceEngine._preserves_consequence_flow`
- **K4–K6 lattice** — see `docs/crk1/CRK1_CONSEQUENCE_TRANSMISSION_LATTICE.md`

All must pass.

---

## 7. System Ready

At this point:

- The continuity loop is active.
- The lineage chain is initialized.
- The constitutional substrate is live.
- The system is consequence-exposed.

The runtime is ready for governance, amendment, and evolution — but not for insulation.

---

## Quick bootstrap (Python)

```python
from src.continuity.constitutional_runtime import ConstitutionalRuntime, ConstitutionalLedgers
from src.crk1 import CRK1Runtime, CRK1RuntimeValidator, InsulationAttackSimulator
from src.crk1.governance_engine import GovernanceEngine
from src.crk1.integrity_monitor import IntegrityMonitor

# ... bootstrap ledgers (see tests/crk1/conftest.py) ...

facade = CRK1Runtime(kernel)
validator = CRK1RuntimeValidator()
engine = GovernanceEngine(facade, validator)
monitor = IntegrityMonitor(facade, validator)

root_id = kernel.ledgers.identity.id
decision = engine.propose(root_id, {
    "type": "policy",
    "content": {"mission": "establish continuity"},
    "justification": "bootstrap",
    "evidence_ids": ["EVD-CRK1-001"],
})
engine.ratify(decision.id)
monitor.check_continuity()
InsulationAttackSimulator(facade).run_all(root_id)
```

Export dashboard data:

```bash
python tools/export_crk1_dashboard.py
```

Open `docs/crk1/crk1_continuity_dashboard.html`.
