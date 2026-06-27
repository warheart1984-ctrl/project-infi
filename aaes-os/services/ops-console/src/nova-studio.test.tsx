import { renderToString } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import {
  createGovernanceEnvelope,
  evaluateGovernanceEnvelope,
  getStudioRouteForMode,
  NovaStudioCanvas,
  studioRoutes,
  type OperatorContext,
  type SkillzMcgeeLedgerSummary,
} from './nova-studio/index.js';

const skillzmcgee: SkillzMcgeeLedgerSummary = {
  source: '.runtime/skillzmcgee/receipts.jsonl',
  available: true,
  receiptCount: 2,
  state: {
    slice_math: {
      last_status: 'ok',
      last_output: { value: 42 },
      last_run_id: 'run-1',
    },
    'llm:slice_math': {
      last_status: 'ok',
      last_output: { text: 'state says 42' },
      last_run_id: 'run-2',
    },
  },
  recentReceipts: [
    {
      id: 'run-2',
      timestamp: '2026-06-26T00:01:00Z',
      actor: 'skillz',
      slice: 'llm:slice_math',
      status: 'ok',
      output: { text: 'state says 42' },
    },
  ],
  capabilities: [
    { name: 'read_file', description: 'Read workspace files under governance', governed: true, receiptRequired: true },
    { name: 'write_file', description: 'Write bounded patches with receipts', governed: true, receiptRequired: true },
    { name: 'run_slice', description: 'Execute governed slices', governed: true, receiptRequired: true },
    { name: 'ask_llm', description: 'Ask lawful LLM adapter', governed: true, receiptRequired: true },
  ],
};

describe('nova-studio canonical module', () => {
  it('defines ops-console-native Nova Studio routes', () => {
    expect(studioRoutes.map((route) => route.path)).toEqual([
      '/nova/studio',
      '/nova/studio/coding-agent',
      '/nova/studio/drift',
      '/nova/studio/control',
      '/nova/studio/replay',
    ]);
    expect(getStudioRouteForMode('replay')?.label).toBe('Replay & Receipts');
  });

  it('renders coding, drift, control, and replay panels inside one canvas', () => {
    const html = renderToString(
      <NovaStudioCanvas
        skillzmcgee={skillzmcgee}
        enforcement={{ status: 'ACTIVE', events: [{ receiptId: 'cen:1', verdict: 'DENY', reasonCode: 'INVARIANT_VIOLATION' }] }}
      />,
    );

    expect(html).toContain('Nova Studio');
    expect(html).toContain('Coding Agent');
    expect(html).toContain('Drift Visualizer');
    expect(html).toContain('Control Tower');
    expect(html).toContain('Replay &amp; Receipts');
    expect(html).toContain('Capability Calls');
    expect(html).toContain('Recent SkillzMcGee Receipts');
    expect(html).toContain('Governance Envelope');
    expect(html).toContain('operator-console');
    expect(html).toContain('run-2');
  });

  it('creates deterministic CRK-2 governance envelopes and detects broken invariants', () => {
    const operatorContext: OperatorContext = {
      operatorId: 'operator-console',
      mode: 'coding-agent',
      continuity: { checkpoint: 'receipt:run-2', receiptCount: 2 },
      activeSlice: 'llm:slice_math',
      governance: { status: 'pending', invariantFailures: [] },
      substrateHealth: { ledgerAvailable: true, receiptCount: 2 },
    };
    const envelope = createGovernanceEnvelope({
      operatorContext,
      capability: skillzmcgee.capabilities[0],
      input: { path: 'README.md' },
      output: { bytes: 128 },
      timestamp: '2026-06-26T00:02:00Z',
      status: 'ok',
    });
    const sameEnvelope = createGovernanceEnvelope({
      operatorContext,
      capability: skillzmcgee.capabilities[0],
      input: { path: 'README.md' },
      output: { bytes: 128 },
      timestamp: '2026-06-26T00:02:00Z',
      status: 'ok',
    });

    expect(envelope.inputHash).toBe(sameEnvelope.inputHash);
    expect(envelope.outputHash).toBe(sameEnvelope.outputHash);
    expect(evaluateGovernanceEnvelope(envelope, { capabilities: skillzmcgee.capabilities, receiptCount: 2 })).toEqual([]);
    expect(evaluateGovernanceEnvelope(
      { ...envelope, capability: 'unknown_capability', continuityCheckpoint: 'receipt:run-3', outputHash: undefined },
      { capabilities: skillzmcgee.capabilities, receiptCount: 1 },
    )).toEqual([
      'capability_signature_match',
      'continuity_checkpoint_monotonicity',
      'no_orphaned_outputs',
    ]);
  });
});
