import { randomUUID } from 'node:crypto';
import type {
  CSMC,
  StewardshipAnchor,
  StewardshipContinuityResult,
  StewardshipFederationPort,
  StewardshipGateKind,
  StewardshipReconstruction,
  StewardshipRegister,
  StewardshipReplayNode,
  StewardshipStage,
} from './types.js';
import { createStewardshipRegister } from './types.js';
import { evaluateStewardshipGate } from './gates.js';

export class CanonicalStewardshipMatrix {
  private readonly registers = new Map<string, StewardshipRegister>();
  private readonly replayNodes: StewardshipReplayNode[] = [];
  private readonly anchors: StewardshipAnchor[] = [];
  private readonly federationPorts = new Map<string, StewardshipFederationPort>();

  createCell(stage: string, artifact: unknown): CSMC {
    const register = createStewardshipRegister(stage as StewardshipStage, artifact);
    this.registers.set(register.id, register);
    const gate = evaluateStewardshipGate('StewardshipContinuityGate', [register], this.replayNodes);
    const anchor: StewardshipAnchor = {
      coordinate: `${stage}:${register.artifactHash}`,
      stage: register.stage,
      anchoredAt: Date.now(),
      stewardshipHash: register.artifactHash,
    };
    this.anchors.push(anchor);
    const replayNode: StewardshipReplayNode = {
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

  evaluateAllGates(registerIds?: string[]): { gate: ReturnType<typeof evaluateStewardshipGate>; registerId: string }[] {
    const targets = registerIds
      ? registerIds.map((id) => this.registers.get(id)).filter(Boolean) as StewardshipRegister[]
      : [...this.registers.values()];
    const kinds: StewardshipGateKind[] = [
      'StewardshipContinuityGate',
      'StewardshipReplayGate',
      'StewardshipLineageGate',
      'StewardshipAuthorityGate',
      'StewardshipEvidenceGate',
      'StewardshipFederationGate',
    ];
    return targets.flatMap((reg) =>
      kinds.map((kind) => ({
        registerId: reg.id,
        gate: evaluateStewardshipGate(kind, [reg], this.replayNodes),
      })),
    );
  }

  reconstructStewardship(fromNodeId?: string): StewardshipReconstruction {
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

  checkContinuity(): StewardshipContinuityResult {
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
      remoteStewardshipHash: '',
    });
  }

  getRegisters(): StewardshipRegister[] {
    return [...this.registers.values()];
  }

  getReplayNodes(): StewardshipReplayNode[] {
    return [...this.replayNodes];
  }

  getAnchors(): StewardshipAnchor[] {
    return [...this.anchors];
  }

  getFederationPorts(): StewardshipFederationPort[] {
    return [...this.federationPorts.values()];
  }
}
