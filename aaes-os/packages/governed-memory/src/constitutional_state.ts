/** Article XV — Constitutional State Runtime (shared substrate of governed state). */

import type { TransitionReceiptV2 } from './receipts_v2.js';
import { isReceiptV2Complete } from './receipts_v2.js';

export type ConstitutionalStateName =
  | 'Proposed'
  | 'Evaluated'
  | 'Approved'
  | 'Executed'
  | 'Observed'
  | 'Challenged'
  | 'Arbitrated'
  | 'Remediated'
  | 'Closed';

export type StateObjectType =
  | 'ClaimState'
  | 'AuthorityState'
  | 'InstitutionState'
  | 'DecisionState'
  | 'ContinuityState'
  | 'SovereigntyState'
  | 'RealityState'
  | 'DomainState';

export const LEGAL_TRANSITIONS: Record<string, ConstitutionalStateName[]> = {
  Proposed: ['Evaluated'],
  Evaluated: ['Approved'],
  Approved: ['Executed'],
  Executed: ['Observed'],
  Observed: ['Challenged', 'Closed'],
  Challenged: ['Arbitrated'],
  Arbitrated: ['Remediated'],
  Remediated: ['Closed'],
};

export const DOMAIN_STATE_MAPS: Record<string, Record<string, ConstitutionalStateName>> = {
  Truth: {
    Supported: 'Evaluated',
    Verified: 'Approved',
    Diverged: 'Challenged',
  },
  Sovereignty: {
    Requested: 'Proposed',
    Delegated: 'Approved',
    Active: 'Executed',
    Suspended: 'Challenged',
    Revoked: 'Remediated',
  },
  Institutional: {
    Draft: 'Proposed',
    Audited: 'Challenged',
    Amended: 'Remediated',
  },
  Continuity: {
    EventRecorded: 'Executed',
  },
  Reproduction: {
    Reproduced: 'Executed',
    Diverged: 'Challenged',
  },
};

export interface StateTransition {
  transition_id: string;
  from_state: string;
  to_state: string;
  receipt_id: string;
  timestamp: string;
  legal_basis?: string;
  receipt_ids_used?: string[];
}

export interface StateObject {
  state_id: string;
  state_type: string;
  version: number;
  current_state: string;
  invariants: string[];
  evidence_requirements: string[];
  authority_model: string[];
  reproducibility_requirements: string[];
  impact_boundaries: string[];
  accountability_chain: string[];
  history: StateTransition[];
}

export interface ReplayResult {
  reconstructed_state: string;
  canonical_state: string;
  diverged: boolean;
  history_length: number;
  reconstructed_version: number;
  canonical_version: number;
  state_id: string;
  replay_hash: string;
}

export function validateTransition(fromState: string, toState: string): void {
  const allowed = LEGAL_TRANSITIONS[fromState] ?? [];
  if (!allowed.includes(toState as ConstitutionalStateName)) {
    throw new Error(`Illegal transition: ${fromState} → ${toState}`);
  }
}

export function mapDomainState(domain: string, domainState: string): string {
  return DOMAIN_STATE_MAPS[domain]?.[domainState] ?? domainState;
}

export function transitionFromReceipt(receipt: TransitionReceiptV2): StateTransition {
  if (!isReceiptV2Complete(receipt)) {
    throw new Error(`incomplete transition receipt: ${receipt.receipt_id}`);
  }
  return {
    transition_id: receipt.receipt_id,
    from_state: receipt.transition.from_state,
    to_state: receipt.transition.to_state,
    receipt_id: receipt.receipt_id,
    timestamp: receipt.timestamp,
    legal_basis: receipt.transition.legal_basis,
    receipt_ids_used: [...receipt.transition.receipt_ids_used],
  };
}

export function applyTransition(state: StateObject, transition: StateTransition): StateObject {
  if (transition.from_state !== state.current_state) {
    throw new Error(
      `Illegal transition for ${state.state_id}: ${state.current_state} → ${transition.to_state}`,
    );
  }
  validateTransition(transition.from_state, transition.to_state);
  return {
    ...state,
    current_state: transition.to_state,
    version: state.version + 1,
    history: [...state.history, transition],
  };
}

export function reconstructState(
  receipts: TransitionReceiptV2[],
  stateObj: StateObject,
): StateObject {
  let working = { ...stateObj, history: [...stateObj.history] };
  for (const receipt of receipts) {
    const transition = transitionFromReceipt(receipt);
    if (receipt.transition.state_id && receipt.transition.state_id !== working.state_id) {
      throw new Error(
        `receipt ${receipt.receipt_id} targets state ${receipt.transition.state_id}, expected ${working.state_id}`,
      );
    }
    working = applyTransition(working, transition);
  }
  return working;
}

export function replayState(
  receipts: TransitionReceiptV2[],
  canonicalState: StateObject,
): ReplayResult {
  const seed: StateObject = {
    state_id: canonicalState.state_id,
    state_type: canonicalState.state_type,
    version: 0,
    current_state: 'Proposed',
    invariants: [...canonicalState.invariants],
    evidence_requirements: [...canonicalState.evidence_requirements],
    authority_model: [...canonicalState.authority_model],
    reproducibility_requirements: [...canonicalState.reproducibility_requirements],
    impact_boundaries: [...canonicalState.impact_boundaries],
    accountability_chain: [...canonicalState.accountability_chain],
    history: [],
  };
  const reconstructed = reconstructState(receipts, seed);
  const diverged =
    reconstructed.current_state !== canonicalState.current_state ||
    reconstructed.version !== canonicalState.version;
  return {
    reconstructed_state: reconstructed.current_state,
    canonical_state: canonicalState.current_state,
    diverged,
    history_length: reconstructed.history.length,
    reconstructed_version: reconstructed.version,
    canonical_version: canonicalState.version,
    state_id: canonicalState.state_id,
    replay_hash: `${reconstructed.current_state}:${reconstructed.version}:${canonicalState.current_state}:${canonicalState.version}`,
  };
}
