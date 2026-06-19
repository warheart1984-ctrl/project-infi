import type { PatchLedger } from './patchLedger.js';

export const PATCH_OUTPUT_SHAPE_001 = 'PATCH_OUTPUT_SHAPE_001';
export const PATCH_DETERMINISM_001 = 'PATCH_DETERMINISM_001';
export const PATCH_SPAN_BOUNDARY_001 = 'PATCH_SPAN_BOUNDARY_001';

declare global {
  // eslint-disable-next-line no-var
  var patchLedger: PatchLedger | undefined;
}

export function getPatchLedger(): PatchLedger | undefined {
  return globalThis.patchLedger;
}

export function isPatchDeployed(patchId: string): boolean {
  const ledger = getPatchLedger();
  const record = ledger?.get(patchId);
  return record?.status === 'DEPLOYED';
}

/** PATCH_OUTPUT_SHAPE_001 — wrap non-objects as structured envelopes. */
export function applyOutputShapePatch(output: unknown): unknown {
  if (typeof output === 'object' && output !== null && !Array.isArray(output)) {
    return output;
  }
  return { type: 'wrapped', value: output };
}

const NON_DETERMINISTIC_KEYS = new Set(['rand', 'random', 'generatedAt', 'at', 'ts', 'timestamp']);

/** PATCH_DETERMINISM_001 — strip volatile fields from object outputs. */
export function sanitizeDeterminism(output: unknown): unknown {
  if (typeof output !== 'object' || output === null || Array.isArray(output)) {
    return output;
  }

  const copy: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(output)) {
    if (NON_DETERMINISTIC_KEYS.has(key)) {
      continue;
    }
    if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}T/.test(value)) {
      continue;
    }
    copy[key] = value;
  }
  return copy;
}

/** Apply all DEPLOYED output patches in constitutional order. */
export function applyDeployedOutputPatches(output: unknown): unknown {
  let current = output;
  if (isPatchDeployed(PATCH_OUTPUT_SHAPE_001)) {
    current = applyOutputShapePatch(current);
  }
  if (isPatchDeployed(PATCH_DETERMINISM_001)) {
    current = sanitizeDeterminism(current);
  }
  return current;
}

export type SpanGuardFn<T> = () => Promise<T>;

/** PATCH_SPAN_BOUNDARY_001 — ensure span close runs even when work throws. */
export async function withSpanGuard<T>(run: SpanGuardFn<T>, close: () => void): Promise<T> {
  if (!isPatchDeployed(PATCH_SPAN_BOUNDARY_001)) {
    return run();
  }

  try {
    return await run();
  } finally {
    close();
  }
}
