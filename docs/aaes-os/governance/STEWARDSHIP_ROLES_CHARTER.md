# Stewardship Roles Charter

What each layer is responsible for.

## Constitutional Layer Responsibilities

- Define invariants (K-∞, CRC-1 through CRC-7)
- Define admissibility and legitimacy
- Approve or veto architectural changes
- Validate continuity claims (CDP-1)
- Maintain governance integrity

**Stewards:** Wendy, Sue, Nishant, Frank, Maher

## Architecture / Runtime Layer Responsibilities

- Implement CRK-1 runtime invariants
- Maintain deterministic execution
- Define type systems and guardrails
- Implement reconstruction, calibration, lineage, and continuity primitives
- Produce proofs (P₁–P₄)

**Stewards:** You, William J. Storey, Nirvisha, Nitesh

See: [CRK1_FORMAL_SEMANTICS.md](../../crk1/runtime/CRK1_FORMAL_SEMANTICS.md), [CRC-V0.1-CANONICAL-RUNTIME-CONTRACT.md](../../crk1/CRC-V0.1-CANONICAL-RUNTIME-CONTRACT.md)

## Implementation Layer Responsibilities

- Build SDKs, APIs, and developer tools
- Implement production systems
- Maintain infrastructure and scaling
- Integrate runtime with real-world systems
- Ensure operational reliability

**Stewards:** Shakeel, Abdullah, Dhaval, Ravi, Deep, Sachin, Emmanuel, Aun, Mike

See: [CEP_OVERVIEW.md](../../../sdk/continuity-sdk/CEP_OVERVIEW.md)

## Decision Escalation

| Change type | Required authority |
|-------------|-------------------|
| Constitutional / invariant | Foundational supermajority |
| Runtime / kernel | Architectural majority + no Foundational veto |
| Implementation / production | Implementation majority + Architectural sign-off |

## Related

- [AAES_OS_NETWORK_GRAPH.md](./AAES_OS_NETWORK_GRAPH.md)
- [FIRST_WAVE_GOVERNANCE_COUNCIL.md](./FIRST_WAVE_GOVERNANCE_COUNCIL.md)
- [MULTI_STEWARD_GOVERNANCE_CHARTER.md](../../crk1/governance/MULTI_STEWARD_GOVERNANCE_CHARTER.md)
