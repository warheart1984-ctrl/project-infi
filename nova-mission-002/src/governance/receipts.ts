import { randomUUID } from "crypto";
import type { GovernedMode } from "../runtime/types";

export interface GovernedReceipt {
  call_id: string;
  operator_id: string;
  timestamp: number;
  invariant_set_version: string;
  mode: GovernedMode;
  invariants_passed: boolean;
  violation_ids?: string[];
}

export function createReceipt(params: {
  operator_id: string;
  invariant_set_version: string;
  mode: GovernedMode;
  invariants_passed: boolean;
  violation_ids?: string[];
}): GovernedReceipt {
  return {
    call_id: randomUUID(),
    operator_id: params.operator_id,
    timestamp: Date.now(),
    invariant_set_version: params.invariant_set_version,
    mode: params.mode,
    invariants_passed: params.invariants_passed,
    violation_ids: params.violation_ids,
  };
}
