import type {
  JudgmentCapabilityProfile,
  JudgmentCycle,
  JudgmentCycleDraft,
} from "./judgment/types.js";

export type { JudgmentCycle, JudgmentCycleDraft, JudgmentCapabilityProfile };
export type { ThresholdView, RecalibrationView, ContinuityLedger } from "./ledger/types.js";

export type AccumulationType = "A1" | "A2" | "A3" | "A4" | "NONE";

export type AccumulationOrigin = "PLA" | "LA" | "SA";

export type EpistemicMode =
  | "OBSERVATION"
  | "INTERPRETATION"
  | "INTEGRATION"
  | "VALIDATION";

export type EpistemicBehaviorProfile = "doctrine" | "framework" | "instrument" | "nascent";

// --- GAME LAYER ---

export type GameEventType = "ACTION" | "SYSTEM" | "GOVERNANCE";

export interface GameEvent {
  id: string;
  actorId: string;
  timestamp: string;
  type: GameEventType;
  action: string;
  context: Record<string, unknown>;
}

export type WorldLayer = "Mechanics" | "Lore" | "Economy" | "Politics" | "Meta";

export interface AccumulationTag {
  origin: AccumulationOrigin;
  accumulationType: AccumulationType;
  targetsLayer: WorldLayer;
  buildsOn: string[];
}

export interface WorldChangeProposal {
  id: string;
  description: string;
  proposedBy: string;
  origin: AccumulationOrigin;
  affectsSystems: string[];
  hypothesis: {
    expectedEffects: string[];
    metrics: string[];
    validationWindowDays: number;
  };
  accumulationType?: AccumulationType;
}

export type GovernanceBehavior = "integrate" | "compress" | "validate" | "correct";

export type ContinuityInterpretation =
  | "listening"
  | "under-listening"
  | "self-referential"
  | "nascent";

export interface PLACriteria {
  noFrameworkExposure: boolean;
  phenomenonAnchored: boolean;
  lineageCompatible: boolean;
  explanatoryGain: boolean;
}

export interface JPSSContributionEvent {
  id: string;
  actor: string;
  timestamp: string;
  accumulationType: AccumulationType;
  targetsLayer: string;
  fromExposure: boolean;
  buildsOn: string[];
  phenomenonAnchor?: string | null;
  lineageCompatible?: boolean;
  /** PLA | LA | SA — set by applyEvent via classifyOrigin */
  origin: AccumulationOrigin;
  /** O / I / I₂ / V — set by applyEvent via classifyMode */
  mode: EpistemicMode;
  governanceBehavior?: GovernanceBehavior | null;
}

/** Event input before origin/mode tagging (applyEvent assigns both) */
export type JPSSContributionEventInput = Omit<JPSSContributionEvent, "origin" | "mode"> & {
  origin?: AccumulationOrigin;
  mode?: EpistemicMode;
};

export interface EpistemicMetrics {
  observationCount: number;
  interpretationCount: number;
  integrationCount: number;
  validationCount: number;
  obsToInterpRatio: number;
  interpToValidationRatio: number;
  externalObservationCount: number;
  profile: EpistemicBehaviorProfile;
}

export interface ValidationContext {
  predictiveAccuracyDelta: number;
  explanatoryCompressionDelta: number;
  crossDomainConvergence: number;
  operationalOutcomeDelta: number;
  critiqueStability: number;
}

export interface DriftSignals {
  predictiveDivergence: number;
  explanatoryInflation: number;
  convergenceFailure: number;
  operationalUnderperformance: number;
  loadSpike: number;
  aggregatePSD: number;
}

export type ChangeStatus = "PROVISIONAL" | "VALIDATED" | "REJECTED" | "ROLLED_BACK";

export interface LineageChange {
  id: string;
  description: string;
  affectsInvariants: string[];
  status: ChangeStatus;
  acceptedAt: string | null;
  validatedAt: string | null;
  originType?: AccumulationOrigin;
}

