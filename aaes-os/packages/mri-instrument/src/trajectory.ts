import type { ConfidenceTensor } from './confidenceTensor.js';
import type { PublicStateVector } from './benchmark.js';

export type TrajectoryVector = {
  continuity: number;
  governance: number;
  memory: number;
  coordination: number;
  magnitude: number;
  confidenceWeightedMagnitude: number;
};

export type TrajectoryBreakdownRow = {
  dimension: keyof PublicStateVector;
  delta: number;
  confidence: number;
  contribution: number;
  direction: 'up' | 'down' | 'flat';
};

export type TrajectorySignatureId =
  | 'stable_continuity_stable_governance'
  | 'stable_continuity_improving_memory'
  | 'stable_continuity_declining_governance'
  | 'low_continuity_positive_trajectory'
  | 'memory_recovery_leading'
  | 'high_continuity_negative_trajectory'
  | 'governance_decay_pulling_continuity'
  | 'memory_improving_coordination_degrading'
  | 'coordination_collapse_high_confidence'
  | 'governance_improving_continuity_degrading'
  | 'subsystem_divergence'
  | 'volatile_low_confidence'
  | 'contradictory_subsystem_motion';

export const TRAJECTORY_SIGNATURE_LABELS: Record<TrajectorySignatureId, string> = {
  stable_continuity_stable_governance: 'Stable continuity, stable governance',
  stable_continuity_improving_memory: 'Stable continuity, improving memory',
  stable_continuity_declining_governance: 'Stable continuity, declining governance',
  low_continuity_positive_trajectory: 'Low continuity, positive trajectory',
  memory_recovery_leading: 'Memory recovery leading continuity',
  high_continuity_negative_trajectory: 'High continuity, negative trajectory',
  governance_decay_pulling_continuity: 'Governance decay pulling continuity down',
  memory_improving_coordination_degrading: 'Improving memory, degrading coordination',
  coordination_collapse_high_confidence: 'Coordination collapse with high confidence',
  governance_improving_continuity_degrading: 'Governance improving, continuity degrading',
  subsystem_divergence: 'Subsystem divergence (high cross-evidence conflict)',
  volatile_low_confidence: 'High motion, low confidence',
  contradictory_subsystem_motion: 'Contradictory subsystem motion',
};

type SignatureRule = {
  id: TrajectorySignatureId;
  riskClass: 'stable' | 'recovery' | 'decline' | 'fragmentation' | 'volatile';
  match: (ctx: SignatureContext) => boolean;
};

type SignatureContext = {
  state: PublicStateVector;
  delta: PublicStateVector;
  trajectory: TrajectoryVector;
  crossEvidenceConsistency: number;
};

const SIGNATURE_CATALOG: SignatureRule[] = [
  {
    id: 'stable_continuity_declining_governance',
    riskClass: 'decline',
    match: ({ state, delta }) => state.continuity >= 65 && delta.governance < -0.02,
  },
  {
    id: 'stable_continuity_improving_memory',
    riskClass: 'stable',
    match: ({ state, delta }) => state.continuity >= 65 && delta.memory > 0.03,
  },
  {
    id: 'memory_improving_coordination_degrading',
    riskClass: 'fragmentation',
    match: ({ delta }) => delta.memory > 0.03 && delta.coordination < -0.02,
  },
  {
    id: 'high_continuity_negative_trajectory',
    riskClass: 'decline',
    match: ({ state, trajectory }) => state.continuity >= 70 && trajectory.magnitude > 0.05 && trajectory.continuity < 0,
  },
  {
    id: 'low_continuity_positive_trajectory',
    riskClass: 'recovery',
    match: ({ state, trajectory }) => state.continuity < 60 && trajectory.magnitude > 0.03 && trajectory.continuity > 0,
  },
  {
    id: 'memory_recovery_leading',
    riskClass: 'recovery',
    match: ({ delta, trajectory }) => delta.memory > 0.04 && trajectory.memory > trajectory.continuity,
  },
  {
    id: 'governance_decay_pulling_continuity',
    riskClass: 'decline',
    match: ({ delta }) => delta.governance < -0.03 && delta.continuity <= 0,
  },
  {
    id: 'coordination_collapse_high_confidence',
    riskClass: 'decline',
    match: ({ delta, trajectory }) => delta.coordination < -0.04 && trajectory.confidenceWeightedMagnitude > 0.05,
  },
  {
    id: 'governance_improving_continuity_degrading',
    riskClass: 'fragmentation',
    match: ({ delta }) => delta.governance > 0.03 && delta.continuity < -0.02,
  },
  {
    id: 'subsystem_divergence',
    riskClass: 'fragmentation',
    match: ({ crossEvidenceConsistency }) => crossEvidenceConsistency < 0.55,
  },
  {
    id: 'volatile_low_confidence',
    riskClass: 'volatile',
    match: ({ trajectory, crossEvidenceConsistency }) =>
      trajectory.magnitude > 0.12 && crossEvidenceConsistency < 0.65,
  },
  {
    id: 'contradictory_subsystem_motion',
    riskClass: 'volatile',
    match: ({ delta }) => {
      const signs = [delta.continuity, delta.governance, delta.memory, delta.coordination].filter(
        (v) => Math.abs(v) > 0.02,
      );
      const pos = signs.filter((v) => v > 0).length;
      const neg = signs.filter((v) => v < 0).length;
      return pos >= 2 && neg >= 2;
    },
  },
  {
    id: 'stable_continuity_stable_governance',
    riskClass: 'stable',
    match: ({ state, delta }) =>
      state.continuity >= 65 &&
      state.governance >= 60 &&
      Math.abs(delta.continuity) < 0.03 &&
      Math.abs(delta.governance) < 0.03,
  },
];

