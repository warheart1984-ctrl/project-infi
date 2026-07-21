import type { Artifact, Glyph, LineageEvent, Organism, UgrJsonValue } from '../models.js';
import type { UgrGraph, UgrGraphEdge, UgrGraphNode, UgrGraphNodeKind } from '../storage/graph.js';
import type { UgrNeo4jAdapter } from '../adapters.js';

export interface UgrNeo4jQueryResult {
  records: readonly Record<string, unknown>[];
}

export interface UgrNeo4jQueryRunner {
  run(cypher: string, params?: Record<string, unknown>): Promise<UgrNeo4jQueryResult>;
}

export interface UgrNeo4jAdapterOptions {
  database?: string;
  labelPrefix?: string;
}

const DEFAULT_OPTIONS: Required<UgrNeo4jAdapterOptions> = {
  database: 'neo4j',
  labelPrefix: 'UGR_',
};

export function createUgrNeo4jSchemaStatements(options: UgrNeo4jAdapterOptions = {}): readonly string[] {
  const config = resolveOptions(options);
  return [
    `CREATE CONSTRAINT ${constraintName(config, 'world_id')} IF NOT EXISTS FOR (n:${label(config, 'World')}) REQUIRE n.world_id IS UNIQUE;`,
    `CREATE CONSTRAINT ${constraintName(config, 'organism_id')} IF NOT EXISTS FOR (n:${label(config, 'Organism')}) REQUIRE n.organism_id IS UNIQUE;`,
    `CREATE CONSTRAINT ${constraintName(config, 'glyph_id')} IF NOT EXISTS FOR (n:${label(config, 'Glyph')}) REQUIRE n.glyph_id IS UNIQUE;`,
    `CREATE CONSTRAINT ${constraintName(config, 'artifact_id')} IF NOT EXISTS FOR (n:${label(config, 'Artifact')}) REQUIRE n.artifact_id IS UNIQUE;`,
    `CREATE CONSTRAINT ${constraintName(config, 'event_id')} IF NOT EXISTS FOR (n:${label(config, 'Event')}) REQUIRE n.event_id IS UNIQUE;`,
  ];
}

export class CypherNeo4jUgrAdapter implements UgrNeo4jAdapter {
  constructor(
    private readonly runner: UgrNeo4jQueryRunner,
    private readonly options: UgrNeo4jAdapterOptions = {},
  ) {}

  async bootstrap(): Promise<void> {
    for (const statement of createUgrNeo4jSchemaStatements(this.options)) {
      await this.runner.run(statement);
    }
  }

  async get_lineage_graph(world_id: string): Promise<UgrGraph> {
    const rows = (await this.runner
      .run(
        `MATCH (world:${label(resolveOptions(this.options), 'World')} {world_id: $world_id})
         OPTIONAL MATCH (world)-[edge]-(node)
         RETURN world, collect(DISTINCT node) AS nodes, collect(DISTINCT edge) AS edges`,
        { world_id },
      )
    ).records;
    const row = rows[0];
    if (!row) {
      return { nodes: [], edges: [] };
    }
    return {
      nodes: normalizeNodes(row.nodes),
      edges: normalizeEdges(row.edges),
    };
  }

  async link_event_to_world(event_id: string, world_id: string): Promise<void> {
    await this.runner.run(
      `MATCH (event:${label(resolveOptions(this.options), 'Event')} {event_id: $event_id})
       MATCH (world:${label(resolveOptions(this.options), 'World')} {world_id: $world_id})
       MERGE (event)-[:CAUSES]->(world)`,
      { event_id, world_id },
    );
  }

  async link_organism_fusion(org1_id: string, org2_id: string, fused_id: string): Promise<void> {
    await this.runner.run(
      `MATCH (org1:${label(resolveOptions(this.options), 'Organism')} {organism_id: $org1_id})
       MATCH (org2:${label(resolveOptions(this.options), 'Organism')} {organism_id: $org2_id})
       MATCH (fused:${label(resolveOptions(this.options), 'Organism')} {organism_id: $fused_id})
       MERGE (org1)-[:MERGED_INTO]->(fused)
       MERGE (org2)-[:MERGED_INTO]->(fused)`,
      { org1_id, org2_id, fused_id },
    );
  }

  async query_related_artifacts(world_id: string): Promise<Artifact[]> {
    return (await this.runner
      .run(
        `MATCH (world:${label(resolveOptions(this.options), 'World')} {world_id: $world_id})-[:CAUSES|RELATED_TO|USES_RULE|PROMOTED_BY]-(artifact:${label(resolveOptions(this.options), 'Artifact')})
         RETURN artifact ORDER BY artifact.artifact_id`,
        { world_id },
      )
      ).records.map((record) => normalizeArtifact(record.artifact));
  }

  async registerGlyph(glyph: Glyph): Promise<void> {
    await this.runner.run(
      `MERGE (glyph:${label(resolveOptions(this.options), 'Glyph')} {glyph_id: $glyph_id})
       SET glyph.symbol = $symbol, glyph.role = $role, glyph.embedding = $embedding`,
      { glyph_id: glyph.glyph_id, symbol: glyph.symbol, role: glyph.role, embedding: glyph.embedding },
    );
  }

  async registerArtifact(artifact: Artifact): Promise<void> {
    await this.runner.run(
      `MERGE (artifact:${label(resolveOptions(this.options), 'Artifact')} {artifact_id: $artifact_id})
       SET artifact.type = $type, artifact.domain = $domain, artifact.text = $text, artifact.conditions = $conditions`,
      {
        artifact_id: artifact.artifact_id,
        type: artifact.type,
        domain: artifact.domain,
        text: artifact.text,
        conditions: artifact.conditions,
      },
    );
  }

