import { randomUUID } from 'node:crypto';

import { Pool } from 'pg';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';

import { createUgrPostgresAdapter } from '../drivers/postgres.js';
import type { Artifact, Glyph, LineageEvent, Organism } from '../models.js';

const shouldRunIntegration = process.env.UGR_INTEGRATION === '1' && Boolean(process.env.UGR_PG_CONNECTION_STRING);

const describeIf = shouldRunIntegration ? describe : describe.skip;

describeIf('live PostgreSQL UGR adapter', () => {
  const connectionString = process.env.UGR_PG_CONNECTION_STRING ?? '';
  const pool = new Pool({ connectionString: connectionString || undefined });
  const schema = `ugr_live_${process.pid}_${randomUUID().replace(/-/g, '').slice(0, 12)}`;
  const adapter = createUgrPostgresAdapter(pool, { schema, tablePrefix: 'ugr_' });

  beforeAll(async () => {
    await adapter.bootstrap();
  });

  afterAll(async () => {
    await pool.query(`drop schema if exists "${schema.replace(/"/g, '""')}" cascade`);
    await pool.end();
  });

  it('round-trips canonical records through a live database', async () => {
    const glyph: Glyph = {
      glyph_id: 'glyph-live-1',
      symbol: '◇',
      role: 'LAW_RULE',
      embedding: [0.25, 0.75],
    };
    const artifact: Artifact = {
      artifact_id: 'artifact-live-1',
      type: 'rule',
      domain: 'law',
      text: 'No decision without evidence.',
      conditions: { world_id: 'world-live-1' },
    };
    const event: LineageEvent = {
      event_id: 'event-live-1',
      world_id: 'world-live-1',
      experiment_id: 'exp-live-1',
      decision: 'approve',
      score: 0.92,
      outcome: { evidence: true },
      hindsight_score: 0.95,
      timestamp: 1,
    };
    const organism: Organism = {
      organism_id: 'organism-live-1',
      worlds: ['world-live-1'],
      mandala_nodes: [{ node_id: 'node-live-1' }],
      glyphs: [glyph],
      risk: { drift: 0.05 },
    };

    await adapter.upsert_glyph(glyph);
    await adapter.upsert_artifact(artifact);
    await adapter.insert_lineage_event(event);
    await adapter.upsert_organism(organism);

    expect(await adapter.fetch_all_glyphs()).toEqual([glyph]);
    expect(await adapter.fetch_artifacts('law')).toEqual([artifact]);
    expect(await adapter.fetch_lineage('world-live-1')).toEqual([event]);
    expect(await adapter.fetch_all_lineage()).toEqual([event]);
    expect(await adapter.fetch_organism('organism-live-1')).toEqual(organism);
    expect(await adapter.fetch_all_organisms()).toEqual([organism]);
  });
});
