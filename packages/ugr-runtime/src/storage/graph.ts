import { cloneArtifact, cloneGlyph, cloneLineageEvent, cloneOrganism, type Artifact, type Glyph, type LineageEvent, type Organism } from '../models.js';
import type { UgrNeo4jAdapter } from '../adapters.js';

export type UgrGraphNodeKind = 'world' | 'organism' | 'glyph' | 'artifact' | 'event';

export type UgrGraphEdgeRelation =
  | 'EVOLVES_FROM'
  | 'USES_RULE'
  | 'MERGED_INTO'
  | 'CAUSES'
  | 'PROMOTED_BY'
  | 'RELATED_TO';

export interface UgrGraphNode {
  id: string;
  kind: UgrGraphNodeKind;
  metadata: Record<string, unknown>;
}

export interface UgrGraphEdge {
  from: string;
  to: string;
  relation: UgrGraphEdgeRelation;
}

export interface UgrGraph {
  nodes: readonly UgrGraphNode[];
  edges: readonly UgrGraphEdge[];
}

export interface UgrGraphStorage {
  get_lineage_graph(world_id: string): Promise<UgrGraph>;
  link_event_to_world(event_id: string, world_id: string): Promise<void>;
  link_organism_fusion(org1_id: string, org2_id: string, fused_id: string): Promise<void>;
  query_related_artifacts(world_id: string): Promise<Artifact[]>;
  registerGlyph(glyph: Glyph): Promise<void>;
  registerArtifact(artifact: Artifact): Promise<void>;
  registerEvent(event: LineageEvent): Promise<void>;
  registerOrganism(organism: Organism): Promise<void>;
}

export interface UgrGraphStorageOptions {
  adapter?: UgrNeo4jAdapter;
}

export class InMemoryUgrGraphStorage implements UgrGraphStorage {
  private readonly nodes = new Map<string, UgrGraphNode>();
  private readonly edges: UgrGraphEdge[] = [];
  private readonly artifacts = new Map<string, Artifact>();
  private readonly events = new Map<string, LineageEvent>();
  private readonly adapter?: UgrNeo4jAdapter;

  constructor(options: UgrGraphStorageOptions = {}) {
    this.adapter = options.adapter;
  }

  async get_lineage_graph(world_id: string): Promise<UgrGraph> {
    return (await this.adapter?.get_lineage_graph(world_id)) ?? this.buildLineageGraph(world_id);
  }

  async link_event_to_world(event_id: string, world_id: string): Promise<void> {
    this.edges.push({ from: event_id, to: world_id, relation: 'CAUSES' });
    await this.adapter?.link_event_to_world(event_id, world_id);
  }

  async link_organism_fusion(org1_id: string, org2_id: string, fused_id: string): Promise<void> {
    this.edges.push({ from: org1_id, to: fused_id, relation: 'MERGED_INTO' });
    this.edges.push({ from: org2_id, to: fused_id, relation: 'MERGED_INTO' });
    await this.adapter?.link_organism_fusion(org1_id, org2_id, fused_id);
  }

  async query_related_artifacts(world_id: string): Promise<Artifact[]> {
    return (await this.adapter?.query_related_artifacts(world_id)) ?? this.buildRelatedArtifacts(world_id);
  }

  async registerGlyph(glyph: Glyph): Promise<void> {
    this.nodes.set(glyph.glyph_id, { id: glyph.glyph_id, kind: 'glyph', metadata: { glyph: cloneGlyph(glyph) } });
    await this.adapter?.registerGlyph(cloneGlyph(glyph));
  }

  async registerArtifact(artifact: Artifact): Promise<void> {
    this.artifacts.set(artifact.artifact_id, cloneArtifact(artifact));
    this.nodes.set(artifact.artifact_id, { id: artifact.artifact_id, kind: 'artifact', metadata: { artifact: cloneArtifact(artifact) } });
    await this.adapter?.registerArtifact(cloneArtifact(artifact));
  }

  async registerEvent(event: LineageEvent): Promise<void> {
    this.events.set(event.event_id, cloneLineageEvent(event));
    this.nodes.set(event.event_id, { id: event.event_id, kind: 'event', metadata: { event: cloneLineageEvent(event) } });
    await this.adapter?.registerEvent(cloneLineageEvent(event));
  }

  async registerOrganism(organism: Organism): Promise<void> {
    this.nodes.set(organism.organism_id, { id: organism.organism_id, kind: 'organism', metadata: { organism: cloneOrganism(organism) } });
    await this.adapter?.registerOrganism(cloneOrganism(organism));
  }

  private buildLineageGraph(world_id: string): UgrGraph {
    const nodes = [...this.nodes.values()].filter((node) => node.id === world_id || this.edges.some((edge) => edge.from === node.id || edge.to === node.id));
    const edges = this.edges.filter((edge) => edge.from === world_id || edge.to === world_id || edge.from.startsWith(`${world_id}:`) || edge.to.startsWith(`${world_id}:`));
    return {
      nodes,
      edges,
    };
  }

  private buildRelatedArtifacts(world_id: string): Artifact[] {
    const relatedIds = new Set(
      this.edges
        .filter((edge) => edge.from === world_id || edge.to === world_id)
        .flatMap((edge) => [edge.from, edge.to]),
    );
    return [...this.artifacts.values()]
      .filter((artifact) => relatedIds.has(artifact.artifact_id) || artifact.conditions.world_id === world_id)
      .map(cloneArtifact);
  }
}
