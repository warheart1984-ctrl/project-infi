import { randomUUID, createHash } from "crypto";
import { runPreCallInvariants, runPostCallInvariants } from "../governance/invariants";
import { createReceipt } from "../governance/receipts";
import { appendLineage } from "../governance/lineage";
import { localPredict } from "../model/localClient";
import type {
  GovernedContext,
  GovernedResult,
  CE1Record,
  CRR1Record,
  CLG1Record,
} from "./types";

export type { GovernedContext, GovernedResult, GovernedMode } from "./types";

const DEFAULT_MODEL_PATH = "./models/local-llm";

function runCE1(input: string, output: string): CE1Record {
  return {
    id: randomUUID(),
    calibration_event: createHash("sha256").update(`ce1:${input}:${output}`).digest("hex"),
    timestamp: Date.now(),
  };
}

function runCRR1(input: string, output: string): CRR1Record {
  return {
    id: randomUUID(),
    reconstruction_hash: createHash("sha256").update(`crr1:${input}:${output}`).digest("hex"),
    timestamp: Date.now(),
  };
}

function runCLG1(lineageParent: string | null, callId: string): CLG1Record {
  return {
    id: randomUUID(),
    parent_id: lineageParent,
    append_hash: createHash("sha256").update(`clg1:${lineageParent}:${callId}`).digest("hex"),
    timestamp: Date.now(),
  };
}

/**
 * Single governed adapter for all local inference. Operator-facing code must use this.
 */
export async function governedPredict(
  input: string,
  context: GovernedContext
): Promise<GovernedResult> {
  const checkCtx = {
    input,
    operator_id: context.operator_id,
    mode: context.mode,
  };

  const preViolations = runPreCallInvariants(checkCtx);
  if (preViolations.length > 0) {
    const receipt = createReceipt({
      operator_id: context.operator_id,
      invariant_set_version: context.invariant_set_version,
      mode: context.mode,
      invariants_passed: false,
      violation_ids: preViolations.map((v) => v.id),
    });
    const lineage = appendLineage({
      operator_id: context.operator_id,
      call_id: receipt.call_id,
      payload: JSON.stringify({ refused: true, violations: preViolations }),
    });
    throw new GovernedRefusalError(preViolations.map((v) => v.message).join("; "), {
      output: "",
      receipt,
      lineage,
      ce1: runCE1(input, ""),
      crr1: runCRR1(input, ""),
      clg1: runCLG1(lineage.parent_id, receipt.call_id),
    });
  }

  const modelPath = context.model_path ?? DEFAULT_MODEL_PATH;
  const output = await localPredict(input, { model_path: modelPath });

  const postViolations = runPostCallInvariants(checkCtx, output);
  const invariantsPassed = postViolations.length === 0;

  const receipt = createReceipt({
    operator_id: context.operator_id,
    invariant_set_version: context.invariant_set_version,
    mode: context.mode,
    invariants_passed: invariantsPassed,
    violation_ids: postViolations.map((v) => v.id),
  });

  const lineage = appendLineage({
    operator_id: context.operator_id,
    call_id: receipt.call_id,
    payload: JSON.stringify({ input, output }),
  });

  const ce1 = runCE1(input, output);
  const crr1 = runCRR1(input, output);
  const clg1 = runCLG1(lineage.parent_id, receipt.call_id);

  if (!invariantsPassed) {
    throw new GovernedRefusalError(postViolations.map((v) => v.message).join("; "), {
      output,
      receipt,
      lineage,
      ce1,
      crr1,
      clg1,
    });
  }

  return { output, receipt, lineage, ce1, crr1, clg1 };
}

export class GovernedRefusalError extends Error {
  readonly result: GovernedResult;

  constructor(message: string, result: GovernedResult) {
    super(message);
    this.name = "GovernedRefusalError";
    this.result = result;
  }
}
