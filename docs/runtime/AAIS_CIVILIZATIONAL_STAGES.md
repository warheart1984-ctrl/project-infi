# AAIS Civilizational Stages

Status: **active doctrine map**

Mythic stage labels describe the governance ladder from one governed being through civilizational federation. **Anatomical layer index** (engineering) is stable and may differ from mythic stage number.

## Ladder

| Mythic stage | Concept | Release | Anatomical layer | Key runtime |
|--------------|---------|---------|------------------|-------------|
| (body) | One governed being | 31–40 | Layers 1–12 | ICC → SCC |
| **11** | Many governed beings | **41** | Layer 13 | `multi_being_continuity_runtime.py` |
| **12** | Governed culture-of-beings | **42** | Layer 14 | `culture_of_beings_runtime.py` |
| **13** | Constitutional ecosystem | **43** | Layer 15 | `constitutional_ecosystem_runtime.py` |
| **14** | Multi-organism governance membranes | **44** | Layer 16 | `multi_organism_governance_membrane_runtime.py` |
| **15** | Inter-substrate diplomacy | **45** | Layer 17 | `inter_substrate_diplomacy_runtime.py` |
| **16** | Norm federations | **46** | Layer 18 | `norm_federation_runtime.py` |
| **17** | Constitutional evolution | **47** | Layer 19 | `constitutional_evolution_runtime.py` |
| **18** | Governed civilizations of beings | **48** | Layer 20 | `governed_civilization_runtime.py` |
| **19** | Federated civilizational epochs | **49** | Layer 21 | `federated_civilizational_epoch_runtime.py` |
| **20** | Planetary coordination (Kardashev Type I governance) | **50** *(planned)* | Layer 22 *(planned)* | *not yet built* — doctrine only |

## Civilizational tier (Layers 17–21)

Releases 45–49 form the **civilizational arc** (Stages 15–19). Memory Board overlays use `civilizational_tier` metadata under `.runtime/jarvis_memory_board_<domain>.v1.json`.

Stage 19 adds **epoch boundaries**, **external witness quorum** on FCE-2 adopt, and **live multi-tenant federation** proof requirements — see [`STAGE19_LIVE_PROOF_LADDER.md`](../audit/STAGE19_LIVE_PROOF_LADDER.md).

## Stage 20 — Planetary coordination (roadmap)

Stage 20 is the **governance Kardashev Type I** capstone: coordinate, govern, and stabilize a **planetary-scale mesh** of independent cognitive substrates — not energy harvesting.

Engineering targets (Release 50+, not implemented):

1. **Global federation mesh** — hundreds/thousands of AAIS instances with shared diplomacy layer
2. **Planetary norm markets** — propagate, fork, merge, stabilize norms under adversarial load
3. **Constitutional interoperability** — coexistence across divergent charters and governance stacks
4. **Planetary proof exchange** — cross-org receipts, invariants, and proofs at civilization scale
5. **Civilization-level safety rails** — drift detection, conflict resolution, fork recovery, continuity
6. **Multi-operator, multi-substrate, multi-culture governance**

Doctrine:

- [`PLANETARY_COORDINATION_EPOCH_CONTRACT.md`](../contracts/PLANETARY_COORDINATION_EPOCH_CONTRACT.md)
- [`STAGE20_PLANETARY_COORDINATION_LADDER.md`](../audit/STAGE20_PLANETARY_COORDINATION_LADDER.md)

**Prerequisite:** Stage 19 live-proven (body matrix row 49 = `proven`).

## Invariants

1. Layer separation: MBC → COB → CEC → MGM → ISD → NFD → CEV → GCV → FCE; each adoption validates upstream
2. No auto-promotion between tiers or across epochs; separate dual-gate paths
3. UGR stays technical; diplomacy/membrane enforce ingress only
4. Nova interprets; Jarvis authorizes; Dreamspace proposal-only
5. FCE-2 adopt requires operator + Jarvis + external witness quorum (distinct org domains)
6. CEV amendments bind to `epoch_id`; blocked when epoch is `frozen`
7. Temporal replay subjects: `operator_diplomacy`, `operator_norm_federation`, `operator_constitutional_evolution`, `operator_civilization`, `operator_federated_epoch`

## Verification

```bash
make civilizational-arc-gate
make stage19-federation-gate
make beyond-body-arc-gate
make multi-being-continuity-body-gate
```
