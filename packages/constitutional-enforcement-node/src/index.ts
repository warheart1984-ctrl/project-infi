import { createHash } from 'node:crypto';

export type TransitionType = 'state_update' | 'law_mutation' | 'runtime_action' | 'evidence_commit';
export type EnforcementVerdict = 'ALLOW' | 'DENY';
export type EnforcementAction = 'ALLOW' | 'DENY' | 'FREEZE' | 'MANDATORY_REVIEW';
export type EnforcementReasonCode =
  | 'ALLOWED'
  | 'CAPABILITY_DENIED'
  | 'INVARIANT_VIOLATION'
  | 'INVALID_TRANSITION'
  | 'MALFORMED_TRANSITION'
  | 'REPLAY_DETECTED'
  | 'TOKEN_INVALID_SIGNATURE'
  | 'TOKEN_EXPIRED'
  | 'TOKEN_SCOPE_DENIED'
  | 'TOKEN_REPLAYED'
  | 'TOKEN_TRANSITION_MISMATCH';
export type EnforcementReceiptCategory = 'allow' | 'deny' | 'anomaly' | 'replay' | 'token_refusal';
export type ConstitutionalDimension =
  | 'continuity'
  | 'governance'
  | 'memory'
  | 'coordination'
  | 'confidence';
export type MRIStateSnapshot = Record<ConstitutionalDimension, number>;
export type AuthorityTokenType = 'VT' | 'FT' | 'MRT' | 'RT';

export interface ConstitutionalRuntimeContext {
  corridorId: string;
  capabilities: string[];
}

export interface EnforcementContext {
  actor: string;
  mriSnapshot: MRIStateSnapshot;
  runtimeContext: ConstitutionalRuntimeContext;
}

export interface AuthorityTokenInput {
  tokenId: string;
  tokenType: AuthorityTokenType;
  scope: string[];
  transitionId: string;
  expiresAt: string;
  issuedAt?: string;
}

export interface AuthorityToken extends AuthorityTokenInput {
  issuedAt: string;
  signature: string;
}

export interface ProposedTransition {
  transitionId: string;
  transitionType: TransitionType;
  payload: unknown;
  requestedCapabilities: string[];
  context: EnforcementContext;
  authorityToken?: AuthorityToken;
}

export interface InvariantEvaluation {
  invariantId: string;
  passed: boolean;
  message: string;
  action?: EnforcementAction;
}

export interface ConstitutionalInvariant {
  invariantId: string;
  evaluate: (transition: ProposedTransition) => InvariantEvaluation;
}

export interface EnforcementDecision {
  verdict: EnforcementVerdict;
  action: EnforcementAction;
  reasonCode: EnforcementReasonCode;
  reasonDetail: string;
}

export interface EnforcementReceipt {
  receiptId: string;
  transitionId: string;
  transitionType: TransitionType;
  actor: string;
  verdict: EnforcementVerdict;
  action: EnforcementAction;
  reasonCode: EnforcementReasonCode;
  reasonDetail: string;
  category: EnforcementReceiptCategory;
  stage: 'receipt';
  evaluations: InvariantEvaluation[];
  mriSnapshotHash: string;
  payloadHash: string;
  authorityTokenId?: string;
  previousReceiptHash: string | null;
  receiptHash: string;
  issuedAt: string;
}

export interface EnforcementResult {
  decision: EnforcementDecision;
  committed: boolean;
  receipt: EnforcementReceipt;
}

export interface InterceptedTransition {
  stage: 'intercept';
  transition: ProposedTransition;
}

export interface EvaluatedTransition {
  stage: 'evaluate';
  transition: ProposedTransition;
  evaluations: InvariantEvaluation[];
  decision: EnforcementDecision;
}

export interface ConstitutionalEnforcementNodeOptions {
  invariants: ConstitutionalInvariant[];
  issuedAt?: () => string;
}

const AUTHORITY_TOKEN_DOMAIN = 'AAES-CEN-AUTHORITY-TOKEN-v1';

