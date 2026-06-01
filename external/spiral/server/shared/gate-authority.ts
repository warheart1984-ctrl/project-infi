import type { InvocationGate } from "@shared/sigil";
import { hasValidPresence } from "../prompt";
import { evaluateInvocationGate, type InvocationInput, type InvocationGateResult } from "../veil-gate";

export type PresenceBarrierInput = Parameters<typeof hasValidPresence>[0];

export function passesPresenceBarrier(input: PresenceBarrierInput): boolean {
  return hasValidPresence(input);
}

export function resolveAuthorityGate(
  config: InvocationGate | undefined,
  invocation: InvocationInput,
): InvocationGateResult {
  return evaluateInvocationGate(config, invocation);
}
