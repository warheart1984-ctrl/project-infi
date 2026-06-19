export type MRIPhase = 'before' | 'after';

export type StateVectorKey = 'R' | 'K' | 'G' | 'D' | 'X';

export type StateVector = Record<StateVectorKey, number>;

export type RiskType =
  | 'single_point_of_failure'
  | 'documentation_gap'
  | 'governance_ambiguity'
  | 'decision_bottleneck'
  | 'coordination_overload';

export type InterventionType =
  | 'succession_protocol'
  | 'documentation_sprint'
  | 'decision_workflow'
  | 'governance_clarification'
  | 'coordination_simplification';

export interface ContinuityInputs {
  singlePointsOfFailure: number;
  criticalRoles: number;
  documentedKnowledge: number;
  totalRequiredKnowledge: number;
  clearGovernanceElements: number;
  totalGovernanceElements: number;
  medianDecisionTime: number;
  expectedDecisionTime: number;
  coordinationLoad: number;
  coordinationCapacity: number;
}

export interface GovernanceInputs {
  authorityClarity: number;
  escalationClarity: number;
  roleDefinitionQuality: number;
  decisionTransparency: number;
}

export interface MemoryInputs {
  documentationCoverage: number;
  artifactAccessibility: number;
  successionReadiness: number;
}

export interface ConfidenceInputs {
  observationCompleteness: number;
  dataQuality: number;
  sourceReliability: number;
  temporalFreshness: number;
  /** Cross-evidence agreement (0–1); defaults to observation completeness when omitted. */
  crossEvidenceConsistency?: number;
}

export interface OrgMeasurement {
  orgId: string;
  label: string;
  phase: MRIPhase;
  measuredAt: string;
  continuityInputs: ContinuityInputs;
  governanceInputs: GovernanceInputs;
  memoryInputs: MemoryInputs;
  confidenceInputs: ConfidenceInputs;
}

export interface Risk {
  id: string;
  type: RiskType;
  description: string;
  impact: number;
  feasibility: number;
  urgency: number;
}

export interface Intervention {
  id: string;
  type: InterventionType;
  targetRiskId: string;
  description: string;
  expectedContinuityDelta: number;
  expectedGovernanceDelta: number;
  expectedMemoryDelta: number;
  implementationSteps: string[];
  score: number;
}

export interface MRIResult {
  measurement: OrgMeasurement;
  scores: {
    continuity: number;
    governance: number;
    memory: number;
    confidence: number;
  };
  state: StateVector;
  risks: Risk[];
  interventions: Intervention[];
}

export interface MRIComparison {
  orgId: string;
  before: MRIResult;
  after: MRIResult;
  deltaState: StateVector;
}

export interface BeforeAfterReport {
  orgId: string;
  beforeContinuity: number;
  afterContinuity: number;
  continuityDelta: number;
  beforeConfidence: number;
  afterConfidence: number;
  largestStateTransitions: { key: StateVectorKey; delta: number }[];
  summary: string;
}

const stateVectorKeys: StateVectorKey[] = ['R', 'K', 'G', 'D', 'X'];

function round(value: number, decimals = 3): number {
  const scale = 10 ** decimals;
  return Math.round(value * scale) / scale;
}

function clamp(value: number, min: number, max: number): number {
  if (!Number.isFinite(value)) return min;
  return Math.min(max, Math.max(min, value));
}

function percentage(numerator: number, denominator: number): number {
  if (denominator <= 0) return 0;
  return clamp((numerator / denominator) * 100, 0, 100);
}

function inversePercentage(numerator: number, denominator: number): number {
  if (denominator <= 0) return 0;
  return clamp(100 - (numerator / denominator) * 100, 0, 100);
}

export function computeContinuityComponents(input: ContinuityInputs): StateVector {
  return {
    R: round(inversePercentage(input.singlePointsOfFailure, input.criticalRoles)),
    K: round(percentage(input.documentedKnowledge, input.totalRequiredKnowledge)),
    G: round(percentage(input.clearGovernanceElements, input.totalGovernanceElements)),
    D: round(inversePercentage(input.medianDecisionTime, input.expectedDecisionTime)),
    X: round(inversePercentage(input.coordinationLoad, input.coordinationCapacity)),
  };
}

