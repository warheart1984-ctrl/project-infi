import {
  routeSovereignXLlmInference,
  type SovereignXEngineBackend,
} from './engineBridge.js';
import type { SovereignXRouter } from './SovereignXRouter.js';
import type {
  GovernanceLimits,
  RouteEvaluation,
  RuntimeStats,
  RelationshipTrustView,
  SovereignXModelDecision,
  SovereignXRoutingHint,
} from './types.js';
import { trustPolicyForGovernanceLevel, type GovernanceTrustLevel, type GovernanceTrustPolicy } from './trust.js';
import { SovereignXRouter as SovereignXRouterImpl } from './SovereignXRouter.js';

export type SovereignRouterXPricingSegment =
  | 'Individual'
  | 'Professional'
  | 'Team'
  | 'Enterprise'
  | 'Public Sector';

export type SovereignRouterXPricingStrategy =
  | 'Subscription-led'
  | 'Usage-led'
  | 'Assurance-led'
  | 'Enterprise bundle';

export interface SovereignRouterXPricingInput {
  segment: SovereignRouterXPricingSegment;
  monthlyCustomers: number;
  routedRequestsPerCustomer: number;
  governanceReviewsPerCustomer: number;
  knowledgeUpdatesPerCustomer: number;
  serviceHoursPerCustomer: number;
  compliancePressure: number;
  workloadVolatility: number;
  supportComplexity: number;
  privateDeployment: boolean;
  assuranceRequired: boolean;
  governanceLevel?: GovernanceTrustLevel;
  trust?: RelationshipTrustView;
}

export interface SovereignRouterXPricingPlanProfile {
  strategy: SovereignRouterXPricingStrategy;
  packaging: string;
  valueFocus: string;
  marginDriver: string;
}

export interface SovereignRouterXPricingScenario extends SovereignRouterXPricingPlanProfile {
  targetMarginBand: string;
  score: number;
  estimatedRevenueUsd: number;
  estimatedCostUsd: number;
  estimatedGrossMarginUsd: number;
  estimatedGrossMarginPct: number;
}

export interface SovereignRouterXPricingLedgerEntry {
  requestId: string;
  recordedAt: string;
  segment: SovereignRouterXPricingSegment;
  strategy: SovereignRouterXPricingStrategy;
  routedRequests: number;
  monthlyCustomers: number;
  estimatedRevenueUsd: number;
  estimatedCostUsd: number;
  estimatedGrossMarginUsd: number;
  estimatedGrossMarginPct: number;
  selectedModel: SovereignXModelDecision['model'];
  backend: SovereignXEngineBackend | 'delay' | 'drop';
  routeReason: string;
}

export interface SovereignRouterXPricingRequestPacket {
  objective: string;
  current_state?: string;
  done: string[];
  next_action: string;
  files: string[];
  verification: string;
  blockers: string[];
  governanceLevel?: GovernanceTrustLevel;
  trust?: RelationshipTrustView;
}

export interface SovereignRouterXPricingEvaluation {
  input: SovereignRouterXPricingInput;
  requestPacket: SovereignRouterXPricingRequestPacket;
  strategyScenarios: SovereignRouterXPricingScenario[];
  recommendedScenario: SovereignRouterXPricingScenario;
  routing: {
    routeEvaluation: RouteEvaluation;
    backend: SovereignXEngineBackend | 'delay' | 'drop';
    modelDecision: SovereignXModelDecision;
    routingHint: SovereignXRoutingHint;
    trust?: RelationshipTrustView;
    trustPolicy: GovernanceTrustPolicy;
  };
  economics: {
    monthlyRevenueUsd: number;
    monthlyDirectCostUsd: number;
    grossMarginUsd: number;
    grossMarginPct: number;
    routedRequests: number;
    requestRevenueUsd: number;
    requestCostUsd: number;
    requestGrossMarginUsd: number;
    requestGrossMarginPct: number;
  };
  ledgerEntry: SovereignRouterXPricingLedgerEntry;
}

type PricingRates = {
  subscriptionMultiplier: number;
  usageMultiplier: number;
  assuranceMultiplier: number;
  knowledgeMultiplier: number;
  serviceMultiplier: number;
};

