/**
 * Operator-facing façades (verbs) over Tri-Strata ledgers.
 */

import type {
  AuthorityEnvelope,
  ExecutionSpan,
  ExecutionTrace,
  IntentRecord,
  ReasoningStep,
  ReplayResult,
} from './types.js';
import { IntentLedger } from './intentLedger.js';
import { AuthorityLedger } from './authorityLedger.js';
import { ExecutionSpanManager } from './executionMemory.js';
import { GovernanceEnforcementEngine } from './governanceEnforcement.js';
import { replay as replaySpan } from './replay.js';

export interface GovernedMemoryDefaults {
  intentLedger?: IntentLedger;
  authorityLedger?: AuthorityLedger;
  spanManager?: ExecutionSpanManager;
  governance?: GovernanceEnforcementEngine;
}

function resolveDefaults(d?: GovernedMemoryDefaults) {
  const intentLedger = d?.intentLedger ?? new IntentLedger();
  const authorityLedger = d?.authorityLedger ?? new AuthorityLedger();
  const spanManager = d?.spanManager ?? new ExecutionSpanManager();
  const governance =
    d?.governance ?? new GovernanceEnforcementEngine(intentLedger, authorityLedger);
  return { intentLedger, authorityLedger, spanManager, governance };
}

export function createIntent(
  goal: string,
  constraints: string[],
  operatorKey: string,
  defaults?: GovernedMemoryDefaults,
): IntentRecord {
  const { intentLedger } = resolveDefaults(defaults);
  return intentLedger.append({
    operator_id: operatorKey,
    semantic_goal: goal,
    constraints,
    success_criteria: [],
    horizon: 'short',
    signature: operatorKey,
  });
}

export function issueAuthority(
  intentVersion: number,
  capabilities: string[],
  governanceKey: string,
  defaults?: GovernedMemoryDefaults,
): AuthorityEnvelope {
  const { authorityLedger } = resolveDefaults(defaults);
  const token = authorityLedger.issue({
    issued_by: governanceKey,
    issued_to: 'operator',
    capabilities,
    scope: {
      resources: ['*'],
      time_limit_ms: Date.now() + 60_000,
      intent_version: intentVersion,
    },
    delegation_chain: [governanceKey],
  });
  return {
    token,
    nonce: `${token.token_id}:nonce`,
    envelope_signature: token.signature,
  };
}

export function startSpan(
  intentVersion: number,
  authorityTokenId: string,
  defaults?: GovernedMemoryDefaults,
): ExecutionSpan {
  const { spanManager } = resolveDefaults(defaults);
  return spanManager.startSpan({
    intent_version: intentVersion,
    authority_token_id: authorityTokenId,
  });
}

export function validateStep(
  step: ReasoningStep,
  intentVersion: number,
  authorityTokenId: string,
  defaults?: GovernedMemoryDefaults,
): ReturnType<GovernanceEnforcementEngine['validateTraceStep']> {
  const { governance } = resolveDefaults(defaults);
  return governance.validateTraceStep(toExecutionTrace(step, intentVersion, authorityTokenId));
}

export function completeSpan(
  spanId: string,
  defaults?: GovernedMemoryDefaults,
): ExecutionSpan {
  const { spanManager } = resolveDefaults(defaults);
  return spanManager.complete(spanId);
}

export function recordTrace(
  spanId: string,
  step: ReasoningStep,
  intentVersion: number,
  authorityTokenId: string,
  defaults?: GovernedMemoryDefaults,
): ExecutionTrace {
  const resolved = resolveDefaults(defaults);
  const trace = toExecutionTrace(step, intentVersion, authorityTokenId);
  resolved.governance.validateTraceStep(trace);
  const updated = resolved.spanManager.recordTrace(spanId, trace);
  return updated.trace.at(-1)!;
}

export function replay(spanId: string, defaults?: GovernedMemoryDefaults): ReplayResult {
  const resolved = resolveDefaults(defaults);
  return replaySpan(spanId, {
    spanManager: resolved.spanManager,
    intentLedger: resolved.intentLedger,
    authorityLedger: resolved.authorityLedger,
    governance: resolved.governance,
  });
}

function toExecutionTrace(
  step: ReasoningStep,
  intentVersion: number,
  authorityTokenId: string,
): ExecutionTrace {
  return {
    timestamp: Date.now(),
    step_type: step.step_type ?? 'reasoning',
    content: step.content,
    justification: step.justification,
    references: {
      intent_version: intentVersion,
      authority_token_id: authorityTokenId,
    },
  };
}