export function continuityScore(state: StateVector): number {
  return round(0.25 * state.R + 0.25 * state.K + 0.2 * state.G + 0.15 * state.D + 0.15 * state.X);
}

export function governanceScore(input: GovernanceInputs): number {
  return round(
    0.3 * clamp(input.authorityClarity, 0, 100)
      + 0.25 * clamp(input.escalationClarity, 0, 100)
      + 0.25 * clamp(input.roleDefinitionQuality, 0, 100)
      + 0.2 * clamp(input.decisionTransparency, 0, 100),
  );
}

export function memoryScore(input: MemoryInputs): number {
  return round(
    0.4 * clamp(input.documentationCoverage, 0, 100)
      + 0.35 * clamp(input.artifactAccessibility, 0, 100)
      + 0.25 * clamp(input.successionReadiness, 0, 100),
  );
}

export function computeConfidence(input: ConfidenceInputs): number {
  return round(
    0.3 * clamp(input.observationCompleteness, 0, 1)
      + 0.3 * clamp(input.dataQuality, 0, 1)
      + 0.2 * clamp(input.sourceReliability, 0, 1)
      + 0.2 * clamp(input.temporalFreshness, 0, 1),
  );
}

export function computeDeltaState(before: StateVector, after: StateVector): StateVector {
  return {
    R: round(after.R - before.R),
    K: round(after.K - before.K),
    G: round(after.G - before.G),
    D: round(after.D - before.D),
    X: round(after.X - before.X),
  };
}

export function detectRisks(state: StateVector): Risk[] {
  const risks: Risk[] = [];

  if (state.R < 70) {
    risks.push({
      id: 'risk_spf',
      type: 'single_point_of_failure',
      description: 'Critical AAES OS roles lack explicit backup ownership.',
      impact: 9,
      feasibility: 7,
      urgency: 8,
    });
  }

  if (state.K < 70) {
    risks.push({
      id: 'risk_docs',
      type: 'documentation_gap',
      description: 'Operational knowledge is not sufficiently documented or transferable.',
      impact: 9,
      feasibility: 8,
      urgency: 8,
    });
  }

  if (state.G < 70) {
    risks.push({
      id: 'risk_gov',
      type: 'governance_ambiguity',
      description: 'Decision rights, escalation paths, or role boundaries are unclear.',
      impact: 8,
      feasibility: 6,
      urgency: 7,
    });
  }

  if (state.D < 70) {
    risks.push({
      id: 'risk_decision',
      type: 'decision_bottleneck',
      description: 'Decisions move slower than the expected operating cadence.',
      impact: 7,
      feasibility: 7,
      urgency: 6,
    });
  }

  if (state.X < 70) {
    risks.push({
      id: 'risk_coord',
      type: 'coordination_overload',
      description: 'Coordination load is too high for the current operating capacity.',
      impact: 7,
      feasibility: 6,
      urgency: 7,
    });
  }

  return risks;
}

export function recommendInterventions(risks: Risk[], confidence: number): Intervention[] {
  const safeConfidence = clamp(confidence, 0, 1);
  const confidenceMultiplier = 0.5 + 0.5 * safeConfidence;

  return risks
    .map((risk) => {
      const type = interventionTypeForRisk(risk.type);
      const score = round(risk.impact * risk.feasibility * risk.urgency * confidenceMultiplier);

      return {
        id: `int_${risk.id}`,
        type,
        targetRiskId: risk.id,
        description: interventionDescription(type),
        expectedContinuityDelta: round(Math.min(15, risk.impact * 1.5)),
        expectedGovernanceDelta: risk.type === 'governance_ambiguity' ? 15 : 5,
        expectedMemoryDelta: risk.type === 'documentation_gap' ? 15 : 5,
        implementationSteps: interventionSteps(type),
        score,
      };
    })
    .sort((a, b) => b.score - a.score);
}

export function runMRI(measurement: OrgMeasurement): MRIResult {
  const state = computeContinuityComponents(measurement.continuityInputs);
  const confidence = computeConfidence(measurement.confidenceInputs);
  const risks = detectRisks(state);

  return {
    measurement,
    scores: {
      continuity: continuityScore(state),
      governance: governanceScore(measurement.governanceInputs),
      memory: memoryScore(measurement.memoryInputs),
      confidence,
    },
    state,
    risks,
    interventions: recommendInterventions(risks, confidence),
  };
}

