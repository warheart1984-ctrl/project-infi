import { createHash } from 'node:crypto';
import { createEvidenceReceipt, type EvidenceReceipt } from '@aaes-os/evidence-receipts';

export type CognitiveRisk = 'low' | 'medium' | 'high' | 'critical';
export type ArchitectRuntimeName =
  | 'ArchitectRuntime'
  | 'BuilderRuntime'
  | 'IntegrationRuntime'
  | 'SafetyRuntime';

export interface ClosureInvariant {
  readonly id: string;
  readonly rule: string;
  readonly applies_to: 'all_layers';
}

export interface UnifiedGovernanceContract {
  readonly contract_id: string;
  readonly issued_by: 'UGR';
  readonly scope: 'global';
  readonly applies_to_layers: '1-infinity';
  readonly closure_invariants: Readonly<Record<string, ClosureInvariant>>;
  readonly governance_chain: Readonly<{
    readonly meta_governance: 'UGR';
    readonly runtime_governance: 'UCR';
    readonly cognitive_governance: 'ALA';
    readonly immune_governance: 'IGR';
  }>;
  readonly mutation_physics: Readonly<{
    readonly envelope_format: 'deterministic-reversible';
    readonly reversibility: true;
    readonly replay_equivalence: 'EGL-1';
  }>;
}

export interface CognitiveSituation {
  readonly situationId: string;
  readonly intent: string;
  readonly risk: CognitiveRisk;
  readonly requestedRuntimes: ReadonlyArray<ArchitectRuntimeName>;
  readonly targetFiles: ReadonlyArray<string>;
}

export interface CognitiveModeContract {
  readonly contract_id: string;
  readonly parent_contract_id: string;
  readonly runtime_family: 'ALA';
  readonly allowed_runtimes: ReadonlyArray<ArchitectRuntimeName>;
  readonly invariants: ReadonlyArray<string>;
  readonly bounds: Readonly<{
    readonly max_depth: number;
    readonly max_files: number;
    readonly target_files: ReadonlyArray<string>;
  }>;
}

export interface ArchitectureComponent {
  readonly name: 'UGRUCRBridge' | ArchitectRuntimeName;
  readonly responsibility: string;
}

export interface ArchitecturePlan {
  readonly plan_id: string;
  readonly contract_id: string;
  readonly intent: string;
  readonly invariants: ReadonlyArray<string>;
  readonly components: ReadonlyArray<ArchitectureComponent>;
  readonly risks: ReadonlyArray<string>;
}

export interface ArchitectRuntimeInput {
  readonly contract: CognitiveModeContract;
  readonly situation: CognitiveSituation;
}

export type PreStateSnapshot = Readonly<Record<string, string | null>>;

export interface MutationPatch {
  readonly operation: 'upsert';
  readonly path: string;
  readonly content: string;
  readonly previous_content: string | null;
  readonly previous_content_hash: string | null;
}

export interface BuildPlan {
  readonly build_id: string;
  readonly contract_id: string;
  readonly pre_state_hash: string;
  readonly patches: ReadonlyArray<MutationPatch>;
}

export interface BuilderRuntimeInput {
  readonly contract: CognitiveModeContract;
  readonly architecture: ArchitecturePlan;
  readonly pre_state: PreStateSnapshot;
}

export type ReversePatch =
  | Readonly<{
      operation: 'restore';
      path: string;
      content: string;
      content_hash: string;
    }>
  | Readonly<{
      operation: 'delete';
      path: string;
      content: null;
      content_hash: null;
    }>;

export interface EnvelopePatch extends MutationPatch {
  readonly patch_hash: string;
  readonly reverse_patch: ReversePatch;
}

export interface DeterministicMutationEnvelope {
  readonly envelope_id: string;
  readonly runtime: 'IntegrationRuntime';
  readonly contract_id: string;
  readonly parent_contract_id: string;
  readonly pre_state_hash: string;
  readonly replay_profile: 'EGL-1';
  readonly invariants_applied: ReadonlyArray<string>;
  readonly patches: ReadonlyArray<EnvelopePatch>;
}

export interface IntegrationResult {
  readonly integration_id: string;
  readonly contract_id: string;
  readonly envelopes: ReadonlyArray<DeterministicMutationEnvelope>;
}

