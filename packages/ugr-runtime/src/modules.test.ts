import { describe, expect, it, vi } from 'vitest';

import type { UgrNeo4jAdapter, UgrPgvectorAdapter, UgrPostgresAdapter } from './adapters.js';
import { cloneArtifact, cloneGlyph, cloneLineageEvent, cloneOrganism, type Artifact, type Embedding, type Glyph, type LineageEvent, type Organism } from './models.js';
import { InMemoryUgrGraphStorage } from './storage/graph.js';
import { InMemoryUgrSqlStorage } from './storage/sql.js';
import { InMemoryUgrVectorStorage } from './storage/vector.js';
import { createUgrRuntimeService } from './runtime.js';

describe('UGR modules', () => {
  it('stores and clones canonical model records', () => {
    const glyph: Glyph = {
      glyph_id: 'glyph-1',
      symbol: '◇',
      role: 'LAW_RULE',
      embedding: [0.1, 0.2],
    };
    const artifact: Artifact = {
      artifact_id: 'artifact-1',
      type: 'rule',
      domain: 'law',
      text: 'No decision without evidence.',
      conditions: { world_id: 'world-1' },
    };
    const event: LineageEvent = {
      event_id: 'event-1',
      world_id: 'world-1',
      experiment_id: 'exp-1',
      decision: 'approve',
      score: 0.9,
      outcome: { result: 'safe' },
      hindsight_score: 0.85,
      timestamp: 1,
    };
    const organism: Organism = {
      organism_id: 'org-1',
      worlds: ['world-1'],
      mandala_nodes: [{ node_id: 'node-1' }],
      glyphs: [glyph],
      risk: { drift: 0.1 },
    };

    expect(cloneGlyph(glyph)).toEqual(glyph);
    expect(cloneArtifact(artifact)).toEqual(artifact);
    expect(cloneLineageEvent(event)).toEqual(event);
    expect(cloneOrganism(organism)).toEqual(organism);
  });

  it('round-trips records through in-memory SQL, graph, and vector storage', async () => {
    const sql = new InMemoryUgrSqlStorage();
    const graph = new InMemoryUgrGraphStorage();
    const vector = new InMemoryUgrVectorStorage();

    const glyph: Glyph = { glyph_id: 'glyph-1', symbol: '◉', role: 'MED_PROTOCOL', embedding: [1, 0] };
    const artifact: Artifact = {
      artifact_id: 'artifact-1',
      type: 'contract',
      domain: 'medicine',
      text: 'Protocol follows evidence.',
      conditions: { world_id: 'world-1' },
    };
    const embedding: Embedding = {
      embedding_id: 'embedding-1',
      vector: [0.9, 0.1],
      metadata: { domain: 'medicine' },
    };
    const event: LineageEvent = {
      event_id: 'event-1',
      world_id: 'world-1',
      experiment_id: 'exp-1',
      decision: 'approve',
      score: 0.7,
      outcome: { efficacy: 0.8 },
      hindsight_score: 0.75,
      timestamp: 2,
    };
    const organism: Organism = {
      organism_id: 'org-1',
      worlds: ['world-1'],
      mandala_nodes: [{ node_id: 'node-1' }],
      glyphs: [glyph],
      risk: { toxicity: 0.2 },
    };

    await sql.upsert_glyph(glyph);
    await sql.upsert_artifact(artifact);
    await sql.insert_lineage_event(event);
    await sql.upsert_organism(organism);
    await graph.registerGlyph(glyph);
    await graph.registerArtifact(artifact);
    await graph.registerEvent(event);
    await graph.registerOrganism(organism);
    await graph.link_event_to_world(event.event_id, event.world_id);
    await vector.store_embedding(embedding);

    expect(await sql.fetch_all_glyphs()).toEqual([glyph]);
    expect(await sql.fetch_artifacts('medicine')).toEqual([artifact]);
    expect(await sql.fetch_lineage('world-1')).toEqual([event]);
    expect(await sql.fetch_organism('org-1')).toEqual(organism);
    expect((await graph.get_lineage_graph('world-1')).edges).toEqual([
      { from: 'event-1', to: 'world-1', relation: 'CAUSES' },
    ]);
    expect(await graph.query_related_artifacts('world-1')).toEqual([artifact]);
    expect(await vector.query_neighbors([1, 0], 1)).toEqual([embedding]);
  });

  it('exposes UGR API routes and HTTP responses', async () => {
    const service = createUgrRuntimeService({ host: '127.0.0.1', port: 0 });
    try {
      const started = await service.start();

      const glyph: Glyph = { glyph_id: 'glyph-1', symbol: '◇', role: 'LAW_RULE', embedding: [0.1, 0.2] };
      await service.api.putGlyph(glyph);

      const health = await fetch(`${started.url}/health`);
      const glyphs = await fetch(`${started.url}/ugr/v1/glyphs`);
      const glyphLookup = await fetch(`${started.url}/ugr/v1/glyphs/glyph-1`);

      expect(service.api.getRoutes()).toEqual(
        expect.arrayContaining([
          expect.objectContaining({ method: 'GET', path: '/ugr/v1/glyphs' }),
          expect.objectContaining({ method: 'GET', path: '/ugr/v1/glyphs/{glyph_id}' }),
          expect.objectContaining({ method: 'POST', path: '/ugr/v1/constitution/artifacts' }),
        ]),
      );
      expect(service.api.getGrpcService()).toEqual(
        expect.arrayContaining([
          expect.objectContaining({ name: 'GetGlyphs' }),
          expect.objectContaining({ name: 'GetOrganism' }),
        ]),
      );
      expect(health.status).toBe(200);
      expect(await health.json()).toEqual({ ok: true });
      expect(await glyphs.json()).toEqual({ glyphs: [glyph] });
      expect(await glyphLookup.json()).toEqual({ glyph });
    } finally {
      await service.stop();
    }
  });

  it('enforces the replay-vs-repeat invariant unless divergence is declared', async () => {
    const service = createUgrRuntimeService();
    const replayCheck = {
      objective: 'compare treatment protocols',
      constitutional_context: {
        domain: 'medicine',
        world_id: 'med-arena-1',
      },
    } as const;

    await service.api.putArtifact({
      artifact_id: 'artifact-replay-1',
      type: 'precedent',
      domain: 'medicine',
      text: 'Replayable protocol comparison result.',
      conditions: {
        objective: replayCheck.objective,
        constitutional_context: replayCheck.constitutional_context,
        replayable_result: true,
        evidence_ids: ['evidence-1'],
      },
    });

    expect(await service.hasReplayableResult(replayCheck)).toBe(true);
    expect(await service.shouldRepeatExperiment(replayCheck)).toEqual({
      has_replayable_result: true,
      should_repeat_experiment: false,
      reason: 'replayable_result_exists',
      matched_source_id: 'artifact-replay-1',
    });
    await expect(service.assertExperimentMayRun(replayCheck)).rejects.toThrow(
      'Replayable result already exists for objective "compare treatment protocols" in the same constitutional context',
    );
    expect(await service.shouldRepeatExperiment({
        ...replayCheck,
        divergence_reason: 'New cohort assumptions and external evidence',
      })).toEqual({
      has_replayable_result: true,
      should_repeat_experiment: true,
      reason: 'declared_divergence',
      matched_source_id: 'artifact-replay-1',
    });
  });

  it('wires explicit PostgreSQL, Neo4j, and pgvector adapters', async () => {
    const postgres: UgrPostgresAdapter = {
      fetch_all_glyphs: () => [],
      fetch_all_artifacts: () => [],
      fetch_all_organisms: () => [],
      fetch_artifacts: () => [],
      fetch_lineage: () => [],
      fetch_all_lineage: () => [],
      fetch_organism: () => undefined,
      upsert_glyph: () => undefined,
      upsert_artifact: () => undefined,
      insert_lineage_event: () => undefined,
      upsert_organism: () => undefined,
    };
    const neo4j: UgrNeo4jAdapter = {
      get_lineage_graph: () => ({ nodes: [], edges: [] }),
      link_event_to_world: () => undefined,
      link_organism_fusion: () => undefined,
      query_related_artifacts: () => [],
      registerGlyph: () => undefined,
      registerArtifact: () => undefined,
      registerEvent: () => undefined,
      registerOrganism: () => undefined,
    };
    const pgvector: UgrPgvectorAdapter = {
      store_embedding: () => undefined,
      query_neighbors: () => [],
      delete_embedding: () => undefined,
    };

    const service = createUgrRuntimeService({
      adapters: {
        postgres,
        neo4j,
        pgvector,
      },
    });

    expect(await service.sql.fetch_all_glyphs()).toEqual([]);
    expect(await service.graph.get_lineage_graph('world-1')).toEqual({ nodes: [], edges: [] });
    expect(await service.vector.query_neighbors([1, 0], 1)).toEqual([]);
  });

  it('invokes the configured shutdown hook when the runtime stops', async () => {
    const shutdown = vi.fn(async () => undefined);
    const service = createUgrRuntimeService({
      shutdown,
    });

    try {
      await service.start();
    } finally {
      await service.stop();
    }

    expect(shutdown).toHaveBeenCalledTimes(1);
  });
});