export function runMRIComparison(before: OrgMeasurement, after: OrgMeasurement): MRIComparison {
  const beforeResult = runMRI(before);
  const afterResult = runMRI(after);

  return {
    orgId: before.orgId,
    before: beforeResult,
    after: afterResult,
    deltaState: computeDeltaState(beforeResult.state, afterResult.state),
  };
}

export {
  buildMRIOutputV2,
  evaluateInvariantFitness,
  type InvariantFitnessResult,
  type MRIOutputV2,
} from './mriV2.js';
export {
  computeBenchmarkDeltas,
  summarizeBenchmarks,
  summarizeBenchmarksDetailed,
  publicScoresFromComparison,
  type BenchmarkDelta,
  type BenchmarkSnapshot,
  type BenchmarkSummary,
  type PublicDimensionScores,
} from './benchmark.js';
export {
  computeConfidenceTensor,
  confidenceTensorScalar,
  type ConfidenceTensor,
} from './confidenceTensor.js';
export {
  computeTrajectoryVector,
  detectTrajectorySignatures,
  projectPublicState,
  trajectoryBreakdownTable,
  TRAJECTORY_SIGNATURE_LABELS,
  type TrajectoryBreakdownRow,
  type TrajectorySignatureId,
  type TrajectoryVector,
} from './trajectory.js';
export { PILOT_AFTER, PILOT_BEFORE, PILOT_BENCHMARKS } from './pilotFixtures.js';

export function generateBeforeAfterReport(comparison: MRIComparison): BeforeAfterReport {
  const continuityDelta = round(comparison.after.scores.continuity - comparison.before.scores.continuity);
  const largestStateTransitions = stateVectorKeys
    .map((key) => ({ key, delta: comparison.deltaState[key] }))
    .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta));

  const summary = `Continuity increased by ${continuityDelta} points with confidence ${comparison.after.scores.confidence}. Largest state transition: ${largestStateTransitions[0]?.key ?? 'none'} ${formatDelta(largestStateTransitions[0]?.delta ?? 0)}.`;

  return {
    orgId: comparison.orgId,
    beforeContinuity: comparison.before.scores.continuity,
    afterContinuity: comparison.after.scores.continuity,
    continuityDelta,
    beforeConfidence: comparison.before.scores.confidence,
    afterConfidence: comparison.after.scores.confidence,
    largestStateTransitions,
    summary,
  };
}

function interventionTypeForRisk(type: RiskType): InterventionType {
  switch (type) {
    case 'single_point_of_failure':
      return 'succession_protocol';
    case 'documentation_gap':
      return 'documentation_sprint';
    case 'decision_bottleneck':
      return 'decision_workflow';
    case 'governance_ambiguity':
      return 'governance_clarification';
    case 'coordination_overload':
      return 'coordination_simplification';
  }
}

function interventionDescription(type: InterventionType): string {
  switch (type) {
    case 'succession_protocol':
      return 'Define backup owners and succession paths for critical AAES OS roles.';
    case 'documentation_sprint':
      return 'Create and validate transferable documentation for critical AAES OS operations.';
    case 'decision_workflow':
      return 'Install a clear decision workflow with lightweight receipts.';
    case 'governance_clarification':
      return 'Clarify decision rights, escalation paths, and role boundaries.';
    case 'coordination_simplification':
      return 'Reduce unnecessary dependencies and simplify coordination load.';
  }
}

function interventionSteps(type: InterventionType): string[] {
  switch (type) {
    case 'succession_protocol':
      return ['Identify critical roles', 'Assign backups', 'Document ownership', 'Review succession coverage'];
    case 'documentation_sprint':
      return ['List fragile knowledge', 'Assign documentation owners', 'Write artifacts', 'Validate transferability'];
    case 'decision_workflow':
      return ['Map current decisions', 'Define target workflow', 'Record decisions', 'Review cycle time'];
    case 'governance_clarification':
      return ['List key decision types', 'Assign authorities', 'Define escalation paths', 'Publish governance map'];
    case 'coordination_simplification':
      return ['Find high-dependency tasks', 'Remove unnecessary dependencies', 'Assign coordination owners', 'Re-measure load'];
  }
}

function formatDelta(value: number): string {
  return value >= 0 ? `+${value}` : String(value);
}
