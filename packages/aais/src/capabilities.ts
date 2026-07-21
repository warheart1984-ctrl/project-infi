export type AAISCapabilityKind =
  | 'engine'
  | 'generator'
  | 'registry'
  | 'dashboard'
  | 'verifier'
  | 'agent'
  | 'optimizer'
  | 'orchestrator'
  | 'loader'
  | 'scheduler'
  | 'analyzer'
  | 'ledger'
  | 'graph'
  | 'database';

export type AAISPreferredModel = 'qwen-3b' | 'qwen-7b';

export interface AAISRoutingHint {
  preferredModel?: AAISPreferredModel;
  reason?: string;
}

export interface AAISRoutingCatalog {
  smallPrompt: AAISRoutingHint;
  largePrompt: AAISRoutingHint;
  deepReasoning: AAISRoutingHint;
  fastIteration: AAISRoutingHint;
  referenceRuntimeComposer: AAISRoutingHint;
  conformanceSuiteGenerator: AAISRoutingHint;
  implementationGapResolver: AAISRoutingHint;
}

export interface AAISCapabilityDescriptor {
  id: string;
  name: string;
  kind: AAISCapabilityKind;
  summary: string;
}

export interface ReferenceRuntimeComposition {
  name: 'Reference Runtime Composer';
  flow: readonly ['llm', 'jarvis', 'nova'];
  components: readonly string[];
}

export interface ConformanceSuite {
  name: 'Conformance Suite Generator';
  subject: string;
  checks: readonly string[];
  evidence: readonly string[];
}

export interface ImplementationGapResolution {
  name: 'Implementation Gap Resolver';
  intent: readonly string[];
  implementation: readonly string[];
  missing: readonly string[];
  prioritizedWork: readonly {
    priority: number;
    item: string;
  }[];
  summary: string;
}

const AAIS_FLOW = ['llm', 'jarvis', 'nova'] as const;

export const routing: AAISRoutingCatalog = {
  smallPrompt: {
    preferredModel: 'qwen-3b',
    reason: 'small prompt',
  },
  largePrompt: {
    preferredModel: 'qwen-7b',
    reason: 'large prompt',
  },
  deepReasoning: {
    preferredModel: 'qwen-7b',
    reason: 'deep reasoning',
  },
  fastIteration: {
    preferredModel: 'qwen-3b',
    reason: 'fast iteration',
  },
  referenceRuntimeComposer: {
    preferredModel: 'qwen-7b',
    reason: 'reference runtime composer',
  },
  conformanceSuiteGenerator: {
    preferredModel: 'qwen-7b',
    reason: 'conformance suite generator',
  },
  implementationGapResolver: {
    preferredModel: 'qwen-7b',
    reason: 'implementation gap resolver',
  },
};

