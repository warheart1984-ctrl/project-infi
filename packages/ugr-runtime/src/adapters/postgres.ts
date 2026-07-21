import type { Artifact, Glyph, LineageEvent, Organism, UgrJsonValue } from '../models.js';
import type { UgrPostgresAdapter } from '../adapters.js';

export interface UgrPostgresQueryResult {
  rows: readonly Record<string, unknown>[];
}

export interface UgrPostgresQueryRunner {
  query(sql: string, params?: readonly unknown[]): Promise<UgrPostgresQueryResult>;
}

export interface UgrPostgresAdapterOptions {
  schema?: string;
  tablePrefix?: string;
}

const DEFAULT_OPTIONS: Required<UgrPostgresAdapterOptions> = {
  schema: 'public',
  tablePrefix: 'ugr_',
};

export function createUgrPostgresSchemaStatements(options: UgrPostgresAdapterOptions = {}): readonly string[] {
  const config = resolveOptions(options);
  return [
    `create schema if not exists ${quoteIdentifier(config.schema)};`,
    `create table if not exists ${qualifiedName(config, 'glyphs')} (
      glyph_id text primary key,
      symbol text not null,
      role text not null,
      embedding jsonb not null
    );`,
    `create table if not exists ${qualifiedName(config, 'artifacts')} (
      artifact_id text primary key,
      type text not null,
      domain text not null,
      text text not null,
      conditions jsonb not null
    );`,
    `create table if not exists ${qualifiedName(config, 'lineage_events')} (
      event_id text primary key,
      world_id text not null,
      experiment_id text not null,
      decision text not null,
      score double precision not null,
      outcome jsonb not null,
      hindsight_score double precision not null,
      timestamp double precision not null
    );`,
    `create table if not exists ${qualifiedName(config, 'organisms')} (
      organism_id text primary key,
      worlds jsonb not null,
      mandala_nodes jsonb not null,
      glyphs jsonb not null,
      risk jsonb not null
    );`,
  ];
}

export class SqlPostgresUgrAdapter implements UgrPostgresAdapter {
  constructor(
    private readonly runner: UgrPostgresQueryRunner,
    private readonly options: UgrPostgresAdapterOptions = {},
  ) {}

  async bootstrap(): Promise<void> {
    for (const statement of createUgrPostgresSchemaStatements(this.options)) {
      await this.runner.query(statement);
    }
  }

  async fetch_all_glyphs(): Promise<Glyph[]> {
    return (await this.runner
      .query(`select glyph_id, symbol, role, embedding from ${qualifiedName(resolveOptions(this.options), 'glyphs')} order by glyph_id`))
      .rows.map(rowToGlyph);
  }

  async fetch_all_artifacts(): Promise<Artifact[]> {
    return (await this.runner
      .query(`select artifact_id, type, domain, text, conditions from ${qualifiedName(resolveOptions(this.options), 'artifacts')} order by artifact_id`))
      .rows.map(rowToArtifact);
  }

  async fetch_all_organisms(): Promise<Organism[]> {
    return (await this.runner
      .query(`select organism_id, worlds, mandala_nodes, glyphs, risk from ${qualifiedName(resolveOptions(this.options), 'organisms')} order by organism_id`))
      .rows.map(rowToOrganism);
  }

  async fetch_artifacts(domain: string): Promise<Artifact[]> {
    return (await this.runner
      .query(
        `select artifact_id, type, domain, text, conditions from ${qualifiedName(resolveOptions(this.options), 'artifacts')} where domain = $1 order by artifact_id`,
        [domain],
      )
      ).rows.map(rowToArtifact);
  }

  async fetch_lineage(world_id: string): Promise<LineageEvent[]> {
    return (await this.runner
      .query(
        `select event_id, world_id, experiment_id, decision, score, outcome, hindsight_score, timestamp from ${qualifiedName(resolveOptions(this.options), 'lineage_events')} where world_id = $1 order by timestamp, event_id`,
        [world_id],
      )
      ).rows.map(rowToLineageEvent);
  }