export interface IntegrationRuntimeInput {
  readonly contract: CognitiveModeContract;
  readonly architecture: ArchitecturePlan;
  readonly build: BuildPlan;
  readonly pre_state_hash: string;
}

export interface SafetyDecision {
  readonly verdict: 'ALLOW' | 'DENY';
  readonly reason: string;
  readonly checked_invariants: ReadonlyArray<string>;
}

export interface SafetyRuntimeInput {
  readonly contract: CognitiveModeContract;
  readonly integration: IntegrationResult;
  readonly replayed_integration: IntegrationResult;
}

export interface Egl1EquivalenceResult {
  readonly equivalent: boolean;
  readonly criterion_id: 'EGL-1';
  readonly reason: string;
}

export interface ArchitectAgentLoopInput {
  readonly situation: CognitiveSituation;
  readonly pre_state: PreStateSnapshot;
  readonly issued_at: string;
}

export interface ArchitectAgentAct {
  readonly act_id: string;
  readonly ugc: UnifiedGovernanceContract;
  readonly cmc: CognitiveModeContract;
  readonly architecture: ArchitecturePlan;
  readonly build: BuildPlan;
  readonly integration: IntegrationResult;
  readonly safety: SafetyDecision;
  readonly egl: Egl1EquivalenceResult;
  readonly receipt: EvidenceReceipt;
}

const CLOSURE_INVARIANTS: Readonly<Record<string, ClosureInvariant>> = Object.freeze({
  I1_governance_supremacy: Object.freeze({
    id: 'I1_governance_supremacy',
    rule: 'No layer may bypass constitutional governance or execute outside policy.',
    applies_to: 'all_layers',
  }),
  I2_envelope_bound_mutation: Object.freeze({
    id: 'I2_envelope_bound_mutation',
    rule: 'All mutation must occur through deterministic, reversible envelopes with replay equivalence.',
    applies_to: 'all_layers',
  }),
  I3_contract_closure: Object.freeze({
    id: 'I3_contract_closure',
    rule: 'No layer may authorize itself; all cognitive acts must trace to a valid UGR-issued contract.',
    applies_to: 'all_layers',
  }),
  I4_replay_equivalence: Object.freeze({
    id: 'I4_replay_equivalence',
    rule: 'All cognitive acts must be replay-equivalent under identical state and contract.',
    applies_to: 'all_layers',
  }),
  I5_layer_non_proliferation: Object.freeze({
    id: 'I5_layer_non_proliferation',
    rule: 'No new layer may be created unless it reduces drift, increases determinism, or strengthens governance.',
    applies_to: 'all_layers',
  }),
});

export function createDefaultUnifiedGovernanceContract(): UnifiedGovernanceContract {
  return Object.freeze({
    contract_id: 'UGC-v1',
    issued_by: 'UGR',
    scope: 'global',
    applies_to_layers: '1-infinity',
    closure_invariants: CLOSURE_INVARIANTS,
    governance_chain: Object.freeze({
      meta_governance: 'UGR',
      runtime_governance: 'UCR',
      cognitive_governance: 'ALA',
      immune_governance: 'IGR',
    }),
    mutation_physics: Object.freeze({
      envelope_format: 'deterministic-reversible',
      reversibility: true,
      replay_equivalence: 'EGL-1',
    }),
  });
}

export class UGRUCRBridge {
  constructor(private readonly ugc: UnifiedGovernanceContract = createDefaultUnifiedGovernanceContract()) {}

