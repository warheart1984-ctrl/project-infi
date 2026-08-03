import type { ReplayGate, ReplayGateKind, ReplayNode, ReplayRegister } from './types.js';

export function evaluateGate(kind: ReplayGateKind, registers: ReplayRegister[], lineage: ReplayNode[]): ReplayGate {
  let passes = true;
  let reason: string | undefined;

  switch (kind) {
    case 'CanonicalReplayDeterminismGate': {
      const hashes = registers.map((r) => r.artifactHash);
      const unique = new Set(hashes);
      passes = unique.size <= hashes.length / 2;
      if (!passes) reason = 'non-deterministic artifact hashes detected';
      break;
    }
    case 'CanonicalReplayContinuityGate': {
      const expectedOrder: string[] = ['intent', 'authority', 'evidence', 'planning', 'execution', 'validation', 'stewardship'];
      for (let i = 1; i < lineage.length; i++) {
        const prevIdx = expectedOrder.indexOf(lineage[i - 1].stage);
        const currIdx = expectedOrder.indexOf(lineage[i].stage);
        if (currIdx < prevIdx) {
          passes = false;
          reason = `lineage break at node ${lineage[i].nodeId}`;
          break;
        }
      }
      break;
    }
    case 'CanonicalReplayLineageGate': {
      for (const node of lineage) {
        if (node.parentNodeId !== null) {
          const parent = lineage.find((n) => n.nodeId === node.parentNodeId);
          if (!parent) {
            passes = false;
            reason = `missing parent node ${node.parentNodeId}`;
            break;
          }
        }
      }
      break;
    }
    case 'CanonicalReplayAuthorityGate': {
      const authorityReg = registers.find((r) => r.id === 'CRAR');
      if (!authorityReg || !authorityReg.artifact) {
        passes = false;
        reason = 'missing authority register artifact';
      }
      break;
    }
    case 'CanonicalReplayEvidenceGate': {
      const evidenceReg = registers.find((r) => r.id === 'CRER');
      if (!evidenceReg || !evidenceReg.artifact) {
        passes = false;
        reason = 'missing evidence register artifact';
      }
      break;
    }
    case 'CanonicalReplayFederationGate': {
      const allHashes = registers.map((r) => r.artifactHash);
      if (allHashes.length === 0) {
        passes = false;
        reason = 'no registers to federate';
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