  async registerEvent(event: LineageEvent): Promise<void> {
    await this.runner.run(
      `MERGE (event:${label(resolveOptions(this.options), 'Event')} {event_id: $event_id})
       SET event.world_id = $world_id, event.experiment_id = $experiment_id, event.decision = $decision, event.score = $score, event.outcome = $outcome, event.hindsight_score = $hindsight_score, event.timestamp = $timestamp`,
      {
        event_id: event.event_id,
        world_id: event.world_id,
        experiment_id: event.experiment_id,
        decision: event.decision,
        score: event.score,
        outcome: event.outcome,
        hindsight_score: event.hindsight_score,
        timestamp: event.timestamp,
      },
    );
  }

  async registerOrganism(organism: Organism): Promise<void> {
    await this.runner.run(
      `MERGE (organism:${label(resolveOptions(this.options), 'Organism')} {organism_id: $organism_id})
       SET organism.worlds = $worlds, organism.mandala_nodes = $mandala_nodes, organism.glyphs = $glyphs, organism.risk = $risk`,
      {
        organism_id: organism.organism_id,
        worlds: organism.worlds,
        mandala_nodes: organism.mandala_nodes,
        glyphs: organism.glyphs,
        risk: organism.risk,
      },
    );
  }
}

function normalizeNodes(value: unknown): readonly UgrGraphNode[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .map((node) => normalizeNode(node))
    .filter((node): node is UgrGraphNode => node !== undefined);
}

function normalizeEdges(value: unknown): readonly UgrGraphEdge[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .map((edge) => normalizeEdge(edge))
    .filter((edge): edge is UgrGraphEdge => edge !== undefined);
}

function normalizeNode(value: unknown): UgrGraphNode | undefined {
  if (!value || typeof value !== 'object') {
    return undefined;
  }
  const record = value as Record<string, unknown>;
  const properties = extractProperties(record);
  const id =
    properties.id ??
    properties.world_id ??
    properties.organism_id ??
    properties.glyph_id ??
    properties.artifact_id ??
    properties.event_id ??
    record.id ??
    record.world_id ??
    record.organism_id ??
    record.glyph_id ??
    record.artifact_id ??
    record.event_id;
  const kind = normalizeNodeKind(record.kind ?? properties.kind ?? record.labels);
  if (!id || !kind) {
    return undefined;
  }
  return {
    id: String(id),
    kind,
    metadata: normalizeRecord(record.metadata ?? properties ?? record),
  };
}

function normalizeEdge(value: unknown): UgrGraphEdge | undefined {
  if (!value || typeof value !== 'object') {
    return undefined;
  }
  const record = value as Record<string, unknown>;
  const relation = record.relation ?? record.type;
  const from =
    record.from ??
    record.startNodeElementId ??
    (record.start && typeof record.start === 'object' ? (record.start as Record<string, unknown>).elementId : undefined) ??
    record.source;
  const to =
    record.to ??
    record.endNodeElementId ??
    (record.end && typeof record.end === 'object' ? (record.end as Record<string, unknown>).elementId : undefined) ??
    record.target;
  if (!from || !to || !relation) {
    return undefined;
  }
  return {
    from: String(from),
    to: String(to),
    relation: String(relation) as UgrGraphEdge['relation'],
  };
}

function normalizeArtifact(value: unknown): Artifact {
  if (!value || typeof value !== 'object') {
    throw new Error('Expected Neo4j artifact record');
  }
  const record = value as Record<string, unknown>;
  const properties = extractProperties(record);
  return {
    artifact_id: String(properties.artifact_id ?? record.artifact_id),
    type: String(properties.type ?? record.type),
    domain: String(properties.domain ?? record.domain),
    text: String(properties.text ?? record.text),
    conditions: normalizeRecord(properties.conditions ?? record.conditions),
  };
}

function normalizeNodeKind(value: unknown): UgrGraphNodeKind | undefined {
  if (Array.isArray(value)) {
    for (const label of value) {
      const kind = normalizeNodeKind(label);
      if (kind) {
        return kind;
      }
    }
    return undefined;
  }

  const kindValue = String(value ?? '').toLowerCase();
  const stripped = kindValue.startsWith('ugr_') ? kindValue.slice(4) : kindValue;
  const kind = stripped.replace(/^worlds?$/, 'world');
  switch (kind) {
    case 'world':
    case 'organism':
    case 'glyph':
    case 'artifact':
    case 'event':
      return kind;
    default:
      return undefined;
  }
}

function normalizeRecord(value: unknown): Record<string, UgrJsonValue> {
  if (value && typeof value === 'object' && !Array.isArray(value)) {
    return value as Record<string, UgrJsonValue>;
  }
  throw new Error('Expected record-like value from Neo4j');
}

function extractProperties(record: Record<string, unknown>): Record<string, unknown> {
  const properties = record.properties;
  if (properties && typeof properties === 'object' && !Array.isArray(properties)) {
    return properties as Record<string, unknown>;
  }
  return record;
}

function resolveOptions(options: UgrNeo4jAdapterOptions): Required<UgrNeo4jAdapterOptions> {
  return {
    database: options.database ?? DEFAULT_OPTIONS.database,
    labelPrefix: options.labelPrefix ?? DEFAULT_OPTIONS.labelPrefix,
  };
}

function label(options: Required<UgrNeo4jAdapterOptions>, name: string): string {
  return `${options.labelPrefix}${name}`;
}

function constraintName(options: Required<UgrNeo4jAdapterOptions>, name: string): string {
  return `${options.labelPrefix.toLowerCase()}_${name}`;
}
