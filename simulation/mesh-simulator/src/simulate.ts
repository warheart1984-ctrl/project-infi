#!/usr/bin/env tsx
import {
  createConstitutionalSandbox,
  type ConstitutionalSandbox,
  type DomainName,
} from './index.js';
import { runGovernanceDriftStress, runLoadStress } from './simulator.js';

const scenario = process.argv[2] ?? 'all';

function submitCanonicalExperiment(sandbox: ConstitutionalSandbox, worldId: string): void {
  const world = sandbox.registry.get_world(worldId).world_contract;
  const commonMetrics = {
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
  };

  const requestByDomain: Record<DomainName, Parameters<ConstitutionalSandbox['submit_experiment']>[0]> = {
    law: {
      world_id: worldId,
      intent: {
        description: 'Simulate a contract breach case for canonical artifact export',
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
    },
    medicine: {
      world_id: worldId,
      intent: {
        description: 'Compare treatment A vs B for canonical artifact export',
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
    },
    science: {
      world_id: worldId,
      intent: {
        description: 'Test a falsifiable model against observations for canonical artifact export',
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
    },
    economics: {
      world_id: worldId,
      intent: {
        description: 'Run a market stability policy simulation for canonical artifact export',
        domain: 'economics',
        authority: 'economist',
        purpose: 'comparison',
      },
      spec: {
        operation: 'market_simulation',
        model_ref: 'eco_model_v1',
        inputs: {
          policy: { incentive_distortion: 'low' },
          market: { volatility: 0.3, gini: 0.25, rules: ['baseline'] },
          agents: [{ strategy: 'cooperate' }],
        },
        parameters: { horizon_days: 90 },
        validation: { required_metrics: ['efficiency', 'inequality'] },
      },
    },
    society: {
      world_id: worldId,
      intent: {
        description: 'Run a market stability policy simulation for canonical artifact export',
        domain: 'economics',
        authority: 'policy_analyst',
        purpose: 'comparison',
      },
      spec: {
        operation: 'market_simulation',
        model_ref: 'eco_model_v1',
        inputs: {
          policy: { incentive_distortion: 'low' },
          market: { volatility: 0.3, gini: 0.25, rules: ['baseline'] },
          agents: [{ strategy: 'cooperate' }],
        },
        parameters: { horizon_days: 90 },
        validation: { required_metrics: ['efficiency', 'inequality'] },
      },
    },
    custom: {
      world_id: worldId,
      intent: {
        description: 'Run a canonical governed experiment',
        domain: world.domain,
        authority: 'operator',
        purpose: 'comparison',
      },
      spec: {
        operation: world.sandbox.execution.allowed_operations[0] ?? 'experiment',
        model_ref: world.simulation.models[0]?.model_id ?? 'custom_model_v1',
        inputs: {},
        parameters: {},
        validation: { required_metrics: ['result'] },
      },
    },
  };

  sandbox.submit_experiment(requestByDomain[world.domain] ?? requestByDomain.custom, commonMetrics);
}

async function emitCanonicalArtifacts(worldId: string, outputPath?: string): Promise<void> {
  const sandbox = createConstitutionalSandbox();
  submitCanonicalExperiment(sandbox, worldId);
  const jsonl = sandbox.export_runtime_artifacts_jsonl(worldId);
  if (outputPath) {
    await sandbox.write_runtime_artifacts_jsonl(worldId, outputPath);
    return;
  }
  process.stdout.write(`${jsonl}\n`);
}

async function main(): Promise<void> {
  if (scenario === 'artifacts') {
    const worldId = process.argv[3] ?? 'law_arena_1';
    const outputPath = process.argv[4];
    await emitCanonicalArtifacts(worldId, outputPath);
    return;
  }

  console.log('=== PSOM Mesh Simulator ===\n');

  if (scenario === 'load' || scenario === 'all') {
    const load = runLoadStress();
    console.log('Load stress scenario:');
    console.log(JSON.stringify(load, null, 2));
    console.log();
  }

  if (scenario === 'governance-drift' || scenario === 'all') {
    const drift = runGovernanceDriftStress();
    console.log('Governance drift scenario:');
    console.log(JSON.stringify(drift, null, 2));
  }
}

void main();