  issueCognitiveModeContract(situation: CognitiveSituation): CognitiveModeContract {
    if (!situation.situationId.trim()) throw new Error('situationId is required');
    if (!situation.intent.trim()) throw new Error('intent is required');
    if (situation.requestedRuntimes.length === 0) throw new Error('requestedRuntimes must not be empty');
    if (situation.targetFiles.length === 0) throw new Error('targetFiles must not be empty');
    if (situation.targetFiles.some((target) => !target.trim())) {
      throw new Error('targetFiles must not contain empty paths');
    }
    if (new Set(situation.targetFiles).size !== situation.targetFiles.length) {
      throw new Error('targetFiles must be unique');
    }

    const allowed = uniqueRuntimes(situation.requestedRuntimes);
    const maxFiles = situation.risk === 'low' ? 24 : 12;
    if (situation.targetFiles.length > maxFiles) {
      throw new Error(`targetFiles exceeds max_files bound of ${maxFiles}`);
    }
    const idSeed = {
      parent_contract_id: this.ugc.contract_id,
      situation,
      invariants: Object.keys(this.ugc.closure_invariants),
      allowed,
    };

    return Object.freeze({
      contract_id: `CMC-${slug(situation.situationId)}-${sha256Hex(idSeed).slice(0, 12)}`,
      parent_contract_id: this.ugc.contract_id,
      runtime_family: 'ALA',
      allowed_runtimes: Object.freeze(allowed),
      invariants: Object.freeze(Object.keys(this.ugc.closure_invariants)),
      bounds: Object.freeze({
        max_depth: situation.risk === 'critical' ? 1 : 2,
        max_files: maxFiles,
        target_files: Object.freeze([...situation.targetFiles]),
      }),
    });
  }
}

export class ArchitectRuntime {
  execute(input: ArchitectRuntimeInput): ArchitecturePlan {
    assertRuntimeAllowed(input.contract, 'ArchitectRuntime');
    if (!input.situation.intent.trim()) throw new Error('situation intent is required');

    const components: ArchitectureComponent[] = [
      {
        name: 'UGRUCRBridge',
        responsibility: 'derive CognitiveModeContract from UnifiedGovernanceContract',
      },
      {
        name: 'ArchitectRuntime',
        responsibility: 'convert cognitive situation into architecture plan',
      },
      {
        name: 'BuilderRuntime',
        responsibility: 'convert architecture plan into deterministic patch proposals',
      },
      {
        name: 'IntegrationRuntime',
        responsibility: 'wrap patch proposals in reversible deterministic mutation envelopes',
      },
      {
        name: 'SafetyRuntime',
        responsibility: 'veto envelope drift, missing invariants, or replay inequivalence',
      },
    ];

    return Object.freeze({
      plan_id: `ARCH-${sha256Hex({
        contract_id: input.contract.contract_id,
        intent: input.situation.intent,
        files: input.situation.targetFiles,
      }).slice(0, 12)}`,
      contract_id: input.contract.contract_id,
      intent: input.situation.intent,
      invariants: Object.freeze([...input.contract.invariants]),
      components: Object.freeze(components),
      risks: Object.freeze(input.situation.risk === 'low' ? [] : ['requires safety runtime review']),
    });
  }
}

export class BuilderRuntime {
  execute(input: BuilderRuntimeInput): BuildPlan {
    assertRuntimeAllowed(input.contract, 'BuilderRuntime');
    if (input.architecture.contract_id !== input.contract.contract_id) {
      throw new Error('architecture contract mismatch');
    }
    if (input.contract.bounds.target_files.length === 0) {
      throw new Error('at least one target file is required');
    }

    for (const target of input.contract.bounds.target_files) {
      if (!Object.prototype.hasOwnProperty.call(input.pre_state, target)) {
        throw new Error(`pre_state is missing target: ${target}`);
      }
    }

    const preStateHash = hashPreState(input.pre_state);
    const patches = Object.freeze(
      input.contract.bounds.target_files.map((target) => {
        const previousContent = input.pre_state[target] ?? null;
        return Object.freeze({
          operation: 'upsert' as const,
          path: target,
          content: stableStringify({
            architecture_plan: input.architecture.plan_id,
            contract_id: input.contract.contract_id,
            invariants: input.architecture.invariants,
            target,
          }),
          previous_content: previousContent,
          previous_content_hash: previousContent === null ? null : hashContent(previousContent),
        });
      }),
    );

    return Object.freeze({
      build_id: `BUILD-${sha256Hex({
        contract_id: input.contract.contract_id,
        pre_state_hash: preStateHash,
        patches,
      }).slice(0, 12)}`,
      contract_id: input.contract.contract_id,
      pre_state_hash: preStateHash,
      patches,
    });
  }
}

