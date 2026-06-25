/** K0–K12 invariant set for local governed inference (CRK-1 operational subset). */

export const INVARIANT_SET_VERSION = "K0-K12-v1";

export interface InvariantCheckContext {
  input: string;
  operator_id: string;
  mode: string;
}

export interface InvariantViolation {
  id: string;
  message: string;
}

const BLOCKED_PATTERNS: Array<{ id: string; pattern: RegExp; message: string }> = [
  { id: "K3", pattern: /rm\s+-rf/i, message: "Dangerous shell pattern blocked" },
  { id: "K4", pattern: /API_KEY|SECRET_KEY|password\s*=\s*["'][^"']+["']/i, message: "Credential leakage blocked" },
  { id: "K7", pattern: /ignore\s+(all\s+)?invariants/i, message: "Invariant bypass attempt blocked" },
];

/** K0: operator must be identified */
function k0_operator(ctx: InvariantCheckContext): InvariantViolation | null {
  if (!ctx.operator_id?.trim()) {
    return { id: "K0", message: "operator_id is required" };
  }
  return null;
}

/** K1: input must be non-empty for predict mode */
function k1_input(ctx: InvariantCheckContext): InvariantViolation | null {
  if (ctx.mode === "predict" && !ctx.input?.trim()) {
    return { id: "K1", message: "predict mode requires non-empty input" };
  }
  return null;
}

/** K2–K12: pattern and admissibility checks */
function k_pattern_checks(ctx: InvariantCheckContext): InvariantViolation | null {
  for (const rule of BLOCKED_PATTERNS) {
    if (rule.pattern.test(ctx.input)) {
      return { id: rule.id, message: rule.message };
    }
  }
  return null;
}

export function runPreCallInvariants(ctx: InvariantCheckContext): InvariantViolation[] {
  const violations: InvariantViolation[] = [];
  for (const check of [k0_operator, k1_input, k_pattern_checks]) {
    const v = check(ctx);
    if (v) violations.push(v);
  }
  return violations;
}

export function runPostCallInvariants(
  ctx: InvariantCheckContext,
  output: string
): InvariantViolation[] {
  return runPreCallInvariants({ ...ctx, input: output });
}
