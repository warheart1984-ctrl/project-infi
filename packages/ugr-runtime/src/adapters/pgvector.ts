import type { Embedding, UgrJsonValue } from '../models.js';
import type { UgrPgvectorAdapter } from '../adapters.js';
import { toSql as vectorToSql } from 'pgvector';

export interface UgrPgvectorQueryResult {
  rows: readonly Record<string, unknown>[];
}

export interface UgrPgvectorQueryRunner {
  query(sql: string, params?: readonly unknown[]): Promise<UgrPgvectorQueryResult>;
}

export interface UgrPgvectorAdapterOptions {
  schema?: string;
  tableName?: string;
  dimensions?: number;
}

const DEFAULT_OPTIONS: Required<Omit<UgrPgvectorAdapterOptions, 'dimensions'>> & { dimensions: number } = {
  schema: 'public',
  tableName: 'ugr_embeddings',
  dimensions: 1536,
};

export function createUgrPgvectorSchemaStatements(options: UgrPgvectorAdapterOptions = {}): readonly string[] {
  const config = resolveOptions(options);
  return [
    'create extension if not exists vector;',
    `create table if not exists ${qualifiedName(config)} (
      embedding_id text primary key,
      embedding vector(${config.dimensions}) not null,
      metadata jsonb not null
    );`,
    `create index if not exists ${indexName(config)} on ${qualifiedName(config)} using ivfflat (embedding vector_cosine_ops);`,
  ];
}

export class PgvectorUgrAdapter implements UgrPgvectorAdapter {
  constructor(
    private readonly runner: UgrPgvectorQueryRunner,
    private readonly options: UgrPgvectorAdapterOptions = {},
  ) {}

  async bootstrap(): Promise<void> {
    for (const statement of createUgrPgvectorSchemaStatements(this.options)) {
      await this.runner.query(statement);
    }
  }

  async store_embedding(embedding: Embedding): Promise<void> {
    const config = resolveOptions(this.options);
    await this.runner.query(
      `insert into ${qualifiedName(config)} (embedding_id, embedding, metadata)
       values ($1, $2::vector, $3::jsonb)
       on conflict (embedding_id) do update set embedding = excluded.embedding, metadata = excluded.metadata`,
      [embedding.embedding_id, vectorToSql([...embedding.vector]) ?? vectorLiteral(embedding.vector), JSON.stringify(embedding.metadata)],
    );
  }

  async query_neighbors(vector: readonly number[], k: number): Promise<Embedding[]> {
    const config = resolveOptions(this.options);
    return (await this.runner
      .query(
        `select embedding_id, embedding, metadata
         from ${qualifiedName(config)}
         order by embedding <-> $1::vector
         limit $2`,
        [vectorLiteral(vector), k],
      )
      ).rows.map(rowToEmbedding);
  }

  async delete_embedding(id: string): Promise<void> {
    const config = resolveOptions(this.options);
    await this.runner.query(`delete from ${qualifiedName(config)} where embedding_id = $1`, [id]);
  }
}

function rowToEmbedding(row: Record<string, unknown>): Embedding {
  return {
    embedding_id: String(row.embedding_id),
    vector: normalizeVector(row.embedding),
    metadata: normalizeRecord(row.metadata),
  };
}

function normalizeVector(value: unknown): readonly number[] {
  if (Array.isArray(value) && value.every((item) => typeof item === 'number')) {
    return value;
  }
  if (typeof value === 'string') {
    const parsed = JSON.parse(value) as unknown;
    if (Array.isArray(parsed) && parsed.every((item) => typeof item === 'number')) {
      return parsed;
    }
    if (typeof parsed === 'string') {
      return parseVectorLiteral(parsed);
    }
  }
  throw new Error('Expected vector value from pgvector row');
}

function parseVectorLiteral(value: string): readonly number[] {
  const trimmed = value.trim();
  const match = trimmed.match(/^\[([^\]]*)\]$/);
  if (!match) {
    throw new Error('Expected pgvector literal');
  }
  const body = match[1]?.trim() ?? '';
  if (!body) {
    return [];
  }
  return body.split(',').map((part) => Number(part.trim()));
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
  throw new Error('Expected metadata object from pgvector row');
}

function vectorLiteral(vector: readonly number[]): string {
  return `[${vector.map((value) => Number.isFinite(value) ? String(value) : '0').join(',')}]`;
}

function resolveOptions(options: UgrPgvectorAdapterOptions): Required<UgrPgvectorAdapterOptions> {
  return {
    schema: options.schema ?? DEFAULT_OPTIONS.schema,
    tableName: options.tableName ?? DEFAULT_OPTIONS.tableName,
    dimensions: options.dimensions ?? DEFAULT_OPTIONS.dimensions,
  };
}

function qualifiedName(options: Required<UgrPgvectorAdapterOptions>): string {
  return `${quoteIdentifier(options.schema)}.${quoteIdentifier(options.tableName)}`;
}

function indexName(options: Required<UgrPgvectorAdapterOptions>): string {
  return quoteIdentifier(`${options.tableName}_embedding_ivfflat`);
}

function quoteIdentifier(identifier: string): string {
  return `"${identifier.replace(/"/g, '""')}"`;
}