export class IntegrationRuntime {
  execute(input: IntegrationRuntimeInput): IntegrationResult {
    assertRuntimeAllowed(input.contract, 'IntegrationRuntime');
    if (!input.pre_state_hash.trim()) throw new Error('pre_state_hash is required');
    if (input.architecture.contract_id !== input.contract.contract_id) {
      throw new Error('architecture contract mismatch');
    }
    if (input.build.contract_id !== input.contract.contract_id) {
      throw new Error('build contract mismatch');
    }
    if (
      stableStringify(input.build.patches.map((patch) => patch.path)) !==
      stableStringify(input.contract.bounds.target_files)
    ) {
      throw new Error('build patch targets do not match contract');
    }
    if (input.build.pre_state_hash !== input.pre_state_hash) {
      throw new Error('pre_state_hash does not match build pre-state');
    }

    const patches = Object.freeze(input.build.patches.map((patch) => withReversePatch(patch)));
    const envelopeBase = {
      runtime: 'IntegrationRuntime',
      contract_id: input.contract.contract_id,
      parent_contract_id: input.contract.parent_contract_id,
      pre_state_hash: input.pre_state_hash,
      replay_profile: 'EGL-1',
      invariants_applied: input.architecture.invariants,
      patches,
    } as const;
    const envelope: DeterministicMutationEnvelope = Object.freeze({
      envelope_id: `ENV-${sha256Hex(envelopeBase)}`,
      runtime: 'IntegrationRuntime',
      contract_id: input.contract.contract_id,
      parent_contract_id: input.contract.parent_contract_id,
      pre_state_hash: input.pre_state_hash,
      replay_profile: 'EGL-1',
      invariants_applied: Object.freeze([...input.architecture.invariants]),
      patches,
    });

    return Object.freeze({
      integration_id: `INT-${sha256Hex({ contract_id: input.contract.contract_id, envelopes: [envelope.envelope_id] }).slice(0, 12)}`,
      contract_id: input.contract.contract_id,
      envelopes: Object.freeze([envelope]),
    });
  }
}

export class SafetyRuntime {
  evaluate(input: SafetyRuntimeInput): SafetyDecision {
    assertRuntimeAllowed(input.contract, 'SafetyRuntime');

    if (!input.replayed_integration) {
      return deny(input.contract, 'missing replayed integration');
    }
    if (input.integration.envelopes.length !== input.replayed_integration.envelopes.length) {
      return deny(input.contract, 'EGL-1 replay mismatch');
    }
    for (let index = 0; index < input.integration.envelopes.length; index += 1) {
      const envelope = input.integration.envelopes[index];
      const replayedEnvelope = input.replayed_integration.envelopes[index];
      if (
        !envelope ||
        !replayedEnvelope ||
        !evaluateEgl1ReplayEquivalence(envelope, replayedEnvelope).equivalent
      ) {
        return deny(input.contract, 'EGL-1 replay mismatch');
      }
    }

    for (const integration of [input.integration, input.replayed_integration]) {
      if (integration.contract_id !== input.contract.contract_id) {
        return deny(input.contract, 'integration contract mismatch');
      }
      if (integration.envelopes.length === 0) {
        return deny(input.contract, 'integration contains no mutation envelopes');
      }
      for (const envelope of integration.envelopes) {
        if (envelope.contract_id !== input.contract.contract_id) {
          return deny(input.contract, 'envelope contract mismatch');
        }
        if (envelope.parent_contract_id !== input.contract.parent_contract_id) {
          return deny(input.contract, 'envelope parent contract mismatch');
        }
        if (envelope.replay_profile !== 'EGL-1') {
          return deny(input.contract, 'missing EGL-1 replay profile');
        }
        if (envelope.invariants_applied.length !== input.contract.invariants.length) {
          return deny(input.contract, 'invariant set mismatch');
        }
        if (
          stableStringify(envelope.patches.map((patch) => patch.path)) !==
          stableStringify(input.contract.bounds.target_files)
        ) {
          return deny(input.contract, 'patch target set mismatch');
        }
        for (const invariant of input.contract.invariants) {
          if (!envelope.invariants_applied.includes(invariant)) {
            return deny(input.contract, `missing invariant: ${invariant}`);
          }
        }
        for (const patch of envelope.patches) {
          if (patch.patch_hash !== `sha256:${sha256Hex(toMutationPatch(patch))}`) {
            return deny(input.contract, 'patch hash mismatch');
          }
          if (!input.contract.bounds.target_files.includes(patch.path)) {
            return deny(input.contract, `patch target is outside contract: ${patch.path}`);
          }
          if (
            patch.previous_content_hash !==
            (patch.previous_content === null ? null : hashContent(patch.previous_content))
          ) {
            return deny(input.contract, 'previous content hash mismatch');
          }
          if (patch.reverse_patch.path !== patch.path) {
            return deny(input.contract, 'patch is not reversible');
          }
          if (patch.previous_content === null) {
            if (
              patch.reverse_patch.operation !== 'delete' ||
              patch.reverse_patch.content !== null ||
              patch.reverse_patch.content_hash !== null
            ) {
              return deny(input.contract, 'new-file patch does not have an exact delete inverse');
            }
          } else if (
            patch.reverse_patch.operation !== 'restore' ||
            patch.reverse_patch.content !== patch.previous_content ||
            patch.reverse_patch.content_hash !== hashContent(patch.previous_content)
          ) {
            return deny(input.contract, 'existing-file patch does not have an exact restore inverse');
          }
        }
        if (envelope.envelope_id !== `ENV-${sha256Hex(toEnvelopeBase(envelope))}`) {
          return deny(input.contract, 'envelope hash mismatch');
        }
      }
    }

    return Object.freeze({
      verdict: 'ALLOW',
      reason: 'all envelopes satisfy contract, reversibility, and replay profile',
      checked_invariants: Object.freeze([...input.contract.invariants]),
    });
  }
}

