/**
 * Deterministic governance replay — re-validates invariants only (no LLM/tool re-execution).
 */

import type { ReplayResult } from './types.js';
import { ExecutionSpanManager } from './executionMemory.js';
import { GovernanceEnforcementEngine } from './governanceEnforcement.js';
import { IntentLedger } from './intentLedger.js';
import { AuthorityLedger } from './authorityLedger.js';

const DRIFT_THRESHOLD = 0.35;

export function replay(
  spanId: string,
  options?: {
    spanManager?: ExecutionSpanManager;
    intentLedger?: IntentLedger;
    authorityLedger?: AuthorityLedger;
    governance?: GovernanceEnforcementEngine;
  },
): ReplayResult {
  const spanManager = options?.spanManager ?? new ExecutionSpanManager();
  const intentLedger = options?.intentLedger ?? new IntentLedger();
  const authorityLedger = options?.authorityLedger ?? new AuthorityLedger();
  const governance = options?.governance ?? new GovernanceEnforcementEngine(intentLedger, authorityLedger);

  const span = spanManager.get(spanId);
  if (!span) {
    return {
      success: false,
      violations: [{ code: 'EXECUTION_FAULT', message: `span not found: ${spanId}` }],
    };
  }

  for (const [index, trace] of span.trace.entries()) {
    try {
      governance.validateTraceStep(trace);
    } catch (error) {
      return {
        success: false,
        violations: [{
          code: 'EXECUTION_UNGOVERNED',
          message: error instanceof Error ? error.message : String(error),
          step_index: index,
        }],
        step_index: index,
      };
    }

    if (trace.content.length === 0 || trace.justification.length === 0) {
      return {
        success: false,
        violations: [
          {
            code: 'INTENT_DRIFT',
            message: `semantic drift at step ${index}`,
            step_index: index,
          },
        ],
        step_index: index,
      };
    }
  }

  return { success: true, violations: [] };
}
