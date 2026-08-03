import type { TemporalGate, TemporalGateKind, TemporalRegister, TemporalReplayNode } from './types.js';

export function evaluateTemporalGate(
  kind: TemporalGateKind,
  registers: TemporalRegister[],
  lineage: TemporalReplayNode[],
): TemporalGate {
  let passes = true;
  let reason: string | undefined;

  switch (kind) {
    case 'TemporalOrderGate': {
      const sorted = [...registers].sort((a, b) => a.temporalOrder - b.temporalOrder);
      for (let i = 1; i < sorted.length; i++) {
        if (sorted[i].temporalOrder <= sorted[i - 1].temporalOrder) {
          passes = false;
          reason = 'temporal ordering violation detected';
          break;
        }
      }
      break;
    }
    case 'TemporalContinuityGate': {
      const expectedOrder = ['intent', 'authority', 'evidence', 'planning', 'execution', 'validation', 'stewardship'];
      for (let i = 1; i < lineage.length; i++) {
        const prevIdx = expectedOrder.indexOf(lineage[i - 1].stage);
        const currIdx = expectedOrder.indexOf(lineage[i].stage);
        if (currIdx < prevIdx) {
          passes = false;
          reason = `temporal continuity break at node ${lineage[i].nodeId}`;
          break;
        }
      }
      break;
    }
    case 'TemporalReplayGate': {
      for (const [i, node] of lineage.entries()) {
        if (node.parentNodeId !== null && i > 0) {
          const parent = lineage.find((n) => n.nodeId === node.parentNodeId);
          if (!parent) {
            passes = false;
            reason = `missing parent in temporal replay at node ${node.nodeId}`;
            break;
          }
        }
      }
      break;
    }
    case 'TemporalLineageGate': {
      const seen = new Set<string>();
      for (const node of lineage) {
        if (seen.has(node.nodeId)) {
          passes = false;
          reason = `duplicate node in temporal lineage: ${node.nodeId}`;
          break;
        }
        seen.add(node.nodeId);
      }
      break;
    }
    case 'TemporalAuthorityGate': {
      const authReg = registers.find((r) => r.id === 'CTAR');
      if (!authReg || !authReg.artifact) {
        passes = false;
        reason = 'missing authority register for temporal authority gate';
      }
      break;
    }
    case 'TemporalFederationGate': {
      const allHashes = registers.map((r) => r.artifactHash);
      const unique = new Set(allHashes);
      if (unique.size !== allHashes.length) {
        passes = false;
        reason = 'duplicate temporal hashes during federation check';
      }
      break;
    }
  }

  return {
    kind,
    passes,
    evaluatedAt: Date.now(),
    reason,
  };
}
