# AAIS Capability Registry

AAIS exposes a compact capability catalog that keeps the surrounding runtime honest and makes the new abilities visible in the docs site itself.

## Live Runtime Check

```ts
import { AAISRuntime } from '@aaes-os/aais';

const aais = new AAISRuntime();
console.log(aais.describeFlow());
console.log(aais.describeCapabilities().map((capability) => capability.name));
```

The shared flow is:

`llm -> jarvis -> nova`

## Constitutional Routing Hints

AAIS now emits a routing hint alongside each result so SovereignX can choose between the local `qwen-3b` and `qwen-7b` models without guessing.

- `smallPrompt` -> `qwen-3b`
- `largePrompt` -> `qwen-7b`
- `deepReasoning` -> `qwen-7b`
- `fastIteration` -> `qwen-3b`

## Live Capability Provenance

```ts
import { AAISRuntime } from '@aaes-os/aais';

const aais = new AAISRuntime();
const provenance = aais.getAAISProvenance({
  surface: 'docs-site',
  prompt: 'document the constitutional proof surface with provenance tracing',
});

console.log(provenance.capabilityName);
console.log(provenance.capabilityFile);
console.log(provenance.routingHint?.preferredModel);
```

The provenance record keeps the runtime traceable:

- `capabilityName` identifies the capability resolver.
- `capabilityFile` points at the source of the catalog.
- `resolver` names the AAIS module that resolved the hint.
- `routingHint` carries the constitutional model choice that SovereignX can consume.

## AAIS Capability Routing Table

| Capability Name | Description | Routing Hint (Preferred Model) | Reason |
| --- | --- | --- | --- |
| `smallPrompt` | Handles short, lightweight requests | `qwen-3b` | Lower latency, faster iteration |
| `largePrompt` | Handles long or complex prompts | `qwen-7b` | More context window and deeper reasoning |
| `deepReasoning` | Multi-step reasoning, planning, synthesis | `qwen-7b` | Stronger chain reconstruction |
| `fastIteration` | Rapid cycles, code edits, refactors | `qwen-3b` | Speed-first routing |
| `Reference Runtime Composer` | Builds runtime compositions | `qwen-7b` | Structural reasoning required |
| `Conformance Suite Generator` | Generates conformance suites | `qwen-7b` | High-precision validation |
| `Implementation Gap Resolver` | Identifies missing implementation details | `qwen-7b` | Semantic gap analysis |

## AAIS -> SovereignX -> Engine Provenance (JSON View)

```ts
import { getAAISProvenance } from '@aaes-os/aais';
import { createFreeCodingStack } from '@aaes-os/coding-assistant';

export default async function ProvenanceJsonViewer() {
  const provenance = await getAAISProvenance({
    surface: 'docs-site',
    prompt: 'show constitutional provenance for aaes routing',
  });
  const { assistant } = await createFreeCodingStack();
  const router = assistant.getSovereignXRouter();

  const view = {
    capability: {
      name: provenance.capabilityName,
      file: provenance.capabilityFile,
      resolver: provenance.resolver,
    },
    routingHint: provenance.routingHint ?? null,
    routerDecision: provenance.routerDecision ?? null,
    override: router?.getOverride() ?? null,
  };

  return JSON.stringify(view, null, 2);
}
```

This view is meant to render as a raw, inspectable JSON block in the docs site so the full routing chain stays visible.

## Core Engines

- `Universal Project Memory Engine` - compresses and restores cross-project memory.
- `Context Compression Engine` - reduces context while preserving governance-critical meaning.
- `Automatic Context Loader` - loads the right context pack for the active project slice.
- `Cross-Project Knowledge Graph` - links shared facts across repositories and workspaces.
- `Knowledge Distillation Engine` - compresses learned structure into durable summaries.
- `Cache Intelligence` - uses cache state to avoid redundant work.

## Evidence And Governance

