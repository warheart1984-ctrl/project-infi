import { Pool, type ClientBase, type PoolConfig, type PoolClient, type QueryResult } from 'pg';
import { registerTypes } from 'pgvector/pg';

import { PgvectorUgrAdapter, type UgrPgvectorAdapterOptions, type UgrPgvectorQueryRunner } from '../adapters/pgvector.js';

export interface UgrPgvectorQueryLike {
  query(text: string, params?: readonly unknown[]): Promise<QueryResult<Record<string, unknown>>>;
}

export function createUgrPgvectorPool(config: PoolConfig): Pool {
  return new Pool(config);
}

export async function registerUgrPgvectorTypes(client: ClientBase): Promise<ClientBase> {
  await registerTypes(client);
  return client;
}

export function createUgrPgvectorQueryRunner(client: UgrPgvectorQueryLike): UgrPgvectorQueryRunner {
  return {
    async query(sql: string, params?: readonly unknown[]) {
      const result = await client.query(sql, params);
      return {
        rows: result.rows as readonly Record<string, unknown>[],
      };
    },
  };
}

export function createUgrPgvectorAdapter(
  client: UgrPgvectorQueryLike | PoolClient,
  options: UgrPgvectorAdapterOptions = {},
): PgvectorUgrAdapter {
  return new PgvectorUgrAdapter(createUgrPgvectorQueryRunner(client), options);
}
