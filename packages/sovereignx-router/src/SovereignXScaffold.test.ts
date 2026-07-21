import { describe, expect, it } from 'vitest';

import {
  SovereignX,
  SovereignXScaffold,
  SovereignXViolationError,
  createSovereignXScaffold,
  type SovereignXExecutionContract,
  type SovereignXClaim,
  type SovereignXProofSurface,
  type SovereignXReceipt,
} from './scaffold.ts';

function expectViolation(fn: () => unknown): SovereignXViolationError {
  try {
    fn();
  } catch (error) {
    expect(error).toBeInstanceOf(SovereignXViolationError);
    return error as SovereignXViolationError;
  }

  throw new Error('Expected a SovereignXViolationError to be thrown');
}

function createGovernance(intentId: string, extras: Partial<NonNullable<SovereignXReceipt['governance']>> = {}) {
  return {
    intentId,
    ...extras,
  };
}

function createExecutionContract(operation: string, subjectId: string, intentId: string): SovereignXExecutionContract {
  return {
    operation,
    subjectId,
    intentId,
    authority: `intent ${intentId} authorized by AAES governance`,
    evidence: {
      receipts: [`receipt-${operation}`],
      artifacts: [`receipt:receipt-${operation}`, `evidence:evidence-${operation}`, 'route:CPU'],
      summary: `${operation} execution is evidenced by the emitted receipt and routed evidence.`,
    },
    verification: {
      method: 'Replay the routed work item, validate the execution proof surface, and inspect the emitted receipt.',
      validator: 'SovereignX scaffold execution contract',
      replayArtifacts: [`receipt-${operation}`, `evidence-${operation}`],
      replayable: true,
    },
    compliance: {
      requirements: [
        'Intent must be registered before execution',
        'Authority must resolve through governed intent',
        'Evidence must exist for the execution path',
        'Verification must remain replayable',
        'Truth boundary must be declared',
      ],
      satisfied: true,
      issues: [],
    },
    truthBoundary: `SovereignX proves governed execution for ${subjectId}, not full cluster orchestration.`,
  };
}