type PricingSpecMatrixRow = {
  segment: SovereignRouterXPricingSegment;
  targetMarginBand: string;
  models: SovereignRouterXPricingPlanProfile[];
};

const DEFAULT_INPUT: SovereignRouterXPricingInput = {
  segment: 'Professional',
  monthlyCustomers: 1,
  routedRequestsPerCustomer: 120,
  governanceReviewsPerCustomer: 2,
  knowledgeUpdatesPerCustomer: 4,
  serviceHoursPerCustomer: 0,
  compliancePressure: 35,
  workloadVolatility: 45,
  supportComplexity: 35,
  privateDeployment: false,
  assuranceRequired: false,
  governanceLevel: 'basic',
};

const DEFAULT_LIMITS: GovernanceLimits = {
  maxGpuJobs: 2,
  maxCpuJobs: 32,
  maxConcurrentJobs: 8,
  maxGpuTempC: 82,
  maxVramBytes: 20 * 1024 * 1024 * 1024,
  maxTokensPerAgentPerMin: 8_000,
  maxFlopsPerAgentPerMin: 50_000_000,
};

const DEFAULT_RUNTIME: RuntimeStats = {
  activeGpuJobs: 1,
  activeCpuJobs: 3,
  gpuUtil: 0.34,
  cpuUtil: 0.42,
  gpuTempC: 57,
  vramUsedBytes: 6 * 1024 * 1024 * 1024,
  vramTotalBytes: 24 * 1024 * 1024 * 1024,
};

const SEGMENT_MARGIN_BANDS: Record<SovereignRouterXPricingSegment, string> = {
  Individual: '55-70%',
  Professional: '60-75%',
  Team: '62-78%',
  Enterprise: '70-85%',
  'Public Sector': '65-80%',
};

const STRATEGY_PROFILES: Record<SovereignRouterXPricingStrategy, SovereignRouterXPricingPlanProfile> = {
  'Subscription-led': {
    strategy: 'Subscription-led',
    packaging: 'Predictable monthly plan with governance and workflow access.',
    valueFocus: 'Stable access and simple billing.',
    marginDriver: 'Subscription mix offsets support and orchestration overhead.',
  },
  'Usage-led': {
    strategy: 'Usage-led',
    packaging: 'Lower base fee with metered routed requests and storage.',
    valueFocus: 'Align spend to activity.',
    marginDriver: 'Variable usage is manageable with metering and caps.',
  },
  'Assurance-led': {
    strategy: 'Assurance-led',
    packaging: 'Governance, evidence, replay, and policy bundle.',
    valueFocus: 'Traceability and auditability.',
    marginDriver: 'Standardized assurance work creates durable margin.',
  },
  'Enterprise bundle': {
    strategy: 'Enterprise bundle',
    packaging: 'Private deployment, support, assurance, and services in one wrapper.',
    valueFocus: 'One accountable commercial path.',
    marginDriver: 'Bundling protects margin when procurement and support are material.',
  },
};

const STRATEGY_RATE_MULTIPLIERS: Record<SovereignRouterXPricingStrategy, PricingRates> = {
  'Subscription-led': {
    subscriptionMultiplier: 1.2,
    usageMultiplier: 0.85,
    assuranceMultiplier: 0.9,
    knowledgeMultiplier: 0.9,
    serviceMultiplier: 0.92,
  },
  'Usage-led': {
    subscriptionMultiplier: 0.6,
    usageMultiplier: 1.3,
    assuranceMultiplier: 0.88,
    knowledgeMultiplier: 0.95,
    serviceMultiplier: 0.98,
  },
  'Assurance-led': {
    subscriptionMultiplier: 0.92,
    usageMultiplier: 0.95,
    assuranceMultiplier: 1.35,
    knowledgeMultiplier: 1.08,
    serviceMultiplier: 1.02,
  },
  'Enterprise bundle': {
    subscriptionMultiplier: 1.45,
    usageMultiplier: 1.05,
    assuranceMultiplier: 1.5,
    knowledgeMultiplier: 1.15,
    serviceMultiplier: 1.35,
  },
};

