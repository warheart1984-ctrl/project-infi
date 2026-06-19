/** PATCH_OUTPUT_SHAPE_001 — wrap non-objects before invariant evaluation. */
export function normalizeOutputShape(result: unknown): unknown {
  if (result !== null && typeof result === 'object' && !Array.isArray(result)) {
    return result;
  }
  return { type: typeof result, value: result };
}

/** PATCH_DETERMINISM_001 — scrub timestamps and random fields before invariant evaluation. */
export function sanitizeDeterminism<T>(obj: T): T {
  return JSON.parse(
    JSON.stringify(obj, (key, value) => {
      if (typeof value === 'number' && value > 1e12) {
        return '<timestamp>';
      }
      if (typeof value === 'number' && key === 'rand') {
        return '<random>';
      }
      return value;
    }),
  ) as T;
}

export function applyOutputPatches(result: unknown): unknown {
  return sanitizeDeterminism(normalizeOutputShape(result));
}
