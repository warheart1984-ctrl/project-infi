import neo4j from 'neo4j-driver';

import type { UgrPersistenceAdapters } from './adapters.js';
import { createUgrNeo4jAdapter, createUgrNeo4jDriver } from './drivers/neo4j.js';
import { createUgrPgPool, createUgrPostgresAdapter } from './drivers/postgres.js';
import { createUgrPgvectorAdapter, createUgrPgvectorPool } from './drivers/pgvector.js';
import { createUgrRuntimeService, type UgrRuntimeConfig, type UgrRuntimeService } from './runtime.js';

export interface UgrRuntimeEnvConfig {
  host: string;
  port: number;
  postgresConnectionString?: string;
  postgresSchema: string;
  postgresTablePrefix: string;
  neo4jUri?: string;
  neo4jUsername?: string;
  neo4jPassword?: string;
  neo4jDatabase: string;
  neo4jLabelPrefix: string;
  pgvectorConnectionString?: string;
  pgvectorSchema: string;
  pgvectorTableName: string;
  pgvectorDimensions: number;
}

export interface UgrRuntimeEnvResources {
  adapters: Partial<UgrPersistenceAdapters>;
  shutdown(): Promise<void>;
}

const DEFAULT_ENV_CONFIG: UgrRuntimeEnvConfig = {
  host: '127.0.0.1',
  port: 0,
  postgresSchema: 'public',
  postgresTablePrefix: 'ugr_',
  neo4jDatabase: 'neo4j',
  neo4jLabelPrefix: 'UGR_',
  pgvectorSchema: 'public',
  pgvectorTableName: 'ugr_embeddings',
  pgvectorDimensions: 1536,
};

export function loadUgrRuntimeEnvConfig(env: NodeJS.ProcessEnv = process.env): UgrRuntimeEnvConfig {
  return {
    ...DEFAULT_ENV_CONFIG,
    host: env.UGR_HOST ?? DEFAULT_ENV_CONFIG.host,
    port: parsePort(env.UGR_PORT, DEFAULT_ENV_CONFIG.port),
    postgresConnectionString: env.UGR_PG_CONNECTION_STRING,
    postgresSchema: env.UGR_PG_SCHEMA ?? DEFAULT_ENV_CONFIG.postgresSchema,
    postgresTablePrefix: env.UGR_PG_TABLE_PREFIX ?? DEFAULT_ENV_CONFIG.postgresTablePrefix,
    neo4jUri: env.UGR_NEO4J_URI,
    neo4jUsername: env.UGR_NEO4J_USERNAME,
    neo4jPassword: env.UGR_NEO4J_PASSWORD,
    neo4jDatabase: env.UGR_NEO4J_DATABASE ?? DEFAULT_ENV_CONFIG.neo4jDatabase,
    neo4jLabelPrefix: env.UGR_NEO4J_LABEL_PREFIX ?? DEFAULT_ENV_CONFIG.neo4jLabelPrefix,
    pgvectorConnectionString: env.UGR_PGVECTOR_CONNECTION_STRING ?? env.UGR_PG_CONNECTION_STRING,
    pgvectorSchema: env.UGR_PGVECTOR_SCHEMA ?? DEFAULT_ENV_CONFIG.pgvectorSchema,
    pgvectorTableName: env.UGR_PGVECTOR_TABLE_NAME ?? DEFAULT_ENV_CONFIG.pgvectorTableName,
    pgvectorDimensions: parsePort(env.UGR_PGVECTOR_DIMENSIONS, DEFAULT_ENV_CONFIG.pgvectorDimensions),
  };
}

export async function createUgrRuntimeAdaptersFromEnv(
  env: NodeJS.ProcessEnv = process.env,
): Promise<Partial<UgrPersistenceAdapters>> {
  const bundle = await createUgrRuntimeResourcesFromEnv(env);
  return bundle.adapters;
}

export async function createUgrRuntimeResourcesFromEnv(
  env: NodeJS.ProcessEnv = process.env,
): Promise<UgrRuntimeEnvResources> {
  const config = loadUgrRuntimeEnvConfig(env);
  const adapters: Partial<UgrPersistenceAdapters> = {};
  const shutdownCallbacks: Array<() => Promise<void>> = [];

  try {
    if (config.postgresConnectionString) {
      const postgresPool = createUgrPgPool({ connectionString: config.postgresConnectionString });
      const postgresAdapter = createUgrPostgresAdapter(postgresPool, {
        schema: config.postgresSchema,
        tablePrefix: config.postgresTablePrefix,
      });
      await postgresAdapter.bootstrap();
      adapters.postgres = postgresAdapter;
      shutdownCallbacks.push(async () => {
        await postgresPool.end();
      });
    }

    if (config.neo4jUri && config.neo4jUsername && config.neo4jPassword) {
      const driver = createUgrNeo4jDriver(
        config.neo4jUri,
        neo4j.auth.basic(config.neo4jUsername, config.neo4jPassword),
      );
      const neo4jAdapter = createUgrNeo4jAdapter(driver, {
        database: config.neo4jDatabase,
        labelPrefix: config.neo4jLabelPrefix,
      });
      await neo4jAdapter.bootstrap();
      adapters.neo4j = neo4jAdapter;
      shutdownCallbacks.push(async () => {
        await driver.close();
      });
    }

    if (config.pgvectorConnectionString) {
      const pgvectorPool = createUgrPgvectorPool({ connectionString: config.pgvectorConnectionString });
      const pgvectorAdapter = createUgrPgvectorAdapter(pgvectorPool, {
        schema: config.pgvectorSchema,
        tableName: config.pgvectorTableName,
        dimensions: config.pgvectorDimensions,
      });
      await pgvectorAdapter.bootstrap();
      adapters.pgvector = pgvectorAdapter;
      shutdownCallbacks.push(async () => {
        await pgvectorPool.end();
      });
    }

    return {
      adapters,
      async shutdown(): Promise<void> {
        await closeCallbacksInReverse(shutdownCallbacks);
      },
    };
  } catch (error) {
    await closeCallbacksInReverse(shutdownCallbacks);
    throw error;
  }
}

export async function createUgrRuntimeServiceFromEnv(
  env: NodeJS.ProcessEnv = process.env,
): Promise<UgrRuntimeService> {
  const config = loadUgrRuntimeEnvConfig(env);
  const resources = await createUgrRuntimeResourcesFromEnv(env);
  return createUgrRuntimeService({
    host: config.host,
    port: config.port,
    adapters: resources.adapters,
    shutdown: resources.shutdown,
  } satisfies Partial<UgrRuntimeConfig>);
}

function parsePort(value: string | undefined, fallback: number): number {
  if (value === undefined || value.trim().length === 0) {
    return fallback;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : fallback;
}

async function closeCallbacksInReverse(callbacks: Array<() => Promise<void>>): Promise<void> {
  let firstError: unknown;
  for (let index = callbacks.length - 1; index >= 0; index -= 1) {
    try {
      await callbacks[index]?.();
    } catch (error) {
      firstError ??= error;
    }
  }
  if (firstError) {
    throw firstError instanceof Error ? firstError : new Error(String(firstError));
  }
}
