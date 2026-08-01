import { randomUUID } from 'node:crypto';
import type {
  CTGC,
  TemporalAnchor,
  TemporalContinuityResult,
  TemporalFederationPort,
  TemporalGateKind,
  TemporalReconstruction,
  TemporalRegister,
  TemporalReplayNode,
  TemporalStage,
} from './types.js';
import { createTemporalRegister } from './types.js';
import { evaluateTemporalGate } from './gates.js';

export class CanonicalTemporalGrid {
  private readonly registers = new Map<string, TemporalRegister>();
  private readonly replayNodes: TemporalReplayNode[] = [];
  private readonly anchors: TemporalAnchor[] = [];
  private readonly federationPorts = new Map<string, TemporalFederationPort>();

  createCell(stage: string, artifact: unknown): CTGC {
    const register = createTemporalRegister(stage as TemporalStage, artifact);
    this.registers.set(register.id, register);
    const gate = evaluateTemporalGate('TemporalOrderGate', [register], this.replayNodes);
    const anchor: TemporalAnchor = {
      coordinate: `${stage}:${register.artifactHash}`,
      stage: register.stage,
      anchoredAt: Date.now(),
      temporalHash: register.artifactHash,
    };
    this.anchors.push(anchor);
    const replayNode: TemporalReplayNode = {
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

  evaluateAllGates(registerIds?: string[]): { gate: ReturnType<typeof evaluateTemporalGate>; registerId: string }[] {
    const targets = registerIds
      ? registerIds.map((id) => this.registers.get(id)).filter(Boolean) as TemporalRegister[]
      : [...this.registers.values()];
    const kinds: TemporalGateKind[] = [
      'TemporalOrderGate',
      'TemporalContinuityGate',
      'TemporalReplayGate',
      'TemporalLineageGate',
      'TemporalAuthorityGate',
      'TemporalFederationGate',
    ];
    return targets.flatMap((reg) =>
      kinds.map((kind) => ({
        registerId: reg.id,
        gate: evaluateTemporalGate(kind, [reg], this.replayNodes),
      })),
    );
  }

  reconstructTemporal(fromNodeId?: string): TemporalReconstruction {
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

  checkContinuity(): TemporalContinuityResult {
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
      remoteTemporalHash: '',
    });
  }

  getRegisters(): TemporalRegister[] {
    return [...this.registers.values()];
  }

  getReplayNodes(): TemporalReplayNode[] {
    return [...this.replayNodes];
  }

  getAnchors(): TemporalAnchor[] {
    return [...this.anchors];
  }

  getFederationPorts(): TemporalFederationPort[] {
    return [...this.federationPorts.values()];
  }
}
