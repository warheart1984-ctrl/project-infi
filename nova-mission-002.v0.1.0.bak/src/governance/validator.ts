import type { AgentAction } from "../types/actions";
import type { ValidationResult } from "../types/actions";
import type { InvariantState } from "../types/invariants";
import { getInvariants } from "./invariants";
import { emitViolation } from "../events/lifecycle";
import { violationId } from "./kernelStatus";

function buildState(action: AgentAction): InvariantState {
  const payload = action.payload;
  return {
    action,
    diff: typeof payload.diff === "string" ? payload.diff : undefined,
    code: typeof payload.code === "string" ? payload.code : undefined,
    prompt: typeof payload.prompt === "string" ? payload.prompt : undefined,
  };
}

export async function validateAction(action: AgentAction): Promise<ValidationResult> {
  const state = buildState(action);
  const checked: string[] = [];

  for (const inv of getInvariants()) {
    checked.push(inv.id);
    const ok = await inv.check(state);
    if (!ok) {
      const violation = {
        id: violationId(),
        invariantId: inv.id,
        description: inv.description,
        message: inv.description,
        severity: inv.severity,
        action,
      };
      if (inv.severity === "error") {
        emitViolation(violation);
        return {
          ok: false,
          reason: `Invariant violated: ${inv.id} — ${inv.description}`,
          violation,
        };
      }
      emitViolation(violation);
    }
  }

  return { ok: true };
}

export async function trace(): Promise<import("../types/receipts").GovernanceTrace> {
  const { getLedger, getLedgerTailHash } = await import("./ledger");
  return {
    receipts: [...getLedger()],
    ledgerHash: getLedgerTailHash(),
  };
}
