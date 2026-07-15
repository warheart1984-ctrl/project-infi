import { describe, expect, it } from 'vitest';

import { CypherNeo4jUgrAdapter, createUgrNeo4jSchemaStatements, type UgrNeo4jQueryRunner } from './neo4j.js';

describe('Neo4j UGR adapter', () => {
  it('emits schema constraints for the UGR graph model', () => {
    const statements = createUgrNeo4jSchemaStatements();

    expect(statements).toEqual(
      expect.arrayContaining([
        expect.stringContaining('FOR (n:UGR_World) REQUIRE n.world_id IS UNIQUE'),
        expect.stringContaining('FOR (n:UGR_Organism) REQUIRE n.organism_id IS UNIQUE'),
        expect.stringContaining('FOR (n:UGR_Glyph) REQUIRE n.glyph_id IS UNIQUE'),
        expect.stringContaining('FOR (n:UGR_Artifact) REQUIRE n.artifact_id IS UNIQUE'),
        expect.stringContaining('FOR (n:UGR_Event) REQUIRE n.event_id IS UNIQUE'),
      ]),
    );
  });

  it('translates graph operations to Cypher calls', async () => {
    const calls: Array<{ cypher: string; params?: Record<string, unknown> }> = [];
    const runner: UgrNeo4jQueryRunner = {
      async run(cypher: string, params?: Record<string, unknown>) {
        calls.push({ cypher, params });
        if (cypher.includes('RETURN world, collect(DISTINCT node) AS nodes, collect(DISTINCT edge) AS edges')) {
          return {
            records: [
              {
                nodes: [
                  { id: 'world-1', kind: 'world', metadata: { world_id: 'world-1' } },
                ],
                edges: [
                  { from: 'event-1', to: 'world-1', relation: 'CAUSES' },
                ],
              },
            ],
          };
        }
        if (cypher.includes('RETURN artifact ORDER BY artifact.artifact_id')) {
          return {
            records: [
              {
                artifact: {
                  artifact_id: 'artifact-1',
                  type: 'rule',
                  domain: 'law',
                  text: 'Evidence first.',
                  conditions: { objective: 'cypher-test' },
                },
              },
            ],
          };
        }
        return { records: [] };
      },
    };

    const adapter = new CypherNeo4jUgrAdapter(runner);

    expect(await adapter.get_lineage_graph('world-1')).toEqual({
      nodes: [{ id: 'world-1', kind: 'world', metadata: { world_id: 'world-1' } }],
      edges: [{ from: 'event-1', to: 'world-1', relation: 'CAUSES' }],
    });
    expect(await adapter.query_related_artifacts('world-1')).toEqual([
      {
        artifact_id: 'artifact-1',
        type: 'rule',
        domain: 'law',
        text: 'Evidence first.',
        conditions: { objective: 'cypher-test' },
      },
    ]);

    await adapter.link_event_to_world('event-2', 'world-2');
    await adapter.link_organism_fusion('org-1', 'org-2', 'org-fused');
    await adapter.registerGlyph({ glyph_id: 'glyph-1', symbol: '◇', role: 'LAW_RULE', embedding: [1, 2] });
    await adapter.registerArtifact({
      artifact_id: 'artifact-2',
      type: 'precedent',
      domain: 'law',
      text: 'Case law.',
      conditions: { objective: 'register' },
    });
    await adapter.registerEvent({
      event_id: 'event-2',
      world_id: 'world-2',
      experiment_id: 'exp-2',
      decision: 'approve',
      score: 1,
      outcome: { result: 'ok' },
      hindsight_score: 1,
      timestamp: 2,
    });
    await adapter.registerOrganism({
      organism_id: 'org-3',
      worlds: ['world-3'],
      mandala_nodes: [{ node_id: 'node-3' }],
      glyphs: [],
      risk: { drift: 0.3 },
    });

    expect(calls.some((call) => call.cypher.includes('MATCH (event:UGR_Event {event_id: $event_id})'))).toBe(true);
    expect(calls.some((call) => call.cypher.includes('MATCH (org1:UGR_Organism {organism_id: $org1_id})'))).toBe(true);
    expect(calls.some((call) => call.cypher.includes('MERGE (glyph:UGR_Glyph {glyph_id: $glyph_id})'))).toBe(true);
    expect(calls.some((call) => call.cypher.includes('MERGE (artifact:UGR_Artifact {artifact_id: $artifact_id})'))).toBe(true);
    expect(calls.some((call) => call.cypher.includes('MERGE (organism:UGR_Organism {organism_id: $organism_id})'))).toBe(true);
  });
});
