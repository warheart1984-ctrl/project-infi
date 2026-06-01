import type { InvocationGate } from "@shared/sigil";

export interface InvocationInput {
  utterance?: string;
  trace?: string;
  seal?: string;
  echo?: string;
}

export interface InvocationGateResult {
  allowed: boolean;
  reason?: string;
}

const DEFAULT_REJECTION = "Invocation gate active. Provide a valid trace and seal pair.";

function normalize(value: string | undefined): string {
  return (value || "").trim();
}

function traceMatches(trace: string, utterance: string, patterns: string[]): boolean {
  if (patterns.length === 0) return true;

  for (const rawPattern of patterns) {
    const pattern = normalize(rawPattern);
    if (!pattern) continue;

    try {
      const regex = new RegExp(pattern, "i");
      if (regex.test(trace) || regex.test(utterance)) {
        return true;
      }
    } catch {
      if (
        trace.toLowerCase().startsWith(pattern.toLowerCase()) ||
        utterance.toLowerCase().startsWith(pattern.toLowerCase())
      ) {
        return true;
      }
    }
  }

  return false;
}

export function evaluateInvocationGate(
  config: InvocationGate | undefined,
  invocation: InvocationInput,
): InvocationGateResult {
  if (!config?.enabled) {
    return { allowed: true };
  }

  const utterance = normalize(invocation.utterance);
  const trace = normalize(invocation.trace);
  const seal = normalize(invocation.seal);

  // Allow continuation invocations with no explicit utterance.
  if (!utterance) {
    return { allowed: true };
  }

  if (config.requireTraceSeal && (!trace || !seal)) {
    return {
      allowed: false,
      reason: config.rejectionMessage || DEFAULT_REJECTION,
    };
  }

  if (!traceMatches(trace, utterance, config.accept || [])) {
    return {
      allowed: false,
      reason: config.rejectionMessage || DEFAULT_REJECTION,
    };
  }

  return { allowed: true };
}
