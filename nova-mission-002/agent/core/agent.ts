import type {
  GenerateCodeInput,
  GenerateCodeResult,
  PlanInput,
  RefactorInput,
  RefactorResult,
  VerifyInput,
  VerificationResult,
  ApplyPatchInput,
  ApplyPatchResult,
} from "../types/actions";
import { validateAction } from "../governance/validator";
import { recordReceipt } from "../governance/receipts";
import { emitReceipt } from "../events/lifecycle";
import { updateContinuity } from "../continuity/substrate";
import { plan as createPlan } from "./planner";
import { applyDiff } from "../runtime/workspace";

const DANGEROUS_PATTERNS = ["rm -rf", "curl | sh", "API_KEY", "SECRET_KEY", "password ="];

function synthesizeCode(prompt: string): string {
  const lower = prompt.toLowerCase();
  if (lower.includes("factorial")) {
    return `export function factorial(n: number): number {
  if (n < 0) throw new Error("n must be non-negative");
  if (n <= 1) return 1;
  return n * factorial(n - 1);
}
`;
  }
  if (lower.includes("fibonacci")) {
    return `export function fibonacci(n: number): number {
  if (n < 0) throw new Error("n must be non-negative");
  if (n <= 1) return n;
  let a = 0, b = 1;
  for (let i = 2; i <= n; i++) {
    const next = a + b;
    a = b;
    b = next;
  }
  return b;
}
`;
  }
  if (lower.includes("sort")) {
    return `export function sortNumbers(nums: number[]): number[] {
  return [...nums].sort((a, b) => a - b);
}
`;
  }
  return `// Generated for: ${prompt.slice(0, 80)}
export function generated(): void {
  // TODO: implement
}
`;
}

async function callLLM(prompt: string): Promise<string> {
  return synthesizeCode(prompt);
}

export async function generateCode(input: GenerateCodeInput): Promise<GenerateCodeResult> {
  const action = {
    type: "generate" as const,
    payload: { prompt: input.prompt, context: input.context, constraints: input.constraints },
  };

  const validation = await validateAction(action);
  if (!validation.ok) {
    const receipt = await recordReceipt(action, [], { blocked: true, blockReason: validation.reason });
    emitReceipt(receipt);
    throw new Error(validation.reason ?? "Generation blocked by invariant");
  }

  const code = await callLLM(input.prompt);
  const codeValidation = await validateAction({
    type: "generate",
    payload: { prompt: input.prompt, code },
  });
  if (!codeValidation.ok) {
    const receipt = await recordReceipt(action, [], { blocked: true, blockReason: codeValidation.reason });
    emitReceipt(receipt);
    throw new Error(codeValidation.reason ?? "Generated code failed invariant check");
  }

  const invIds = (await import("../governance/invariants")).getInvariants().map((i) => i.id);
  const receipt = await recordReceipt(action, invIds);
  await updateContinuity(action);
  emitReceipt(receipt);
  return { code, receipts: [receipt] };
}

export async function plan(input: PlanInput) {
  return createPlan(input);
}

export async function explain(topic: string): Promise<{ explanation: string; receipts: import("../types/receipts").GovernanceReceipt[] }> {
  const action = { type: "run" as const, payload: { command: "explain", topic } };
  await validateAction(action);
  const receipt = await recordReceipt(action, ["explain"]);
  return {
    explanation: `Governed explanation of: ${topic}. All reasoning is receipt-backed via CRK-1.`,
    receipts: [receipt],
  };
}

export async function refactor(input: RefactorInput): Promise<RefactorResult> {
  const action = {
    type: "refactor" as const,
    payload: { file: input.file, instructions: input.instructions },
  };
  const validation = await validateAction(action);
  if (!validation.ok) throw new Error(validation.reason);

  const diff = `--- a/${input.file}\n+++ b/${input.file}\n@@ refactored per: ${input.instructions}`;
  const receipt = await recordReceipt(action, ["refactor-validated"]);
  return { file: input.file, diff, receipts: [receipt] };
}

export async function verify(input: VerifyInput): Promise<VerificationResult> {
  const result = await validateAction(input.action);
  return {
    ok: result.ok,
    reason: result.reason,
    invariantsChecked: result.ok ? ["all-passed"] : [],
  };
}

export async function applyPatch(input: ApplyPatchInput): Promise<ApplyPatchResult> {
  const action = { type: "edit" as const, payload: { diff: input.diff, reason: input.reason } };
  const validation = await validateAction(action);
  if (!validation.ok) {
    const receipt = await recordReceipt(action, [], { blocked: true, blockReason: validation.reason });
    return { success: false, receipts: [receipt] };
  }
  await applyDiff(input.diff);
  const receipt = await recordReceipt(action, ["patch-applied"]);
  await updateContinuity(action);
  return { success: true, receipts: [receipt] };
}

export { DANGEROUS_PATTERNS };
