import type { AgentAction, ValidationResult } from "../types/actions";
import type { GovernanceReceipt } from "../types/receipts";
import { validateAction } from "../governance/validator";
import { recordReceipt } from "../governance/receipts";
import { appendToLedger, getLedger, getLedgerTailHash } from "../governance/ledger";
import * as agent from "../core/agent";

/**
 * Constitutional agent runtime — single entry point for governed agent actions.
 * Every action flows through validate → execute → receipt → ledger.append.
 */
export class AgentRuntime {
  /** Validate an action against registered invariants before execution. */
  async validate(action: AgentAction): Promise<ValidationResult> {
    return validateAction(action);
  }

  /** Record a governance receipt and append it to the hash-chained ledger. */
  async receipt(
    action: AgentAction,
    invariantsChecked: string[],
    options?: { blocked?: boolean; blockReason?: string }
  ): Promise<GovernanceReceipt> {
    return recordReceipt(action, invariantsChecked, options);
  }

  /** Hash-chained governance ledger surface. */
  readonly ledger = {
    append: appendToLedger,
    list: getLedger,
    tailHash: getLedgerTailHash,
  };

  generateCode = agent.generateCode;
  plan = agent.plan;
  explain = agent.explain;
  refactor = agent.refactor;
  verify = agent.verify;
  applyPatch = agent.applyPatch;
}
