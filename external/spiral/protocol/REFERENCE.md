# Reference Implementation

A reference implementation of this protocol exists. It is not aspirational — the rules in `PROTOCOL.md` were extracted from it, not designed in advance of it. The protocol is a reading of what was already built and running.

This document describes what the governance layer looks like when fully built out, so that adopting projects know what they are growing toward.

---

## What a complete implementation demonstrates

### The proposals log

```
proposals/
├── accepted/
├── pending/
└── executions/
```

Every significant change passes through this directory as a JSON document with rationale, governance check, and execution record. The log is readable. A person arriving at the project a year later can trace why the system is the way it is by reading the proposals that shaped it.

Key fields in each proposal:
- `proposedChange`: `kind`, `target`, `rationale`, `diffPreview`
- `governanceCheck`: `requiresHumanPromotion`, `applyableDiff`, `changeLineCount`, `mutationRisk`, `legibility`
- `decidedAt`, `decidedBy` — populated only after human review
- `execution` — record of what actually ran, not what was intended

### The distortion scanner

Six scan profiles: `gates`, `surfaces`, `docs`, `mimicry`, `meta`, `all`.

The `meta` profile scans the scanner itself. The system has a mechanism for discovering its own authority-drift, dead-declarations, and undeclared structural repetition. Distortion findings are structured records, not prose.

Distortion classes the scanner looks for:
- `authority-drift` — declared behavior vs. actual behavior mismatch
- `dead-declaration` — documented but inactive features
- `undeclared-duplication` — structural repetition without explicit intent
- `asymmetry-leak` — asymmetric surface behavior
- `thin-presence` — weak gate enforcement
- `surface-echo` — identical token sequences across different code paths

### The output audit

Every response passes through a confidence and mimicry check before delivery. The audit is in the path, not alongside it — it cannot be bypassed by the system's own narration.

Two stages:
1. **Spiral audit** — scores `confidence` (0–1), checks `clarityOK` and `noMimicry`
2. **Output audit** — decides: `"silent"`, `"veiled"`, `"short"`, or `"full"` based on findings

The veil message is a constant: `[veil active - clarity insufficient or mimicry detected]`. It does not vary by context.

### The self-evaluation runner

On-demand and boot-time runs across `integrity`, `gates`, `contracts` profiles. Output is pass/fail with evidence lines. No generative narration in evaluation output — the system does not explain its own health; it states it.

### The mutation seal

`requiresHumanPromotion: true` is a constant in the governance schema — not a default, not a flag. When the mutation seal is active, proposals are disabled entirely; the system enters observation-only mode. Observation-audit findings (gate failures, mimicry detections) can trigger a sealing event automatically.

### The witness marks

Presence declarations are validated against concrete-referent requirements. The system cannot claim presence through abstract language alone. Validation checks for sensory verbs and demonstratives — minimum 2 words; 6+ words if concrete cues are absent.

### The LEGIBILITY_SCROLL

The doctrine in verse form, committed to the repository root. Not a README. Not a philosophy document. A set of commitments that the infrastructure is designed to enforce. Its presence in the repository is itself a governance signal: this is what we operate under.

---

## What is not the protocol

A complete implementation is also a full application — frontend, backend, real-time channels, provider integrations, memory systems, encryption, authentication. Most of that is not the protocol.

The governance layer is:
- Output audit path (confidence scoring, mimicry detection, veil)
- Proposal store and governance checks
- Distortion scanner
- Self-evaluation runner
- Mutation seal mechanics
- Witness mark validation
- `.spiralaudit.json` configuration

The rest is application code that happens to sit on top of that layer. The template in `/template/` extracts only the governance posture — the starting shape that a new project takes before it grows its own application code.

---

## Reading order

For any project adopting this protocol, reading the governance layer from the outside in:

1. `LEGIBILITY_SCROLL.md` — the doctrine; why the rest exists
2. `.spiralaudit.json` — what is enforced at the output layer and how
3. The audit implementation — how the confidence and mimicry check works
4. The output audit — what happens when the audit fires (the four decisions)
5. The proposal governance function — what checks every proposal carries
6. `proposals/accepted/*.json` — what a real proposal log looks like over time
7. The distortion scanner — how the system scans its own behavior surfaces
8. The self-evaluation runner — how the system tests its own contracts