  async fetch_all_lineage(): Promise<LineageEvent[]> {
    return (await this.runner
      .query(
        `select event_id, world_id, experiment_id, decision, score, outcome, hindsight_score, timestamp from ${qualifiedName(resolveOptions(this.options), 'lineage_events')} order by timestamp, event_id`,
      )
      ).rows.map(rowToLineageEvent);
  }

  async fetch_organism(id: string): Promise<Organism | undefined> {
    const row = (await this.runner
      .query(
        `select organism_id, worlds, mandala_nodes, glyphs, risk from ${qualifiedName(resolveOptions(this.options), 'organisms')} where organism_id = $1 limit 1`,
        [id],
      )
    ).rows[0];
    return row ? rowToOrganism(row) : undefined;
  }

  async upsert_glyph(glyph: Glyph): Promise<void> {
    await this.runner.query(
      `insert into ${qualifiedName(resolveOptions(this.options), 'glyphs')} (glyph_id, symbol, role, embedding)
       values ($1, $2, $3, $4::jsonb)
       on conflict (glyph_id) do update set symbol = excluded.symbol, role = excluded.role, embedding = excluded.embedding`,
      [glyph.glyph_id, glyph.symbol, glyph.role, JSON.stringify(glyph.embedding)],
    );
  }

  async upsert_artifact(artifact: Artifact): Promise<void> {
    await this.runner.query(
      `insert into ${qualifiedName(resolveOptions(this.options), 'artifacts')} (artifact_id, type, domain, text, conditions)
       values ($1, $2, $3, $4, $5::jsonb)
       on conflict (artifact_id) do update set type = excluded.type, domain = excluded.domain, text = excluded.text, conditions = excluded.conditions`,
      [artifact.artifact_id, artifact.type, artifact.domain, artifact.text, JSON.stringify(artifact.conditions)],
    );
  }

  async insert_lineage_event(event: LineageEvent): Promise<void> {
    await this.runner.query(
      `insert into ${qualifiedName(resolveOptions(this.options), 'lineage_events')} (event_id, world_id, experiment_id, decision, score, outcome, hindsight_score, timestamp)
       values ($1, $2, $3, $4, $5, $6::jsonb, $7, $8)
       on conflict (event_id) do update set world_id = excluded.world_id, experiment_id = excluded.experiment_id, decision = excluded.decision, score = excluded.score, outcome = excluded.outcome, hindsight_score = excluded.hindsight_score, timestamp = excluded.timestamp`,
      [
        event.event_id,
        event.world_id,
        event.experiment_id,
        event.decision,
        event.score,
        JSON.stringify(event.outcome),
        event.hindsight_score,
        event.timestamp,
      ],
    );
  }

  async upsert_organism(organism: Organism): Promise<void> {
    await this.runner.query(
      `insert into ${qualifiedName(resolveOptions(this.options), 'organisms')} (organism_id, worlds, mandala_nodes, glyphs, risk)
       values ($1, $2::jsonb, $3::jsonb, $4::jsonb, $5::jsonb)
       on conflict (organism_id) do update set worlds = excluded.worlds, mandala_nodes = excluded.mandala_nodes, glyphs = excluded.glyphs, risk = excluded.risk`,
      [
        organism.organism_id,
        JSON.stringify(organism.worlds),
        JSON.stringify(organism.mandala_nodes),
        JSON.stringify(organism.glyphs),
        JSON.stringify(organism.risk),
      ],
    );
  }
}

function rowToGlyph(row: Record<string, unknown>): Glyph {
  return {
    glyph_id: String(row.glyph_id),
    symbol: String(row.symbol),
    role: String(row.role),
    embedding: normalizeArray(row.embedding),
  };
}

function rowToArtifact(row: Record<string, unknown>): Artifact {
  return {
    artifact_id: String(row.artifact_id),
    type: String(row.type),
    domain: String(row.domain),
    text: String(row.text),
    conditions: normalizeRecord(row.conditions),
  };
}

