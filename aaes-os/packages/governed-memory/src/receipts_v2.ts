/** Receipt v2 — Six-Dimension Runtime Contract + Article XIV Remediation Lifecycle. */

export type LifecycleStage =
  | 'decision'
  | 'observation'
  | 'divergence'
  | 'remediation'
  | 'closure';

export type ReproducibilityMode =
  | 'exact'
  | 'structural'
  | 'approximate'
  | 'non_reproducible';

export type ClaimType =
  | 'factual'
  | 'procedural'
  | 'authority'
  | 'continuity'
  | 'reality';

// --- Shared blocks -----------------------------------------------------------

export interface EvidenceSourceV2 {
  id: string;
  type: string;
  provenance: string;
}

export interface ChainOfCustodyEntryV2 {
  holder: string;
  timestamp: string;
  action: string;
}

export interface EvidenceSufficiencyV2 {
  continuity: boolean;
  truth: boolean;
  sovereignty: boolean;
  institutional: boolean;
}

export interface EvidenceBundleV2 {
  bundle_id: string;
  sources: EvidenceSourceV2[];
  modalities: string[];
  chain_of_custody: ChainOfCustodyEntryV2[];
  sufficiency: EvidenceSufficiencyV2;
}

export interface DelegationLinkV2 {
  from: string;
  to: string;
  scope: string;
  timestamp: string;
}

export interface ConsentBlockV2 {
  granted_by?: string;
  timestamp?: string;
  terms?: string;
}

export interface AuthorityBlockV2 {
  source: string;
  jurisdiction: string;
  delegation_chain: DelegationLinkV2[];
  consent?: ConsentBlockV2;
  legitimacy_basis: string;
}

export interface ReproducibilityBlockV2 {
  is_reproducible: boolean;
  mode: ReproducibilityMode;
  constraints?: string;
  reproduction_reference_id?: string;
}

export interface ImpactBoundaryV2 {
  scope_in: string[];
  scope_out: string[];
  notes?: string;
}

export interface AccountabilityChainEntryV2 {
  role: string;
  party_id: string;
  responsibility_scope: string;
  escalation_path?: string;
}

export interface AccountabilityBlockV2 {
  primary_accountable_party: string;
  accountability_chain: AccountabilityChainEntryV2[];
}

export interface ReceiptContextV2 {
  mission_id?: string;
  task_id?: string;
  observer_id?: string;
}

export interface ReceiptInputsV2 {
  request_id: string;
  payload_hash: string;
  context: ReceiptContextV2;
}

export interface ReceiptOutputsV2 {
  status: string;
  result_hash: string;
  notes?: string;
}

export interface InvariantBlockV2 {
  name: string;
  description: string;
  satisfied: boolean;
}

export interface SignaturesBlockV2 {
  runtime_signature: string;
  observer_signature?: string;
}

export interface ContinuityBlockV2 {
  previous_receipt_id?: string;
  thread_id?: string;
  lineage_hash: string;
}

export interface LifecycleBlockV2 {
  stage: LifecycleStage;
  previous_stage_receipt_id?: string | null;
  next_stage_expected?: string | null;
}

// --- Base receipt ------------------------------------------------------------

export interface BaseReceiptV2 {
  receipt_id: string;
  runtime: string;
  timestamp: string;
  action_type: string;

  inputs: ReceiptInputsV2;
  outputs: ReceiptOutputsV2;

  invariant: InvariantBlockV2;
  evidence: EvidenceBundleV2;
  authority: AuthorityBlockV2;
  reproducibility: ReproducibilityBlockV2;
  impact_boundary: ImpactBoundaryV2;
  accountability: AccountabilityBlockV2;

  signatures: SignaturesBlockV2;
  continuity: ContinuityBlockV2;
  lifecycle: LifecycleBlockV2;
}

// --- Runtime-specific receipts ----------------------------------------------

export interface TruthReceiptV2 extends BaseReceiptV2 {
  claim: {
    claim_id: string;
    claim_type: ClaimType;
    statement: string;
  };
  verification: {
    method: string;
    confidence: number;
    evidence_used: string[];
    contradictions?: string[];
  };
}

