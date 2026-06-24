export type Id = string;
export type ISOTime = string;
export type Comparator = ">" | ">=" | "<" | "<=" | "==" | "!=" | "in" | "out";

export interface Threshold {
  id: string;
  name: string;
  domain: string;
  metric: string;
  comparator: Comparator;
  value: unknown;
  unit?: string;
  context?: Record<string, unknown>;
  intent: string;
  version: number;
  active: boolean;
  createdAt: ISOTime;
  createdBy: Id;
  lastUpdatedAt: ISOTime;
  lastUpdatedBy: Id;
}

export interface ThresholdVersion {
  thresholdId: string;
  version: number;
  snapshot: Threshold;
  deltaRationale: string;
  recalibrationEventId?: string;
  createdAt: ISOTime;
  createdBy: Id;
}

export interface ThresholdDelta {
  thresholdId: Id;
  before: Threshold;
  after: Partial<Threshold>;
  rationale: string;
  recalibrationEventId?: Id;
}

export interface Invariant {
  id: string;
  description: string;
  nonDerogable: boolean;
  checkThresholdChange?: (before: Threshold, after: Threshold) => boolean;
}

export interface InvariantSet {
  invariants: Invariant[];
}

export type RecalibrationDecision = "approved" | "rejected" | "deferred" | "escalated";

export type RecalibrationTriggerReason =
  | "systematic_misclassification"
  | "late_intervention"
  | "over_intervention"
  | "drift_signal"
  | "failure_pattern"
  | "operator_feedback";

export interface RecalibrationTrigger {
  thresholdId: string;
  reason: RecalibrationTriggerReason;
  evidence: unknown[];
}

export type RecalibrationFailureMode =
  | "CalibrationDrift"
  | "RecalibrationFailure"
  | "RecalibrationCapture"
  | "FalseRecalibration"
  | "OverRecalibration"
  | "UnderRecalibration"
  | "MetaDrift"
  | "ThresholdCollapse"
  | "AdversarialRecalibration"
  | "RecalibrationInversion"
  | "RecalibrationParalysis"
  | "RecalibrationMyopia";

export interface RecalibrationEvent {
  eventId: string;
  timestamp: ISOTime;
  scope: "local" | "subsystem" | "system" | "constitutional";
  triggerType: "evidence" | "drift" | "failure" | "mandate" | "other";
  failureModeBefore?: RecalibrationFailureMode;
  proposedChanges: {
    id: string;
    before: Threshold;
    after: Threshold;
    rationale: string;
  }[];
  invariantsChecked: Invariant[];
  decision: RecalibrationDecision;
  legitimacyBasis: string;
  continuityEffect?: "improved" | "degraded" | "ambiguous";
  decidedBy: string;
  /** CRK-1.J — legitimate judgment summary attached by governance engine. */
  legitimateJudgment?: LegitimateJudgmentSummary;
}

/** Slim CRK-1.J result on recalibration events (avoids circular imports). */
export interface LegitimateJudgmentSummary {
  legitimate: boolean;
  category: "CRK-1.J";
  satisfiedRequirements: string[];
  failedRequirements: string[];
  gaps: string[];
}

export interface ObservationPattern {
  id: Id;
  domain: string;
  description: string;
  evidence: Id[];
  proposedBy: Id;
  createdAt: ISOTime;
  status: "open" | "formalized" | "rejected";
  tags?: string[];
}

export interface ProtoThreshold {
  id: Id;
  patternId: Id;
  domain: string;
  metric: string;
  comparator: Comparator;
  value: unknown;
  unit?: string;
  intent: string;
  proposedBy: Id;
  createdAt: ISOTime;
  status: "draft" | "testing" | "adopted" | "rejected";
  notes?: string;
}

export type ObserverStage = "person" | "observer" | "senior_observer" | "steward";

export interface ObserverProfile {
  id: Id;
  name: string;
  stage: ObserverStage;
  joinedAt: ISOTime;
  capabilities: {
    perception: number;
    interpretation: number;
    hypothesis: number;
    judgment: number;
    stewardship: number;
  };
  driftScore: number;
  flags: {
    captured?: boolean;
    fragmented?: boolean;
    dependent?: boolean;
    exhausted?: boolean;
  };
}

export interface ThresholdLifecycle {
  observationPattern: ObservationPattern;
  protoThresholds: ProtoThreshold[];
  threshold: Threshold | null;
  deltas: ThresholdDelta[];
}

export interface MetricHistory {
  values: number[];
  timestamps: string[];
}

export interface ValidationContext {
  historyForThreshold?: Record<string, MetricHistory>;
  lateInterventionsForThreshold?: Record<string, number>;
  falsePositiveRateForThreshold?: Record<string, number>;
  continuityFailuresLast30Days?: number;
  misclassified?: boolean;
  late?: boolean;
  over?: boolean;
  operator_feedback?: boolean;
  pattern?: string | null;
}

export interface DriftSignals {
  strong?: boolean;
  klDivergence?: number;
  meanShift?: number;
  domain?: string;
  metric?: string;
}

export type ThresholdCreateInput = Omit<
  Threshold,
  "version" | "active" | "createdAt" | "lastUpdatedAt" | "lastUpdatedBy"
> & { lastUpdatedBy?: Id };

export function mergeThreshold(before: Threshold, patch: Partial<Threshold>): Threshold {
  return { ...before, ...patch };
}