export class ArchitectAgentLoop {
  private readonly bridge: UGRUCRBridge;
  private readonly architectRuntime = new ArchitectRuntime();
  private readonly builderRuntime = new BuilderRuntime();
  private readonly integrationRuntime = new IntegrationRuntime();
  private readonly safetyRuntime = new SafetyRuntime();

  constructor(private readonly ugc: UnifiedGovernanceContract = createDefaultUnifiedGovernanceContract()) {
    this.bridge = new UGRUCRBridge(ugc);
  }

  execute(input: ArchitectAgentLoopInput): ArchitectAgentAct {
    if (!input.issued_at.trim()) throw new Error('issued_at is required');

    const cmc = this.bridge.issueCognitiveModeContract(input.situation);
    const architecture = this.architectRuntime.execute({
      contract: cmc,
      situation: input.situation,
    });
    const build = this.builderRuntime.execute({
      contract: cmc,
      architecture,
      pre_state: input.pre_state,
    });
    const integrationInput: IntegrationRuntimeInput = {
      contract: cmc,
      architecture,
      build,
      pre_state_hash: build.pre_state_hash,
    };
    const integration = this.integrationRuntime.execute(integrationInput);
    const replayedIntegration = this.integrationRuntime.execute(integrationInput);
    const envelope = integration.envelopes[0];
    const replayedEnvelope = replayedIntegration.envelopes[0];
    if (!envelope || !replayedEnvelope) {
      throw new Error('integration must produce an envelope for EGL-1 evaluation');
    }

    const egl = evaluateEgl1ReplayEquivalence(envelope, replayedEnvelope);
    const safety = this.safetyRuntime.evaluate({
      contract: cmc,
      integration,
      replayed_integration: replayedIntegration,
    });
    const actSubject = Object.freeze({
      ugc_contract_id: this.ugc.contract_id,
      cmc_contract_id: cmc.contract_id,
      architecture_plan_id: architecture.plan_id,
      build_id: build.build_id,
      integration_id: integration.integration_id,
      envelope_ids: Object.freeze(integration.envelopes.map((entry) => entry.envelope_id)),
      egl_criterion_id: egl.criterion_id,
      egl_equivalent: egl.equivalent,
      safety_verdict: safety.verdict,
    });
    const actId = `ACT-${sha256Hex(actSubject)}`;
    const receipt = Object.freeze(
      createEvidenceReceipt({
        claimLabel: `architect-agent-loop:${safety.verdict.toLowerCase()}`,
        subsystem: 'architect-agent-loop',
        evidenceRefs: [
          this.ugc.contract_id,
          cmc.contract_id,
          architecture.plan_id,
          build.build_id,
          integration.integration_id,
          ...integration.envelopes.map((entry) => entry.envelope_id),
          `${egl.criterion_id}:${String(egl.equivalent)}`,
        ],
        subject: Object.freeze({ act_id: actId, ...actSubject }),
        kind: 'runtime',
        issuedAt: input.issued_at,
      }),
    );

    return Object.freeze({
      act_id: actId,
      ugc: this.ugc,
      cmc,
      architecture,
      build,
      integration,
      safety,
      egl,
      receipt,
    });
  }
}