function directionFor(delta: number): 'up' | 'down' | 'flat' {
  if (delta > 0.01) return 'up';
  if (delta < -0.01) return 'down';
  return 'flat';
}

/** T(t) = C ⊙ ΔS(t) on normalized [-1,1] deltas per dimension. */
export function computeTrajectoryVector(
  deltaState: PublicStateVector,
  tensor: ConfidenceTensor,
): TrajectoryVector {
  const continuity = tensor.observationCompleteness * deltaState.continuity;
  const governance = tensor.dataQuality * deltaState.governance;
  const memory = tensor.sourceReliability * deltaState.memory;
  const coordination = tensor.temporalFreshness * deltaState.coordination;

  const components = [continuity, governance, memory, coordination];
  const magnitude = Math.sqrt(components.reduce((sum, v) => sum + v * v, 0));
  const meanConfidence =
    (tensor.observationCompleteness +
      tensor.dataQuality +
      tensor.sourceReliability +
      tensor.temporalFreshness +
      tensor.crossEvidenceConsistency) /
    5;
  const confidenceWeightedMagnitude = magnitude * meanConfidence;

  return {
    continuity,
    governance,
    memory,
    coordination,
    magnitude,
    confidenceWeightedMagnitude,
  };
}

export function buildTrajectoryBreakdown(
  deltaState: PublicStateVector,
  tensor: ConfidenceTensor,
  trajectory: TrajectoryVector,
): TrajectoryBreakdownRow[] {
  const dims: (keyof PublicStateVector)[] = ['continuity', 'governance', 'memory', 'coordination'];
  const confMap: Record<keyof PublicStateVector, number> = {
    continuity: tensor.observationCompleteness,
    governance: tensor.dataQuality,
    memory: tensor.sourceReliability,
    coordination: tensor.temporalFreshness,
    confidence: tensor.crossEvidenceConsistency,
  };
  const trajMap: Record<keyof PublicStateVector, number> = {
    continuity: trajectory.continuity,
    governance: trajectory.governance,
    memory: trajectory.memory,
    coordination: trajectory.coordination,
    confidence: 0,
  };

  return dims.map((dimension) => ({
    dimension,
    delta: deltaState[dimension],
    confidence: confMap[dimension],
    contribution: trajMap[dimension],
    direction: directionFor(deltaState[dimension]),
  }));
}

/** @deprecated Use buildTrajectoryBreakdown */
export const trajectoryBreakdownTable = buildTrajectoryBreakdown;

export function classifyTrajectorySignatures(
  state: PublicStateVector,
  deltaState: PublicStateVector,
  trajectory: TrajectoryVector,
  crossEvidenceConsistency: number,
): TrajectorySignatureId[] {
  const ctx: SignatureContext = { state, delta: deltaState, trajectory, crossEvidenceConsistency };
  const matched = SIGNATURE_CATALOG.filter((rule) => rule.match(ctx)).map((rule) => rule.id);
  return matched.length > 0 ? matched : ['stable_continuity_stable_governance'];
}

/** @deprecated Use classifyTrajectorySignatures */
export function detectTrajectorySignatures(
  current: PublicStateVector,
  deltaState: PublicStateVector,
  trajectory: TrajectoryVector,
  crossEvidenceConsistency: number,
): TrajectorySignatureId[] {
  return classifyTrajectorySignatures(current, deltaState, trajectory, crossEvidenceConsistency);
}

export function projectPublicState(
  current: PublicStateVector,
  deltaState: PublicStateVector,
  steps = 2,
): PublicStateVector[] {
  const out: PublicStateVector[] = [current];
  let cursor = { ...current };
  for (let step = 1; step <= steps; step += 1) {
    const scale = step;
    cursor = {
      continuity: clampScore(cursor.continuity + deltaState.continuity * 100 * scale),
      governance: clampScore(cursor.governance + deltaState.governance * 100 * scale),
      memory: clampScore(cursor.memory + deltaState.memory * 100 * scale),
      coordination: clampScore(cursor.coordination + deltaState.coordination * 100 * scale),
      confidence: cursor.confidence,
    };
    out.push(cursor);
  }
  return out;
}

function clampScore(value: number): number {
  return Math.max(0, Math.min(100, value));
}
