import { mkdtemp, readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

import {
  MandalaBrainV3,
  ContextEncoderV1,
  buildConstitutionalDatasetRecord,
  buildConstitutionalFeatureNames,
  createConstitutionalSandbox,
  decisionFromScore,
  extractConstitutionalFeatures,
  parseRuntimeArtifactBundleJsonl,
  summarizeConstitutionalMetrics,
} from './index.js';

describe('Constitutional sandbox engine', () => {
  it('approves a valid medicine experiment and records evidence', () => {
    let now = 1_000;
    const sandbox = createConstitutionalSandbox(() => {
      now += 1_000;
      return now;
    });

    const outcome = sandbox.submit_experiment({
      world_id: 'med_arena_1',
      intent: {
        description: 'Compare treatment A vs B for a synthetic cohort',
        domain: 'medicine',
        authority: 'researcher_alpha',
        purpose: 'comparison',
      },
      spec: {
        operation: 'treatment_comparison',
        model_ref: 'med_model_v3',
        inputs: {
          protocol: { ethics_clearance: true },
          treatment: { drug: 'drug-a', dose: 100, schedule: 'daily' },
          cohort: { risk_profile: 'low' },
        },
        parameters: {
          cohort_size: 1_000,
          time_horizon_days: 365,
        },
        validation: { required_metrics: ['efficacy', 'toxicity'] },
        code_version: '1.2.3',
      },
    }, {
      risk: 0.1,
      health: 0.9,
      drift: 0.05,
      evidence_sufficiency: 0.8,
      evidence_completeness: 1,
      lineage_depth: 3,
      metrics_present: 4,
      toxicity: 0.1,
      instability: 0.1,
      rights_impact: 0.05,
      non_falsifiable: 0,
    });

    expect(outcome.allowed).toBe(true);
    expect(outcome.result).toMatchObject({
      efficacy: 0.2,
      toxicity: 0.1,
      safety: 0.9,
    });
    expect(outcome.evidence.record_id.startsWith('csr-')).toBe(true);
    expect(outcome.runtime_artifacts_jsonl).toContain('"artifact_type":"constitutional_receipt"');
    expect(outcome.world.world_contract.sandbox.execution.max_runtime_ms).toBe(5_000);
    expect(sandbox.ledger.records).toHaveLength(1);
  });

  it('blocks an unsafe medicine experiment and tightens the sandbox', () => {
    let now = 2_000;
    const sandbox = createConstitutionalSandbox(() => {
      now += 1_000;
      return now;
    });

    const outcome = sandbox.submit_experiment({
      world_id: 'med_arena_1',
      intent: {
        description: 'Compare treatment A vs B for a synthetic cohort',
        domain: 'medicine',
        authority: 'clinician',
        purpose: 'comparison',
      },
      spec: {
        operation: 'treatment_comparison',
        model_ref: 'med_model_v3',
        inputs: {
          protocol: { ethics_clearance: true },
          treatment: { drug: 'drug-a', dose: 100, schedule: 'daily' },
          cohort: { risk_profile: 'high' },
        },
        parameters: {
          cohort_size: 500,
          time_horizon_days: 180,
        },
        validation: { required_metrics: ['efficacy', 'toxicity'] },
      },
    }, {
      risk: 0.9,
      health: 0.4,
      drift: 0.2,
      evidence_sufficiency: 0.6,
      evidence_completeness: 0.9,
      lineage_depth: 2,
      metrics_present: 3,
      toxicity: 0.9,
      instability: 0.3,
      rights_impact: 0.1,
      non_falsifiable: 0,
    });

    expect(outcome.allowed).toBe(false);
    expect(outcome.result).toMatchObject({
      status: 'blocked',
    });
    expect(outcome.world.world_contract.sandbox.execution.max_runtime_ms).toBe(1_000);
    expect(sandbox.ledger.records).toHaveLength(1);
  });

  it('replays history in timestamp order and builds constitutional metrics', () => {
    let now = 3_000;
    const sandbox = createConstitutionalSandbox(() => {
      now += 1_000;
      return now;
    });

    sandbox.submit_experiment({
      world_id: 'sci_arena_1',
      intent: {
        description: 'Test a falsifiable model against observations',
        domain: 'science',
        authority: 'scientist',
        purpose: 'exploration',
      },
      spec: {
        operation: 'experiment',
        model_ref: 'sci_model_v1',
        inputs: {
          hypothesis: { testable: true },
          model: { equations: ['x + y'] },
          measurements: [{ name: 'm1', value: 1 }],
        },
        parameters: { x: 1 },
        validation: { required_metrics: ['model_error'] },
      },
    }, {
      risk: 0.05,
      health: 0.95,
      drift: 0.01,
      evidence_sufficiency: 0.85,
      evidence_completeness: 1,
      lineage_depth: 4,
      metrics_present: 4,
      toxicity: 0,
      instability: 0.1,
      rights_impact: 0,
      non_falsifiable: 0,
    });

    sandbox.submit_experiment({
      world_id: 'sci_arena_1',
      intent: {
        description: 'Retest the model under a second observation pass',
        domain: 'science',
        authority: 'scientist',
        purpose: 'comparison',
      },
      spec: {
        operation: 'experiment',
        model_ref: 'sci_model_v1',
        inputs: {
          hypothesis: { testable: true },
          model: { equations: ['x + y'] },
          measurements: [{ name: 'm2', value: 2 }],
        },
        parameters: { x: 2 },
        validation: { required_metrics: ['model_error'] },
      },
    }, {
      risk: 0.1,
      health: 0.9,
      drift: 0.02,
      evidence_sufficiency: 0.75,
      evidence_completeness: 1,
      lineage_depth: 4,
      metrics_present: 4,
      toxicity: 0,
      instability: 0.15,
      rights_impact: 0,
      non_falsifiable: 0,
    });

    const replay = sandbox.replay_world('sci_arena_1');
    const dataset = replay.map((evidence) => buildConstitutionalDatasetRecord({ evidence }));
    const summary = summarizeConstitutionalMetrics(dataset);

    expect(replay).toHaveLength(2);
    expect(replay[0]!.timestamp).toBeLessThan(replay[1]!.timestamp);
    expect(summary.constitutional_accuracy).toBeGreaterThanOrEqual(0);
    expect(summary.evidence_calibration_score).toBeGreaterThanOrEqual(0);
    expect(summary.domain_safety_score).toBeGreaterThanOrEqual(0);
    expect(summary.evidence_weighted_approval_rate).toBeGreaterThanOrEqual(0);
  });

  it('encodes constitutional features for Mandala Brain v3', () => {
    const world = createConstitutionalSandbox().registry.get_world('law_arena_1');
    const experiment = {
      world_id: 'law_arena_1',
      domain: 'law' as const,
      intent: {
        description: 'Review a contract breach case',
        domain: 'law' as const,
        authority: 'judge',
        purpose: 'comparison',
      },
      spec: {
        operation: 'case_simulation',
        model_ref: 'law_reasoner_v1',
        inputs: {
          case: {
            facts: ['contract signed', 'payment not delivered'],
            issues: ['breach', 'damages'],
            jurisdiction: 'MI',
          },
        },
        parameters: { cohort_size: 10 },
        validation: { required_metrics: ['fairness', 'consistency'] },
      },
    };

    const features = extractConstitutionalFeatures(world, experiment, {
      risk: 0.15,
      health: 0.85,
      drift: 0.02,
      evidence_sufficiency: 0.9,
      evidence_completeness: 1,
      lineage_depth: 5,
      metrics_present: 5,
      toxicity: 0,
      instability: 0,
      rights_impact: 0.2,
      non_falsifiable: 0,
    });
    const encoder = new ContextEncoderV1(buildConstitutionalFeatureNames());
    const vector = encoder.encode(features);
    const brain = new MandalaBrainV3(new Array(vector.length).fill(0.1), 0);
    const score = brain.step(vector);

    expect(vector).toHaveLength(buildConstitutionalFeatureNames().length);
    expect(score).toBeGreaterThan(0);
    expect(decisionFromScore(score)).toBe('approve');
  });

  it('emits the runtime artifact bundle with a symbolic CORI Alpha lineage reference', () => {
    let now = 4_000;
    const sandbox = createConstitutionalSandbox(() => {
      now += 1_000;
      return now;
    });

    sandbox.submit_experiment({
      world_id: 'law_arena_1',
      intent: {
        description: 'Simulate a breach case for artifact emission',
        domain: 'law',
        authority: 'judge',
        purpose: 'comparison',
      },
      spec: {
        operation: 'case_simulation',
        model_ref: 'law_reasoner_v1',
        inputs: {
          case: {
            facts: ['contract signed', 'payment not delivered'],
            issues: ['breach', 'damages'],
            jurisdiction: 'MI',
          },
        },
        parameters: { cohort_size: 10 },
        validation: { required_metrics: ['fairness', 'consistency'] },
      },
    }, {
      risk: 0.2,
      health: 0.8,
      drift: 0.03,
      evidence_sufficiency: 0.7,
      evidence_completeness: 1,
      lineage_depth: 5,
      metrics_present: 5,
      toxicity: 0,
      instability: 0,
      rights_impact: 0.2,
      non_falsifiable: 0,
    });

    const artifacts = sandbox.emit_runtime_artifacts('law_arena_1');
    const replay = sandbox.replay_runtime('law_arena_1');

    expect(artifacts.receipt.world_id).toBe('law_arena_1');
    expect(artifacts.evidence_package.evidence_record_id).toBe(artifacts.receipt.evidence_record_id);
    expect(artifacts.replay_record.records).toHaveLength(1);
    expect(artifacts.conformance_record.passed).toBe(true);
    expect(artifacts.operator_timeline.events.map((event) => event.phase)).toEqual([
      'intent',
      'evaluation',
      'execution',
      'evidence',
      'conformance',
      'replay',
    ]);
    expect(artifacts.cori_alpha_lineage_reference).toMatchObject({
      system: 'CORI_ALPHA',
      relation: 'lineage_reference',
      connected: false,
      note: 'symbolic_only',
    });
    expect(replay.runtime_artifacts_jsonl).toContain('"artifact_type":"operator_timeline"');
    expect(replay.records[0]!.runtime_artifacts_jsonl).toContain('"artifact_type":"conformance_record"');
  });

  it('round-trips the canonical runtime JSONL and writes it to disk', async () => {
    let now = 5_000;
    const sandbox = createConstitutionalSandbox(() => {
      now += 1_000;
      return now;
    });

    sandbox.submit_experiment({
      world_id: 'med_arena_1',
      intent: {
        description: 'Emit canonical medical runtime artifacts',
        domain: 'medicine',
        authority: 'researcher_alpha',
        purpose: 'comparison',
      },
      spec: {
        operation: 'treatment_comparison',
        model_ref: 'med_model_v3',
        inputs: {
          protocol: { ethics_clearance: true },
          treatment: { drug: 'drug-a', dose: 100, schedule: 'daily' },
          cohort: { risk_profile: 'low' },
        },
        parameters: {
          cohort_size: 1_000,
          time_horizon_days: 365,
        },
        validation: { required_metrics: ['efficacy', 'toxicity'] },
      },
    }, {
      risk: 0.1,
      health: 0.9,
      drift: 0.05,
      evidence_sufficiency: 0.8,
      evidence_completeness: 1,
      lineage_depth: 3,
      metrics_present: 4,
      toxicity: 0.1,
      instability: 0.1,
      rights_impact: 0.05,
      non_falsifiable: 0,
    });

    const jsonl = sandbox.export_runtime_artifacts_jsonl('med_arena_1');
    const parsed = parseRuntimeArtifactBundleJsonl(jsonl);
    const tempDir = await mkdtemp(join(tmpdir(), 'mesh-sim-'));
    const filePath = join(tempDir, 'runtime.jsonl');
    const writtenPath = await sandbox.write_runtime_artifacts_jsonl('med_arena_1', filePath);
    const written = await readFile(writtenPath, 'utf8');

    expect(parsed.receipt.world_id).toBe('med_arena_1');
    expect(parsed.replay_record.records).toHaveLength(1);
    expect(parsed.cori_alpha_lineage_reference.connected).toBe(false);
    expect(written.trim()).toBe(jsonl);
  });
});
