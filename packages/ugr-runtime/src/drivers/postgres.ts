import { Pool, type PoolConfig, type PoolClient, type QueryResult } from 'pg';

import { SqlPostgresUgrAdapter, type UgrPostgresAdapterOptions, type UgrPostgresQueryRunner } from '../adapters/postgres.js';

export interface UgrPgQueryLike {
  query(text: string, params?: readonly unknown[]): Promise<QueryResult<Record<string, unknown>>>;
}

export function createUgrPgPool(config: PoolConfig): Pool {
  return new Pool(config);
}

export function createUgrPostgresQueryRunner(client: UgrPgQueryLike): UgrPostgresQueryRunner {
  return {
    async query(sql: string, params?: readonly unknown[]) {
      const result = await client.query(sql, params);
      return {
        rows: result.rows as readonly Record<string, unknown>[],
      };
    },
  };
}

export function createUgrPostgresAdapter(
  client: UgrPgQueryLike | PoolClient,
  options: UgrPostgresAdapterOptions = {},
): SqlPostgresUgrAdapter {
  return new SqlPostgresUgrAdapter(createUgrPostgresQueryRunner(client), options);
}
