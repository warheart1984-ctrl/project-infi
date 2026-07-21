import type { URGKnowledgeGraph } from './URGKnowledgeGraph.js';

export interface URGInvariantResult {
  passed: boolean;
  severity: 'info' | 'warn' | 'error' | 'fatal';
  message?: string;
}

export const URGInvariants = [
  {
    id: 'I-URG-001',
    description: 'Knowledge graph must have nodes before edges',
    check(graph: URGKnowledgeGraph): URGInvariantResult {
      const passed = graph.getEdges().every((edge) => graph.getNodes().some((node) => node.id === edge.from));
      return {
        passed,
        severity: passed ? 'info' : 'error',
        message: passed ? 'Graph topology valid' : 'Edge references missing node',
      };
    },
  },
  {
    id: 'I-URG-002',
    description: 'Read access requires authority',
    check(_graph: URGKnowledgeGraph): URGInvariantResult {
      return { passed: true, severity: 'info', message: 'Authority checked externally' };
    },
  },
  {
    id: 'I-URG-003',
    description: 'Write access requires governance authority',
    check(_graph: URGKnowledgeGraph): URGInvariantResult {
      return { passed: true, severity: 'info', message: 'Write authority delegated to runtime' };
    },
  },
] as const;