- `Evidence & Citation Engine` - attaches evidence and citations to AAIS claims.
- `Decision Ledger` - records AAIS decisions in deterministic order.
- `Immutable Evidence Archive` - retains evidence snapshots without mutation.
- `Provenance Graph` - preserves lineage across AAIS outputs and inputs.
- `Constitutional Compliance Dashboard` - summarizes compliance status for the governed runtime.
- `Independent Verifier` - checks AAIS outputs against constitutional constraints.
- `Constitutional Memory Validator` - validates memory claims against constitutional rules.
- `Drift Detection Engine` - detects drift from the constitutional baseline.
- `Contradiction Detector` - finds contradictory claims across evidence and intent.
- `Missing Evidence Detector` - finds unsupported claims and absent proof.
- `Pattern Mining Engine` - surfaces recurring patterns from the evidence corpus.

## Orchestration And Optimization

- `Auto-Orchestrator` - selects and sequences runtime capabilities automatically.
- `Parallel Execution Scheduler` - schedules independent work in parallel.
- `Runtime Evolution Manager` - manages approved runtime evolution steps.
- `Latency Optimizer` - minimizes response latency under governance constraints.
- `Token Optimizer` - reduces token usage while preserving meaning.
- `Resource Optimizer` - balances compute, memory, and storage usage.
- `Capability Discovery Engine` - finds the best approved capability for a task.
- `Runtime Performance Dashboard` - shows runtime performance and bottleneck data.

## Agents And Registries

- `Agent Registry` - lists available AAIS agent surfaces.
- `Tool Registry` - lists available tools and capabilities.
- `Knowledge Registry` - indexes known facts, policies, and runbooks.
- `Skill Library` - publishes reusable skill definitions.
- `Workflow Marketplace` - publishes approved workflow templates.
- `Autonomous Testing Agent` - generates and executes validation checks.
- `Autonomous Documentation Agent` - produces documentation aligned with runtime evidence.

## Generators

- `Architecture Generator` - drafts architectural surfaces from approved intent.
- `API Generator` - generates API surfaces from the governing specification.
- `SDK Generator` - generates SDK packaging and exports.
- `Database Designer` - designs durable storage shapes for governed data.
- `Diagram Generator` - produces traceable architecture diagrams.
- `Deployment Generator` - produces deterministic deployment plans.

## Named Runtime Helpers

- `Reference Runtime Composer` - assembles approved runtime components into a reference surface.
- `Conformance Suite Generator` - builds validation suites from architectural requirements.
- `Implementation Gap Resolver` - compares intent to implementation and prioritizes missing work.

## AAIS Coding Capability Registry

AAIS also exposes a coding-oriented registry for governed change work:

| Capability | Routing | Constraints |
| --- | --- | --- |
| `RefactorCode` | `fastIteration -> qwen-3b`, `deepReasoning -> qwen-7b` | preserve tests, retain guarded logic, preserve behavior |
| `GenerateModule` | `largePrompt -> qwen-7b` | align with architecture, register in DI/container, include minimal tests |
| `ExplainCode` | `smallPrompt -> qwen-3b` | no hallucinated APIs, reference actual code lines |
| `AddTests` | `deepReasoning -> qwen-7b` | compile, cover critical paths, link to requirements |
| `MigrateAPI` | `deepReasoning -> qwen-7b` | preserve behavior, mark deprecated paths, update docs |
| `DesignSchema` | `referenceRuntimeComposer -> qwen-7b` | align with governed data shapes, remain traceable to requirements |

`AAISRuntime.describeCodingCapabilities()` returns the coding catalog at runtime.

## Coding Provenance Graph

```ts
import { createCodingProvenanceGraph } from '@aaes-os/aais';

const graph = createCodingProvenanceGraph([
  {
    capabilityName: 'RefactorCode',
    filesChanged: ['packages/aais/src/codingCapabilities.ts'],
    testsRan: ['pnpm --filter @aaes-os/aais test'],
    model: 'qwen-7b',
    constraintsApplied: ['must preserve tests passing', 'must not remove guarded logic'],
    evidence: ['AAIS coding capability registry', 'routing hint provenance'],
  },
]);

console.log(graph.records);
```

Each record captures the capability, changed files, tests, model, constraints, and evidence that supported the change.

## Capability Notes

- `AAISRuntime.describeCapabilities()` returns this catalog at runtime.
- `AAISRuntime.describeFlow()` returns the shared `llm -> jarvis -> nova` sequence.
- The catalog is intentionally compact so it can be used as a live registry and not just a static list.
