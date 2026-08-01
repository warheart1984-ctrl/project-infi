import { randomUUID } from 'node:crypto';
import type {
  AuthorityAnchor,
  AuthorityContinuityResult,
  AuthorityFederationPort,
  AuthorityGateKind,
  AuthorityReconstruction,
  AuthorityRegister,
  AuthorityReplayNode,
  AuthorityStage,
  CAMC,
} from './types.js';
import { createAuthorityRegister } from './types.js';
import { evaluateAuthorityGate } from './gates.js';

export class CanonicalAuthorityMatrix {
  private readonly registers = new Map<string, AuthorityRegister>();
  private readonly replayNodes: AuthorityReplayNode[] = [];
  private readonly anchors: AuthorityAnchor[] = [];
  private readonly federationPorts = new Map<string, AuthorityFederationPort>();

  createCell(stage: string, artifact: unknown): CAMC {
    const register = createAuthorityRegister(stage as AuthorityStage, artifact);
    this.registers.set(register.id, register);
    const gate = evaluateAuthorityGate('AuthorityLegitimacyGate', [register], this.replayNodes);
    const anchor: AuthorityAnchor = {
      coordinate: `${stage}:${register.artifactHash}`,
      stage: register.stage,
      anchoredAt: Date.now(),
      authorityHash: register.artifactHash,
    };
    this.anchors.push(anchor);
    const replayNode: AuthorityReplayNode = {
      nodeId: randomUUID(),
      stage: register.stage,
      registerSnapshot: { [register.id]: register.artifactHash } as Record<string, string>,
      gatesPassed: [],
      parentNodeId: this.replayNodes.length > 0 ? this.replayNodes[this.replayNodes.length - 1].nodeId : null,
      replayedAt: Date.now(),
    };
    this.replayNodes.push(replayNode);
    return { register, gate, anchor, replayNode, federationPort: null };
  }

  evaluateAllGates(registerIds?: string[]): { gate: ReturnType<typeof evaluateAuthorityGate>; registerId: string }[] {
    const targets = registerIds
      ? registerIds.map((id) => this.registers.get(id)).filter(Boolean) as AuthorityRegister[]
      : [...this.registers.values()];
    const kinds: AuthorityGateKind[] = [
      'AuthorityLegitimacyGate',
      'AuthorityContinuityGate',
      'AuthorityReplayGate',
      'AuthorityLineageGate',
      'AuthorityEvidenceGate',
      'AuthorityFederationGate',
    ];
    return targets.flatMap((reg) =>
      kinds.map((kind) => ({
        registerId: reg.id,
        gate: evaluateAuthorityGate(kind, [reg], this.replayNodes),
      })),
    );
  }

  reconstructAuthority(fromNodeId?: string): AuthorityReconstruction {
    const startIdx = fromNodeId
      ? this.replayNodes.findIndex((n) => n.nodeId === fromNodeId)
      : 0;
    const lineage = startIdx >= 0 ? this.replayNodes.slice(startIdx) : [];
    return {
      nodeId: randomUUID(),
      reconstructedLineage: lineage,
      isDeterministic: lineage.every(
        (n, i) => i === 0 || n.parentNodeId === this.replayNodes[this.replayNodes.indexOf(n) - 1]?.nodeId,
      ),
      completedAt: Date.now(),
    };
  }

  checkContinuity(): AuthorityContinuityResult {
    const expectedOrder = ['intent', 'authority', 'evidence', 'planning', 'execution', 'validation', 'stewardship'];
    for (let i = 1; i < this.replayNodes.length; i++) {
      const prevIdx = expectedOrder.indexOf(this.replayNodes[i - 1].stage);
      const currIdx = expectedOrder.indexOf(this.replayNodes[i].stage);
      if (currIdx < prevIdx) {
        return { isContinuous: false, breakAtIndex: i, checkedNodes: this.replayNodes.length };
      }
    }
    return { isContinuous: true, breakAtIndex: null, checkedNodes: this.replayNodes.length };
  }

  synchronizeFederation(worldId: string): void {
    this.federationPorts.set(worldId, {
      worldId,
      lastSyncTimestamp: Date.now(),
      remoteAuthorityHash: '',
    });
  }

  getRegisters(): AuthorityRegister[] {
    return [...this.registers.values()];
  }

  getReplayNodes(): AuthorityReplayNode[] {
    return [...this.replayNodes];
  }

  getAnchors(): AuthorityAnchor[] {
    return [...this.anchors];
  }

  getFederationPorts(): AuthorityFederationPort[] {
    return [...this.federationPorts.values()];
  }
}
