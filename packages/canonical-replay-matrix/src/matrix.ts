import { randomUUID } from 'node:crypto';
import type {
  CRMC,
  ReplayAnchor,
  ReplayContinuityResult,
  ReplayFederationPort,
  ReplayFederationSync,
  ReplayGateKind,
  ReplayNode,
  ReplayReconstruction,
  ReplayRegister,
  ReplayStage,
} from './types.js';
import { createReplayRegister, hashArtifact } from './types.js';
import { evaluateGate } from './gates.js';

export class CanonicalReplayMatrix {
  private readonly registers = new Map<string, ReplayRegister>();
  private readonly nodes: ReplayNode[] = [];
  private readonly anchors: ReplayAnchor[] = [];
  private readonly federationPorts = new Map<string, ReplayFederationPort>();

  createCell(stage: string, artifact: unknown): CRMC {
    const register = createReplayRegister(stage as ReplayStage, artifact);
    this.registers.set(register.id, register);
    const gate = evaluateGate('CanonicalReplayDeterminismGate', [register], this.nodes);
    const anchor: ReplayAnchor = {
      coordinate: `${stage}:${register.artifactHash}`,
      stage: register.stage,
      anchoredAt: Date.now(),
      artifactHash: register.artifactHash,
    };
    this.anchors.push(anchor);
    const node: ReplayNode = {
      nodeId: randomUUID(),
      stage: register.stage,
      registerSnapshot: { [register.id]: register.artifactHash } as Record<string, string>,
      gatesPassed: [],
      parentNodeId: this.nodes.length > 0 ? this.nodes[this.nodes.length - 1].nodeId : null,
      replayedAt: Date.now(),
    };
    this.nodes.push(node);
    const federationPort: ReplayFederationPort | null = null;
    return { register, gate, anchor, node, federationPort };
  }

  evaluateAllGates(registerIds?: string[]): { gate: ReturnType<typeof evaluateGate>; registerId: string }[] {
    const targets = registerIds
      ? registerIds.map((id) => this.registers.get(id)).filter(Boolean) as ReplayRegister[]
      : [...this.registers.values()];
    const kinds: ReplayGateKind[] = [
      'CanonicalReplayDeterminismGate',
      'CanonicalReplayContinuityGate',
      'CanonicalReplayLineageGate',
      'CanonicalReplayAuthorityGate',
      'CanonicalReplayEvidenceGate',
      'CanonicalReplayFederationGate',
    ];
    return targets.flatMap((reg) =>
      kinds.map((kind) => ({
        registerId: reg.id,
        gate: evaluateGate(kind, [reg], this.nodes),
      })),
    );
  }

  reconstructLineage(fromNodeId?: string): ReplayReconstruction {
    const startIdx = fromNodeId
      ? this.nodes.findIndex((n) => n.nodeId === fromNodeId)
      : 0;
    const lineage = startIdx >= 0 ? this.nodes.slice(startIdx) : [];
    return {
      nodeId: randomUUID(),
      reconstructedLineage: lineage,
      isDeterministic: lineage.every(
        (n, i) => i === 0 || n.parentNodeId === this.nodes[this.nodes.indexOf(n) - 1]?.nodeId,
      ),
      completedAt: Date.now(),
    };
  }

  checkContinuity(): ReplayContinuityResult {
    const expectedOrder = ['intent', 'authority', 'evidence', 'planning', 'execution', 'validation', 'stewardship'];
    for (let i = 1; i < this.nodes.length; i++) {
      const prevIdx = expectedOrder.indexOf(this.nodes[i - 1].stage);
      const currIdx = expectedOrder.indexOf(this.nodes[i].stage);
      if (currIdx < prevIdx) {
        return { isContinuous: false, breakAtIndex: i, checkedNodes: this.nodes.length };
      }
    }
    return { isContinuous: true, breakAtIndex: null, checkedNodes: this.nodes.length };
  }

  synchronizeFederation(worldId: string, remoteNodeIds: string[]): ReplayFederationSync {
    const conflicts: string[] = [];
    const synchronizedNodes: string[] = [];
    for (const remoteId of remoteNodeIds) {
      const localNode = this.nodes.find((n) => n.nodeId === remoteId);
      if (localNode) {
        synchronizedNodes.push(remoteId);
        const localHash = hashArtifact(localNode.registerSnapshot);
        if (localHash !== localNode.nodeId) {
          conflicts.push(remoteId);
        }
      }
    }
    this.federationPorts.set(worldId, {
      worldId,
      lastSyncTimestamp: Date.now(),
      remoteNodeId: remoteNodeIds[0] ?? '',
      remoteArtifactHash: '',
    });
    return { worldId, synchronizedNodes, conflicts, syncedAt: Date.now() };
  }

  getRegisters(): ReplayRegister[] {
    return [...this.registers.values()];
  }

  getNodes(): ReplayNode[] {
    return [...this.nodes];
  }

  getAnchors(): ReplayAnchor[] {
    return [...this.anchors];
  }

  getFederationPorts(): ReplayFederationPort[] {
    return [...this.federationPorts.values()];
  }
}