export function evaluateEgl1ReplayEquivalence(
  left: DeterministicMutationEnvelope,
  right: DeterministicMutationEnvelope,
): Egl1EquivalenceResult {
  const equivalent =
    left.envelope_id === right.envelope_id &&
    left.contract_id === right.contract_id &&
    left.pre_state_hash === right.pre_state_hash &&
    stableStringify(left.patches) === stableStringify(right.patches) &&
    stableStringify(left.invariants_applied) === stableStringify(right.invariants_applied);

  return Object.freeze({
    equivalent,
    criterion_id: 'EGL-1',
    reason: equivalent
      ? 'deterministic envelope replay equivalent'
      : 'deterministic envelope replay mismatch',
  });
}

function uniqueRuntimes(runtimes: ReadonlyArray<ArchitectRuntimeName>): ArchitectRuntimeName[] {
  return [...new Set(runtimes)];
}

function assertRuntimeAllowed(contract: CognitiveModeContract, runtime: ArchitectRuntimeName): void {
  if (!contract.allowed_runtimes.includes(runtime)) {
    throw new Error(`${runtime} is not allowed by ${contract.contract_id}`);
  }
}

function withReversePatch(patch: MutationPatch): EnvelopePatch {
  return Object.freeze({
    ...patch,
    patch_hash: `sha256:${sha256Hex(patch)}`,
    reverse_patch:
      patch.previous_content === null
        ? Object.freeze({
            operation: 'delete' as const,
            path: patch.path,
            content: null,
            content_hash: null,
          })
        : Object.freeze({
            operation: 'restore' as const,
            path: patch.path,
            content: patch.previous_content,
            content_hash: hashContent(patch.previous_content),
          }),
  });
}

function toMutationPatch(patch: EnvelopePatch): MutationPatch {
  return {
    operation: patch.operation,
    path: patch.path,
    content: patch.content,
    previous_content: patch.previous_content,
    previous_content_hash: patch.previous_content_hash,
  };
}

function toEnvelopeBase(envelope: DeterministicMutationEnvelope): Omit<DeterministicMutationEnvelope, 'envelope_id'> {
  return {
    runtime: envelope.runtime,
    contract_id: envelope.contract_id,
    parent_contract_id: envelope.parent_contract_id,
    pre_state_hash: envelope.pre_state_hash,
    replay_profile: envelope.replay_profile,
    invariants_applied: envelope.invariants_applied,
    patches: envelope.patches,
  };
}

function deny(contract: CognitiveModeContract, reason: string): SafetyDecision {
  return Object.freeze({
    verdict: 'DENY',
    reason,
    checked_invariants: Object.freeze([...contract.invariants]),
  });
}

function slug(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 64);
}

function sha256Hex(value: unknown): string {
  return createHash('sha256').update(stableStringify(value), 'utf8').digest('hex');
}

export function hashPreState(preState: PreStateSnapshot): string {
  return `sha256:${sha256Hex(preState)}`;
}

function hashContent(content: string): string {
  return `sha256:${sha256Hex(content)}`;
}

function stableStringify(value: unknown): string {
  if (Array.isArray(value)) {
    return `[${value.map((entry) => stableStringify(entry)).join(',')}]`;
  }
  if (value !== null && typeof value === 'object') {
    const record = value as Record<string, unknown>;
    return `{${Object.keys(record)
      .filter((key) => typeof record[key] !== 'undefined')
      .sort()
      .map((key) => `${JSON.stringify(key)}:${stableStringify(record[key])}`)
      .join(',')}}`;
  }
  return JSON.stringify(value);
}
