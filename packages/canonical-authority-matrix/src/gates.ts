import type { AuthorityGate, AuthorityGateKind, AuthorityRegister, AuthorityReplayNode } from './types.js';

export function evaluateAuthorityGate(
  kind: AuthorityGateKind,
  registers: AuthorityRegister[],
  lineage: AuthorityReplayNode[],
): AuthorityGate {
  let passes = true;
  let reason: string | undefined;

  switch (kind) {
    case 'AuthorityLegitimacyGate': {
      const authReg = registers.find((r) => r.id === 'AAR');
      if (!authReg || !authReg.artifact) {
        passes = false;
        reason = 'missing authority register — cannot verify legitimacy';
      }
      break;
    }
    case 'AuthorityContinuityGate': {
      const expectedOrder = ['intent', 'authority', 'evidence', 'planning', 'execution', 'validation', 'stewardship'];
      for (let i = 1; i < lineage.length; i++) {
        const prevIdx = expectedOrder.indexOf(lineage[i - 1].stage);
        const currIdx = expectedOrder.indexOf(lineage[i].stage);
        if (currIdx < prevIdx) {
          passes = false;
          reason = `authority continuity break at node ${lineage[i].nodeId}`;
          break;
        }
      }
      break;
    }
    case 'AuthorityReplayGate': {
      for (const [i, node] of lineage.entries()) {
        if (node.parentNodeId !== null && i > 0) {
          const parent = lineage.find((n) => n.nodeId === node.parentNodeId);
          if (!parent) {
            passes = false;
            reason = `missing parent in replay lineage at node ${node.nodeId}`;
            break;
          }
        }
      }
      break;
    }
    case 'AuthorityLineageGate': {
      const seen = new Set<string>();
      for (const node of lineage) {
        if (seen.has(node.nodeId)) {
          passes = false;
          reason = `duplicate node in authority lineage: ${node.nodeId}`;
          break;
        }
        seen.add(node.nodeId);
      }
      break;
    }
    case 'AuthorityEvidenceGate': {
      const evidenceReg = registers.find((r) => r.id === 'AER');
      if (!evidenceReg || !evidenceReg.artifact) {
        passes = false;
        reason = 'missing evidence register for authority evidence gate';
      }
      break;
    }
    case 'AuthorityFederationGate': {
      const allHashes = registers.map((r) => r.artifactHash);
      const unique = new Set(allHashes);
      if (unique.size !== allHashes.length) {
        passes = false;
        reason = 'duplicate authority hashes detected during federation check';
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
