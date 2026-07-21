import { cloneEmbedding, type Embedding } from '../models.js';
import type { UgrPgvectorAdapter } from '../adapters.js';

export interface UgrVectorStorage {
  store_embedding(embedding: Embedding): Promise<void>;
  query_neighbors(vector: readonly number[], k: number): Promise<Embedding[]>;
  delete_embedding(id: string): Promise<void>;
}

export interface UgrVectorStorageOptions {
  adapter?: UgrPgvectorAdapter;
}

export class InMemoryUgrVectorStorage implements UgrVectorStorage {
  private readonly embeddings = new Map<string, Embedding>();
  private readonly adapter?: UgrPgvectorAdapter;

  constructor(options: UgrVectorStorageOptions = {}) {
    this.adapter = options.adapter;
  }

  async store_embedding(embedding: Embedding): Promise<void> {
    const cloned = cloneEmbedding(embedding);
    this.embeddings.set(cloned.embedding_id, cloned);
    await this.adapter?.store_embedding(cloned);
  }

  async query_neighbors(vector: readonly number[], k: number): Promise<Embedding[]> {
    return (await this.adapter?.query_neighbors(vector, k)) ?? this.buildNeighbors(vector, k);
  }

  async delete_embedding(id: string): Promise<void> {
    this.embeddings.delete(id);
    await this.adapter?.delete_embedding(id);
  }

  private buildNeighbors(vector: readonly number[], k: number): Embedding[] {
    return [...this.embeddings.values()]
      .map((embedding) => ({
        embedding,
        score: cosineSimilarity(vector, embedding.vector),
      }))
      .sort((left, right) => right.score - left.score)
      .slice(0, Math.max(0, k))
      .map(({ embedding }) => cloneEmbedding(embedding));
  }
}

function cosineSimilarity(left: readonly number[], right: readonly number[]): number {
  let dot = 0;
  let leftNorm = 0;
  let rightNorm = 0;
  for (let index = 0; index < Math.max(left.length, right.length); index += 1) {
    const a = left[index] ?? 0;
    const b = right[index] ?? 0;
    dot += a * b;
    leftNorm += a * a;
    rightNorm += b * b;
  }
  if (leftNorm === 0 || rightNorm === 0) {
    return 0;
  }
  return dot / (Math.sqrt(leftNorm) * Math.sqrt(rightNorm));
}