export interface SovereigntyReceiptV2 extends BaseReceiptV2 {
  delegation: {
    granted_by: string;
    granted_to: string;
    scope: string;
    jurisdiction: string;
    terms?: string;
  };
  legitimacy: {
    basis: string;
    validated: boolean;
    conflicts?: string[];
  };
}

export interface ReproductionReceiptV2 extends BaseReceiptV2 {
  reproduction: {
    reference_receipt_id: string;
    divergence: {
      diverged: boolean;
      divergence_points?: string[];
      structural_match: boolean;
      output_match: boolean;
    };
  };
}

export interface ContinuityReceiptV2 extends BaseReceiptV2 {
  event: {
    event_id: string;
    event_type: string;
    timestamp_observed: string;
  };
  lineage: {
    chain_of_custody: string[];
    continuity_satisfied: boolean;
  };
}

export interface InstitutionalReceiptV2 extends BaseReceiptV2 {
  procedure: {
    procedure_id: string;
    version: string;
    steps_followed: string[];
    deviations?: string[];
  };
  compliance: {
    compliant: boolean;
    violations?: string[];
  };
}

export interface ArbitrationReceiptV2 extends BaseReceiptV2 {
  conflict: {
    runtimes_in_conflict: string[];
    conflict_type: string;
    evidence_presented: string[];
  };
  resolution: {
    winning_runtime: string;
    rationale: string;
    precedence_rule: string;
  };
}

// --- Article XIV lifecycle receipts -----------------------------------------

export interface ObservationPayloadV2 {
  observed_status: string;
  observed_at: string;
  observer_jurisdiction: string;
  notes?: string;
}

export interface DivergencePayloadV2 {
  nature: string;
  magnitude: string;
  evidence_receipt_ids: string[];
  expected_outcome_hash?: string;
  observed_outcome_hash?: string;
}

export interface RemediationPayloadV2 {
  required_actions: string[];
  responsible_party: string;
  restitution?: string | null;
  escalation_path?: string | null;
  constitutional_trigger: boolean;
  deadline?: string | null;
}

export interface ClosurePayloadV2 {
  remediation_completed: boolean;
  restitution_delivered?: boolean;
  institutional_review_performed?: boolean;
  reviewing_body: string;
  constitutional_amendment_id?: string | null;
}

export interface DecisionReceiptV2 extends BaseReceiptV2 {
  lifecycle: LifecycleBlockV2 & { stage: 'decision' };
}

export interface ObservationReceiptV2 extends BaseReceiptV2 {
  lifecycle: LifecycleBlockV2 & { stage: 'observation' };
  observation: ObservationPayloadV2;
}

export interface RiskScopeV2 {
  runtime: string;
  invariant: string;
  tenant?: string;
}

export interface RiskFactorV2 {
  factor: string;
  weight: number;
  value: number;
}

export type PredictedFailureType =
  | 'remediation_failure'
  | 'amendment_required'
  | 'governance_breakdown';

export interface PredictedFailureV2 {
  type: PredictedFailureType;
  invariant: string;
  probability: number;
  horizon: string;
}

export type RecommendedActionType =
  | 'initiate_amendment_analysis'
  | 'escalate_remediation'
  | 'increase_observer_scrutiny'
  | 'acknowledge_or_dismiss';

export type ActionUrgency = 'low' | 'medium' | 'high' | 'critical';

export interface RecommendedActionV2 {
  type: RecommendedActionType;
  target: string;
  urgency: ActionUrgency;
}

export interface ConstitutionalRiskPayloadV2 {
  risk_score: number;
  scope: RiskScopeV2;
  risk_factors: RiskFactorV2[];
  predicted_failures: PredictedFailureV2[];
  recommended_actions: RecommendedActionV2[];
  horizon: string;
  lookback_days: number;
}

export interface RiskReceiptV2 extends ObservationReceiptV2 {
  action_type: 'constitutional_risk_forecast';
  runtime: 'ConstitutionalRiskRuntime';
  constitutional_risk: ConstitutionalRiskPayloadV2;
}

export interface ConstitutionalRiskState {
  state_id: string;
  state_type: 'constitutional_risk';
  scope: RiskScopeV2;
  snapshot_at: string;
  risk_score: number;
  risk_factors: RiskFactorV2[];
  predicted_failures: PredictedFailureV2[];
  recommended_actions: RecommendedActionV2[];
}

