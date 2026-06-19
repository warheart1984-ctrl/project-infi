import { createEvidenceReceipt, type EvidenceReceipt } from '@aaes-os/evidence-receipts';
import {
  createLawOfLawsLedger,
  type LawOfLawsEntry,
} from '@aaes-os/meta-constitutional-calculus';
import type { MRIOutputV2 } from '@aaes-os/mri-instrument';
import { modelStateTransition, type NimfStateModel } from '@aaes-os/nimf';

export type EvolutionMode = 'Genesis' | 'Resonance' | 'Sacrifice';
export type EvolutionDecision = 'promote' | 'retain' | 'revert';

export interface InvariantProposalInput {
  invariantId: string;
  expression: string;
  mode?: EvolutionMode;
}

export interface InvariantProposal extends Required<InvariantProposalInput> {
  status: 'proposed';
}

export interface ConstitutionalEvolutionDecision {
  invariantId: string;
  decision: EvolutionDecision;
  mode: EvolutionMode;
  stage: 'soft' | 'constitutional' | 'reverted';
  nimf: NimfStateModel;
  receipt: EvidenceReceipt;
  lawOfLawsEntry: LawOfLawsEntry;
}

const evolutionLedger = createLawOfLawsLedger();

export function proposeInvariant(input: InvariantProposalInput): InvariantProposal {
  return {
    invariantId: input.invariantId,
    expression: input.expression,
    mode: input.mode ?? 'Genesis',
    status: 'proposed',
  };
}

export function evaluateInvariantFitness(input: {
  proposal: InvariantProposal;
  mri: MRIOutputV2;
}): ConstitutionalEvolutionDecision {
  const nimf = modelStateTransition(input.mri);
  const avgDelta =
    (input.mri.delta_state.continuity +
      input.mri.delta_state.governance +
      input.mri.delta_state.memory +
      input.mri.delta_state.coordination) /
    4;
  const decision: EvolutionDecision =
    avgDelta > 0.01 && input.mri.evidence.meanConfidence >= 0.55
      ? 'promote'
      : avgDelta < -0.01
        ? 'revert'
        : 'retain';
  return decisionRecord(input.proposal.invariantId, decision, input.proposal.mode, nimf);
}

export function promoteInvariant(invariantId: string): ConstitutionalEvolutionDecision {
  return decisionRecord(invariantId, 'promote', 'Resonance', emptyNimf());
}

export function retainInvariant(invariantId: string): ConstitutionalEvolutionDecision {
  return decisionRecord(invariantId, 'retain', 'Resonance', emptyNimf());
}

export function revertInvariant(invariantId: string): ConstitutionalEvolutionDecision {
  return decisionRecord(invariantId, 'revert', 'Sacrifice', emptyNimf());
}

function decisionRecord(
  invariantId: string,
  decision: EvolutionDecision,
  mode: EvolutionMode,
  nimf: NimfStateModel,
): ConstitutionalEvolutionDecision {
  const stage = decision === 'promote' ? 'constitutional' : decision === 'revert' ? 'reverted' : 'soft';
  const subject = { invariantId, decision, mode, stage, nimf };
  const receipt = createEvidenceReceipt({
    claimLabel: `constitutional-evolution:${decision}`,
    subsystem: 'constitutional-evolution',
    evidenceRefs: [`invariant:${invariantId}`, `mode:${mode}`],
    subject,
  });
  const lawOfLawsEntry = evolutionLedger.append({
    entryType: 'evolution_decision',
    subjectId: invariantId,
    payload: subject,
  });
  return { invariantId, decision, mode, stage, nimf, receipt, lawOfLawsEntry };
}

function emptyNimf(): NimfStateModel {
  return {
    velocity: { continuity: 0, governance: 0, memory: 0, coordination: 0, confidence: 0 },
    acceleration: { continuity: 0, governance: 0, memory: 0, coordination: 0, confidence: 0 },
    volatility: 0,
    confidenceWeightedRisk: 0,
  };
}