export class ConstitutionalEnforcementNode {
  private readonly invariants: ConstitutionalInvariant[];
  private readonly issuedAt: () => string;
  private readonly stateStore = new Map<string, unknown>();
  private readonly ledger: EnforcementReceipt[] = [];
  private readonly seenTransitions = new Set<string>();
  private readonly usedAuthorityTokens = new Set<string>();

  constructor(options: ConstitutionalEnforcementNodeOptions) {
    this.invariants = [...options.invariants];
    this.issuedAt = options.issuedAt ?? (() => new Date().toISOString());
  }

  intercept(transition: ProposedTransition): InterceptedTransition {
    return { stage: 'intercept', transition };
  }

  evaluate(intercepted: InterceptedTransition): EvaluatedTransition {
    const transition = intercepted.transition;
    const malformed = validateTransitionShape(transition);
    if (malformed) {
      return this.evaluated(transition, [], this.decision('DENY', 'DENY', 'MALFORMED_TRANSITION', malformed));
    }
    if (this.seenTransitions.has(transition.transitionId)) {
      return this.evaluated(transition, [], this.decision('DENY', 'DENY', 'REPLAY_DETECTED', 'transition replay detected'));
    }

    const capabilityDenied = transition.requestedCapabilities.find(
      (capability) => !transition.context.runtimeContext.capabilities.includes(capability),
    );
    if (capabilityDenied) {
      return this.evaluated(
        transition,
        [],
        this.decision('DENY', 'DENY', 'CAPABILITY_DENIED', `capability denied: ${capabilityDenied}`),
      );
    }

    const tokenDecision = this.validateAuthorityToken(transition);
    if (tokenDecision) {
      return this.evaluated(transition, [], tokenDecision);
    }

    const evaluations = this.invariants.map((invariant) => invariant.evaluate(transition));
    const failed = evaluations.find((evaluation) => !evaluation.passed);
    if (failed) {
      return this.evaluated(
        transition,
        evaluations,
        this.decision('DENY', failed.action ?? 'DENY', 'INVARIANT_VIOLATION', failed.message),
      );
    }

    return this.evaluated(transition, evaluations, this.decision('ALLOW', 'ALLOW', 'ALLOWED', 'transition admitted by CEN'));
  }

  allow(evaluated: EvaluatedTransition): EnforcementResult {
    return this.finish(evaluated, true);
  }

  deny(evaluated: EvaluatedTransition): EnforcementResult {
    return this.finish(evaluated, false);
  }

  receipt(evaluated: EvaluatedTransition): EnforcementReceipt {
    return this.createReceipt(evaluated.transition, evaluated.decision, evaluated.evaluations);
  }

  execute(transition: ProposedTransition): EnforcementResult {
    const evaluated = this.evaluate(this.intercept(transition));
    return evaluated.decision.verdict === 'ALLOW' ? this.allow(evaluated) : this.deny(evaluated);
  }

  getState(transitionId: string): unknown {
    return this.stateStore.get(transitionId);
  }

  receipts(): EnforcementReceipt[] {
    return [...this.ledger];
  }

  private finish(evaluated: EvaluatedTransition, requestedCommit: boolean): EnforcementResult {
    const committed = requestedCommit && evaluated.decision.verdict === 'ALLOW';
    if (committed) {
      this.stateStore.set(evaluated.transition.transitionId, evaluated.transition.payload);
    }
    if (evaluated.transition.transitionId.trim()) {
      this.seenTransitions.add(evaluated.transition.transitionId);
    }
    if (evaluated.transition.authorityToken && evaluated.decision.reasonCode !== 'TOKEN_REPLAYED') {
      this.usedAuthorityTokens.add(evaluated.transition.authorityToken.tokenId);
    }
    const receipt = this.receipt(evaluated);
    this.ledger.push(receipt);
    return { decision: evaluated.decision, committed, receipt };
  }