const SEGMENT_BASE_SCORE: Record<SovereignRouterXPricingSegment, Record<SovereignRouterXPricingStrategy, number>> = {
  Individual: {
    'Subscription-led': 34,
    'Usage-led': 28,
    'Assurance-led': 26,
    'Enterprise bundle': 10,
  },
  Professional: {
    'Subscription-led': 33,
    'Usage-led': 31,
    'Assurance-led': 30,
    'Enterprise bundle': 24,
  },
  Team: {
    'Subscription-led': 34,
    'Usage-led': 30,
    'Assurance-led': 33,
    'Enterprise bundle': 32,
  },
  Enterprise: {
    'Subscription-led': 31,
    'Usage-led': 32,
    'Assurance-led': 36,
    'Enterprise bundle': 40,
  },
  'Public Sector': {
    'Subscription-led': 28,
    'Usage-led': 25,
    'Assurance-led': 35,
    'Enterprise bundle': 42,
  },
};

const pricingScenarioMatrix: PricingSpecMatrixRow[] = [
  {
    segment: 'Individual',
    targetMarginBand: SEGMENT_MARGIN_BANDS.Individual,
    models: [
      { ...STRATEGY_PROFILES['Subscription-led'] },
      { ...STRATEGY_PROFILES['Usage-led'] },
      { ...STRATEGY_PROFILES['Assurance-led'] },
      { ...STRATEGY_PROFILES['Enterprise bundle'] },
    ],
  },
  {
    segment: 'Professional',
    targetMarginBand: SEGMENT_MARGIN_BANDS.Professional,
    models: [
      { ...STRATEGY_PROFILES['Subscription-led'] },
      { ...STRATEGY_PROFILES['Usage-led'] },
      { ...STRATEGY_PROFILES['Assurance-led'] },
      { ...STRATEGY_PROFILES['Enterprise bundle'] },
    ],
  },
  {
    segment: 'Team',
    targetMarginBand: SEGMENT_MARGIN_BANDS.Team,
    models: [
      { ...STRATEGY_PROFILES['Subscription-led'] },
      { ...STRATEGY_PROFILES['Usage-led'] },
      { ...STRATEGY_PROFILES['Assurance-led'] },
      { ...STRATEGY_PROFILES['Enterprise bundle'] },
    ],
  },
  {
    segment: 'Enterprise',
    targetMarginBand: SEGMENT_MARGIN_BANDS.Enterprise,
    models: [
      { ...STRATEGY_PROFILES['Subscription-led'] },
      { ...STRATEGY_PROFILES['Usage-led'] },
      { ...STRATEGY_PROFILES['Assurance-led'] },
      { ...STRATEGY_PROFILES['Enterprise bundle'] },
    ],
  },
  {
    segment: 'Public Sector',
    targetMarginBand: SEGMENT_MARGIN_BANDS['Public Sector'],
    models: [
      { ...STRATEGY_PROFILES['Subscription-led'] },
      { ...STRATEGY_PROFILES['Usage-led'] },
      { ...STRATEGY_PROFILES['Assurance-led'] },
      { ...STRATEGY_PROFILES['Enterprise bundle'] },
    ],
  },
];

function createPricingRouter(): SovereignXRouter {
  const router = new SovereignXRouterImpl();
  router.registerIntent({
    id: 'sovereign-router-x-pricing',
    domain: 'governance',
    rules: 'Route pricing evaluation requests through the constitutional orchestration path before any model selection.',
    allowedTargets: ['CPU', 'GPU', 'DELAY', 'DROP'],
    maxTokensPerAgentPerMin: DEFAULT_LIMITS.maxTokensPerAgentPerMin,
    maxFlopsPerAgentPerMin: DEFAULT_LIMITS.maxFlopsPerAgentPerMin,
  });
  return router;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function toFiniteNumber(value: unknown, fallback: number): number {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    return fallback;
  }
  return value;
}

function clamp(value: number, minimum: number, maximum: number): number {
  return Math.min(maximum, Math.max(minimum, value));
}

function round(value: number): number {
  return Math.round(value * 100) / 100;
}

function currency(value: number): number {
  return round(value);
}