export interface DivergenceReceiptV2 extends BaseReceiptV2 {
  lifecycle: LifecycleBlockV2 & { stage: 'divergence' };
  divergence: DivergencePayloadV2;
}

export interface RemediationReceiptV2 extends BaseReceiptV2 {
  lifecycle: LifecycleBlockV2 & { stage: 'remediation' };
  remediation: RemediationPayloadV2;
}

export interface ClosureReceiptV2 extends BaseReceiptV2 {
  lifecycle: LifecycleBlockV2 & { stage: 'closure' };
  closure: ClosurePayloadV2;
}

// --- Article XV transition receipts -------------------------------------------

export interface TransitionPayloadV2 {
  from_state: string;
  to_state: string;
  legal_basis: string;
  receipt_ids_used: string[];
  state_id?: string;
  state_type?: string;
}

export interface TransitionReceiptV2 extends BaseReceiptV2 {
  action_type: 'state_transition';
  transition: TransitionPayloadV2;
}

// --- Article XVI amendment receipts -------------------------------------------

export type AmendmentChangeType = 'addition' | 'modification' | 'removal';

export type AmendmentStage =
  | 'proposed'
  | 'evaluated'
  | 'ratified'
  | 'implemented'
  | 'observed'
  | 'closed';

export interface AmendmentPayloadV2 {
  article: string;
  change_type: AmendmentChangeType;
  justification: string;
  trigger_receipt_id: string;
  amendment_stage: AmendmentStage;
  immutable_override?: boolean;
  unanimous_sovereign_ratification?: boolean;
}

export interface AmendmentReceiptV2 extends BaseReceiptV2 {
  action_type: 'constitutional_amendment';
  amendment: AmendmentPayloadV2;
}

export interface AmendmentProposalReceiptV2 extends AmendmentReceiptV2 {
  amendment: AmendmentPayloadV2 & { amendment_stage: 'proposed' };
}

export interface AmendmentEvaluationReceiptV2 extends AmendmentReceiptV2 {
  amendment: AmendmentPayloadV2 & { amendment_stage: 'evaluated' };
}

export interface AmendmentRatificationReceiptV2 extends AmendmentReceiptV2 {
  amendment: AmendmentPayloadV2 & { amendment_stage: 'ratified' };
}

export interface AmendmentImplementationReceiptV2 extends AmendmentReceiptV2 {
  amendment: AmendmentPayloadV2 & { amendment_stage: 'implemented' };
}

export interface AmendmentObservationReceiptV2 extends AmendmentReceiptV2 {
  amendment: AmendmentPayloadV2 & { amendment_stage: 'observed' };
}

export interface AmendmentClosureReceiptV2 extends AmendmentReceiptV2 {
  amendment: AmendmentPayloadV2 & { amendment_stage: 'closed' };
}

// --- Observer verification receipts -------------------------------------------

export interface ObserverVerificationPayloadV2 {
  state_reconstructed: boolean;
  state_replayed: boolean;
  divergence_detected: boolean;
  remediation_valid: boolean;
  amendments_valid: boolean;
  target_id?: string | null;
  notes?: string | null;
}

export interface ObserverAccountabilitySummaryV2 {
  responsible_parties: string[];
}

export interface ObserverVerificationReceiptV2 extends BaseReceiptV2 {
  runtime: 'observer';
  action_type: 'observer_verification';
  verification: ObserverVerificationPayloadV2;
  observer_accountability?: ObserverAccountabilitySummaryV2;
}

export interface ObserverDivergencePayloadV2 {
  divergence_points: string[];
  target_receipt_ids: string[];
  rationale: string;
}

export interface ObserverDivergenceReceiptV2 extends BaseReceiptV2 {
  runtime: 'observer';
  action_type: 'observer_divergence';
  observer_divergence: ObserverDivergencePayloadV2;
}

export interface ObserverRemediationRequestPayloadV2 {
  requested_actions: string[];
  responsible_party: string;
  trigger_receipt_id: string;
}

export interface ObserverRemediationRequestReceiptV2 extends BaseReceiptV2 {
  runtime: 'observer';
  action_type: 'observer_remediation_request';
  observer_remediation_request: ObserverRemediationRequestPayloadV2;
}

