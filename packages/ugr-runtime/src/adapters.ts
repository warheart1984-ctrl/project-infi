import type { Artifact, Embedding, Glyph, LineageEvent, Organism } from './models.js';

export type Awaitable<T> = T | Promise<T>;

export interface UgrPostgresAdapter {
  fetch_all_glyphs(): Awaitable<Glyph[]>;
  fetch_all_artifacts(): Awaitable<Artifact[]>;
  fetch_all_organisms(): Awaitable<Organism[]>;
  fetch_artifacts(domain: string): Awaitable<Artifact[]>;
  fetch_lineage(world_id: string): Awaitable<LineageEvent[]>;
  fetch_all_lineage(): Awaitable<LineageEvent[]>;
  fetch_organism(id: string): Awaitable<Organism | undefined>;
  upsert_glyph(glyph: Glyph): Awaitable<void>;
  upsert_artifact(artifact: Artifact): Awaitable<void>;
  insert_lineage_event(event: LineageEvent): Awaitable<void>;
  upsert_organism(organism: Organism): Awaitable<void>;
}

export interface UgrNeo4jAdapter {
  get_lineage_graph(world_id: string): Awaitable<import('./storage/graph.js').UgrGraph>;
  link_event_to_world(event_id: string, world_id: string): Awaitable<void>;
  link_organism_fusion(org1_id: string, org2_id: string, fused_id: string): Awaitable<void>;
  query_related_artifacts(world_id: string): Awaitable<Artifact[]>;
  registerGlyph(glyph: Glyph): Awaitable<void>;
  registerArtifact(artifact: Artifact): Awaitable<void>;
  registerEvent(event: LineageEvent): Awaitable<void>;
  registerOrganism(organism: Organism): Awaitable<void>;
}

export interface UgrPgvectorAdapter {
  store_embedding(embedding: Embedding): Awaitable<void>;
  query_neighbors(vector: readonly number[], k: number): Awaitable<Embedding[]>;
  delete_embedding(id: string): Awaitable<void>;
}

export interface UgrPersistenceAdapters {
  postgres: UgrPostgresAdapter;
  neo4j: UgrNeo4jAdapter;
  pgvector: UgrPgvectorAdapter;
}