function stableHash(input: string): string {
  let hash = 2166136261;
  for (let index = 0; index < input.length; index += 1) {
    hash ^= input.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return `srx-${(hash >>> 0).toString(16).padStart(8, '0')}`;
}

function buildRequestPacket(input: SovereignRouterXPricingInput, recommendation: SovereignRouterXPricingScenario): SovereignRouterXPricingRequestPacket {
  return {
    objective: `Evaluate Sovereign Router X pricing for ${input.segment} customers and recommend the best commercial plan.`,
    current_state: `${input.monthlyCustomers} customers, ${input.routedRequestsPerCustomer} routed requests per customer, ${input.governanceReviewsPerCustomer} governance reviews, ${input.knowledgeUpdatesPerCustomer} knowledge updates, ${input.serviceHoursPerCustomer} service hours, compliance pressure ${input.compliancePressure}/100, volatility ${input.workloadVolatility}/100, support complexity ${input.supportComplexity}/100.`,
    done: [
      `Segment selected: ${input.segment}`,
      `Pricing strategies scored: ${recommendation.strategy}`,
      'Unit economics derived from the layered pricing model.',
    ],
    next_action: 'Use Sovereign Router X to validate the commercial plan and return a structured recommendation.',
    files: [
      'docs/crk1/release/SOVEREIGN_ROUTER_X_PRICING.spec.json',
      'docs/crk1/release/SOVEREIGN_ROUTER_X_PRICING.md',
      'docs/crk1/release/SOVEREIGN_ROUTER_X_FINANCE_RELEASE.md',
    ],
    verification: 'Validate that the selected pricing plan preserves the target margin band and routes through the constitutional policy layer.',
    blockers: input.privateDeployment ? ['Private deployment requested', 'Confirm operator approval for dedicated routing'] : [],
    governanceLevel: input.governanceLevel,
    trust: input.trust ? cloneTrustView(input.trust) : undefined,
  };
}

function getPricingRatios(strategy: SovereignRouterXPricingStrategy): PricingRates {
  return STRATEGY_RATE_MULTIPLIERS[strategy];
}

function deriveModelHint(input: SovereignRouterXPricingInput, strategy: SovereignRouterXPricingStrategy): SovereignXRoutingHint {
  if (input.privateDeployment || input.assuranceRequired || strategy === 'Enterprise bundle' || input.compliancePressure >= 65) {
    return {
      preferredModel: 'qwen-7b',
      reason: 'enterprise and assurance-heavy pricing requests route to the larger reasoning surface',
    };
  }

  if (input.workloadVolatility >= 55 || input.routedRequestsPerCustomer >= 250) {
    return {
      preferredModel: 'qwen-7b',
      reason: 'high-volume or volatile pricing requests need the larger reasoning surface',
    };
  }

  return {
    preferredModel: 'qwen-3b',
    reason: 'lightweight pricing requests stay on the smaller reasoning surface',
  };
}

function scoreStrategy(input: SovereignRouterXPricingInput, strategy: SovereignRouterXPricingStrategy): number {
  const base = SEGMENT_BASE_SCORE[input.segment][strategy];
  const compliance = input.compliancePressure;
  const volatility = input.workloadVolatility;
  const support = input.supportComplexity;
  const requests = input.routedRequestsPerCustomer;
  const governance = input.governanceReviewsPerCustomer;

  const requestSignal = clamp(Math.log10(Math.max(1, requests)) * 12, 0, 36);
  const governanceSignal = clamp(governance * 4, 0, 24);
  const privateDeploymentSignal = input.privateDeployment ? 10 : 0;
  const assuranceSignal = input.assuranceRequired ? 12 : 0;

  switch (strategy) {
    case 'Subscription-led':
      return round(base + (100 - volatility) * 0.22 + (100 - compliance) * 0.12 + (100 - support) * 0.16 + clamp(24 - requests / 20, 0, 24));
    case 'Usage-led':
      return round(base + volatility * 0.28 + requestSignal + (100 - compliance) * 0.06);
    case 'Assurance-led':
      return round(base + compliance * 0.28 + governanceSignal + support * 0.08 + assuranceSignal + privateDeploymentSignal * 0.2);
    case 'Enterprise bundle':
      return round(base + compliance * 0.26 + support * 0.22 + privateDeploymentSignal + assuranceSignal + clamp(requests / 25, 0, 18));
  }
}

function estimateMonthlyEconomics(
  input: SovereignRouterXPricingInput,
  strategy: SovereignRouterXPricingStrategy,
): {
  revenueUsd: number;
  costUsd: number;
  marginUsd: number;
  marginPct: number;
} {
  const rates = getPricingRatios(strategy);
  const subscriptionFee = 49 * rates.subscriptionMultiplier;
  const usageFee = 0.09 * rates.usageMultiplier;
  const assuranceFee = 10 * rates.assuranceMultiplier;
  const knowledgeFee = 0.5 * rates.knowledgeMultiplier;
  const serviceFee = 125 * rates.serviceMultiplier;

  const revenueUsd = input.monthlyCustomers * (
    subscriptionFee +
    input.routedRequestsPerCustomer * usageFee +
    input.governanceReviewsPerCustomer * assuranceFee +
    input.knowledgeUpdatesPerCustomer * knowledgeFee +
    input.serviceHoursPerCustomer * serviceFee
  );

  const directCostUsd = input.monthlyCustomers * (
    8 +
    input.routedRequestsPerCustomer * (0.02 + 0.01 + 0.005) +
    input.governanceReviewsPerCustomer * 6 +
    input.knowledgeUpdatesPerCustomer * 0.15 +
    input.serviceHoursPerCustomer * 75
  );

  const marginUsd = revenueUsd - directCostUsd;
  const marginPct = revenueUsd > 0 ? (marginUsd / revenueUsd) * 100 : 0;

  return {
    revenueUsd: currency(revenueUsd),
    costUsd: currency(directCostUsd),
    marginUsd: currency(marginUsd),
    marginPct: round(marginPct),
  };
}

function buildScenario(input: SovereignRouterXPricingInput, strategy: SovereignRouterXPricingStrategy): SovereignRouterXPricingScenario {
  const economics = estimateMonthlyEconomics(input, strategy);
  return {
    ...STRATEGY_PROFILES[strategy],
    targetMarginBand: SEGMENT_MARGIN_BANDS[input.segment],
    score: scoreStrategy(input, strategy),
    estimatedRevenueUsd: economics.revenueUsd,
    estimatedCostUsd: economics.costUsd,
    estimatedGrossMarginUsd: economics.marginUsd,
    estimatedGrossMarginPct: economics.marginPct,
  };
}

function normalizeInput(value: SovereignRouterXPricingInput | unknown): SovereignRouterXPricingInput {
  if (!isRecord(value)) {
    return { ...DEFAULT_INPUT };
  }

  const segment = String(value.segment ?? DEFAULT_INPUT.segment) as SovereignRouterXPricingSegment;
  if (!Object.hasOwn(SEGMENT_MARGIN_BANDS, segment)) {
    throw new Error(`Unsupported pricing segment: ${String(value.segment)}`);
  }

  return {
    segment,
    monthlyCustomers: Math.max(1, Math.round(toFiniteNumber(value.monthlyCustomers, DEFAULT_INPUT.monthlyCustomers))),
    routedRequestsPerCustomer: Math.max(1, Math.round(toFiniteNumber(value.routedRequestsPerCustomer, DEFAULT_INPUT.routedRequestsPerCustomer))),
    governanceReviewsPerCustomer: Math.max(0, Math.round(toFiniteNumber(value.governanceReviewsPerCustomer, DEFAULT_INPUT.governanceReviewsPerCustomer))),
    knowledgeUpdatesPerCustomer: Math.max(0, Math.round(toFiniteNumber(value.knowledgeUpdatesPerCustomer, DEFAULT_INPUT.knowledgeUpdatesPerCustomer))),
    serviceHoursPerCustomer: round(Math.max(0, toFiniteNumber(value.serviceHoursPerCustomer, DEFAULT_INPUT.serviceHoursPerCustomer))),
    compliancePressure: clamp(toFiniteNumber(value.compliancePressure, DEFAULT_INPUT.compliancePressure), 0, 100),
    workloadVolatility: clamp(toFiniteNumber(value.workloadVolatility, DEFAULT_INPUT.workloadVolatility), 0, 100),
    supportComplexity: clamp(toFiniteNumber(value.supportComplexity, DEFAULT_INPUT.supportComplexity), 0, 100),
    privateDeployment: Boolean(value.privateDeployment ?? DEFAULT_INPUT.privateDeployment),
    assuranceRequired: Boolean(value.assuranceRequired ?? DEFAULT_INPUT.assuranceRequired),
    governanceLevel: isGovernanceTrustLevel(value.governanceLevel) ? value.governanceLevel : DEFAULT_INPUT.governanceLevel,
    trust: isTrustView(value.trust) ? cloneTrustView(value.trust) : undefined,
  };
}

function buildRuntimeStats(input: SovereignRouterXPricingInput): RuntimeStats {
  return {
    ...DEFAULT_RUNTIME,
    activeGpuJobs: clamp(Math.ceil(input.routedRequestsPerCustomer / 300), 0, 8),
    activeCpuJobs: clamp(Math.ceil(input.monthlyCustomers * 1.5), 1, 24),
    gpuUtil: clamp(0.2 + input.workloadVolatility / 180, 0, 0.95),
    cpuUtil: clamp(0.25 + input.supportComplexity / 200, 0, 0.95),
    gpuTempC: clamp(52 + input.compliancePressure / 5 + (input.privateDeployment ? 4 : 0), 45, 84),
    vramUsedBytes: clamp(4 * 1024 * 1024 * 1024 + input.routedRequestsPerCustomer * 12_000_000, 0, DEFAULT_RUNTIME.vramTotalBytes),
  };
}

function isTrustView(value: unknown): value is RelationshipTrustView {
  return Boolean(
    value &&
      typeof value === 'object' &&
      !Array.isArray(value) &&
      typeof (value as RelationshipTrustView).score === 'number' &&
      typeof (value as RelationshipTrustView).band === 'string' &&
      Array.isArray((value as RelationshipTrustView).evidenceIds),
  );
}

function isGovernanceTrustLevel(value: unknown): value is GovernanceTrustLevel {
  return value === 'basic' || value === 'enhanced' || value === 'full';
}

function cloneTrustView(value: RelationshipTrustView): RelationshipTrustView {
  return {
    score: value.score,
    band: value.band,
    evidenceIds: [...value.evidenceIds],
    authority: value.authority ? { ...value.authority } : undefined,
    provenance: value.provenance ? { ...value.provenance } : undefined,
  };
}

export function normalizeSovereignRouterXPricingInput(value: SovereignRouterXPricingInput | unknown): SovereignRouterXPricingInput {
  return normalizeInput(value);
}

export function listSovereignRouterXPricingScenarioMatrix(): PricingSpecMatrixRow[] {
  return pricingScenarioMatrix.map((row) => ({
    segment: row.segment,
    targetMarginBand: row.targetMarginBand,
    models: row.models.map((model) => ({ ...model })),
  }));
}

export function evaluateSovereignRouterXPricing(
  value: SovereignRouterXPricingInput | unknown,
  options?: {
    router?: SovereignXRouter;
    requestId?: string;
    recordedAt?: string;
  },
): SovereignRouterXPricingEvaluation {
  const input = normalizeInput(value);
  const router = options?.router ?? createPricingRouter();
  const scenarios = (Object.keys(STRATEGY_PROFILES) as SovereignRouterXPricingStrategy[]).map((strategy) => buildScenario(input, strategy));
  const recommendedScenario = [...scenarios].sort((left, right) => right.score - left.score || right.estimatedGrossMarginUsd - left.estimatedGrossMarginUsd)[0];
  const routingHint = deriveModelHint(input, recommendedScenario.strategy);
  const routedRequests = input.monthlyCustomers * input.routedRequestsPerCustomer;
  const prompt = [
    `segment=${input.segment}`,
    `monthlyCustomers=${input.monthlyCustomers}`,
    `routedRequestsPerCustomer=${input.routedRequestsPerCustomer}`,
    `governanceReviewsPerCustomer=${input.governanceReviewsPerCustomer}`,
    `knowledgeUpdatesPerCustomer=${input.knowledgeUpdatesPerCustomer}`,
    `serviceHoursPerCustomer=${input.serviceHoursPerCustomer}`,
    `compliancePressure=${input.compliancePressure}`,
    `workloadVolatility=${input.workloadVolatility}`,
    `supportComplexity=${input.supportComplexity}`,
    `privateDeployment=${input.privateDeployment}`,
    `assuranceRequired=${input.assuranceRequired}`,
    `recommendedStrategy=${recommendedScenario.strategy}`,
  ].join('\n');

  const promptTokens = Math.max(24, Math.ceil(prompt.length / 12));
  const routed = routeSovereignXLlmInference(
    router,
    {
      id: options?.requestId ?? stableHash(`${input.segment}:${input.monthlyCustomers}:${input.routedRequestsPerCustomer}:${recommendedScenario.strategy}`),
      agentId: 'sovereign-router-x-pricing',
      intentId: 'sovereign-router-x-pricing',
      prompt,
      promptTokens,
      estimatedFlops: promptTokens * 1200 + routedRequests * 75,
      maxTokens: 768,
      temperature: 0.1,
      model: routingHint.preferredModel,
      priority: input.privateDeployment || input.assuranceRequired ? 2 : 1,
      routingHint,
      governanceLevel: input.governanceLevel,
      trust: input.trust,
    },
    buildRuntimeStats(input),
    DEFAULT_LIMITS,
  );

  const economics = estimateMonthlyEconomics(input, recommendedScenario.strategy);
  const requestPacket = buildRequestPacket(input, recommendedScenario);
  const requestId = options?.requestId ?? stableHash(`${input.segment}:${input.monthlyCustomers}:${input.routedRequestsPerCustomer}:${recommendedScenario.strategy}`);
  const recordedAt = options?.recordedAt ?? new Date().toISOString();

  return {
    input,
    requestPacket,
    strategyScenarios: scenarios.sort((left, right) => right.score - left.score || right.estimatedGrossMarginUsd - left.estimatedGrossMarginUsd),
    recommendedScenario,
    routing: {
      routeEvaluation: routed.routeEvaluation,
      backend: routed.backend,
      modelDecision: routed.modelDecision ?? {
        model: routingHint.preferredModel ?? 'qwen-3b',
        reason: routingHint.reason ?? 'pricing request routed to the default model',
        overrideApplied: false,
      },
      routingHint,
      trust: input.trust ? { ...input.trust } : undefined,
      trustPolicy: trustPolicyForGovernanceLevel(input.governanceLevel),
    },
    economics: {
      monthlyRevenueUsd: economics.revenueUsd,
      monthlyDirectCostUsd: economics.costUsd,
      grossMarginUsd: economics.marginUsd,
      grossMarginPct: economics.marginPct,
      routedRequests,
      requestRevenueUsd: currency(economics.revenueUsd / routedRequests),
      requestCostUsd: currency(economics.costUsd / routedRequests),
      requestGrossMarginUsd: currency(economics.marginUsd / routedRequests),
      requestGrossMarginPct: round(economics.marginPct),
    },
    ledgerEntry: {
      requestId,
      recordedAt,
      segment: input.segment,
      strategy: recommendedScenario.strategy,
      routedRequests,
      monthlyCustomers: input.monthlyCustomers,
      estimatedRevenueUsd: economics.revenueUsd,
      estimatedCostUsd: economics.costUsd,
      estimatedGrossMarginUsd: economics.marginUsd,
      estimatedGrossMarginPct: economics.marginPct,
      selectedModel: routed.modelDecision?.model ?? routingHint.preferredModel ?? 'qwen-3b',
      backend: routed.backend,
      routeReason: routed.routeEvaluation.effectiveDecision.reason,
    },
  };
}

export function createPricingLedgerEntry(
  evaluation: SovereignRouterXPricingEvaluation,
): SovereignRouterXPricingLedgerEntry {
  return { ...evaluation.ledgerEntry };
}
