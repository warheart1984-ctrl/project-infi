export interface URGNode {
  id: string;
  label: string;
  payload?: unknown;
}

export interface URGEdge {
  from: string;
  to: string;
  label: string;
}

export class URGKnowledgeGraph {
  private readonly nodes = new Map<string, URGNode>();
  private readonly edges: URGEdge[] = [];

  addNode(node: URGNode): URGNode {
    this.nodes.set(node.id, node);
    return node;
  }

  addEdge(edge: URGEdge): URGEdge {
    this.edges.push(edge);
    return edge;
  }

  getNodes(): URGNode[] {
    return [...this.nodes.values()];
  }

  getEdges(): URGEdge[] {
    return [...this.edges];
  }
}
