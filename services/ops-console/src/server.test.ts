import { createServer, type Server } from 'node:http';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';

import { describe, expect, it, afterAll, beforeAll, vi } from 'vitest';

import { app } from './server.js';
import { resetSovereignXClusterControlState } from './sovereignxClusterGovernance.js';

describe('GET /telemetry', () => {
  let server: Server;
  let baseUrl = '';

  beforeAll(async () => {
    await new Promise<void>((resolve) => {
      server = createServer(app);
      server.listen(0, '127.0.0.1', () => {
        const address = server.address();
        const port = typeof address === 'object' && address ? address.port : 4000;
        baseUrl = `http://127.0.0.1:${port}`;
        resolve();
      });
    });
  });

  afterAll(async () => {
    await new Promise<void>((resolve, reject) => {
      server.close((error) => {
        if (error) {
          reject(error);
          return;
        }
        resolve();
      });
    });
  });

  it('returns drift, topPatterns, and lastFaults keys', async () => {
    const response = await fetch(`${baseUrl}/telemetry`);
    expect(response.status).toBe(200);

    const body = (await response.json()) as {
      drift: { score: number; totalFaults: number; uniquePatterns: number };
      topPatterns: unknown[];
      lastFaults: unknown[];
      patchTimeline: unknown[];
      sovereignxHardware: { source: string; cycle: { decision: string } };
      hardwareBenchmarks: { available: boolean; summary: { recommendation: string } };
      sovereignxClusterGovernance: { traceabilityMatrix: { summary: { capabilityCount: number } } };
      constitutionalTraceability: { summary: { capabilityCount: number } };
    };

    expect(body.drift).toEqual(
      expect.objectContaining({
        score: expect.any(Number),
        totalFaults: expect.any(Number),
        uniquePatterns: expect.any(Number),
      }),
    );
    expect(body.drift.totalFaults).toBeGreaterThan(0);
    expect(Array.isArray(body.topPatterns)).toBe(true);
    expect(Array.isArray(body.lastFaults)).toBe(true);
    expect(Array.isArray(body.patchTimeline)).toBe(true);
    expect(['env', 'file', 'system']).toContain(body.sovereignxHardware.source);
    expect(['PROMOTE', 'RETRACT', 'MAINTAIN', 'QUARANTINE']).toContain(body.sovereignxHardware.cycle.decision);
    expect(body.hardwareBenchmarks.available).toBe(true);
    expect(body.hardwareBenchmarks.summary.recommendation).toMatch(/CPU|governed/i);
    expect(body.sovereignxClusterGovernance.traceabilityMatrix.summary.capabilityCount).toBeGreaterThanOrEqual(8);
    expect(body.constitutionalTraceability.summary.capabilityCount).toBeGreaterThanOrEqual(8);
  });

  it('returns hardware console summary and live SSE events', async () => {
    const summaryResponse = await fetch(`${baseUrl}/hardware/summary`);
    expect(summaryResponse.status).toBe(200);

    const summaryBody = (await summaryResponse.json()) as {
      available: boolean;
      nodes: { nodeId: string; backend: string; thermalWarnings: string[] }[];
      statusStrip: { throttlingEvents: number; quarantinedNodes: number };
      benchmarkSpecs: { id: string; targetRoutes: string[] }[];
      hardwareEvidenceRefs: string[];
    };

    expect(summaryBody.available).toBe(true);
    expect(summaryBody.nodes.length).toBeGreaterThan(0);
    expect(summaryBody.statusStrip.throttlingEvents).toBeGreaterThanOrEqual(0);
    expect(summaryBody.benchmarkSpecs.length).toBeGreaterThan(0);
    expect(Array.isArray(summaryBody.hardwareEvidenceRefs)).toBe(true);

    const streamResponse = await fetch(`${baseUrl}/hardware/stream`);
    expect(streamResponse.status).toBe(200);
    expect(streamResponse.headers.get('content-type')).toContain('text/event-stream');

    const reader = streamResponse.body?.getReader();
    expect(reader).toBeDefined();
    const chunk = await reader!.read();
    const text = new TextDecoder().decode(chunk.value);
    expect(text).toContain('event: summary');
    expect(text).toContain('data: ');
    await reader!.cancel();
  });

  it('runs hardware replays and benchmark runs as constitutional evidence', async () => {
    const previousEvidenceStore = process.env.SOVEREIGNX_HARDWARE_EVIDENCE_STORE;
    const tempDir = mkdtempSync(path.join(tmpdir(), 'sovereignx-hardware-evidence-'));
    const storePath = path.join(tempDir, 'hardware-evidence.jsonl');
    process.env.SOVEREIGNX_HARDWARE_EVIDENCE_STORE = storePath;

    try {
      const replayResponse = await fetch(`${baseUrl}/hardware/replay`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          workloadId: 'llm-prod',
          currentRoute: 'gpu',
          counterfactualRoute: 'cpu',
        }),
      });

      expect(replayResponse.status).toBe(200);
      const replayBody = (await replayResponse.json()) as {
        artifact: { id: string; kind: string; payload: { comparison: { workloadId: string; currentRoute: string; counterfactualRoute: string } } };
        comparison: { workloadId: string; currentRoute: string; counterfactualRoute: string; delta: { latencyP95Ms: number } };
        summary: { entryCount: number; replayCount: number };
      };
      expect(replayBody.artifact.kind).toBe('replay');
      expect(replayBody.comparison.workloadId).toBe('llm-prod');
      expect(replayBody.comparison.currentRoute).toBe('gpu');
      expect(replayBody.comparison.counterfactualRoute).toBe('cpu');
      expect(replayBody.summary.replayCount).toBeGreaterThanOrEqual(1);

      const benchmarkResponse = await fetch(`${baseUrl}/hardware/benchmarks/run`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          benchmarkId: 'llm-chat-128k',
          routes: ['cpu', 'gpu'],
        }),
      });

      expect(benchmarkResponse.status).toBe(200);
      const benchmarkBody = (await benchmarkResponse.json()) as {
        benchmarkSpec: { id: string };
        runs: { artifact: { id: string; kind: string; payload: { route: string } }; metrics: { latencyP95Ms: number } }[];
        summary: { entryCount: number; benchmarkCount: number };
      };
      expect(benchmarkBody.benchmarkSpec.id).toBe('llm-chat-128k');
      expect(benchmarkBody.runs.length).toBe(2);
      expect(benchmarkBody.summary.benchmarkCount).toBeGreaterThanOrEqual(2);
      expect(benchmarkBody.runs.every((run) => run.artifact.kind === 'benchmark')).toBe(true);
    } finally {
      if (previousEvidenceStore === undefined) {
        delete process.env.SOVEREIGNX_HARDWARE_EVIDENCE_STORE;
      } else {
        process.env.SOVEREIGNX_HARDWARE_EVIDENCE_STORE = previousEvidenceStore;
      }
      rmSync(tempDir, { recursive: true, force: true });
    }
  });

  it('surfaces SovereignX hardware telemetry and governor state from the adapter', async () => {
    const previousTelemetryJson = process.env.SOVEREIGNX_HARDWARE_TELEMETRY_JSON;
    process.env.SOVEREIGNX_HARDWARE_TELEMETRY_JSON = JSON.stringify({
      cpuTempC: 67,
      gpuTempC: 68,
      cpuVolt: 1.08,
      gpuVolt: 1.09,
      powerDrawFraction: 0.58,
      utilization: 0.91,
      utilizationSamples: [
        { atMs: 1_700_000_000_000 - 150, utilization: 0.87 },
        { atMs: 1_700_000_000_000 - 50, utilization: 0.92 },
      ],
      observedAtMs: 1_700_000_000_000,
    });

    try {
      const response = await fetch(`${baseUrl}/sovereignx/hardware`);
      expect(response.status).toBe(200);

      const body = (await response.json()) as {
        source: string;
        sourceDetail: string;
        telemetry: { cpuTempC: number; gpuTempC: number; utilization: number };
        cycle: { decision: string; transitions: { kind: string }[]; evidence: { valid: boolean } };
        governor: { contract: { Contract: { Name: string } }; recentEvents: unknown[] };
        benchmarks: { available: boolean; summary: { recommendation: string } };
      };

      expect(body.source).toBe('env');
      expect(body.sourceDetail).toBe('SOVEREIGNX_HARDWARE_TELEMETRY_JSON');
      expect(body.telemetry.cpuTempC).toBe(67);
      expect(body.cycle.decision).toBe('PROMOTE');
      expect(body.cycle.transitions.map((transition) => transition.kind)).toEqual(['PROMOTE', 'RETRACT']);
      expect(body.cycle.evidence.valid).toBe(true);
      expect(body.governor.contract.Contract.Name).toBe('GOA-Constitutional-Hardware-Governance');
      expect(body.governor.recentEvents.length).toBeGreaterThan(0);
      expect(body.benchmarks.available).toBe(true);
      expect(body.benchmarks.summary.recommendation).toContain('CPU');
  } finally {
      if (previousTelemetryJson === undefined) {
        delete process.env.SOVEREIGNX_HARDWARE_TELEMETRY_JSON;
      } else {
        process.env.SOVEREIGNX_HARDWARE_TELEMETRY_JSON = previousTelemetryJson;
      }
    }
  });

  it('persists live hardware snapshots to the replay store', async () => {
    const previousReplayStore = process.env.SOVEREIGNX_HARDWARE_REPLAY_STORE;
    const tempDir = mkdtempSync(path.join(tmpdir(), 'sovereignx-replay-'));
    const storePath = path.join(tempDir, 'hardware-replay.jsonl');
    process.env.SOVEREIGNX_HARDWARE_REPLAY_STORE = storePath;

    try {
      const firstResponse = await fetch(`${baseUrl}/sovereignx/hardware`);
      expect(firstResponse.status).toBe(200);
      const firstBody = (await firstResponse.json()) as {
        cycle: { decision: string };
        replayStore: { available: boolean };
      };

      const replayResponse = await fetch(`${baseUrl}/sovereignx/hardware/replay`);
      expect(replayResponse.status).toBe(200);
      const replayBody = (await replayResponse.json()) as {
        available: boolean;
        storePath: string;
        entryCount: number;
        latest: { decision: string } | null;
        recentRecords: { decision: string }[];
      };

      expect(firstBody.replayStore.available).toBe(true);
      expect(replayBody.available).toBe(true);
      expect(replayBody.storePath).toBe(path.resolve(storePath));
      expect(replayBody.entryCount).toBe(1);
      expect(replayBody.latest?.decision).toBe(firstBody.cycle.decision);
      expect(replayBody.recentRecords).toHaveLength(1);

      const secondResponse = await fetch(`${baseUrl}/sovereignx/hardware`);
      expect(secondResponse.status).toBe(200);
      const secondReplayResponse = await fetch(`${baseUrl}/sovereignx/hardware/replay`);
      const secondReplayBody = (await secondReplayResponse.json()) as {
        entryCount: number;
        latest: { decision: string } | null;
      };

      expect(secondReplayBody.entryCount).toBe(2);
      expect(['PROMOTE', 'RETRACT', 'MAINTAIN', 'QUARANTINE']).toContain(secondReplayBody.latest?.decision ?? '');
    } finally {
      if (previousReplayStore === undefined) {
        delete process.env.SOVEREIGNX_HARDWARE_REPLAY_STORE;
      } else {
        process.env.SOVEREIGNX_HARDWARE_REPLAY_STORE = previousReplayStore;
      }
      rmSync(tempDir, { recursive: true, force: true });
    }
  });

  it('surfaces the vendor thermal bridge snapshot from the dedicated route', async () => {
    const previousThermalJson = process.env.SOVEREIGNX_THERMAL_SENSOR_JSON;
    process.env.SOVEREIGNX_THERMAL_SENSOR_JSON = JSON.stringify({
      vendor: 'acme-thermal',
      deviceFamily: 'acme-x1',
      sensors: [
        { name: 'package', temperatureC: 68, fanRpm: 1200, voltageV: 1.01, powerWatts: 42 },
        { name: 'vrm', temperatureC: 62, fanRpm: 900, voltageV: 0.98, powerWatts: 18 },
      ],
    });

    try {
      const response = await fetch(`${baseUrl}/sovereignx/hardware/thermal-bridge`);
      expect(response.status).toBe(200);

      const body = (await response.json()) as {
        source: string;
        vendor: string;
        deviceFamily: string;
        healthy: boolean;
        sensors: { name: string; temperatureC: number }[];
        summary: { hottestSensor: string; alertCount: number };
      };

      expect(body.source).toBe('env');
      expect(body.vendor).toBe('acme-thermal');
      expect(body.deviceFamily).toBe('acme-x1');
      expect(body.healthy).toBe(true);
      expect(body.sensors).toHaveLength(2);
      expect(body.summary.hottestSensor).toBe('package');
      expect(body.summary.alertCount).toBe(0);
    } finally {
      if (previousThermalJson === undefined) {
        delete process.env.SOVEREIGNX_THERMAL_SENSOR_JSON;
      } else {
        process.env.SOVEREIGNX_THERMAL_SENSOR_JSON = previousThermalJson;
      }
    }
  });

  it('runs the operator override drill without mutating the live governor', async () => {
    const response = await fetch(`${baseUrl}/sovereignx/hardware/override-drill`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        requestedDecision: 'RETRACT',
        authority: 'SovereignX.Router',
        reason: 'operator drill',
      }),
    });

    expect(response.status).toBe(200);
    const body = (await response.json()) as {
      drill: {
        available: boolean;
        authority: string;
        requestedDecision: string;
        baselineDecision: string;
        accepted: boolean;
        driftFromBaseline: boolean;
        previewState: { lastDecision: string };
      };
      snapshot: { cycle: { decision: string } };
    };

    expect(body.drill.available).toBe(true);
    expect(body.drill.authority).toBe('SovereignX.Router');
    expect(body.drill.requestedDecision).toBe('RETRACT');
    expect(body.drill.accepted).toBe(true);
    expect(['PROMOTE', 'RETRACT', 'MAINTAIN', 'QUARANTINE']).toContain(body.drill.baselineDecision);
    expect(body.drill.previewState.lastDecision).toBe('RETRACT');
    expect(body.drill.driftFromBaseline).toBe(body.drill.baselineDecision !== 'RETRACT');
    expect(['PROMOTE', 'RETRACT', 'MAINTAIN', 'QUARANTINE']).toContain(body.snapshot.cycle.decision);
  });

  it('validates replayed hardware decisions and chaos cases', async () => {
    const previousTelemetryJson = process.env.SOVEREIGNX_HARDWARE_TELEMETRY_JSON;
    const previousReplayStore = process.env.SOVEREIGNX_HARDWARE_REPLAY_STORE;
    const tempDir = mkdtempSync(path.join(tmpdir(), 'sovereignx-validation-'));
    const storePath = path.join(tempDir, 'hardware-replay.jsonl');
    process.env.SOVEREIGNX_HARDWARE_REPLAY_STORE = storePath;
    process.env.SOVEREIGNX_HARDWARE_TELEMETRY_JSON = JSON.stringify({
      cpuTempC: 66,
      gpuTempC: 67,
      cpuVolt: 1.06,
      gpuVolt: 1.07,
      powerDrawFraction: 0.52,
      utilization: 0.89,
      utilizationSamples: [
        { atMs: 1_700_100_000_000 - 120, utilization: 0.84 },
        { atMs: 1_700_100_000_000 - 30, utilization: 0.91 },
      ],
      observedAtMs: 1_700_100_000_000,
    });

    try {
      await fetch(`${baseUrl}/sovereignx/hardware`);
      await fetch(`${baseUrl}/sovereignx/hardware`);

      const response = await fetch(`${baseUrl}/sovereignx/hardware/replay/validation`);
      expect(response.status).toBe(200);

      const body = (await response.json()) as {
        available: boolean;
        recordCount: number;
        baselineMatches: number;
        baselineMismatches: number;
        chaosRuns: number;
        chaosQuarantines: number;
        passed: boolean;
        rows: { decisionMatched: boolean; stateMatched: boolean; chaosDecisions: { quarantined: boolean }[] }[];
      };

      expect(body.available).toBe(true);
      expect(body.recordCount).toBe(2);
      expect(body.baselineMismatches).toBe(0);
      expect(body.baselineMatches).toBe(2);
      expect(body.chaosRuns).toBeGreaterThan(0);
      expect(body.chaosQuarantines).toBeGreaterThan(0);
      expect(body.passed).toBe(true);
      expect(body.rows.every((row) => row.decisionMatched && row.stateMatched)).toBe(true);
      expect(body.rows.some((row) => row.chaosDecisions.some((chaos) => chaos.quarantined))).toBe(true);
    } finally {
      if (previousReplayStore === undefined) {
        delete process.env.SOVEREIGNX_HARDWARE_REPLAY_STORE;
      } else {
        process.env.SOVEREIGNX_HARDWARE_REPLAY_STORE = previousReplayStore;
      }
      if (previousTelemetryJson === undefined) {
        delete process.env.SOVEREIGNX_HARDWARE_TELEMETRY_JSON;
      } else {
        process.env.SOVEREIGNX_HARDWARE_TELEMETRY_JSON = previousTelemetryJson;
      }
      rmSync(tempDir, { recursive: true, force: true });
    }
  });

  it('routes governed work across multiple cluster nodes', async () => {
    const response = await fetch(`${baseUrl}/sovereignx/cluster-routing`);
    expect(response.status).toBe(200);

    const body = (await response.json()) as {
      clusterRouting: {
        clusterDecision: { action: string; nodeId: string | null; backend: string };
        selectedNode: { nodeId: string; role: string } | null;
        summary: { nodeCount: number; eligibleNodeCount: number };
        alternateNodes: { nodeId: string }[];
      };
    };

    expect(body.clusterRouting.clusterDecision.action).toBe('dispatch');
    expect(body.clusterRouting.clusterDecision.nodeId).toBe('cluster-gpu-a');
    expect(body.clusterRouting.selectedNode?.nodeId).toBe('cluster-gpu-a');
    expect(body.clusterRouting.summary.nodeCount).toBe(3);
    expect(body.clusterRouting.summary.eligibleNodeCount).toBeGreaterThanOrEqual(2);
    expect(body.clusterRouting.alternateNodes.map((node) => node.nodeId)).toContain('cluster-mixed-a');
  });

  it('controls live cluster membership and surfaces autoscaling, failover, and traceability', async () => {
    try {
      const controlResponse = await fetch(`${baseUrl}/sovereignx/cluster-membership/control`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          action: 'quarantine',
          nodeId: 'cluster-gpu-a',
          reason: 'operator drill',
        }),
      });

      expect(controlResponse.status).toBe(200);
      const controlBody = (await controlResponse.json()) as {
        controlState: { quarantinedNodeIds: string[]; desiredNodeCount: number };
        clusterGovernance: {
          summary: { quarantinedNodeCount: number; activeNodeCount: number };
          autoscaling: { action: string; recommendedNodeCount: number };
          failover: { action: string; toNodeId: string | null };
          soakChaosValidation: { available: boolean; passed: boolean; chaosRuns: number; stableSelections: number };
          traceabilityMatrix: { summary: { capabilityCount: number; requirementCount: number; evidenceCount: number; testCount: number } };
        };
        traceabilityMatrix: { rows: { capabilityId: string }[] };
      };

      expect(controlBody.controlState.quarantinedNodeIds).toContain('cluster-gpu-a');
      expect(controlBody.controlState.desiredNodeCount).toBeGreaterThan(0);
      expect(controlBody.clusterGovernance.summary.quarantinedNodeCount).toBeGreaterThanOrEqual(1);
      expect(['scale_up', 'scale_down', 'hold']).toContain(controlBody.clusterGovernance.autoscaling.action);
      expect(controlBody.clusterGovernance.autoscaling.recommendedNodeCount).toBeGreaterThan(0);
      expect(['failover', 'hold']).toContain(controlBody.clusterGovernance.failover.action);
      expect(controlBody.clusterGovernance.soakChaosValidation.available).toBe(true);
      expect(controlBody.clusterGovernance.soakChaosValidation.chaosRuns).toBeGreaterThan(0);
      expect(controlBody.clusterGovernance.traceabilityMatrix.summary.capabilityCount).toBeGreaterThanOrEqual(8);
      expect(controlBody.traceabilityMatrix.rows.some((row) => row.capabilityId === 'cluster-membership-control')).toBe(true);

      const validationResponse = await fetch(`${baseUrl}/sovereignx/cluster-membership/validation`);
      expect(validationResponse.status).toBe(200);
      const validationBody = (await validationResponse.json()) as {
        soakChaosValidation: { passed: boolean; stableSelections: number; chaosRuns: number };
      };
      expect(validationBody.soakChaosValidation.stableSelections).toBeGreaterThan(0);
      expect(validationBody.soakChaosValidation.chaosRuns).toBeGreaterThan(0);
    } finally {
      resetSovereignXClusterControlState();
    }
  });

  it('returns the constitutional traceability matrix as a first-class runtime entry', async () => {
    const response = await fetch(`${baseUrl}/constitutional-traceability`);
    expect(response.status).toBe(200);

    const body = (await response.json()) as {
      matrix: {
        available: boolean;
        source: string;
        rows: { capabilityId: string; capabilityName: string; constitutionalRequirements: string[]; architecturalComponent: string; evidenceIds: string[]; tests: string[] }[];
        summary: { capabilityCount: number; requirementCount: number; evidenceCount: number; testCount: number; proofSurfaceCount: number };
      };
    };

    expect(body.matrix.available).toBe(true);
    expect(body.matrix.source).toBe('live-cluster-governance');
    expect(body.matrix.summary.capabilityCount).toBeGreaterThanOrEqual(8);
    expect(body.matrix.summary.requirementCount).toBeGreaterThanOrEqual(5);
    expect(body.matrix.rows.some((row) => row.capabilityId === 'soak-chaos-validation')).toBe(true);
    expect(body.matrix.rows.every((row) => row.constitutionalRequirements.length > 0)).toBe(true);
    expect(body.matrix.rows.every((row) => row.evidenceIds.length > 0)).toBe(true);
    expect(body.matrix.rows.every((row) => row.tests.length > 0)).toBe(true);
  });

  it('returns the proof-surface catalog for operators and dashboards', async () => {
    const response = await fetch(`${baseUrl}/proof-surfaces`);
    expect(response.status).toBe(200);
    expect(response.headers.get('content-type')).toContain('application/json');

    const body = (await response.json()) as {
      catalog: { schemaVersion: string; surfaces: unknown[] };
      records: unknown[];
      summaries: { identity: { id: string }; proofLevel: string; domain: string; healthIndicator: string }[];
    };

    expect(body.catalog.schemaVersion).toBe('1.0');
    expect(body.records.length).toBeGreaterThan(0);
    expect(body.summaries.some((surface) => surface.identity.id === '@aaes-os/aaes-governance' && surface.domain === 'Governance')).toBe(true);
    expect(body.summaries.some((surface) => surface.identity.id === '@aaes-os/sovereignx-router' && surface.domain === 'Execution')).toBe(true);
    expect(body.summaries.some((surface) => surface.identity.id === '@aaes-os/sovereignx-hardware-runtime-governor' && surface.domain === 'Runtime')).toBe(true);
    expect(body.summaries.some((surface) => surface.identity.id === '@aaes-os/sovereignx-cluster-routing-runtime' && surface.domain === 'Execution')).toBe(true);
    expect(body.summaries.some((surface) => surface.identity.id === '@aaes-os/sovereignx-cluster-governance-runtime' && surface.domain === 'Governance')).toBe(true);
    expect(body.summaries.some((surface) => surface.identity.id === '@aaes-os/constitutional-traceability-runtime' && surface.domain === 'Runtime')).toBe(true);
    expect(body.summaries.every((surface) => typeof surface.healthIndicator === 'string')).toBe(true);
  });

  it('returns the live hardware governor snapshot through the dedicated route', async () => {
    const response = await fetch(`${baseUrl}/sovereignx/hardware`);
    expect(response.status).toBe(200);

    const body = (await response.json()) as {
      source: string;
      telemetry: { observedAtMs?: number };
      cycle: { decision: string };
      governor: { state: { lastDecision: string } };
    };

    expect(['env', 'file', 'system']).toContain(body.source);
    expect(body.telemetry.observedAtMs).toBeTypeOf('number');
    expect(['PROMOTE', 'RETRACT', 'MAINTAIN', 'QUARANTINE']).toContain(body.cycle.decision);
    expect(['PROMOTE', 'RETRACT', 'MAINTAIN', 'QUARANTINE']).toContain(body.governor.state.lastDecision);
  });

  it('returns the constitutional evidence graph rooted in the release receipt', async () => {
    const response = await fetch(`${baseUrl}/evidence-graph`);
    expect(response.status).toBe(200);

    const body = (await response.json()) as {
      summary: { rootReceiptId: string; proofSurfaceCount: number; claimCount: number; unresolvedClaims: string[] };
      graph: { rootReceipt: { receiptId: string }; claims: unknown[] };
    };

    expect(body.summary.rootReceiptId).toBe(body.graph.rootReceipt.receiptId);
    expect(body.summary.proofSurfaceCount).toBeGreaterThan(0);
    expect(body.summary.claimCount).toBeGreaterThan(0);
    expect(body.summary.unresolvedClaims).toHaveLength(0);
  });

  it('returns the arena mode snapshot for the tournament console', async () => {
    const response = await fetch(`${baseUrl}/arena`);
    expect(response.status).toBe(200);
    expect(response.headers.get('content-type')).toContain('application/json');

    const body = (await response.json()) as {
      arenaId: string;
      map: { width: number; height: number; terrainGrid: string[][] };
      agents: { name: string; faction: string; talents: { name: string }[] }[];
      challengeRuns: { runId: string; status: string; proofLevel: string; timeline: unknown[] }[];
      scorecard: { proofLevel: string; readinessLevel: string; challengePassRate: number };
      lifecycle: { stage: string; status: string; artifacts: string[] }[];
      certificate: { certificateId: string; readinessLevel: string; challengeResults: string };
      tournament: { tournamentId: string; rounds: { matchId: string; winner: string | null; tracePath: string | null }[][] };
      replayReports: Record<string, { integrityScore: number; tracePath: string }>;
      battleScars: { scarId: string; type: string }[];
      digitalThread: string[];
    };

    expect(body.arenaId).toMatch(/^arena-/);
    expect(body.map.width).toBeGreaterThan(0);
    expect(body.map.height).toBeGreaterThan(0);
    expect(body.map.terrainGrid).toHaveLength(body.map.height);
    expect(body.agents.length).toBeGreaterThan(0);
    expect(body.agents.every((agent) => agent.talents.length > 0)).toBe(true);
    expect(body.challengeRuns.length).toBeGreaterThan(0);
    expect(body.challengeRuns.every((run) => Array.isArray(run.timeline) && run.timeline.length > 0)).toBe(true);
    expect(body.scorecard.proofLevel).toMatch(/^P[0-5]$/);
    expect(body.scorecard.readinessLevel).toMatch(/prototype|candidate|production-ready/);
    expect(body.lifecycle.map((phase) => phase.stage)).toEqual(['Design', 'Build', 'Verify', 'Challenge', 'Certify', 'Release', 'Observe', 'Learn']);
    expect(body.certificate.certificateId).toMatch(/^certificate-/);
    expect(body.certificate.challengeResults).toContain('challenges');
    expect(body.tournament.rounds.length).toBeGreaterThan(0);
    expect(Object.keys(body.replayReports).length).toBeGreaterThan(0);
    expect(Object.values(body.replayReports).every((report) => report.integrityScore >= 0 && report.integrityScore <= 100)).toBe(true);
    expect(body.battleScars.length).toBeGreaterThan(0);
    expect(body.digitalThread.length).toBeGreaterThan(0);
  });

  it('allows the studio to fetch proof surfaces cross-origin', async () => {
    const response = await fetch(`${baseUrl}/proof-surfaces`, {
      method: 'OPTIONS',
    });

    expect(response.status).toBe(204);
    expect(response.headers.get('access-control-allow-origin')).toBe('*');
    expect(response.headers.get('access-control-allow-methods')).toContain('GET');
  });

  it('surfaces CAB ledger summary and invariant status for operators', async () => {
    const previousStore = process.env.CAB_STORE;
    const tempDir = mkdtempSync(path.join(tmpdir(), 'cab-ledger-'));
    const storePath = path.join(tempDir, 'ledger.jsonl');
    const records = [
      {
        sequence: 1,
        object_type: 'IntentRecord',
        object_id: 'cab.intent.ops',
        created_at: '2026-06-19T12:00:00Z',
        superseded: false,
        payload: { intent_id: 'cab.intent.ops', created_at: '2026-06-19T12:00:00Z' },
      },
      {
        sequence: 2,
        object_type: 'DecisionRecord',
        object_id: 'cab.decision.ops',
        created_at: '2026-06-19T12:01:00Z',
        superseded: false,
        payload: {
          decision_id: 'cab.decision.ops',
          intent_refs: ['cab.intent.ops'],
          evidence_chain_refs: ['cab.evidence.ops'],
          continuity_receipt_refs: ['cab.receipt.ops'],
          govern_policy_refs: ['policy:ops'],
          created_at: '2026-06-19T12:01:00Z',
        },
      },
      {
        sequence: 3,
        object_type: 'EvidenceChain',
        object_id: 'cab.evidence.ops',
        created_at: '2026-06-19T12:02:00Z',
        superseded: false,
        payload: { chain_id: 'cab.evidence.ops', created_at: '2026-06-19T12:02:00Z' },
      },
      {
        sequence: 4,
        object_type: 'ContinuityReceipt',
        object_id: 'cab.receipt.ops',
        created_at: '2026-06-19T12:03:00Z',
        superseded: false,
        payload: { receipt_id: 'cab.receipt.ops', trace_id: 'ct.ops', created_at: '2026-06-19T12:03:00Z' },
      },
    ];
    writeFileSync(storePath, `${records.map((record) => JSON.stringify(record)).join('\n')}\n`, 'utf8');
    process.env.CAB_STORE = storePath;

    try {
      const response = await fetch(`${baseUrl}/telemetry`);
      expect(response.status).toBe(200);
      const body = (await response.json()) as {
        cab: {
          available: boolean;
          entryCount: number;
          activeCount: number;
          invariants: { passed: boolean; results: { invariantId: string; status: string }[] };
          latest: { intents: string[]; decisions: string[]; evidenceChains: string[]; continuityReceipts: string[] };
        };
      };
      expect(body.cab.available).toBe(true);
      expect(body.cab.entryCount).toBe(4);
      expect(body.cab.activeCount).toBe(4);
      expect(body.cab.invariants.passed).toBe(true);
      expect(body.cab.invariants.results.map((result) => result.invariantId)).toEqual(['CL', 'RC', 'TI', 'SU', 'NE']);
      expect(body.cab.latest).toEqual({
        intents: ['cab.intent.ops'],
        decisions: ['cab.decision.ops'],
        evidenceChains: ['cab.evidence.ops'],
        continuityReceipts: ['cab.receipt.ops'],
        reconstructionPlans: [],
      });
    } finally {
      if (previousStore === undefined) {
        delete process.env.CAB_STORE;
      } else {
        process.env.CAB_STORE = previousStore;
      }
      rmSync(tempDir, { recursive: true, force: true });
    }
  });

  it('persists pricing ledger entries and surfaces margin telemetry', async () => {
    const previousLedgerPath = process.env.PRICING_LEDGER_PATH;
    const tempDir = mkdtempSync(path.join(tmpdir(), 'pricing-ledger-'));
    const storePath = path.join(tempDir, 'ledger.jsonl');
    process.env.PRICING_LEDGER_PATH = storePath;

    try {
      const entry = {
        requestId: 'srx-ledger-001',
        recordedAt: '2026-07-11T00:00:00.000Z',
        segment: 'Enterprise',
        strategy: 'Enterprise bundle',
        routedRequests: 5400,
        monthlyCustomers: 12,
        estimatedRevenueUsd: 42000,
        estimatedCostUsd: 21000,
        estimatedGrossMarginUsd: 21000,
        estimatedGrossMarginPct: 50,
        selectedModel: 'qwen-7b',
        backend: 'opencl',
        routeReason: 'enterprise pricing request routed to the larger reasoning surface',
      };

      const postResponse = await fetch(`${baseUrl}/pricing/ledger`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ entry }),
      });

      expect(postResponse.status).toBe(201);

      const ledgerResponse = await fetch(`${baseUrl}/pricing/ledger`);
      expect(ledgerResponse.status).toBe(200);
      const ledgerBody = (await ledgerResponse.json()) as {
        entryCount: number;
        totalRevenueUsd: number;
        totalGrossMarginUsd: number;
        grossMarginPct: number;
        recentEntries: { requestId: string; strategy: string }[];
      };

      expect(ledgerBody.entryCount).toBe(1);
      expect(ledgerBody.totalRevenueUsd).toBe(42000);
      expect(ledgerBody.totalGrossMarginUsd).toBe(21000);
      expect(ledgerBody.grossMarginPct).toBe(50);
      expect(ledgerBody.recentEntries[0]?.requestId).toBe('srx-ledger-001');

      const telemetryResponse = await fetch(`${baseUrl}/telemetry`);
      const telemetryBody = (await telemetryResponse.json()) as {
        pricing: {
          entryCount: number;
          totalRevenueUsd: number;
          totalGrossMarginUsd: number;
          bySegment: { segment: string; entryCount: number }[];
        };
      };

      expect(telemetryBody.pricing.entryCount).toBe(1);
      expect(telemetryBody.pricing.totalRevenueUsd).toBe(42000);
      expect(telemetryBody.pricing.bySegment[0]?.segment).toBe('Enterprise');
    } finally {
      if (previousLedgerPath === undefined) {
        delete process.env.PRICING_LEDGER_PATH;
      } else {
        process.env.PRICING_LEDGER_PATH = previousLedgerPath;
      }
      rmSync(tempDir, { recursive: true, force: true });
    }
  });

  it('proxies treasury schedule data with PayPal adapter payloads', async () => {
    const realFetch = globalThis.fetch.bind(globalThis);
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.startsWith(baseUrl)) {
        return realFetch(input, init);
      }
      if (url.endsWith('/v1/auth/login')) {
        return new Response(JSON.stringify({ sessionId: 'ops-console-session' }), {
          status: 200,
          headers: { 'content-type': 'application/json' },
        });
      }

      if (url.endsWith('/v1/billing/treasury/schedule')) {
        return new Response(JSON.stringify({
          schedule: {
            scheduledAt: '2026-07-11T00:00:00.000Z',
            source: 'ledger',
            customerId: 'cust-1',
            ownerId: 'owner-1',
            governanceProfile: 'balanced',
            instructions: {
              openAI: { destination: 'OpenAI', channel: 'openai-org-billing', amountUsd: 42, notes: 'Pay OpenAI' },
              tax: { destination: 'IRS', channel: 'irs-direct-pay', amountUsd: 18, notes: 'IRS Direct Pay' },
              ownerProfit: { destination: 'PayPal', channel: 'paypal-payouts', amountUsd: 72, notes: 'Send owner profit through PayPal Payouts' },
            },
            sourcePlan: {
              grossInvoiceUsd: 250,
              openAiUsageCostUsd: 42,
              taxReserveUsd: 18,
              platformReserveUsd: 20,
              ownerProfitUsd: 72,
              totalReserveUsd: 80,
              netAfterReservesUsd: 170,
              providerNotes: {
                customerCollection: 'Collect customer payment through checkout, then record settlement in the treasury ledger.',
                openAI: 'OpenAI costs are separate vendor spend. Keep the treasury reserve aligned with your OpenAI billing cycle.',
                tax: 'IRS remittance should be scheduled through IRS-approved payment channels, not via PayPal.',
                profit: 'Profit can be distributed to the owner through PayPal Payouts after reserves are held.',
              },
              adapters: {
                paypalCheckout: {
                  enabled: true,
                  environment: 'sandbox',
                  apiBaseUrl: 'https://api-m.sandbox.paypal.com',
                  createOrderPath: '/v2/checkout/orders',
                  captureOrderPath: '/v2/checkout/orders/:orderId/capture',
                  orderRequest: {
                    intent: 'CAPTURE',
                    application_context: {
                      brand_name: 'Sovereign Router X',
                      landing_page: 'NO_PREFERENCE',
                      user_action: 'PAY_NOW',
                      return_url: 'http://localhost:4000/treasury/paypal/return',
                      cancel_url: 'http://localhost:4000/treasury/paypal/cancel',
                    },
                    purchase_units: [],
                  },
                },
                paypalPayout: {
                  enabled: true,
                  environment: 'sandbox',
                  apiBaseUrl: 'https://api-m.sandbox.paypal.com',
                  createBatchPath: '/v1/payments/payouts',
                  batchRequest: {
                    sender_batch_header: {
                      sender_batch_id: 'owner-1-batch',
                      email_subject: 'Sovereign Router X owner payout',
                      email_message: 'Your owner-profit payout has been scheduled from the treasury ledger.',
                    },
                    items: [],
                  },
                },
              },
            },
          },
        }), {
          status: 200,
          headers: { 'content-type': 'application/json' },
        });
      }

      return new Response(JSON.stringify({ error: `unexpected fetch to ${url}` }), {
        status: 500,
        headers: { 'content-type': 'application/json' },
      });
    });

    try {
      const res = await fetch(`${baseUrl}/treasury/schedule`);
      expect(res.status).toBe(200);
      const body = (await res.json()) as {
        schedule: {
          sourcePlan: {
            adapters: {
              paypalCheckout: { enabled: boolean; apiBaseUrl: string };
              paypalPayout: { enabled: boolean; apiBaseUrl: string };
            };
          };
          instructions: {
            tax: { channel: string };
          };
        };
      };

      expect(body.schedule.sourcePlan.adapters.paypalCheckout.enabled).toBe(true);
      expect(body.schedule.sourcePlan.adapters.paypalCheckout.apiBaseUrl).toContain('paypal.com');
      expect(body.schedule.sourcePlan.adapters.paypalPayout.enabled).toBe(true);
      expect(body.schedule.instructions.tax.channel).toBe('irs-direct-pay');
      expect(fetchSpy).toHaveBeenCalled();
    } finally {
      fetchSpy.mockRestore();
    }
  });

  it('exports pricing margin reports and cohort history', async () => {
    const previousLedgerPath = process.env.PRICING_LEDGER_PATH;
    const tempDir = mkdtempSync(path.join(tmpdir(), 'pricing-reports-'));
    const storePath = path.join(tempDir, 'ledger.jsonl');
    process.env.PRICING_LEDGER_PATH = storePath;

    try {
      const entries = [
        {
          requestId: 'srx-jan',
          recordedAt: '2026-01-15T00:00:00.000Z',
          segment: 'Professional',
          strategy: 'Subscription-led',
          routedRequests: 400,
          monthlyCustomers: 4,
          estimatedRevenueUsd: 900,
          estimatedCostUsd: 300,
          estimatedGrossMarginUsd: 600,
          estimatedGrossMarginPct: 66.67,
          selectedModel: 'qwen-3b',
          backend: 'cpu',
          routeReason: 'subscription-led fit',
        },
        {
          requestId: 'srx-feb',
          recordedAt: '2026-02-20T00:00:00.000Z',
          segment: 'Enterprise',
          strategy: 'Enterprise bundle',
          routedRequests: 1200,
          monthlyCustomers: 8,
          estimatedRevenueUsd: 2400,
          estimatedCostUsd: 900,
          estimatedGrossMarginUsd: 1500,
          estimatedGrossMarginPct: 62.5,
          selectedModel: 'qwen-7b',
          backend: 'opencl',
          routeReason: 'enterprise bundle fit',
        },
      ];

      for (const entry of entries) {
        const res = await fetch(`${baseUrl}/pricing/ledger`, {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify({ entry }),
        });
        expect(res.status).toBe(201);
      }

      const marginCsv = await fetch(`${baseUrl}/pricing/reports/margin.csv`);
      expect(marginCsv.status).toBe(200);
      expect(marginCsv.headers.get('content-type')).toContain('text/csv');
      const marginText = await marginCsv.text();
      expect(marginText).toContain('"scope","name","entryCount","revenueUsd"');
      expect(marginText).toContain('Enterprise bundle');

      const cohortsCsv = await fetch(`${baseUrl}/pricing/reports/cohorts.csv`);
      expect(cohortsCsv.status).toBe(200);
      const cohortsText = await cohortsCsv.text();
      expect(cohortsText).toContain('2026-01');
      expect(cohortsText).toContain('2026-02');

      const cohorts = await fetch(`${baseUrl}/pricing/cohorts`);
      const cohortsBody = (await cohorts.json()) as { cohortHistory: { cohort: string; entryCount: number }[] };
      expect(cohortsBody.cohortHistory).toHaveLength(2);
      expect(cohortsBody.cohortHistory.map((row) => row.cohort)).toEqual(['2026-01', '2026-02']);
    } finally {
      if (previousLedgerPath === undefined) {
        delete process.env.PRICING_LEDGER_PATH;
      } else {
        process.env.PRICING_LEDGER_PATH = previousLedgerPath;
      }
      rmSync(tempDir, { recursive: true, force: true });
    }
  });

  it('exports CEP artifacts and accepts remote view-state updates', async () => {
    const exportResponse = await fetch(`${baseUrl}/cep/artifacts/export.json`);
    expect(exportResponse.status).toBe(200);
    const exportBody = (await exportResponse.json()) as {
      entryCount: number;
      countsByKind: Record<string, number>;
      records: { id: string; kind: string; title: string }[];
      viewState: { selectedKind: string; selectedArtifactId: string | null };
    };

    expect(exportBody.entryCount).toBeGreaterThan(0);
    expect(exportBody.countsByKind['promotion-request']).toBeGreaterThan(0);
    expect(exportBody.countsByKind['replay-job']).toBeGreaterThan(0);
    expect(exportBody.countsByKind.decision).toBeGreaterThan(0);

    const promotionRequest = exportBody.records.find((record) => record.kind === 'promotion-request');
    expect(promotionRequest).toBeTruthy();

    const kindResponse = await fetch(`${baseUrl}/cep/artifacts/promotion-request`);
    expect(kindResponse.status).toBe(200);
    const kindBody = (await kindResponse.json()) as { artifacts: { id: string; kind: string }[] };
    expect(kindBody.artifacts.length).toBeGreaterThan(0);

    const selectedArtifactId = promotionRequest?.id ?? exportBody.records[0].id;
    const viewStateResponse = await fetch(`${baseUrl}/cep/view-state`, {
      method: 'PATCH',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        selectedKind: 'promotion-request',
        selectedArtifactId,
      }),
    });
    expect(viewStateResponse.status).toBe(200);
    const viewStateBody = (await viewStateResponse.json()) as {
      viewState: { selectedKind: string; selectedArtifactId: string | null };
    };
    expect(viewStateBody.viewState.selectedKind).toBe('promotion-request');
    expect(viewStateBody.viewState.selectedArtifactId).toBe(selectedArtifactId);

    const artifactResponse = await fetch(`${baseUrl}/cep/artifacts/promotion-request/${selectedArtifactId}`);
    expect(artifactResponse.status).toBe(200);
    const artifactBody = (await artifactResponse.json()) as {
      artifact: { id: string; kind: string; payload: unknown };
      viewState: { selectedArtifactId: string | null };
    };
    expect(artifactBody.artifact.id).toBe(selectedArtifactId);
    expect(artifactBody.artifact.kind).toBe('promotion-request');
    expect(artifactBody.viewState.selectedArtifactId).toBe(selectedArtifactId);
  });

  it('connects AAIS health into telemetry', async () => {
    const previousBaseUrl = process.env.AAIS_BASE_URL;
    let aaisServer: Server;
    let aaisBaseUrl = '';
    await new Promise<void>((resolve) => {
      aaisServer = createServer((_req, res) => {
        res.setHeader('content-type', 'application/json');
        res.end(JSON.stringify({
          status: 'healthy',
          service: 'AAIS',
          legacy_api_loaded: true,
          active_model_mode: 'mock',
          ai_status: 'initialized',
          ai_bootstrap_status: 'initialized',
          mock_mode_active: true,
        }));
      });
      aaisServer.listen(0, '127.0.0.1', () => {
        const address = aaisServer.address();
        const port = typeof address === 'object' && address ? address.port : 8000;
        aaisBaseUrl = `http://127.0.0.1:${port}`;
        process.env.AAIS_BASE_URL = aaisBaseUrl;
        resolve();
      });
    });

    try {
      const response = await fetch(`${baseUrl}/telemetry`);
      expect(response.status).toBe(200);
      const body = (await response.json()) as {
        aais: {
          connected: boolean;
          baseUrl: string;
          service: string;
          activeModelMode: string;
          aiStatus: string;
          aiBootstrapStatus: string;
          mockModeActive: boolean;
          legacyApiLoaded: boolean;
        };
      };
      expect(body.aais).toEqual(expect.objectContaining({
        connected: true,
        baseUrl: aaisBaseUrl,
        service: 'AAIS',
        activeModelMode: 'mock',
        aiStatus: 'initialized',
        aiBootstrapStatus: 'initialized',
        mockModeActive: true,
        legacyApiLoaded: true,
      }));
    } finally {
      if (previousBaseUrl === undefined) {
        delete process.env.AAIS_BASE_URL;
      } else {
        process.env.AAIS_BASE_URL = previousBaseUrl;
      }
      await new Promise<void>((resolve, reject) => {
        aaisServer.close((error) => {
          if (error) {
            reject(error);
            return;
          }
          resolve();
        });
      });
    }
  });

  it('exposes production health, readiness, request id, and security headers', async () => {
    const response = await fetch(`${baseUrl}/readiness`);
    expect(response.status).toBe(200);
    expect(response.headers.get('x-content-type-options')).toBe('nosniff');
    expect(response.headers.get('x-frame-options')).toBe('DENY');
    expect(response.headers.get('x-request-id')).toBeTruthy();

    const body = (await response.json()) as {
      ready: boolean;
      checks: { telemetry: boolean; cen: boolean; sovereigntyLedger: boolean; lawOfLawsLedger: boolean };
    };
    expect(body.ready).toBe(true);
    expect(body.checks).toEqual({
      telemetry: true,
      cen: true,
      sovereigntyLedger: true,
      lawOfLawsLedger: true,
    });
  });

  it('returns the seeded MRI operator assessment', async () => {
    const response = await fetch(`${baseUrl}/mri`);
    expect(response.status).toBe(200);

    const body = (await response.json()) as {
      comparison: {
        before: { scores: { continuity: number; confidence: number } };
        after: { scores: { continuity: number; confidence: number } };
        deltaState: Record<string, number>;
      };
      report: { summary: string };
    };

    expect(body.comparison.before.scores.continuity).toBeTypeOf('number');
    expect(body.comparison.after.scores.continuity).toBeGreaterThan(
      body.comparison.before.scores.continuity,
    );
    expect(body.comparison.after.scores.confidence).toBeGreaterThanOrEqual(
      body.comparison.before.scores.confidence,
    );
    expect(body.comparison.deltaState).toEqual(
      expect.objectContaining({
        R: expect.any(Number),
        K: expect.any(Number),
        G: expect.any(Number),
        D: expect.any(Number),
        X: expect.any(Number),
      }),
    );
    expect(body.report.summary).toContain('Continuity increased by');
  });

  it('returns recent document subsystem coverage for operators', async () => {
    const response = await fetch(`${baseUrl}/coverage`);
    expect(response.status).toBe(200);

    const body = (await response.json()) as {
      mappedDocuments: number;
      subsystems: string[];
      documents: { path: string; subsystem: string }[];
    };

    expect(body.mappedDocuments).toBe(38);
    expect(body.subsystems).toContain('trust-root');
    expect(body.subsystems).toContain('ucr-attestation');
    expect(body.subsystems).toContain('runtime-law-spine');
    expect(body.subsystems).toContain('evidence-receipts');
    expect(body.documents.some((doc) => doc.path === 'docs/contracts/AAES_OS_ARCHITECTURE_V1.md')).toBe(true);
  });

  it('returns the CEN enforcement demo receipt', async () => {
    const response = await fetch(`${baseUrl}/cen/demo`);
    expect(response.status).toBe(200);

    const body = (await response.json()) as {
      decision: { verdict: string; reasonCode: string };
      receipt: { receiptId: string; evaluations: unknown[]; mriSnapshotHash: string };
    };

    expect(body.decision.verdict).toBe('DENY');
    expect(body.decision.reasonCode).toBe('INVARIANT_VIOLATION');
    expect(body.receipt.receiptId).toMatch(/^cen:/);
    expect(body.receipt.mriSnapshotHash).toMatch(/^sha3-256:/);
    expect(body.receipt.evaluations.length).toBeGreaterThan(0);
  });

  it('returns the meta-constitutional collapse POD for operators', async () => {
    const response = await fetch(`${baseUrl}/pod/meta_constitutional_collapse`);
    expect(response.status).toBe(200);

    const body = (await response.json()) as {
      pod: { podId: string; rewardMultiplier: number; status: string };
      collapse: { generativeCoreId: string; metaInvariants: unknown[] };
    };

    expect(body.pod.podId).toBe('meta_constitutional_collapse');
    expect(body.pod.rewardMultiplier).toBe(500);
    expect(body.pod.status).toBe('recorded');
    expect(body.collapse.generativeCoreId).toBe('CML-15');
    expect(body.collapse.metaInvariants).toHaveLength(4);
  });

  it('returns CEN events, receipts, sovereignty ledger, NIMF forecast, and law-of-laws entries', async () => {
    const events = await fetch(`${baseUrl}/cen/events`);
    const eventsBody = (await events.json()) as { events: { receiptId: string }[] };
    const [receipt, missingReceipt, sovereignty, forecast, law] = await Promise.all([
      fetch(`${baseUrl}/cen/receipts/${encodeURIComponent(eventsBody.events[0]?.receiptId ?? '')}`),
      fetch(`${baseUrl}/cen/receipts/not-found`),
      fetch(`${baseUrl}/sovereignty-ledger`),
      fetch(`${baseUrl}/nimf/forecast`),
      fetch(`${baseUrl}/meta/law-of-laws`),
    ]);

    expect(events.status).toBe(200);
    expect(receipt.status).toBe(200);
    expect(missingReceipt.status).toBe(404);
    expect(sovereignty.status).toBe(200);
    expect(forecast.status).toBe(200);
    expect(law.status).toBe(200);

    expect(eventsBody.events.length).toBeGreaterThan(0);
    expect((await receipt.json()) as { receipt: { receiptId: string } }).toEqual(
      expect.objectContaining({ receipt: expect.objectContaining({ receiptId: expect.stringMatching(/^cen:/) }) }),
    );
    expect(((await sovereignty.json()) as { entries: unknown[] }).entries.length).toBeGreaterThan(0);
    expect(((await forecast.json()) as { forecast: { horizon: number } }).forecast.horizon).toBe(3);
    expect(((await law.json()) as { entries: unknown[] }).entries.length).toBeGreaterThan(0);
  });

  it('returns patch approval records as JSON for the operator console', async () => {
    const response = await fetch(`${baseUrl}/patches`);
    expect(response.status).toBe(200);
    expect(response.headers.get('content-type')).toContain('application/json');

    const body = (await response.json()) as {
      patches: { patchId: string; status: string; proposedBy: string }[];
    };
    expect(body.patches.length).toBeGreaterThan(0);
    expect(body.patches[0]).toEqual(expect.objectContaining({
      patchId: expect.any(String),
      status: expect.any(String),
      proposedBy: expect.any(String),
    }));
  });

  it('accepts evolution proposal and evaluation requests', async () => {
    const proposed = await fetch(`${baseUrl}/evolution/propose`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ invariantId: 'INV-OPS', expression: 'require governance >= 70' }),
    });
    const evaluated = await fetch(`${baseUrl}/evolution/evaluate`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ invariantId: 'INV-OPS', expression: 'require governance >= 70' }),
    });

    expect(proposed.status).toBe(200);
    expect(evaluated.status).toBe(200);
    expect(((await proposed.json()) as { proposal: { status: string } }).proposal.status).toBe('proposed');
    expect(((await evaluated.json()) as { decision: { decision: string } }).decision.decision).toMatch(/promote|retain|revert/);
  });

  it('surfaces governance evolution timeline entries with continuity and diffs', async () => {
    const response = await fetch(`${baseUrl}/evolution/timeline`);
    expect(response.status).toBe(200);

    const body = (await response.json()) as {
      timelineId: string;
      summary: {
        entryCount: number;
        continuityReports: number;
        governanceDiffs: number;
        replayReports: number;
        validatedAmendments: number;
      };
      entries: {
        eventId: string;
        stage: string;
        continuityReport: {
          reportId: string;
          valid: boolean;
          lineageValid: boolean;
          replayValid: boolean;
          chain: unknown[];
        };
        governanceDiff: { diffId: string; changes: unknown[] } | null;
        replayReport: { replayId: string; decision: string } | null;
      }[];
    };

    expect(body.timelineId).toBe('governance-evolution-timeline');
    expect(body.summary.entryCount).toBeGreaterThan(0);
    expect(body.entries.some((entry) => entry.continuityReport.valid && entry.continuityReport.lineageValid)).toBe(true);
    expect(body.entries.some((entry) => entry.governanceDiff !== null)).toBe(true);
    expect(body.entries.some((entry) => entry.replayReport !== null)).toBe(true);
  });
});
