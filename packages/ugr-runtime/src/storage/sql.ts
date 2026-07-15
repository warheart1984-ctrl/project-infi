import {
  cloneArtifact,
  cloneGlyph,
  cloneLineageEvent,
  cloneOrganism,
  type Artifact,
  type Glyph,
  type LineageEvent,
  type Organism,
} from '../models.js';
import type { UgrPostgresAdapter } from '../adapters.js';

export interface UgrSqlStorage {
  fetch_all_glyphs(): Promise<Glyph[]>;
  fetch_all_artifacts(): Promise<Artifact[]>;
  fetch_all_organisms(): Promise<Organism[]>;
  upsert_glyph(glyph: Glyph): Promise<void>;
  fetch_artifacts(domain: string): Promise<Artifact[]>;
  upsert_artifact(artifact: Artifact): Promise<void>;
  fetch_lineage(world_id: string): Promise<LineageEvent[]>;
  fetch_all_lineage(): Promise<LineageEvent[]>;
  insert_lineage_event(event: LineageEvent): Promise<void>;
  fetch_organism(id: string): Promise<Organism | undefined>;
  upsert_organism(organism: Organism): Promise<void>;
}

export interface UgrSqlStorageOptions {
  adapter?: UgrPostgresAdapter;
}

export class InMemoryUgrSqlStorage implements UgrSqlStorage {
  private readonly glyphs = new Map<string, Glyph>();
  private readonly artifacts = new Map<string, Artifact>();
  private readonly lineage = new Map<string, LineageEvent[]>();
  private readonly organisms = new Map<string, Organism>();
  private readonly adapter?: UgrPostgresAdapter;
  private readonly ready: Promise<void>;

  constructor(options: UgrSqlStorageOptions = {}) {
    this.adapter = options.adapter;
    this.ready = this.hydrateFromAdapter();
  }

  async fetch_all_glyphs(): Promise<Glyph[]> {
    await this.ensureReady();
    return [...this.glyphs.values()].map(cloneGlyph);
  }

  async fetch_all_artifacts(): Promise<Artifact[]> {
    await this.ensureReady();
    return [...this.artifacts.values()].map(cloneArtifact);
  }

  async fetch_all_organisms(): Promise<Organism[]> {
    await this.ensureReady();
    return [...this.organisms.values()].map(cloneOrganism);
  }

  async upsert_glyph(glyph: Glyph): Promise<void> {
    await this.ensureReady();
    const cloned = cloneGlyph(glyph);
    this.glyphs.set(cloned.glyph_id, cloned);
    await this.adapter?.upsert_glyph(cloned);
  }

  async fetch_artifacts(domain: string): Promise<Artifact[]> {
    await this.ensureReady();
    return [...this.artifacts.values()].filter((artifact) => artifact.domain === domain).map(cloneArtifact);
  }

  async upsert_artifact(artifact: Artifact): Promise<void> {
    await this.ensureReady();
    const cloned = cloneArtifact(artifact);
    this.artifacts.set(cloned.artifact_id, cloned);
    await this.adapter?.upsert_artifact(cloned);
  }

  async fetch_lineage(world_id: string): Promise<LineageEvent[]> {
    await this.ensureReady();
    return [...(this.lineage.get(world_id) ?? [])].map(cloneLineageEvent);
  }

  async fetch_all_lineage(): Promise<LineageEvent[]> {
    await this.ensureReady();
    return [...this.lineage.values()].flat().map(cloneLineageEvent);
  }

  async insert_lineage_event(event: LineageEvent): Promise<void> {
    await this.ensureReady();
    const cloned = cloneLineageEvent(event);
    const bucket = this.lineage.get(cloned.world_id) ?? [];
    bucket.push(cloned);
    this.lineage.set(cloned.world_id, bucket);
    await this.adapter?.insert_lineage_event(cloned);
  }

  async fetch_organism(id: string): Promise<Organism | undefined> {
    await this.ensureReady();
    const organism = this.organisms.get(id);
    return organism ? cloneOrganism(organism) : undefined;
  }

  async upsert_organism(organism: Organism): Promise<void> {
    await this.ensureReady();
    const cloned = cloneOrganism(organism);
    this.organisms.set(cloned.organism_id, cloned);
    await this.adapter?.upsert_organism(cloned);
  }

  private async hydrateFromAdapter(): Promise<void> {
    const adapter = this.adapter;
    if (!adapter) {
      return;
    }
    for (const glyph of await adapter.fetch_all_glyphs()) {
      this.glyphs.set(glyph.glyph_id, cloneGlyph(glyph));
    }
    for (const artifact of await adapter.fetch_all_artifacts()) {
      this.artifacts.set(artifact.artifact_id, cloneArtifact(artifact));
    }
    for (const organism of await adapter.fetch_all_organisms()) {
      this.organisms.set(organism.organism_id, cloneOrganism(organism));
    }
    for (const event of await adapter.fetch_all_lineage()) {
      const cloned = cloneLineageEvent(event);
      const bucket = this.lineage.get(cloned.world_id) ?? [];
      bucket.push(cloned);
      this.lineage.set(cloned.world_id, bucket);
    }
  }

  private async ensureReady(): Promise<void> {
    await this.ready;
  }
}
