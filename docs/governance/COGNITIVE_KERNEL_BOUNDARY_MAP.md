# Cognitive Kernel Boundary Map

Status: **active architecture map**

Mythic label (blueprint only): *Cognitive Kernel stack*

Engineering contract: `CognitiveKernelBoundaryMap`

## Problem

Generator, judge, and executor must not collapse into one undifferentiated step. This map assigns **non-overlapping responsibilities** to existing engineering surfaces. It does not authorize new `*_organ.py` modules.

## Role map

| Role | Mythic (comments only) | Engineering surface | Non-responsibilities |
|------|------------------------|---------------------|------------------------|
| **Substrate** | UL substrate | `AaisUlSubstrateEngine` — `src/aais_ul_substrate.py`, [AAIS_D3_SYSTEM_CURRENT_STATE.md](../runtime/AAIS_D3_SYSTEM_CURRENT_STATE.md) | No final answers; no ungoverned execution |
| **Questioner** | Attention / ingress | Cognitive bridge — [AAIS_COGNITIVE_BRIDGE_RUNTIME_LAW.md](../contracts/AAIS_COGNITIVE_BRIDGE_RUNTIME_LAW.md), `src/cog_runtime/` | No execution; no memory writes without law |
| **Answerer** | Speaking / reasoning | `src/speaking_runtime/`, Jarvis finalize paths | No side effects; proposal-only where required |
| **Hysteresis** | Coherence / posture | `OperatorCognitionCoherenceLayer`, `src/safety_envelope.py` | No policy rewrite; holds/degrades under uncertainty |
| **Reflection** | Reflection lobe | Nova Cortex reflection runtime — [NOVA_CORTEX.md](../runtime/NOVA_CORTEX.md) | No direct tool execution |
| **Memory** | Memory board | `jarvis_memory_board.py`, conversation memory, genomes under `governance/subsystem_genomes/` | No constitutional edits |
| **Execution** | OTEM / plug adapter | `otem_runtime.py`, `plug_adapter_runtime.py` (Jarvis-gated) | No self-directed scope expansion |

## Ingress rule

All governed cognitive packets enter through the **bridge** only. Fail-closed on uncertainty ([Cognitive Bridge Runtime Law](../contracts/AAIS_COGNITIVE_BRIDGE_RUNTIME_LAW.md)).

## Swarm coupling

When uncertainty rises across roles, [Swarm Law](../contracts/SWARM_LAW.md) applies: coordinated hold or degrade, not confident bluffing.

## Blueprint reference

Stack ordering in blueprint: [PROJECT_BLUEPRINTS_MASTER.md](../../document/blueprints/PROJECT_BLUEPRINTS_MASTER.md) (CoG OS Cognitive Kernel layer). This map is the **engineering interpretation** of that layer.

## Failure modes

| Anti-pattern | Detection | Response |
|--------------|-----------|----------|
| Executor also judges admission | Missing bridge receipt | Reject packet |
| Answerer triggers tools directly | Bypass OTEM/Jarvis gate | Fail-closed |
| Memory mutation during reflection | Ledger mismatch | Immune protocol / hold |
