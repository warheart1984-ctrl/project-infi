# Governed Runtime Catalog — Twelve Runtimes

Each runtime is specified using the [Unified Runtime Specification Template](./RUNTIME_SPECIFICATION_TEMPLATE.md).

---

## 1. Constitutional Runtime

| Section | Specification |
|---------|----------------|
| **Purpose** | Define what is legal across all runtimes |
| **Invariants** | No action outside constitutional law; no silent amendment |
| **Evidence** | Constitutional text, amendment receipts, sovereign decisions |
| **Authority** | Foundational sovereignty + explicit amendment process |
| **Reproducibility** | Full replay of constitutional changes and decisions |
| **Impact Boundaries** | Law surface only; no direct domain actions |
| **Accountability** | Founders → Sovereign bodies → Amendment stewards |
| **Failure Modes** | Contradictory articles, illegal amendments, missing receipts |
| **Receipts** | `Amendment*ReceiptV2`, constitutional transition receipts |
| **Transitions** | Proposed → Evaluated → Ratified → Implemented → Observed → Closed |
| **Remediation** | Trigger amendment lifecycle on constitutional failure |
| **Closure** | Amendment fully implemented and observed without divergence |

---

## 2. Continuity Runtime

| Section | Specification |
|---------|----------------|
| **Purpose** | Preserve event lineage, evidence chains, and replayability |
| **Invariants** | No orphan events; no broken chains; no unreceipted transitions |
| **Evidence** | Event logs, timestamps, source identifiers |
| **Authority** | Continuity stewards; system operators |
| **Reproducibility** | Full event replay yields same continuity state |
| **Impact Boundaries** | Lineage metadata; no semantic content changes |
| **Accountability** | Operators → Continuity stewards → Institutional runtime |
| **Failure Modes** | Lineage breaks, missing events, conflicting histories |
| **Receipts** | `ContinuityReceiptV2`, `DivergenceReceiptV2` |
| **Transitions** | EventRecorded → Observed → Challenged → Arbitrated → Remediated → Closed |
| **Remediation** | Repair lineage or mark irreparable with explicit divergence |
| **Closure** | Lineage reconciled or formally marked divergent |

---

## 3. UCR (Ultima Cognitive Runtime)

| Section | Specification |
|---------|----------------|
| **Purpose** | Govern reasoning, memory, validation, and execution modes |
| **Invariants** | No reasoning outside allowed modes; no ungoverned execution |
| **Evidence** | Prompts, tool calls, receipts, mode selections |
| **Authority** | Cognitive governance policies; operator constraints |
| **Reproducibility** | Same inputs + modes → same governed trace |
| **Impact Boundaries** | Cognitive outputs and tool invocations only |
| **Accountability** | Runtime designers → operators → institutional oversight |
| **Failure Modes** | Mode misuse, ungoverned tool calls, irreproducible traces |
| **Receipts** | Cognitive receipts, tool-call receipts |
| **Transitions** | PlanProposed → Evaluated → Approved → Executed → Observed → Challenged → Closed |
| **Remediation** | Re-plan under stricter modes; escalate to Arbitration |
| **Closure** | Plan validated or superseded with receipts |

---

## 4. Truth Verification Runtime

| Section | Specification |
|---------|----------------|
| **Purpose** | Govern claims, evidence, and confidence |
| **Invariants** | No truth without verification; no claim without evidence |
| **Evidence** | `EvidenceBundleV2` meeting sufficiency thresholds |
| **Authority** | Truth stewards; configured verification policies |
| **Reproducibility** | Same evidence → same truth verdict |
| **Impact Boundaries** | Claim status only |
| **Accountability** | Truth stewards → institutional oversight |
| **Failure Modes** | Insufficient evidence, conflicting evidence |
| **Receipts** | `TruthReceiptV2`, `DivergenceReceiptV2` |
| **Transitions** | ClaimProposed → Supported → Verified → Challenged → Arbitrated → Remediated → Closed |
| **Remediation** | Re-evaluate with updated evidence |
| **Closure** | Claim status stable under current evidence |

---

## 5. Sovereignty Runtime

| Section | Specification |
|---------|----------------|
| **Purpose** | Govern authority, jurisdiction, consent, delegation, legitimacy |
| **Invariants** | No authority without evidence; no self-authorization |
| **Evidence** | Delegation chains, consent records, jurisdictional rules |
| **Authority** | Sovereign entities and delegation graphs |
| **Reproducibility** | Same delegation graph → same authority verdict |
| **Impact Boundaries** | Authority status; no direct execution |
| **Accountability** | Sovereign bodies → institutional runtime |
| **Failure Modes** | Invalid delegation, conflicting authorities |
| **Receipts** | `SovereigntyReceiptV2`, delegation/revocation receipts |
| **Transitions** | AuthorityRequested → Delegated → Active → Suspended → Revoked → Closed |
| **Remediation** | Correct delegation graph; revoke illegitimate authority |
| **Closure** | Authority validly active or formally revoked |

---

## 6. Knowledge Graph Runtime

| Section | Specification |
|---------|----------------|
| **Purpose** | Maintain machine-readable relationships between entities, events, evidence |
| **Invariants** | No dangling references; no contradictory edges without marking |
| **Evidence** | Source documents, receipts, provenance |
| **Authority** | Graph stewards; ingestion policies |
| **Reproducibility** | Same inputs → same graph state |
| **Impact Boundaries** | Graph structure only |
| **Accountability** | Data stewards → institutional runtime |
| **Failure Modes** | Inconsistent graph, missing provenance |
| **Receipts** | Graph update receipts, conflict receipts |
| **Transitions** | NodeCreated/EdgeCreated → Observed → Challenged → Arbitrated → Remediated → Closed |
| **Remediation** | Mark conflicts; correct or annotate edges |
| **Closure** | Segment reconciled or explicitly marked conflicted |

