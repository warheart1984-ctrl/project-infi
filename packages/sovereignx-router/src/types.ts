export type RouteTarget = 'CPU' | 'GPU' | 'DROP' | 'DELAY';

export type SovereignXPreferredModel = 'qwen-3b' | 'qwen-7b';

export type TrustBand = 'low' | 'medium' | 'high';

export interface ConstitutionalSignature {
  algorithm: 'HMAC-SHA256' | 'Ed25519';
  value: string;
  signer?: string;
  signedAt?: string;
}

export interface TrustProvenance {
  originSystem: string;
  originActorId?: string;
  method: string;
  createdAt?: string;
  standardsTraceabilityIds?: string[];
}

export interface TrustAuthority {
  stewardId?: string;
  consentArtifactIds?: string[];
  delegationChainIds?: string[];
}

export interface RelationshipTrustView {
  score: number;
  band: TrustBand;
  evidenceIds: string[];
  authority?: TrustAuthority;
  provenance?: TrustProvenance;
}

export interface RelationshipLedgerTrustPacket {
  relationshipId: string;
  revision: number;
  subjectId?: string;
  objectId?: string;
  relationshipKind?: string;
  ledgerEntryId?: string;
  receiptId?: string;
  capturedAt?: string;
  governanceLevel: 'basic' | 'enhanced' | 'full';
  authorityChain: string[];
  trust: RelationshipTrustView;
  signature?: ConstitutionalSignature;
}

export interface SovereignXRoutingHint {
  preferredModel?: SovereignXPreferredModel;
  reason?: string;
}

export interface SovereignXModelDecision {
  model: SovereignXPreferredModel;
  reason: string;
  overrideApplied: boolean;
  trust?: RelationshipTrustView;
}

export type RuntimeMode =
  | 'Normal'
  | 'GpuDegraded'
  | 'CpuDegraded'
  | 'CiemsOffline'
  | 'MeasurementUntrusted'
  | 'Quarantine';

export type CiemsDecisionAction = 'allow' | 'throttle' | 'quarantine' | 'kill';

export interface WorkItem {
  id: string;
  agentId: string;
  kind: 'llm_step' | 'render_frame' | 'tool_call' | 'matmul' | 'attention' | 'mlp' | 'physics_step' | string;
  intentId: string;
  costEstimateTokens: number;
  costEstimateFlops: number;
  costEstimateMs?: number;
  priority?: number;
  tenantId?: string;
}

export interface RuntimeStats {
  activeGpuJobs: number;
  activeCpuJobs: number;
  gpuUtil: number;
  cpuUtil: number;
  gpuTempC: number;
  vramUsedBytes: number;
  vramTotalBytes: number;
}

export interface GovernanceLimits {
  maxGpuJobs: number;
  maxCpuJobs: number;
  maxConcurrentJobs: number;
  maxGpuTempC: number;
  maxVramBytes: number;
  maxTokensPerAgentPerMin: number;
  maxFlopsPerAgentPerMin: number;
  gpuKindThreshold?: number;
}

export interface MeasurementHealth {
  trusted: boolean;
  stale: boolean;
  sampleCount: number;
  windowMs: number;
  temperatureVarianceC: number;
  notes: string[];
}

export interface RouteDecision {
  target: RouteTarget;
  reason: string;
  mode: RuntimeMode;
}

export interface EvidenceRecord {
  id: string;
  workItemId: string;
  agentId: string;
  kind: WorkItem['kind'];
  intentId: string;
  estTokens: number;
  estFlops: number;
  runtime: RuntimeStats;
  limits: GovernanceLimits;
  localDecision: RouteDecision;
  timestamp: string;
}

export interface CiemsIntentSpec {
  id: string;
  domain: WorkItem['kind'] | 'governance' | 'continuity' | 'planning' | string;
  rules: string;
  allowedTargets: RouteTarget[];
  maxTokensPerAgentPerMin?: number;
  maxFlopsPerAgentPerMin?: number;
}

export interface CiemsDecision {
  workId: string;
  agentId: string;
  action: CiemsDecisionAction;
  reason: string;
  effectiveTarget?: RouteTarget;
}

export interface AgentBudgetSnapshot {
  agentId: string;
  tokensPerMin: number;
  flopsPerMin: number;
  activeJobs: number;
  priority: number;
}

export interface RouteEvaluation {
  workItem: WorkItem;
  runtime: RuntimeStats;
  limits: GovernanceLimits;
  measurementHealth: MeasurementHealth;
  localDecision: RouteDecision;
  ciemsDecisions: CiemsDecision[];
  effectiveDecision: RouteDecision;
  evidence: EvidenceRecord;
  modelDecision?: SovereignXModelDecision;
  trust?: RelationshipTrustView;
}
