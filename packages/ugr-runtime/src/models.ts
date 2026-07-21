export type UgrJsonPrimitive = string | number | boolean | null;

export type UgrJsonValue =
  | UgrJsonPrimitive
  | readonly UgrJsonValue[]
  | { readonly [key: string]: UgrJsonValue };

export interface Glyph {
  glyph_id: string;
  symbol: string;
  role: string;
  embedding: readonly number[];
}

export interface Artifact {
  artifact_id: string;
  type: 'invariant' | 'rule' | 'precedent' | 'contract' | string;
  domain: string;
  text: string;
  conditions: Record<string, UgrJsonValue>;
}

export interface Embedding {
  embedding_id: string;
  vector: readonly number[];
  metadata: Record<string, UgrJsonValue>;
}

export interface LineageEvent {
  event_id: string;
  world_id: string;
  experiment_id: string;
  decision: string;
  score: number;
  outcome: Record<string, UgrJsonValue>;
  hindsight_score: number;
  timestamp: number;
}

export interface Organism {
  organism_id: string;
  worlds: readonly string[];
  mandala_nodes: readonly Record<string, UgrJsonValue>[];
  glyphs: readonly Glyph[];
  risk: Record<string, number>;
}

export function cloneGlyph(glyph: Glyph): Glyph {
  return {
    ...glyph,
    embedding: [...glyph.embedding],
  };
}

export function cloneArtifact(artifact: Artifact): Artifact {
  return {
    ...artifact,
    conditions: cloneRecord(artifact.conditions),
  };
}

export function cloneEmbedding(embedding: Embedding): Embedding {
  return {
    ...embedding,
    vector: [...embedding.vector],
    metadata: cloneRecord(embedding.metadata),
  };
}

export function cloneLineageEvent(event: LineageEvent): LineageEvent {
  return {
    ...event,
    outcome: cloneRecord(event.outcome),
  };
}

export function cloneOrganism(organism: Organism): Organism {
  return {
    ...organism,
    worlds: [...organism.worlds],
    mandala_nodes: organism.mandala_nodes.map((node) => cloneRecord(node)),
    glyphs: organism.glyphs.map(cloneGlyph),
    risk: { ...organism.risk },
  };
}

export function cloneRecord<T extends Record<string, unknown>>(value: T): T {
  return Object.fromEntries(
    Object.entries(value).map(([key, entry]) => [key, cloneValue(entry)]),
  ) as T;
}

export function cloneValue(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map((entry) => cloneValue(entry));
  }
  if (value && typeof value === 'object') {
    return cloneRecord(value as Record<string, unknown>);
  }
  return value;
}

export function normalizeText(value: string): string {
  return value.trim();
}