describe('SovereignX scaffold', () => {
  it('exports the scaffold namespace and constructors', () => {
    expect(typeof SovereignX.initialize).toBe('function');
    expect(typeof SovereignX.createBuffer).toBe('function');
    expect(typeof SovereignX.createGraphicsPipeline).toBe('function');
    expect(typeof createSovereignXScaffold).toBe('function');
    expect(SovereignXScaffold).toBeTypeOf('function');
  });

  it('exposes the same scaffold API through the package entrypoint', async () => {
    const entrypoint = await import('./index.ts');

    expect(typeof entrypoint.SovereignX.initialize).toBe('function');
    expect(typeof entrypoint.createSovereignXScaffold).toBe('function');
    expect(typeof entrypoint.getDefaultDevice).toBe('function');
  });

  it('initializes the reference runtime and builds governed graphics resources', () => {
    const assetScaffold = createSovereignXScaffold({ applicationName: 'sovereignx-test-assets' });
    const assetSnapshot = assetScaffold.initialize();
    const assetDevice = assetScaffold.getDefaultDevice();

    expect(assetSnapshot.initialized).toBe(true);
    expect(assetSnapshot.deviceCount).toBe(1);
    expect(assetDevice.backend).toBe('reference');

    const buffer = assetScaffold.createBuffer({
      label: 'vertex-data',
      sizeBytes: 4096,
      usage: ['storage'],
      deviceId: assetDevice.id,
      governance: createGovernance('sx.create_buffer'),
    });

    const texture = assetScaffold.createTexture({
      label: 'framebuffer-texture',
      size: { width: 64, height: 64 },
      format: 'rgba8unorm',
      usage: ['sampled', 'render_target'],
      mipLevels: 1,
      deviceId: assetDevice.id,
      governance: createGovernance('sx.create_texture'),
    });

    const vertexShader = assetScaffold.createShader({
      label: 'vertex-shader',
      stage: 'vertex',
      source: 'void main() {}',
      deviceId: assetDevice.id,
      governance: createGovernance('sx.create_shader'),
    });

    const fragmentShader = assetScaffold.createShader({
      label: 'fragment-shader',
      stage: 'fragment',
      source: 'void main() {}',
      deviceId: assetDevice.id,
      governance: createGovernance('sx.create_shader'),
    });

    const graphicsPipeline = assetScaffold.createGraphicsPipeline({
      label: 'main-pipeline',
      vertexShaderId: vertexShader.id,
      fragmentShaderId: fragmentShader.id,
      deviceId: assetDevice.id,
      topology: 'triangle-list',
      governance: createGovernance('sx.create_graphics_pipeline'),
    });

    const frameScaffold = createSovereignXScaffold({ applicationName: 'sovereignx-test-frame' });
    const frameSnapshot = frameScaffold.initialize();
    const frameDevice = frameScaffold.getDefaultDevice();
    const graphicsQueue = frameScaffold.getGraphicsQueue(frameDevice.id);

    expect(frameSnapshot.initialized).toBe(true);
    expect(frameSnapshot.deviceCount).toBe(1);
    expect(graphicsQueue.kind).toBe('graphics');

    const swapchain = frameScaffold.createSwapchain({
      label: 'main-swapchain',
      deviceId: frameDevice.id,
      width: 1280,
      height: 720,
      format: 'rgba8unorm',
      imageCount: 2,
      governance: createGovernance('sx.create_swapchain'),
    });

    const renderPass = frameScaffold.createRenderPass({
      label: 'main-render-pass',
      colorFormats: ['rgba8unorm'],
      depthFormat: 'depth24plus',
      governance: createGovernance('sx.create_render_pass'),
    });

    const framebuffer = frameScaffold.createFramebuffer({
      label: 'main-framebuffer',
      renderPassId: renderPass.id,
      attachments: ['color-attachment-0'],
      width: 1280,
      height: 720,
      governance: createGovernance('sx.create_framebuffer'),
    });

    const commandList = frameScaffold.beginCommands(graphicsQueue, 'frame-1');
    commandList.record(`bind ${buffer.id}`);
    commandList.record(`draw with ${graphicsPipeline.id}`);

    const submitReceipt = frameScaffold.submitCommands(commandList, graphicsQueue, swapchain.id);
    const presentReceipt = frameScaffold.presentSwapchainFrame(swapchain);

    expect(buffer.deviceId).toBe(assetDevice.id);
    expect(texture.deviceId).toBe(assetDevice.id);
    expect(graphicsPipeline.kind).toBe('graphics');
    expect(framebuffer.renderPassId).toBe(renderPass.id);
    expect(submitReceipt.outcome).toBe('allow');
    expect(presentReceipt.outcome).toBe('allow');
    expect(submitReceipt.executionProofSurfaceId).toContain('execution-proof');
    expect(submitReceipt.executionContract.authority).toContain('sx.submit_commands');
    expect(assetScaffold.listReceipts().length).toBeGreaterThan(0);
    expect(frameScaffold.listReceipts().length).toBeGreaterThan(0);
    expect(frameScaffold.listProofSurfaces().length).toBeGreaterThan(0);
    expect(frameScaffold.listProofSurfaces().some((surface) => surface.kind === 'execution')).toBe(true);
    expect(assetScaffold.resolveClaim(`${buffer.id}-claim`)).not.toBeNull();
    expect(frameScaffold.resolveProofSurface(submitReceipt.executionProofSurfaceId)).toMatchObject({
      kind: 'execution',
    });
  });

  it('waits idle through a standalone lifecycle receipt', () => {
    const scaffold = createSovereignXScaffold({ applicationName: 'sovereignx-idle' });
    scaffold.initialize();

    const receipt = scaffold.waitIdle();

    expect(receipt.outcome).toBe('allow');
    expect(receipt.operation).toBe('waitIdle');
    expect(scaffold.listReceipts().some((entry) => entry.operation === 'waitIdle')).toBe(true);
  });

  it('rejects malformed descriptors with inspectable violation receipts', () => {
    const scaffold = createSovereignXScaffold({ applicationName: 'sovereignx-validation' });
    scaffold.initialize();

    const violation = expectViolation(() =>
      scaffold.createBuffer({
        label: 'broken-buffer',
        sizeBytes: 0,
        usage: [],
        governance: createGovernance('sx.create_buffer'),
      }),
    );

    expect(violation.receipt.outcome).toBe('deny');
    expect(violation.receipt.validationIssues.length).toBeGreaterThan(0);
    expect(violation.receipt.reason).toContain('buffer.sizeBytes');
  });

  it('applies governance limits and returns a deterministic non-allow receipt for over-budget work', () => {
    const scaffold = createSovereignXScaffold({ applicationName: 'sovereignx-governance' });
    scaffold.initialize();
    scaffold.setRuntimeLimits({
      maxTokensPerAgentPerMin: 1,
      maxFlopsPerAgentPerMin: 1,
      maxVramBytes: 1_000_000,
    });

    const violation = expectViolation(() =>
      scaffold.createBuffer({
        label: 'oversized-buffer',
        sizeBytes: 16_384,
        usage: ['storage'],
        governance: createGovernance('sx.create_buffer'),
      }),
    );

    expect(['deny', 'delay', 'throttle', 'quarantine']).toContain(violation.receipt.outcome);
    expect(violation.receipt.routeEvaluation).toBeDefined();
    expect(violation.receipt.routeDecision).toBeDefined();
  });

  it('resolves proof surfaces, claims, and receipts through an external evidence graph resolver', () => {
    const scaffold = createSovereignXScaffold({ applicationName: 'sovereignx-evidence' });
    scaffold.initialize();

    const externalClaim: SovereignXClaim = {
      id: 'external-claim',
      role: 'architect',
      statement: 'External claim',
      proofSurfaceId: 'external-surface',
      evidenceIds: ['external-evidence'],
      status: 'verified',
    };
    const externalSurface: SovereignXProofSurface = {
      id: 'external-surface',
      label: 'External surface',
      kind: 'pipeline',
      claimId: 'external-claim',
      evidenceIds: ['external-evidence'],
      proofLevel: 'P2',
      verificationStatus: 'Implemented',
      replayStatus: 'Replayable',
      operationalStatus: 'Prototype',
      truthBoundary: 'external truth boundary',
      sourceId: 'external-source',
      executionContract: createExecutionContract('resolve', 'external-source', 'sx.resolve'),
    };
    const externalReceipt: SovereignXReceipt = {
      id: 'external-receipt',
      kind: 'evidence',
      operation: 'resolve',
      subjectId: 'external-source',
      timestamp: new Date().toISOString(),
      intentId: 'sx.resolve',
      outcome: 'allow',
      reason: 'ok',
      routeDecision: { target: 'CPU', reason: 'local', mode: 'Normal' },
      routeEvaluation: {
        workItem: {
          id: 'work-1',
          agentId: 'agent-1',
          kind: 'tool_call',
          intentId: 'sx.resolve',
          costEstimateTokens: 1,
          costEstimateFlops: 1,
          costEstimateMs: 1,
          priority: 1,
        },
        runtime: {
          activeGpuJobs: 0,
          activeCpuJobs: 0,
          gpuUtil: 0,
          cpuUtil: 0,
          gpuTempC: 0,
          vramUsedBytes: 0,
          vramTotalBytes: 1,
        },
        limits: {
          maxGpuJobs: 1,
          maxCpuJobs: 1,
          maxConcurrentJobs: 1,
          maxGpuTempC: 1,
          maxVramBytes: 1,
          maxTokensPerAgentPerMin: 1,
          maxFlopsPerAgentPerMin: 1,
          gpuKindThreshold: 0,
        },
        measurementHealth: {
          trusted: true,
          stale: false,
          sampleCount: 1,
          windowMs: 1,
          temperatureVarianceC: 0,
          notes: [],
        },
        localDecision: { target: 'CPU', reason: 'local', mode: 'Normal' },
        effectiveDecision: { target: 'CPU', reason: 'local', mode: 'Normal' },
        ciemsDecisions: [],
        evidence: {
          workItemId: 'work-1',
          intentId: 'sx.resolve',
          kind: 'tool_call',
          estTokens: 1,
          estFlops: 1,
          runtime: {
            activeGpuJobs: 0,
            activeCpuJobs: 0,
            gpuUtil: 0,
            cpuUtil: 0,
            gpuTempC: 0,
            vramUsedBytes: 0,
            vramTotalBytes: 1,
          },
          limits: {
            maxGpuJobs: 1,
            maxCpuJobs: 1,
            maxConcurrentJobs: 1,
            maxGpuTempC: 1,
            maxVramBytes: 1,
            maxTokensPerAgentPerMin: 1,
            maxFlopsPerAgentPerMin: 1,
            gpuKindThreshold: 0,
          },
          localDecision: { target: 'CPU', reason: 'local', mode: 'Normal' },
          timestamp: new Date().toISOString(),
        },
      },
      validationIssues: [],
      governance: { intentId: 'sx.resolve' },
      executionProofSurfaceId: 'external-execution-surface',
      executionContract: createExecutionContract('resolve', 'external-source', 'sx.resolve'),
      metadata: {},
    };

    scaffold.setEvidenceGraphResolver({
      resolveClaim: (claimId) => (claimId === externalClaim.id ? externalClaim : null),
      resolveProofSurface: (proofSurfaceId) => (proofSurfaceId === externalSurface.id ? externalSurface : null),
      resolveReceipt: (receiptId) => (receiptId === externalReceipt.id ? externalReceipt : null),
    });

    expect(scaffold.resolveClaim('external-claim')).toEqual(externalClaim);
    expect(scaffold.resolveProofSurface('external-surface')).toEqual(externalSurface);
    expect(scaffold.resolveReceipt('external-receipt')).toEqual(externalReceipt);
  });
});
