/**
 * Long-term memory with in-memory vector similarity search.
 *
 * Uses simple TF-IDF-style term-frequency vectors and cosine similarity
 * so it works without any external dependencies or API calls.
 * Replace with pgvector / Qdrant / OpenAI embeddings for production.
 */

export type MemoryKind = 'profile' | 'preference' | 'project' | 'episode';

export interface RetrievedMemory {
  id: string;
  kind: MemoryKind;
  content: string;
  score: number;
}

interface StoredMemory {
  id: string;
  kind: MemoryKind;
  content: string;
  vector: Map<string, number>;
  createdAt: number;
}

// ── Tokenization & vectorization ──

function tokenize(text: string): string[] {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, ' ')
    .split(/\s+/)
    .filter((t) => t.length > 1);
}

function buildVector(tokens: string[]): Map<string, number> {
  const freq = new Map<string, number>();
  for (const token of tokens) {
    freq.set(token, (freq.get(token) ?? 0) + 1);
  }
  // Normalize
  const magnitude = Math.sqrt(
    Array.from(freq.values()).reduce((sum, v) => sum + v * v, 0),
  );
  if (magnitude > 0) {
    for (const [k, v] of freq) {
      freq.set(k, v / magnitude);
    }
  }
  return freq;
}

function cosineSimilarity(a: Map<string, number>, b: Map<string, number>): number {
  let dot = 0;
  for (const [key, valA] of a) {
    const valB = b.get(key);
    if (valB !== undefined) {
      dot += valA * valB;
    }
  }
  return dot;
}

// ── Memory store (singleton) ──

const MAX_MEMORIES = 500;

const memories: StoredMemory[] = [
  // Seed memory so the system always knows the project context
  {
    id: 'seed-memory-1',
    kind: 'project',
    content: 'User is building AAIS, an Adaptive Autonomous Intelligence System.',
    vector: buildVector(tokenize('User is building AAIS an Adaptive Autonomous Intelligence System')),
    createdAt: Date.now(),
  },
];

/**
 * Retrieve memories most relevant to the input query.
 */
export async function retrieveLongTermMemory(
  input: string,
  topK: number = 5,
): Promise<RetrievedMemory[]> {
  if (!input || memories.length === 0) {
    return [];
  }

  const queryVector = buildVector(tokenize(input));

  const scored = memories.map((mem) => ({
    ...mem,
    score: cosineSimilarity(queryVector, mem.vector),
  }));

  scored.sort((a, b) => b.score - a.score);

  return scored
    .filter((m) => m.score > 0.05)
    .slice(0, topK)
    .map(({ id, kind, content, score }) => ({ id, kind, content, score }));
}

/**
 * Store a user-assistant exchange as an episode memory.
 */
export async function storeLongTermMemory(
  userMessage: string,
  assistantReply: string,
): Promise<void> {
  const combined = `User asked: ${userMessage} — Assistant replied: ${assistantReply.slice(0, 300)}`;
  const tokens = tokenize(combined);

  if (tokens.length < 3) {
    return; // too short to be useful
  }

  const entry: StoredMemory = {
    id: `mem-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    kind: 'episode',
    content: combined.slice(0, 500),
    vector: buildVector(tokens),
    createdAt: Date.now(),
  };

  memories.push(entry);

  // Evict oldest memories if over limit
  while (memories.length > MAX_MEMORIES) {
    // Keep the seed memory (index 0)
    memories.splice(1, 1);
  }
}

/**
 * Store a specific fact (profile, preference, or project note).
 */
export async function storeFactMemory(
  kind: MemoryKind,
  content: string,
): Promise<string> {
  const tokens = tokenize(content);
  const entry: StoredMemory = {
    id: `mem-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    kind,
    content,
    vector: buildVector(tokens),
    createdAt: Date.now(),
  };
  memories.push(entry);
  return entry.id;
}

/**
 * Return current memory count (useful for diagnostics).
 */
export function getMemoryCount(): number {
  return memories.length;
}