  private validateAuthorityToken(transition: ProposedTransition): EnforcementDecision | undefined {
    const token = transition.authorityToken;
    if (!token) return undefined;
    if (this.usedAuthorityTokens.has(token.tokenId)) {
      return this.decision('DENY', 'DENY', 'TOKEN_REPLAYED', 'authority token replayed');
    }
    if (token.signature !== authorityTokenSignature(token)) {
      return this.decision('DENY', 'DENY', 'TOKEN_INVALID_SIGNATURE', 'authority token signature invalid');
    }
    if (Date.parse(token.expiresAt) <= Date.now()) {
      return this.decision('DENY', 'DENY', 'TOKEN_EXPIRED', 'authority token expired');
    }
    if (token.transitionId !== transition.transitionId) {
      return this.decision('DENY', 'DENY', 'TOKEN_TRANSITION_MISMATCH', 'authority token transition mismatch');
    }
    const missingScope = transition.requestedCapabilities.find((capability) => !token.scope.includes(capability));
    if (missingScope) {
      return this.decision('DENY', 'DENY', 'TOKEN_SCOPE_DENIED', `authority token missing scope: ${missingScope}`);
    }
    return undefined;
  }

  private createReceipt(
    transition: ProposedTransition,
    decision: EnforcementDecision,
    evaluations: InvariantEvaluation[],
  ): EnforcementReceipt {
    const previousReceiptHash = this.ledger.at(-1)?.receiptHash ?? null;
    const issuedAt = this.issuedAt();
    const base = {
      transitionId: transition.transitionId,
      transitionType: transition.transitionType,
      actor: transition.context?.actor ?? 'unknown',
      verdict: decision.verdict,
      action: decision.action,
      reasonCode: decision.reasonCode,
      reasonDetail: decision.reasonDetail,
      category: categoryForDecision(decision),
      stage: 'receipt' as const,
      evaluations,
      mriSnapshotHash: hashJson(transition.context?.mriSnapshot ?? {}),
      payloadHash: hashJson(transition.payload),
      authorityTokenId: transition.authorityToken?.tokenId,
      previousReceiptHash,
      issuedAt,
    };
    const receiptHash = hashReceiptBase(base);
    return {
      receiptId: `cen:${receiptHash.slice('sha3-256:'.length)}`,
      ...base,
      receiptHash,
    };
  }

  private evaluated(
    transition: ProposedTransition,
    evaluations: InvariantEvaluation[],
    decision: EnforcementDecision,
  ): EvaluatedTransition {
    return { stage: 'evaluate', transition, evaluations, decision };
  }

  private decision(
    verdict: EnforcementVerdict,
    action: EnforcementAction,
    reasonCode: EnforcementReasonCode,
    reasonDetail: string,
  ): EnforcementDecision {
    return { verdict, action, reasonCode, reasonDetail };
  }
}

export function createResourceFloorInvariant(
  dimension: ConstitutionalDimension,
  floor: number,
): ConstitutionalInvariant {
  return {
    invariantId: `resource-floor:${dimension}:min:${floor}`,
    evaluate(transition) {
      const proposed = readProposedScore(transition, dimension);
      const passed = proposed >= floor;
      return {
        invariantId: `resource-floor:${dimension}:min:${floor}`,
        passed,
        message: passed
          ? `${dimension} satisfies floor ${floor}`
          : `${dimension} ${proposed} fell below constitutional floor ${floor}`,
        action: passed ? 'ALLOW' : 'DENY',
      };
    },
  };
}

export function compileInvariantDsl(source: string): ConstitutionalInvariant {
  const match = /^require\s+(continuity|governance|memory|coordination|confidence)\s*>=\s*(\d+(?:\.\d+)?)$/i.exec(
    source.trim(),
  );
  if (!match) {
    throw new Error(`unsupported invariant DSL: ${source}`);
  }
  const dimension = match[1] as ConstitutionalDimension;
  const floor = Number(match[2]);
  return {
    ...createResourceFloorInvariant(dimension, floor),
    invariantId: `idsl:${dimension}:min:${floor}`,
    evaluate(transition) {
      const proposed = readProposedScore(transition, dimension);
      const passed = proposed >= floor;
      return {
        invariantId: `idsl:${dimension}:min:${floor}`,
        passed,
        message: passed
          ? `${dimension} satisfies DSL floor ${floor}`
          : `${dimension} ${proposed} violated DSL floor ${floor}`,
        action: passed ? 'ALLOW' : 'DENY',
      };
    },
  };
}