export interface LedgerEntry {
  changeId: string;
  originType: AccumulationOrigin | null;
  surpassmentEvidence: string;
  acceptanceEvidence: string;
  validationResult: "PENDING" | "PASSED" | "FAILED";
  driftSignals: DriftSignals | null;
  finalStatus: ChangeStatus;
  notes: string[];
}

export interface Invariant {
  id: string;
  name: string;
  description: string;
  weight: number;
  impact: number;
  status: "ACTIVE" | "UNDER_REVIEW" | "DEPRECATED";
}

export interface ReconstructabilityMetrics {
  reconstructionCost: number;
  reconstructionThreshold: number;
  k4Satisfied: boolean;
}

export interface PLAMetrics {
  plaCount: number;
  plaActors: number;
  plaDepth: number;
  plaToLaIntegrationRate: number;
  plaToLaRatio: number;
  /** How often PLA events hit the same targetsLayer (0–1) */
  clustering: number;
  /** Distinct layers PLA hits relative to event count (0–1) */
  crossDomainRecurrence: number;
  /** Share of PLA-linked changes that passed VAS-1 (0–1) */
  validationSurvival: number;
  /** Weighted scalar: instrument vs framework vs doctrine signal */
  instrumentality: number;
}

export interface LAMetrics {
  laCount: number;
  laActors: number;
  laDepth: number;
}

export interface SAMetrics {
  saCount: number;
  saActors: number;
}

export interface StratumCounts {
  pla: number;
  la: number;
  sa: number;
}

export interface AccumulationScore {
  value: number;
  strata: StratumCounts;
}

export interface PhenomenonLineageCoupling {
  plaCompatible: number;
  plaTotal: number;
  couplingStrength: number;
}

export interface ContinuityGravity {
  phenomenonGravity: number;
  lineageGravity: number;
  totalObservers: number;
}

export interface ThresholdConfig {
  plt1MinEvents: number;
  plt1MinActors: number;
  mat3MinLaEvents: number;
  mat3MinLaActors: number;
  k4Threshold: number;
  k3IntegrationMin: number;
}

export interface ThresholdStatus {
  plt1: boolean;
  mat3: boolean;
  stewardEmergence: boolean;
}

export interface InvariantHealth {
  k1IdentityCoherence: boolean;
  k2GenerativeGrammar: boolean;
  k3Integrability: boolean;
  k4Reconstructability: boolean;
}

export interface StewardCandidate {
  actor: string;
  qualified: boolean;
  plaCapable: boolean;
  laCapable: boolean;
  saCapable: boolean;
  k4Satisfied: boolean;
  hasPlaOrLa: boolean;
}

export interface ContinuityMetrics {
  accumulationCount: number;
  distinctActors: number;
  /** CSS-2 LA-focused MAT-3 */
  mat3: boolean;
  /** PLT-1: phenomena loud in the world */
  plt1: boolean;
  thresholds: ThresholdStatus;
  accumulation: AccumulationScore;
  reconstructability: ReconstructabilityMetrics;
  drift: DriftSignals | null;
  pla: PLAMetrics;
  la: LAMetrics;
  sa: SAMetrics;
  coupling: PhenomenonLineageCoupling;
  gravity: ContinuityGravity;
  invariants: InvariantHealth;
  interpretation: ContinuityInterpretation;
  epistemic: EpistemicMetrics;
}

export interface RAState {
  events: JPSSContributionEvent[];
  eventOrigins: Record<string, AccumulationOrigin>;
  /** Continuity Ledger v2 — completed judgment cycles (primitive) */
  ledgerCycles: JudgmentCycle[];
  /** In-progress cycles not yet appended to ledger */
  cycleDrafts: JudgmentCycleDraft[];
  /** Derived hypotheses — inferred from ledger + drafts */
  capabilityProfiles: Record<string, JudgmentCapabilityProfile>;
  stewardCandidates: StewardCandidate[];
  changes: Record<string, LineageChange>;
  ledger: Record<string, LedgerEntry>;
  invariants: Record<string, Invariant>;
  consequences: {
    changeId: string;
    timestamp: string;
    metric: string;
    value: number;
  }[];
  continuity: ContinuityMetrics;
}
