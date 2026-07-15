import { randomUUID } from 'node:crypto';

import neo4j, { type Driver } from 'neo4j-driver';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';

import { createUgrNeo4jAdapter, createUgrNeo4jDriver } from '../drivers/neo4j.js';
import type { Artifact, Glyph, LineageEvent, Organism } from '../models.js';

const shouldRunIntegration =
  process.env.UGR_INTEGRATION === '1' &&
  Boolean(process.env.UGR_NEO4J_URI) &&
  Boolean(process.env.UGR_NEO4J_USERNAME) &&
  Boolean(process.env.UGR_NEO4J_PASSWORD);

const describeIf = shouldRunIntegration ? describe : describe.skip;

describeIf('live Neo4j UGR adapter', () => {
  const uri = process.env.UGR_NEO4J_URI ?? '';
  const username = process.env.UGR_NEO4J_USERNAME ?? '';
  const password = process.env.UGR_NEO4J_PASSWORD ?? '';
  const database = process.env.UGR_NEO4J_DATABASE ?? 'neo4j';
  const labelPrefix = 'UGR_';
  const worldId = `world-live-${process.pid}-${randomUUID().replace(/-/g, '').slice(0, 10)}`;
  const artifactId = `artifact-live-${process.pid}-${randomUUID().replace(/-/g, '').slice(0, 10)}`;
  const eventId = `event-live-${process.pid}-${randomUUID().replace(/-/g, '').slice(0, 10)}`;
  const organismId = `organism-live-${process.pid}-${randomUUID().replace(/-/g, '').slice(0, 10)}`;

  let driver: Driver;
  let adapter: ReturnType<typeof createUgrNeo4jAdapter>;

  beforeAll(async () => {
    driver = createUgrNeo4jDriver(uri, neo4j.auth.basic(username, password));
    adapter = createUgrNeo4jAdapter(driver, { database, labelPrefix });
    await adapter.bootstrap();
    await runCypher(
      `MERGE (world:${labelPrefix}World {world_id: $world_id})
       SET world.name = $name, world.kind = 'world'`,
      { world_id: worldId, name: 'Live Neo4j World' },
    );
  });

  afterAll(async () => {
    try {
      await runCypher(
        `MATCH (n)
         WHERE n.world_id = $world_id
            OR n.artifact_id = $artifact_id
            OR n.event_id = $event_id
            OR n.organism_id = $organism_id
         DETACH DELETE n`,
        {
          world_id: worldId,
          artifact_id: artifactId,
          event_id: eventId,
          organism_id: organismId,
        },
      );
    } finally {
      await driver.close();
    }
  });

  it('round-trips graph records through a live database', async () => {
    const glyph: Glyph = {
      glyph_id: `glyph-${worldId}`,
      symbol: '◇',
      role: 'LAW_RULE',
      embedding: [0.25, 0.75],
    };
    const artifact: Artifact = {
      artifact_id: artifactId,
      type: 'rule',
      domain: 'law',
      text: 'No decision without evidence.',
      conditions: { world_id: worldId },
    };
    const event: LineageEvent = {
      event_id: eventId,
      world_id: worldId,
      experiment_id: 'exp-live-neo4j',
      decision: 'approve',
      score: 0.92,
      outcome: { evidence: true },
      hindsight_score: 0.95,
      timestamp: 1,
    };
    const organism: Organism = {
      organism_id: organismId,
      worlds: [worldId],
      mandala_nodes: [{ node_id: 'node-live-1' }],
      glyphs: [glyph],
      risk: { drift: 0.05 },
    };

    await adapter.registerGlyph(glyph);
    await adapter.registerArtifact(artifact);
    await adapter.registerEvent(event);
    await adapter.registerOrganism(organism);

    await runCypher(
      `MATCH (world:${labelPrefix}World {world_id: $world_id})
       MATCH (artifact:${labelPrefix}Artifact {artifact_id: $artifact_id})
       MERGE (world)-[:RELATED_TO]->(artifact)`,
      { world_id: worldId, artifact_id: artifactId },
    );

    await adapter.link_event_to_world(event.event_id, worldId);

    const lineageGraph = await adapter.get_lineage_graph(worldId);
    const relatedArtifacts = await adapter.query_related_artifacts(worldId);

    expect(lineageGraph.nodes.some((node) => node.id === worldId && node.kind === 'world')).toBe(true);
    expect(lineageGraph.edges.map((edge) => edge.relation)).toEqual(
      expect.arrayContaining(['CAUSES', 'RELATED_TO']),
    );
    expect(relatedArtifacts).toEqual([artifact]);
  });
});

async function runCypher(cypher: string, params: Record<string, unknown>): Promise<void> {
  if (!driver) {
    throw new Error('Neo4j driver is not initialized');
  }
  const session = driver.session({ database });
  try {
    await session.run(cypher, params);
  } finally {
    await session.close();
  }
}
