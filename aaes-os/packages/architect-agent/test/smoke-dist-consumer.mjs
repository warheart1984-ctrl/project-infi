import { strict as assert } from 'node:assert';

import {
  ArchitectAgentLoop,
  createDefaultUnifiedGovernanceContract,
} from '@aaes-os/architect-agent';

const input = {
  situation: {
    situationId: 'situation:published-dist-smoke',
    intent: 'prove the packed architect-agent runtime executes',
    risk: 'high',
    requestedRuntimes: [
      'ArchitectRuntime',
      'BuilderRuntime',
      'IntegrationRuntime',
      'SafetyRuntime',
    ],
    targetFiles: ['src/existing.ts', 'src/new.ts'],
  },
  pre_state: {
    'src/existing.ts': 'export const version = 1;\n',
    'src/new.ts': null,
  },
  issued_at: '2026-06-30T20:00:00.000Z',
};

const loop = new ArchitectAgentLoop(createDefaultUnifiedGovernanceContract());
const act = loop.execute(input);
const repeated = loop.execute(input);
const envelope = act.integration.envelopes[0];

assert.ok(envelope, 'governed act must contain one mutation envelope');
assert.equal(act.integration.envelopes.length, 1);
assert.deepEqual(
  envelope.patches.map((patch) => patch.path),
  ['src/existing.ts', 'src/new.ts'],
);
assert.equal(envelope.patches[0]?.reverse_patch.operation, 'restore');
assert.equal(envelope.patches[1]?.reverse_patch.operation, 'delete');
assert.match(envelope.pre_state_hash, /^sha256:[0-9a-f]{64}$/);
assert.equal(act.egl.criterion_id, 'EGL-1');
assert.equal(act.egl.equivalent, true);
assert.equal(act.safety.verdict, 'ALLOW');
assert.equal(act.receipt.kind, 'runtime');
assert.equal(act.receipt.claimLabel, 'architect-agent-loop:allow');
assert.equal(Object.isFrozen(act), true);
assert.equal(Object.isFrozen(envelope), true);
assert.equal(Object.isFrozen(envelope.patches), true);
assert.equal(Object.isFrozen(envelope.patches[0]), true);
assert.equal(repeated.act_id, act.act_id);
assert.equal(repeated.integration.envelopes[0]?.envelope_id, envelope.envelope_id);
assert.equal(repeated.receipt.receiptId, act.receipt.receiptId);

process.stdout.write(`${JSON.stringify({
  status: 'ok',
  act_id: act.act_id,
  envelope_id: envelope.envelope_id,
  receipt_id: act.receipt.receiptId,
  egl: act.egl.criterion_id,
})}\n`);