export function issueAuthorityToken(input: AuthorityTokenInput): AuthorityToken {
  const token: AuthorityToken = {
    ...input,
    issuedAt: input.issuedAt ?? new Date().toISOString(),
    signature: '',
  };
  return { ...token, signature: authorityTokenSignature(token) };
}

export function verifyEnforcementReceipt(receipt: EnforcementReceipt): boolean {
  return receipt.receiptHash === hashReceiptBase(receiptBaseFromReceipt(receipt));
}

export function createCenDemoResult(): EnforcementResult {
  const node = new ConstitutionalEnforcementNode({
    invariants: [compileInvariantDsl('require governance >= 70')],
    issuedAt: () => '2026-06-18T22:02:00.000Z',
  });
  return node.execute({
    transitionId: 'transition:cen-demo',
    transitionType: 'law_mutation',
    payload: { law: 'soft invariant proposed' },
    requestedCapabilities: ['law:propose'],
    context: {
      actor: 'operator',
      mriSnapshot: {
        continuity: 72,
        governance: 68,
        memory: 75,
        coordination: 63,
        confidence: 81,
      },
      runtimeContext: {
        corridorId: 'law-evolution',
        capabilities: ['law:propose'],
      },
    },
  });
}

function validateTransitionShape(transition: ProposedTransition): string | undefined {
  if (!transition || typeof transition !== 'object') return 'transition object is required';
  if (!transition.transitionId?.trim()) return 'transitionId is required';
  if (!transition.transitionType) return 'transitionType is required';
  if (!Array.isArray(transition.requestedCapabilities)) return 'requestedCapabilities must be an array';
  if (!transition.context?.runtimeContext || !Array.isArray(transition.context.runtimeContext.capabilities)) {
    return 'runtimeContext capabilities are required';
  }
  if (transition.payload === null || typeof transition.payload === 'undefined') return 'payload is required';
  return undefined;
}

function readProposedScore(
  transition: ProposedTransition,
  dimension: ConstitutionalDimension,
): number {
  if (isRecord(transition.payload) && typeof transition.payload[dimension] === 'number') {
    return transition.payload[dimension];
  }
  return transition.context.mriSnapshot[dimension];
}

function categoryForDecision(decision: EnforcementDecision): EnforcementReceiptCategory {
  if (decision.verdict === 'ALLOW') return 'allow';
  if (decision.reasonCode === 'REPLAY_DETECTED') return 'replay';
  if (decision.reasonCode.startsWith('TOKEN_')) return 'token_refusal';
  if (decision.reasonCode === 'MALFORMED_TRANSITION' || decision.reasonCode === 'INVALID_TRANSITION') return 'anomaly';
  return 'deny';
}

function authorityTokenSignature(token: Omit<AuthorityToken, 'signature'>): string {
  return createHash('sha3-256')
    .update(
      [
        AUTHORITY_TOKEN_DOMAIN,
        token.tokenId,
        token.tokenType,
        token.scope.join(','),
        token.transitionId,
        token.issuedAt,
        token.expiresAt,
      ].join('|'),
      'utf8',
    )
    .digest('hex');
}

function receiptBaseFromReceipt(receipt: EnforcementReceipt): Omit<EnforcementReceipt, 'receiptId' | 'receiptHash'> {
  const { receiptId: _receiptId, receiptHash: _receiptHash, ...base } = receipt;
  return base;
}

function hashReceiptBase(base: unknown): string {
  return hashJson(base);
}

function hashJson(value: unknown): string {
  return `sha3-256:${createHash('sha3-256').update(stableStringify(value), 'utf8').digest('hex')}`;
}

function stableStringify(value: unknown): string {
  if (Array.isArray(value)) {
    return `[${value.map((entry) => stableStringify(entry)).join(',')}]`;
  }
  if (isRecord(value)) {
    return `{${Object.keys(value)
      .filter((key) => typeof value[key] !== 'undefined')
      .sort()
      .map((key) => `${JSON.stringify(key)}:${stableStringify(value[key])}`)
      .join(',')}}`;
  }
  return JSON.stringify(value);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}