function rowToLineageEvent(row: Record<string, unknown>): LineageEvent {
  return {
    event_id: String(row.event_id),
    world_id: String(row.world_id),
    experiment_id: String(row.experiment_id),
    decision: String(row.decision),
    score: Number(row.score),
    outcome: normalizeRecord(row.outcome),
    hindsight_score: Number(row.hindsight_score),
    timestamp: Number(row.timestamp),
  };
}

function rowToOrganism(row: Record<string, unknown>): Organism {
  return {
    organism_id: String(row.organism_id),
    worlds: normalizeStringArray(row.worlds),
    mandala_nodes: normalizeRecordArray(row.mandala_nodes),
    glyphs: normalizeGlyphArray(row.glyphs),
    risk: normalizeNumberRecord(row.risk),
  };
}

function normalizeArray(value: unknown): readonly number[] {
  if (Array.isArray(value) && value.every((item) => typeof item === 'number')) {
    return value;
  }
  if (typeof value === 'string') {
    const parsed = JSON.parse(value) as unknown;
    if (Array.isArray(parsed) && parsed.every((item) => typeof item === 'number')) {
      return parsed;
    }
  }
  throw new Error('Expected numeric JSON array from PostgreSQL row');
}

function normalizeStringArray(value: unknown): readonly string[] {
  if (Array.isArray(value) && value.every((item) => typeof item === 'string')) {
    return value;
  }
  if (typeof value === 'string') {
    const parsed = JSON.parse(value) as unknown;
    if (Array.isArray(parsed) && parsed.every((item) => typeof item === 'string')) {
      return parsed;
    }
  }
  throw new Error('Expected string JSON array from PostgreSQL row');
}

function normalizeRecordArray(value: unknown): readonly Record<string, UgrJsonValue>[] {
  if (Array.isArray(value) && value.every((item) => item && typeof item === 'object' && !Array.isArray(item))) {
    return value as readonly Record<string, UgrJsonValue>[];
  }
  if (typeof value === 'string') {
    const parsed = JSON.parse(value) as unknown;
    if (Array.isArray(parsed) && parsed.every((item) => item && typeof item === 'object' && !Array.isArray(item))) {
      return parsed as readonly Record<string, UgrJsonValue>[];
    }
  }
  throw new Error('Expected record JSON array from PostgreSQL row');
}

function normalizeGlyphArray(value: unknown): readonly Glyph[] {
  return normalizeRecordArray(value).map((entry) => rowToGlyph(entry));
}

function normalizeRecord(value: unknown): Record<string, UgrJsonValue> {
  if (value && typeof value === 'object' && !Array.isArray(value)) {
    return value as Record<string, UgrJsonValue>;
  }
  if (typeof value === 'string') {
    const parsed = JSON.parse(value) as unknown;
    if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
      return parsed as Record<string, UgrJsonValue>;
    }
  }
  throw new Error('Expected JSON object from PostgreSQL row');
}

function normalizeNumberRecord(value: unknown): Record<string, number> {
  const record = normalizeRecord(value);
  const result: Record<string, number> = {};
  for (const [key, entry] of Object.entries(record)) {
    result[key] = Number(entry);
  }
  return result;
}

function resolveOptions(options: UgrPostgresAdapterOptions): Required<UgrPostgresAdapterOptions> {
  return {
    schema: options.schema ?? DEFAULT_OPTIONS.schema,
    tablePrefix: options.tablePrefix ?? DEFAULT_OPTIONS.tablePrefix,
  };
}

function qualifiedName(options: Required<UgrPostgresAdapterOptions>, table: string): string {
  return `${quoteIdentifier(options.schema)}.${quoteIdentifier(`${options.tablePrefix}${table}`)}`;
}

function quoteIdentifier(identifier: string): string {
  return `"${identifier.replace(/"/g, '""')}"`;
}