function slugify(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

function createCapability(
  name: string,
  kind: AAISCapabilityKind,
  summary: string,
): AAISCapabilityDescriptor {
  return {
    id: slugify(name),
    name,
    kind,
    summary,
  };
}

export const AAISCapabilities = [
  createCapability('Universal Project Memory Engine', 'engine', 'Compresses and restores cross-project memory.'),
  createCapability('Context Compression Engine', 'engine', 'Reduces context while preserving governance-critical meaning.'),
  createCapability('Automatic Context Loader', 'loader', 'Loads the right context pack for the active project slice.'),
  createCapability('Cross-Project Knowledge Graph', 'graph', 'Links shared facts across repositories and workspaces.'),
  createCapability('Evidence & Citation Engine', 'ledger', 'Attaches evidence and citations to AAIS claims.'),
  createCapability('Decision Ledger', 'ledger', 'Records AAIS decisions in a deterministic order.'),
  createCapability('Immutable Evidence Archive', 'ledger', 'Retains evidence snapshots without mutation.'),
  createCapability('Provenance Graph', 'graph', 'Preserves lineage across AAIS outputs and inputs.'),
  createCapability('Constitutional Compliance Dashboard', 'dashboard', 'Summarizes compliance status for the governed runtime.'),
  createCapability('Independent Verifier', 'verifier', 'Checks AAIS outputs against constitutional constraints.'),
  createCapability('Autonomous Testing Agent', 'agent', 'Generates and executes validation checks.'),
  createCapability('Autonomous Documentation Agent', 'agent', 'Produces documentation aligned with runtime evidence.'),
  createCapability('Architecture Generator', 'generator', 'Drafts architectural surfaces from approved intent.'),
  createCapability('API Generator', 'generator', 'Generates API surfaces from the governing specification.'),
  createCapability('SDK Generator', 'generator', 'Generates SDK packaging and exports.'),
  createCapability('Database Designer', 'database', 'Designs durable storage shapes for governed data.'),
  createCapability('Diagram Generator', 'generator', 'Produces traceable architecture diagrams.'),
  createCapability('Deployment Generator', 'generator', 'Produces deterministic deployment plans.'),
  createCapability('Version Control Intelligence', 'analyzer', 'Tracks repository state and version drift.'),
  createCapability('Runtime Evolution Manager', 'orchestrator', 'Manages approved runtime evolution steps.'),
  createCapability('Drift Detection Engine', 'analyzer', 'Detects drift from the constitutional baseline.'),
  createCapability('Contradiction Detector', 'analyzer', 'Finds contradictory claims across evidence and intent.'),
  createCapability('Missing Evidence Detector', 'analyzer', 'Finds unsupported claims and absent proof.'),
  createCapability('Gap Analysis Engine', 'analyzer', 'Identifies unresolved architectural gaps.'),
  createCapability('Pattern Mining Engine', 'analyzer', 'Surfaces recurring patterns from the evidence corpus.'),
  createCapability('Knowledge Distillation Engine', 'engine', 'Compresses learned structure into durable summaries.'),
  createCapability('Constitutional Memory Validator', 'verifier', 'Validates memory claims against constitutional rules.'),
  createCapability('Auto-Orchestrator', 'orchestrator', 'Selects and sequences runtime capabilities automatically.'),
  createCapability('Parallel Execution Scheduler', 'scheduler', 'Schedules independent work in parallel.'),
  createCapability('Latency Optimizer', 'optimizer', 'Minimizes response latency under governance constraints.'),
  createCapability('Token Optimizer', 'optimizer', 'Reduces token usage while preserving meaning.'),
  createCapability('Resource Optimizer', 'optimizer', 'Balances compute, memory, and storage usage.'),
  createCapability('Cache Intelligence', 'engine', 'Uses cache state to avoid redundant work.'),
  createCapability('Agent Registry', 'registry', 'Lists available AAIS agent surfaces.'),
  createCapability('Tool Registry', 'registry', 'Lists available tools and capabilities.'),
  createCapability('Knowledge Registry', 'registry', 'Indexes known facts, policies, and runbooks.'),
  createCapability('Skill Library', 'registry', 'Publishes reusable skill definitions.'),
  createCapability('Workflow Marketplace', 'registry', 'Publishes approved workflow templates.'),
  createCapability('Capability Discovery Engine', 'engine', 'Finds the best approved capability for a task.'),
  createCapability('Runtime Performance Dashboard', 'dashboard', 'Shows runtime performance and bottleneck data.'),
  createCapability('Reference Runtime Composer', 'generator', 'Assembles approved runtime components into a reference surface.'),
  createCapability('Conformance Suite Generator', 'generator', 'Builds validation suites from architectural requirements.'),
  createCapability('Implementation Gap Resolver', 'generator', 'Compares intent to implementation and prioritizes missing work.'),
] as const;

export function listAAISCapabilities(): readonly AAISCapabilityDescriptor[] {
  return AAISCapabilities;
}

export function resolveAAISCapability(identifier: string): AAISCapabilityDescriptor | undefined {
  const normalized = slugify(identifier);
  return AAISCapabilities.find(
    (capability) => capability.id === normalized || slugify(capability.name) === normalized,
  );
}

function extractText(payload: unknown): string {
  const fragments: string[] = [];

  const visit = (value: unknown): void => {
    if (typeof value === 'string') {
      fragments.push(value);
      return;
    }

    if (!value || typeof value !== 'object') {
      return;
    }

    const candidate = value as Record<string, unknown>;
    visit(candidate.surface);
    visit(candidate.prompt);
    visit(candidate.description);
    visit(candidate.query);
    visit(candidate.text);
    visit(candidate.systemPrompt);
    visit(candidate.userContent);
    visit(candidate.context);

    if ('input' in candidate && candidate.input && typeof candidate.input === 'object') {
      const input = candidate.input as Record<string, unknown>;
      visit(input.systemPrompt);
      visit(input.userContent);
      visit(input.context);
    }

    if ('payload' in candidate) {
      visit(candidate.payload);
    }
  };

  visit(payload);
  return fragments.join(' ').trim();
}

export function resolveRoutingHint(payload: unknown): AAISRoutingHint {
  const text = extractText(payload).toLowerCase();
  const tokenCount = text ? text.split(/\s+/).filter(Boolean).length : 0;

  if (
    tokenCount >= 48 ||
    /\b(deep|reason|analysis|architecture|conformance|refactor|provenance|gap)\b/.test(text)
  ) {
    return routing.largePrompt;
  }

  if (/\b(iterate|prototype|draft|explore)\b/.test(text)) {
    return routing.fastIteration;
  }

  if (tokenCount <= 18 || /\b(fix|smoke|quick|fast|short|rename|lint)\b/.test(text)) {
    return routing.smallPrompt;
  }

  return routing.deepReasoning;
}

export function composeReferenceRuntime(approvedComponents: readonly string[]): ReferenceRuntimeComposition {
  const components = [...new Set(approvedComponents.map((component) => component.trim()).filter(Boolean))];

  return {
    name: 'Reference Runtime Composer',
    flow: AAIS_FLOW,
    components,
  };
}

export function generateConformanceSuite(subject: string, requirements: readonly string[]): ConformanceSuite {
  const checks = requirements
    .map((requirement) => requirement.trim())
    .filter(Boolean)
    .map((requirement) => `Verify ${subject} satisfies ${requirement}`);

  return {
    name: 'Conformance Suite Generator',
    subject: subject.trim(),
    checks,
    evidence: checks.map((check) => `Evidence required for ${check}`),
  };
}

export function resolveImplementationGap(
  intent: readonly string[],
  implementation: readonly string[],
): ImplementationGapResolution {
  const normalizedImplementation = new Set(
    implementation.map((item) => item.trim()).filter(Boolean),
  );
  const normalizedIntent = intent.map((item) => item.trim()).filter(Boolean);
  const missing = normalizedIntent.filter((item) => !normalizedImplementation.has(item));

  return {
    name: 'Implementation Gap Resolver',
    intent: normalizedIntent,
    implementation: [...normalizedImplementation],
    missing,
    prioritizedWork: missing.map((item, index) => ({
      priority: index + 1,
      item,
    })),
    summary: `${missing.length} gap(s) identified`,
  };
}
