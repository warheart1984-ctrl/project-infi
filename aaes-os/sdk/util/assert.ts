export function equal<T>(a: T, b: T): void {
  if (a !== b) {
    throw new Error(`Assertion failed: ${String(a)} !== ${String(b)}`);
  }
}

export function deepEqual(a: unknown, b: unknown): void {
  const sa = JSON.stringify(a);
  const sb = JSON.stringify(b);
  if (sa !== sb) {
    throw new Error(`Deep assertion failed: ${sa} !== ${sb}`);
  }
}
