/**
 * Mythic: Unified Language Surface — semantic compare
 * Engineering: semanticCompare
 */

/**
 * Stub embedding similarity — returns cosine-like score in [0, 1].
 * Replace with real embeddings when ULS v2 is admitted.
 */
export function semanticCompare(a: string, b: string): number {
  if (!a.trim() || !b.trim()) {
    return 0;
  }
  if (a === b) {
    return 1;
  }

  const tokensA = tokenize(a);
  const tokensB = tokenize(b);
  if (tokensA.size === 0 || tokensB.size === 0) {
    return 0;
  }

  let intersection = 0;
  for (const t of tokensA) {
    if (tokensB.has(t)) {
      intersection += 1;
    }
  }
  const union = tokensA.size + tokensB.size - intersection;
  return union === 0 ? 0 : intersection / union;
}

function tokenize(text: string): Set<string> {
  return new Set(
    text
      .toLowerCase()
      .split(/\W+/)
      .filter((t) => t.length > 1),
  );
}
