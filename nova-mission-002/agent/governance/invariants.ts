import type { Invariant } from "../types/invariants";

const registered: Invariant[] = [];

export function getInvariants(): readonly Invariant[] {
  return registered;
}

export async function requireInvariant(inv: Invariant): Promise<void> {
  if (registered.some((r) => r.id === inv.id)) return;
  registered.push(inv);
}

export function clearInvariants(): void {
  registered.length = 0;
}

export { registered as invariants };
