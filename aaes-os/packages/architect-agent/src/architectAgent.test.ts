import { describe, expect, it } from 'vitest';

import {
  ArchitectAgentLoop,
  ArchitectRuntime,
  BuilderRuntime,
  IntegrationRuntime,
  SafetyRuntime,
  UGRUCRBridge,
  createDefaultUnifiedGovernanceContract,
  evaluateEgl1ReplayEquivalence,
  hashPreState,
} from './index.js';

describe('architect-agent contract bridge', () => {
  it('derives a CMC from UGC closure invariants', () => {
    const ugc = createDefaultUnifiedGovernanceContract();
    const bridge = new UGRUCRBridge(ugc);

    const situation = {
      situationId: 'situation:build-agent-loop',
      intent: 'build governed architect agent loop',
      risk: 'high',
      requestedRuntimes: ['ArchitectRuntime', 'BuilderRuntime', 'IntegrationRuntime', 'SafetyRuntime'],
      targetFiles: ['packages/architect-agent/src/index.ts'],
    } as const;
    const cmc = bridge.issueCognitiveModeContract(situation);
    const repeated = bridge.issueCognitiveModeContract(situation);

    expect(cmc.parent_contract_id).toBe(ugc.contract_id);
    expect(cmc.contract_id).toBe(repeated.contract_id);
    expect(cmc.contract_id).toMatch(/^CMC-situation-build-agent-loop-[0-9a-f]{12}$/);
    expect(cmc.invariants).toEqual(Object.keys(ugc.closure_invariants));
    expect(cmc.allowed_runtimes).toEqual([
      'ArchitectRuntime',
      'BuilderRuntime',
      'IntegrationRuntime',
      'SafetyRuntime',
    ]);
    expect(cmc.bounds.max_files).toBe(12);
    expect(cmc.bounds.max_depth).toBe(2);
  });

  it('rejects duplicate targets and situations outside CMC file bounds', () => {
    const bridge = new UGRUCRBridge();
    const base = {
      situationId: 'situation:bounds',
      intent: 'enforce cognitive mode bounds',
      risk: 'high' as const,
      requestedRuntimes: ['ArchitectRuntime', 'BuilderRuntime', 'IntegrationRuntime', 'SafetyRuntime'] as const,
    };

    expect(() =>
      bridge.issueCognitiveModeContract({
        ...base,
        targetFiles: ['src/a.ts', 'src/a.ts'],
      }),
    ).toThrow('targetFiles must be unique');
    expect(() =>
      bridge.issueCognitiveModeContract({
        ...base,
        targetFiles: Array.from({ length: 13 }, (_, index) => `src/${index}.ts`),
      }),
    ).toThrow('targetFiles exceeds max_files bound of 12');
  });

  it('runs the ALA runtime family under a CMC', () => {
    const ugc = createDefaultUnifiedGovernanceContract();
    const cmc = new UGRUCRBridge(ugc).issueCognitiveModeContract({
      situationId: 'situation:runtime-family',
      intent: 'create contract bridge and deterministic envelopes',
      risk: 'high',
      requestedRuntimes: ['ArchitectRuntime', 'BuilderRuntime', 'IntegrationRuntime', 'SafetyRuntime'],
      targetFiles: ['packages/architect-agent/src/index.ts'],
    });

    const architecture = new ArchitectRuntime().execute({
      contract: cmc,
      situation: {
        situationId: 'situation:runtime-family',
        intent: 'create contract bridge and deterministic envelopes',
        risk: 'high',
        requestedRuntimes: cmc.allowed_runtimes,
        targetFiles: cmc.bounds.target_files,
      },
    });
    const build = new BuilderRuntime().execute({
      contract: cmc,
      architecture,
      pre_state: {
        'packages/architect-agent/src/index.ts': 'original runtime source',
      },
    });
    const integration = new IntegrationRuntime().execute({
      contract: cmc,
      architecture,
      build,
      pre_state_hash: build.pre_state_hash,
    });
    const integrationEnvelope = integration.envelopes[0]!;
    const safety = new SafetyRuntime().evaluate({
      contract: cmc,
      integration,
      replayed_integration: integration,
    });

    expect(architecture.invariants).toEqual(cmc.invariants);
    expect(architecture.components.map((component) => component.name)).toEqual([
      'UGRUCRBridge',
      'ArchitectRuntime',
      'BuilderRuntime',
      'IntegrationRuntime',
      'SafetyRuntime',
    ]);
    expect(build.patches).toHaveLength(1);
    expect(build.patches[0]?.path).toBe('packages/architect-agent/src/index.ts');
    expect(integration.envelopes).toHaveLength(1);
    expect(integration.envelopes[0]?.runtime).toBe('IntegrationRuntime');
    expect(integration.envelopes[0]?.pre_state_hash).toBe(build.pre_state_hash);
    expect(safety.verdict).toBe('ALLOW');
  });

  it('creates deterministic reversible envelopes and evaluates EGL-1 replay equivalence', () => {
    const ugc = createDefaultUnifiedGovernanceContract();
    const cmc = new UGRUCRBridge(ugc).issueCognitiveModeContract({
      situationId: 'situation:envelope',
      intent: 'wrap deterministic mutation envelopes',
      risk: 'medium',
      requestedRuntimes: ['ArchitectRuntime', 'BuilderRuntime', 'IntegrationRuntime', 'SafetyRuntime'],
      targetFiles: ['packages/architect-agent/src/index.ts'],
    });
    const architecture = new ArchitectRuntime().execute({
      contract: cmc,
      situation: {
        situationId: 'situation:envelope',
        intent: 'wrap deterministic mutation envelopes',
        risk: 'medium',
        requestedRuntimes: cmc.allowed_runtimes,
        targetFiles: cmc.bounds.target_files,
      },
    });
    const builderRuntime = new BuilderRuntime();
    const build = builderRuntime.execute({
      contract: cmc,
      architecture,
      pre_state: {
        'packages/architect-agent/src/index.ts': 'state a source',
      },
    });
    const changedBuild = builderRuntime.execute({
      contract: cmc,
      architecture,
      pre_state: {
        'packages/architect-agent/src/index.ts': 'state b source',
      },
    });
    const integrationRuntime = new IntegrationRuntime();

    const first = integrationRuntime.execute({
      contract: cmc,
      architecture,
      build,
      pre_state_hash: build.pre_state_hash,
    });
    const repeated = integrationRuntime.execute({
      contract: cmc,
      architecture,
      build,
      pre_state_hash: build.pre_state_hash,
    });
    const changedState = integrationRuntime.execute({
      contract: cmc,
      architecture,
      build: changedBuild,
      pre_state_hash: changedBuild.pre_state_hash,
    });

    expect(first.envelopes[0]?.envelope_id).toBe(repeated.envelopes[0]?.envelope_id);
    expect(first.envelopes[0]?.envelope_id).not.toBe(changedState.envelopes[0]?.envelope_id);
    expect(first.envelopes[0]?.patches[0]?.reverse_patch).toEqual({
      operation: 'restore',
      path: 'packages/architect-agent/src/index.ts',
      content: 'state a source',
      content_hash: expect.stringMatching(/^sha256:[0-9a-f]{64}$/),
    });
    expect(evaluateEgl1ReplayEquivalence(first.envelopes[0]!, repeated.envelopes[0]!)).toEqual({
      equivalent: true,
      criterion_id: 'EGL-1',
      reason: 'deterministic envelope replay equivalent',
    });
    expect(evaluateEgl1ReplayEquivalence(first.envelopes[0]!, changedState.envelopes[0]!).equivalent).toBe(false);
  });

  it('places every authorized target in one deterministic multi-patch envelope', () => {
    const cmc = new UGRUCRBridge().issueCognitiveModeContract({
      situationId: 'situation:multi-patch',
      intent: 'build a multi-patch deterministic envelope',
      risk: 'medium',
      requestedRuntimes: ['ArchitectRuntime', 'BuilderRuntime', 'IntegrationRuntime', 'SafetyRuntime'],
      targetFiles: [
        'packages/architect-agent/src/index.ts',
        'packages/architect-agent/src/contracts.ts',
      ],
    });
    const situation = {
      situationId: 'situation:multi-patch',
      intent: 'build a multi-patch deterministic envelope',
      risk: 'medium',
      requestedRuntimes: cmc.allowed_runtimes,
      targetFiles: cmc.bounds.target_files,
    } as const;
    const architecture = new ArchitectRuntime().execute({ contract: cmc, situation });
    const build = new BuilderRuntime().execute({
      contract: cmc,
      architecture,
      pre_state: {
        'packages/architect-agent/src/index.ts': 'index source',
        'packages/architect-agent/src/contracts.ts': null,
      },
    });
    const integration = new IntegrationRuntime().execute({
      contract: cmc,
      architecture,
      build,
      pre_state_hash: build.pre_state_hash,
    });

    expect(build.patches.map((patch) => patch.path)).toEqual(situation.targetFiles);
    expect(integration.envelopes).toHaveLength(1);
    expect(integration.envelopes[0]?.patches).toHaveLength(2);
    expect(new Set(integration.envelopes[0]?.patches.map((patch) => patch.patch_hash)).size).toBe(2);
    expect(() =>
      new IntegrationRuntime().execute({
        contract: cmc,
        architecture,
        build: { ...build, patches: build.patches.slice(0, 1) },
        pre_state_hash: build.pre_state_hash,
      }),
    ).toThrow('build patch targets do not match contract');
  });

  it('binds exact inverse patches to the declared pre-state snapshot', () => {
    const targets = ['src/existing.ts', 'src/new.ts'] as const;
    const preState = {
      'src/existing.ts': 'export const version = 1;\n',
      'src/new.ts': null,
    } as const;
    const preStateHash = hashPreState(preState);
    const cmc = new UGRUCRBridge().issueCognitiveModeContract({
      situationId: 'situation:exact-reversal',
      intent: 'prove exact deterministic reversal',
      risk: 'high',
      requestedRuntimes: ['ArchitectRuntime', 'BuilderRuntime', 'IntegrationRuntime', 'SafetyRuntime'],
      targetFiles: targets,
    });
    const architecture = new ArchitectRuntime().execute({
      contract: cmc,
      situation: {
        situationId: 'situation:exact-reversal',
        intent: 'prove exact deterministic reversal',
        risk: 'high',
        requestedRuntimes: cmc.allowed_runtimes,
        targetFiles: targets,
      },
    });
    const build = new BuilderRuntime().execute({
      contract: cmc,
      architecture,
      pre_state: preState,
    });
    const integrationRuntime = new IntegrationRuntime();
    const integration = integrationRuntime.execute({
      contract: cmc,
      architecture,
      build,
      pre_state_hash: preStateHash,
    });

    expect(integration.envelopes[0]?.patches[0]?.reverse_patch).toMatchObject({
      operation: 'restore',
      path: 'src/existing.ts',
      content: 'export const version = 1;\n',
    });
    expect(integration.envelopes[0]?.patches[1]?.reverse_patch).toEqual({
      operation: 'delete',
      path: 'src/new.ts',
      content: null,
      content_hash: null,
    });
    expect(() =>
      integrationRuntime.execute({
        contract: cmc,
        architecture,
        build,
        pre_state_hash: 'sha256:not-the-build-state',
      }),
    ).toThrow('pre_state_hash does not match build pre-state');
  });

  it('vetoes mutation envelopes whose content no longer matches their hashes', () => {
    const target = 'src/governed.ts';
    const cmc = new UGRUCRBridge().issueCognitiveModeContract({
      situationId: 'situation:tamper-veto',
      intent: 'veto post-envelope mutation',
      risk: 'critical',
      requestedRuntimes: ['ArchitectRuntime', 'BuilderRuntime', 'IntegrationRuntime', 'SafetyRuntime'],
      targetFiles: [target],
    });
    const architecture = new ArchitectRuntime().execute({
      contract: cmc,
      situation: {
        situationId: 'situation:tamper-veto',
        intent: 'veto post-envelope mutation',
        risk: 'critical',
        requestedRuntimes: cmc.allowed_runtimes,
        targetFiles: [target],
      },
    });
    const build = new BuilderRuntime().execute({
      contract: cmc,
      architecture,
      pre_state: { [target]: 'trusted source' },
    });
    const integration = new IntegrationRuntime().execute({
      contract: cmc,
      architecture,
      build,
      pre_state_hash: build.pre_state_hash,
    });
    const originalEnvelope = integration.envelopes[0]!;
    const originalPatch = originalEnvelope.patches[0]!;
    const tamperedIntegration = {
      ...integration,
      envelopes: [
        {
          ...originalEnvelope,
          patches: [{ ...originalPatch, content: 'tampered source' }],
        },
      ],
    };

    const safetyRuntime = new SafetyRuntime();
    expect(
      safetyRuntime.evaluate({
        contract: cmc,
        integration,
        replayed_integration: tamperedIntegration,
      } as never),
    ).toMatchObject({
      verdict: 'DENY',
      reason: 'EGL-1 replay mismatch',
    });
    expect(safetyRuntime.evaluate({ contract: cmc, integration } as never)).toMatchObject({
      verdict: 'DENY',
      reason: 'missing replayed integration',
    });
    expect(
      safetyRuntime.evaluate({
        contract: cmc,
        integration: { ...integration, envelopes: [] },
        replayed_integration: { ...integration, envelopes: [] },
      }),
    ).toMatchObject({
      verdict: 'DENY',
      reason: 'integration contains no mutation envelopes',
    });
    expect(
      safetyRuntime.evaluate({
        contract: cmc,
        integration: tamperedIntegration,
        replayed_integration: tamperedIntegration,
      }),
    ).toMatchObject({
      verdict: 'DENY',
      reason: 'patch hash mismatch',
    });
  });

  it('executes the full architect-agent loop as one governed act', () => {
    const loop = new ArchitectAgentLoop(createDefaultUnifiedGovernanceContract());

    const act = loop.execute({
      situation: {
        situationId: 'situation:full-loop',
        intent: 'build the automatic UGR to UCR architect-agent loop',
        risk: 'high',
        requestedRuntimes: ['ArchitectRuntime', 'BuilderRuntime', 'IntegrationRuntime', 'SafetyRuntime'],
        targetFiles: ['packages/architect-agent/src/index.ts'],
      },
      pre_state: {
        'packages/architect-agent/src/index.ts': 'runtime source before act',
      },
      issued_at: '2026-06-30T20:00:00.000Z',
    });

    expect(act.cmc.parent_contract_id).toBe('UGC-v1');
    expect(act.architecture.contract_id).toBe(act.cmc.contract_id);
    expect(act.build.contract_id).toBe(act.cmc.contract_id);
    expect(act.integration.envelopes[0]?.contract_id).toBe(act.cmc.contract_id);
    expect(act.safety.verdict).toBe('ALLOW');
    expect(act.egl.equivalent).toBe(true);
    expect(act.receipt.receiptId).toMatch(/^evidence:/);
    expect(act.receipt.kind).toBe('runtime');
    expect(act.receipt.claimLabel).toBe('architect-agent-loop:allow');
    expect(act.receipt.issuedAt).toBe('2026-06-30T20:00:00.000Z');
  });
});