---

## 7. Institutional Runtime

| Section | Specification |
|---------|----------------|
| **Purpose** | Model organizations, incentives, policies, decision structures |
| **Invariants** | No decision outside institutional procedure |
| **Evidence** | Meeting records, votes, policy documents |
| **Authority** | Institutional charters and roles |
| **Reproducibility** | Same procedure + inputs → same institutional decision |
| **Impact Boundaries** | Institutional decisions only |
| **Accountability** | Institutional leaders → governance bodies |
| **Failure Modes** | Procedural violations, unrecorded decisions |
| **Receipts** | `InstitutionalReceiptV2`, audit receipts |
| **Transitions** | Draft → Approved → Executed → Observed → Audited → Amended → Closed |
| **Remediation** | Re-run or amend decisions under proper procedure |
| **Closure** | Decision validated or superseded |

---

## 8. Reality Runtime

| Section | Specification |
|---------|----------------|
| **Purpose** | Connect models to observed reality (docs, APIs, sensors) |
| **Invariants** | No reality claim without source |
| **Evidence** | Source documents, API responses, sensor logs |
| **Authority** | Reality stewards; source registries |
| **Reproducibility** | Same sources → same reality verdict |
| **Impact Boundaries** | Reality claims only |
| **Accountability** | Data providers → reality stewards → institutional runtime |
| **Failure Modes** | Conflicted sources, unverifiable data, stale reality |
| **Receipts** | Reality receipts, source conflict receipts |
| **Transitions** | ClaimObserved → Verified → Challenged → Diverged → Remediated → Closed |
| **Remediation** | Update or deprecate sources; mark uncertainty |
| **Closure** | Claim stable or explicitly unresolved |

---

## 9. ControlTower Runtime

| Section | Specification |
|---------|----------------|
| **Purpose** | Measure and audit actual AI behavior in production |
| **Invariants** | No unobserved behavior; no unmeasured drift |
| **Evidence** | Logs, metrics, traces, receipts |
| **Authority** | Audit authorities; safety stewards |
| **Reproducibility** | Same inputs → same audit findings |
| **Impact Boundaries** | Audit findings only |
| **Accountability** | System owners → safety stewards → regulators |
| **Failure Modes** | Undetected drift, missing logs |
| **Receipts** | Control tower receipts, drift receipts |
| **Transitions** | BehaviorObserved → Evaluated → Flagged → Remediated → Closed |
| **Remediation** | Mitigate drift; adjust policies or models |
| **Closure** | Behavior back within governed bounds |

---

## 10. Reproduction Runtime

| Section | Specification |
|---------|----------------|
| **Purpose** | Govern independent reproduction of decisions and states |
| **Invariants** | No claim of correctness without reproducibility |
| **Evidence** | Inputs, configs, receipts, environment descriptors |
| **Authority** | Reproduction stewards; observer roles |
| **Reproducibility** | Same inputs → same outputs and receipts |
| **Impact Boundaries** | Reproduction verdicts only |
| **Accountability** | Original decision owners → reproduction stewards |
| **Failure Modes** | Divergent reproductions, missing inputs |
| **Receipts** | `ReproductionReceiptV2`, `DivergenceReceiptV2` |
| **Transitions** | ReproductionRequested → Executed → Observed → Diverged/Matched → Remediated → Closed |
| **Remediation** | Investigate divergence; correct or deprecate original decision |
| **Closure** | Reproduction matches or is formally marked divergent |

---

## 11. Arbitration Runtime

| Section | Specification |
|---------|----------------|
| **Purpose** | Resolve cross-runtime conflicts and divergences |
| **Invariants** | No unresolved conflict; no silent override |
| **Evidence** | Conflicting receipts, evidence bundles, state snapshots |
| **Authority** | Arbitrators; sovereign backing |
| **Reproducibility** | Same conflict → same arbitration outcome |
| **Impact Boundaries** | Conflict resolution only |
| **Accountability** | Arbitrators → sovereignty → institutional runtime |
| **Failure Modes** | Unresolved conflicts, biased arbitration |
| **Receipts** | `ArbitrationReceiptV2`, precedence receipts |
| **Transitions** | ConflictDetected → Evaluated → Ruled → Remediated → Closed |
| **Remediation** | Update affected states and receipts per ruling |
| **Closure** | Conflict resolved and reflected in state |

---

## 12. Domain Runtimes (DAR-Z, Legal, Tribal, Simulation, Civilization)

Each domain runtime instantiates the same template with domain-specific content:

| Section | Pattern |
|---------|---------|
| **Purpose** | Domain-specific responsibilities (mission governance, legal case flow, tribal sovereignty, simulation, civilization dynamics) |
| **Invariants** | Domain guarantees (no retroactive law, valid tribal authority, etc.) |
| **Evidence** | Domain records (cases, treaties, mission logs, simulation events) |
| **Authority** | Domain authorities (courts, councils, game masters) |
| **Reproducibility** | Same domain inputs → same governed outcomes |
| **Impact Boundaries** | Domain scope only |
| **Accountability** | Domain stewards → sovereignty + institutional runtimes |
| **Failure Modes** | Domain-specific violations |
| **Receipts** | Domain receipts (e.g. DAR-Z MissionReceipt, LegalJudgmentReceipt) |
| **Transitions** | Domain mapping onto the universal constitutional graph |
| **Remediation** | Domain-appropriate remediation |
| **Closure** | Domain-specific closure criteria |

---

**Implementation:** Core state graph and runtime in `constitutional_state/`; Receipt v2 and operator integration in `constitutional_substrate/`.