export interface ObserverClosurePayloadV2 {
  verification_receipt_id: string;
  closed: boolean;
  notes?: string | null;
}

export interface ObserverClosureReceiptV2 extends BaseReceiptV2 {
  runtime: 'observer';
  action_type: 'observer_closure';
  observer_closure: ObserverClosurePayloadV2;
}

// --- Transition rules --------------------------------------------------------

export const LIFECYCLE_TRANSITIONS: Record<LifecycleStage, LifecycleStage[]> = {
  decision: ['observation'],
  observation: ['divergence', 'closure'],
  divergence: ['remediation'],
  remediation: ['closure'],
  closure: [],
};

export const AMENDMENT_TRANSITIONS: Record<AmendmentStage, AmendmentStage[]> = {
  proposed: ['evaluated'],
  evaluated: ['ratified'],
  ratified: ['implemented'],
  implemented: ['observed'],
  observed: ['closed'],
  closed: [],
};

export const IMMUTABLE_CORE_ARTICLES = new Set(['XIII', 'XIV', 'XV', 'XVI', 'SEVEN_INVARIANTS']);

export function validateAmendmentTransition(fromStage: AmendmentStage, toStage: AmendmentStage): void {
  const allowed = AMENDMENT_TRANSITIONS[fromStage] ?? [];
  if (!allowed.includes(toStage)) {
    throw new Error(`Illegal amendment transition: ${fromStage} → ${toStage}`);
  }
}

export function validateImmutableAmendment(payload: AmendmentPayloadV2): void {
  const articleKey = payload.article.toUpperCase().replace('ARTICLE ', '').trim();
  if (!IMMUTABLE_CORE_ARTICLES.has(articleKey)) return;
  if (payload.change_type === 'addition') return;
  if (payload.immutable_override && payload.unanimous_sovereign_ratification) return;
  throw new Error(
    `Article ${payload.article} is immutable; modification/removal requires override and ratification`,
  );
}

export function isReceiptV2Complete(receipt: BaseReceiptV2): boolean {
  if (!receipt.receipt_id || !receipt.runtime || !receipt.timestamp) return false;
  if (!receipt.action_type) return false;
  if (!receipt.inputs.request_id || !receipt.inputs.payload_hash) return false;
  if (!receipt.outputs.status || !receipt.outputs.result_hash) return false;
  if (!receipt.invariant.name) return false;
  if (!receipt.evidence.bundle_id) return false;
  const suff = receipt.evidence.sufficiency;
  if (
    suff.continuity === undefined ||
    suff.truth === undefined ||
    suff.sovereignty === undefined ||
    suff.institutional === undefined
  ) {
    return false;
  }
  if (!receipt.authority.source || !receipt.authority.legitimacy_basis) return false;
  if (!receipt.reproducibility.mode) return false;
  if (!receipt.impact_boundary.scope_in.length || !receipt.impact_boundary.scope_out.length) {
    return false;
  }
  if (!receipt.accountability.primary_accountable_party) return false;
  if (!receipt.continuity.lineage_hash) return false;
  if (!receipt.signatures.runtime_signature) return false;
  return true;
}

export function validateLifecycleTransition(
  prior: BaseReceiptV2,
  next: BaseReceiptV2,
): { ok: boolean; reason: string } {
  const allowed = LIFECYCLE_TRANSITIONS[prior.lifecycle.stage] ?? [];
  if (!allowed.includes(next.lifecycle.stage)) {
    return {
      ok: false,
      reason: `invalid transition ${prior.lifecycle.stage} -> ${next.lifecycle.stage}`,
    };
  }
  if (next.lifecycle.previous_stage_receipt_id !== prior.receipt_id) {
    return { ok: false, reason: 'previous_stage_receipt_id must match prior receipt_id' };
  }
  if (prior.lifecycle.stage === 'closure') {
    return { ok: false, reason: 'closure is terminal' };
  }
  return { ok: true, reason: 'ok' };
}

export function closureOrDivergenceFromObservation(
  realityMatchesExpected: boolean,
): 'closure' | 'divergence' {
  return realityMatchesExpected ? 'closure' : 'divergence';
}
