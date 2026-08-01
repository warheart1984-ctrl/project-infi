import type { StewardshipGate, StewardshipGateKind, StewardshipRegister, StewardshipReplayNode } from './types.js';

export function evaluateStewardshipGate(
  kind: StewardshipGateKind,
  registers: StewardshipRegister[],
  lineage: StewardshipReplayNode[],
): StewardshipGate {
  let passes = true;
  let reason: string | undefined;

  switch (kind) {
    case 'StewardshipContinuityGate': {
      const expectedOrder = ['intent', 'authority', 'evidence', 'planning', 'execution', 'validation', 'stewardship'];
      for (let i = 1; i < lineage.length; i++) {
        const prevIdx = expectedOrder.indexOf(lineage[i - 1].stage);
        const currIdx = expectedOrder.indexOf(lineage[i].stage);
        if (currIdx < prevIdx) {
          passes = false;
          reason = `stewardship continuity break at node ${lineage[i].nodeId}`;
          break;
        }
      }
      break;
    }
    case 'StewardshipReplayGate': {
      for (const [i, node] of lineage.entries()) {
        if (node.parentNodeId !== null && i > 0) {
          const parent = lineage.find((n) => n.nodeId === node.parentNodeId);
          if (!parent) {
            passes = false;
            reason = `missing parent in stewardship replay at node ${node.nodeId}`;
            break;
          }
        }
      }
      break;
    }
    case 'StewardshipLineageGate': {
      const seen = new Set<string>();
      for (const node of lineage) {
        if (seen.has(node.nodeId)) {
          passes = false;
          reason = `duplicate node in stewardship lineage: ${node.nodeId}`;
          break;
        }
        seen.add(node.nodeId);
      }
      break;
    }
    case 'StewardshipAuthorityGate': {
      const authReg = registers.find((r) => r.id === 'CSAR');
      if (!authReg || !authReg.artifact) {
        passes = false;
        reason = 'missing authority register for stewardship authority gate';
      }
      break;
    }
    case 'StewardshipEvidenceGate': {
      const evReg = registers.find((r) => r.id === 'CSER');
      if (!evReg || !evReg.artifact) {
        passes = false;
        reason = 'missing evidence register for stewardship evidence gate';
      }
      break;
    }
    case 'StewardshipFederationGate': {
      const allHashes = registers.map((r) => r.artifactHash);
      const unique = new Set(allHashes);
      if (unique.size !== allHashes.length) {
        passes = false;
        reason = 'duplicate stewardship hashes during federation check';
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
