import { describe, expect, it } from 'vitest';

import { SqlPostgresUgrAdapter, createUgrPostgresSchemaStatements, type UgrPostgresQueryRunner } from './postgres.js';

describe('PostgreSQL UGR adapter', () => {
  it('emits schema statements for the UGR tables', () => {
    const statements = createUgrPostgresSchemaStatements();

    expect(statements).toEqual(
      expect.arrayContaining([
        expect.stringContaining('create table if not exists "public"."ugr_glyphs"'),
        expect.stringContaining('create table if not exists "public"."ugr_artifacts"'),
        expect.stringContaining('create table if not exists "public"."ugr_lineage_events"'),
        expect.stringContaining('create table if not exists "public"."ugr_organisms"'),
      ]),
    );
  });

  it('translates row data to canonical UGR records and SQL writes', async () => {
    const calls: Array<{ sql: string; params?: readonly unknown[] }> = [];
    const responses = new Map<string, readonly Record<string, unknown>[]>([
      [
        'glyphs',
        [
          {
            glyph_id: 'glyph-1',
            symbol: '◇',
            role: 'LAW_RULE',
            embedding: [1, 2],
          },
        ],
      ],
      [
        'artifacts',
        [
          {
            artifact_id: 'artifact-1',
            type: 'rule',
            domain: 'law',
            text: 'Evidence first.',
            conditions: { objective: 'test' },
          },
        ],
      ],
      [
        'lineage_events',
        [
          {
            event_id: 'event-1',
            world_id: 'world-1',
            experiment_id: 'exp-1',
            decision: 'approve',
            score: 0.8,
            outcome: { result: 'ok' },
            hindsight_score: 0.9,
            timestamp: 1,
          },
        ],
      ],
      [
        'organisms',
        [
          {
            organism_id: 'org-1',
            worlds: ['world-1'],
            mandala_nodes: [{ node_id: 'node-1' }],
            glyphs: [
              {
                glyph_id: 'glyph-1',
                symbol: '◇',
                role: 'LAW_RULE',
                embedding: [1, 2],
              },
            ],
            risk: { drift: 0.1 },
          },
        ],
      ],
    ]);

    const runner: UgrPostgresQueryRunner = {
      async query(sql: string, params?: readonly unknown[]) {
        calls.push({ sql, params });
        if (sql.includes('from "public"."ugr_glyphs"')) {
          return { rows: responses.get('glyphs') ?? [] };
        }
        if (sql.includes('from "public"."ugr_artifacts"')) {
          return { rows: responses.get('artifacts') ?? [] };
        }
        if (sql.includes('from "public"."ugr_lineage_events"')) {
          return { rows: responses.get('lineage_events') ?? [] };
        }
        if (sql.includes('from "public"."ugr_organisms"')) {
          return { rows: responses.get('organisms') ?? [] };
        }
        return { rows: [] };
      },
    };

    const adapter = new SqlPostgresUgrAdapter(runner);

    expect(await adapter.fetch_all_glyphs()).toEqual([
      {
        glyph_id: 'glyph-1',
        symbol: '◇',
        role: 'LAW_RULE',
        embedding: [1, 2],
      },
    ]);
    expect(await adapter.fetch_all_artifacts()).toEqual([
      {
        artifact_id: 'artifact-1',
        type: 'rule',
        domain: 'law',
        text: 'Evidence first.',
        conditions: { objective: 'test' },
      },
    ]);
    expect(await adapter.fetch_all_lineage()).toEqual([
      {
        event_id: 'event-1',
        world_id: 'world-1',
        experiment_id: 'exp-1',
        decision: 'approve',
        score: 0.8,
        outcome: { result: 'ok' },
        hindsight_score: 0.9,
        timestamp: 1,
      },
    ]);
    expect(await adapter.fetch_all_organisms()).toEqual([
      {
        organism_id: 'org-1',
        worlds: ['world-1'],
        mandala_nodes: [{ node_id: 'node-1' }],
        glyphs: [
          {
            glyph_id: 'glyph-1',
            symbol: '◇',
            role: 'LAW_RULE',
            embedding: [1, 2],
          },
        ],
        risk: { drift: 0.1 },
      },
    ]);

    await adapter.upsert_glyph({ glyph_id: 'glyph-2', symbol: '◉', role: 'MED_PROTOCOL', embedding: [3, 4] });
    await adapter.upsert_artifact({
      artifact_id: 'artifact-2',
      type: 'contract',
      domain: 'medicine',
      text: 'Protocol.',
      conditions: { objective: 'write' },
    });
    await adapter.insert_lineage_event({
      event_id: 'event-2',
      world_id: 'world-2',
      experiment_id: 'exp-2',
      decision: 'reject',
      score: -0.4,
      outcome: { result: 'fail' },
      hindsight_score: -0.2,
      timestamp: 2,
    });
    await adapter.upsert_organism({
      organism_id: 'org-2',
      worlds: ['world-2'],
      mandala_nodes: [{ node_id: 'node-2' }],
      glyphs: [],
      risk: { drift: 0.2 },
    });

    expect(calls.some((call) => call.sql.includes('insert into "public"."ugr_glyphs"'))).toBe(true);
    expect(calls.some((call) => call.sql.includes('insert into "public"."ugr_artifacts"'))).toBe(true);
    expect(calls.some((call) => call.sql.includes('insert into "public"."ugr_lineage_events"'))).toBe(true);
    expect(calls.some((call) => call.sql.includes('insert into "public"."ugr_organisms"'))).toBe(true);
  });
});
