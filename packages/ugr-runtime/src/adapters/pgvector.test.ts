import { describe, expect, it } from 'vitest';

import { PgvectorUgrAdapter, createUgrPgvectorSchemaStatements, type UgrPgvectorQueryRunner } from './pgvector.js';

describe('pgvector UGR adapter', () => {
  it('emits schema statements for the UGR embedding store', () => {
    const statements = createUgrPgvectorSchemaStatements({ dimensions: 4 });

    expect(statements).toEqual(
      expect.arrayContaining([
        expect.stringContaining('create extension if not exists vector;'),
        expect.stringContaining('create table if not exists "public"."ugr_embeddings"'),
        expect.stringContaining('vector(4) not null'),
      ]),
    );
  });

  it('stores, queries, and deletes embeddings through pgvector SQL', async () => {
    const calls: Array<{ sql: string; params?: readonly unknown[] }> = [];
    const runner: UgrPgvectorQueryRunner = {
      async query(sql: string, params?: readonly unknown[]) {
        calls.push({ sql, params });
        if (sql.includes('order by embedding <-> $1::vector')) {
          return {
            rows: [
              {
                embedding_id: 'embedding-1',
                embedding: '[1,2,3]',
                metadata: { domain: 'law' },
              },
            ],
          };
        }
        return { rows: [] };
      },
    };

    const adapter = new PgvectorUgrAdapter(runner, { dimensions: 3 });

    expect(await adapter.query_neighbors([1, 2, 3], 1)).toEqual([
      {
        embedding_id: 'embedding-1',
        vector: [1, 2, 3],
        metadata: { domain: 'law' },
      },
    ]);

    await adapter.store_embedding({
      embedding_id: 'embedding-2',
      vector: [3, 2, 1],
      metadata: { domain: 'medicine' },
    });
    await adapter.delete_embedding('embedding-2');

    expect(calls.some((call) => call.sql.includes('insert into "public"."ugr_embeddings"'))).toBe(true);
    expect(calls.some((call) => call.sql.includes('delete from "public"."ugr_embeddings" where embedding_id = $1'))).toBe(true);
  });
});
