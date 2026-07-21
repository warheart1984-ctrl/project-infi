import { randomUUID } from 'node:crypto';

import { TriCoreBus, type TriCoreMessage } from '@aaes-os/tri-core-protocol';

import { URGKnowledgeGraph } from './URGKnowledgeGraph.js';
import { URGKnowledgeAuthority } from './URGKnowledgeAuthority.js';

export interface URGRuntimeOptions {
  bus?: TriCoreBus;
}

export class URGRuntime {
  private readonly graph = new URGKnowledgeGraph();
  private readonly authority = new URGKnowledgeAuthority();

  constructor(private readonly options: URGRuntimeOptions = {}) {}

  private get bus(): TriCoreBus {
    return this.options.bus ?? new TriCoreBus();
  }

  writeKnowledge(label: string, payload: unknown): TriCoreMessage | null {
    if (!this.authority.canWrite('runtime')) {
      throw new Error('Runtime not authorized to write knowledge');
    }
    this.graph.addNode({ id: randomUUID(), label, payload });
    return this.bus.send({
      id: randomUUID(),
      from: 'runtime',
      to: 'governance',
      type: 'URG_WRITE',
      payload: { label, payload },
      timestamp: Date.now(),
    });
  }

  getGraph(): URGKnowledgeGraph {
    return this.graph;
  }
}
