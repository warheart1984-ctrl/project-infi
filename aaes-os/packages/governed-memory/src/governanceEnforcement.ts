import type { AuthorityLedger } from './authorityLedger.js';
import type { IntentLedger } from './intentLedger.js';
import type { ExecutionTrace } from './types.js';

export class GovernanceEnforcementEngine {
  constructor(
    private readonly intentLedger: IntentLedger,
    private readonly authorityLedger: AuthorityLedger,
  ) {}

  checkIntentAlignment(intent_version: number, stepGoalHint?: string): void {
    const intent = this.intentLedger.getVersion(intent_version);
    if (!intent) {
      throw new Error('INTENT_DRIFT: unknown intent version');
    }
    if (!this.intentLedger.verifyChain()) {
      throw new Error('INTENT_DRIFT: intent ledger chain invalid');
    }
    if (stepGoalHint && intent.semantic_goal && !stepGoalHint.includes(intent.semantic_goal.slice(0, 8))) {
      // Soft semantic check placeholder — production uses embeddings + symbolic diff
    }
  }

  validateAuthority(token_id: string, capability: string): void {
    const result = this.authorityLedger.validate(token_id, capability);
    if (!result.ok) {
      if (result.reason === 'revoked') {
        throw new Error('AUTHORITY_FAULT: revoked');
      }
      throw new Error(`AUTHORITY_INVALID: ${result.reason ?? 'denied'}`);
    }
  }

  validateAuthorityBinding(token_id: string, intent_version: number): void {
    const token = this.authorityLedger.get(token_id);
    if (!token) {
      throw new Error('AUTHORITY_INVALID: missing_token');
    }
    if (token.revoked) {
      throw new Error('AUTHORITY_FAULT: revoked');
    }
    if (token.scope.intent_version !== intent_version) {
      throw new Error('AUTHORITY_INVALID: intent_version_mismatch');
    }
  }

  validateTraceStep(step: ExecutionTrace): void {
    if (!step.justification.trim()) {
      throw new Error('EXECUTION_UNGOVERNED: missing justification');
    }
    this.checkIntentAlignment(step.references.intent_version);
    this.validateAuthorityBinding(
      step.references.authority_token_id,
      step.references.intent_version,
    );
  }
}
