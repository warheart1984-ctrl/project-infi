import { describe, expect, it } from 'vitest';

import { compileUlToIslIntent, createUlRuntime, normalizeUlCommand, parseUlPhrase, validateUlCommand } from './index.js';

const defaults = {
  actor: 'alice',
  evidence: [{ id: 'ul-evidence-1', kind: 'receipt', uri: 'file:///tmp/ul-evidence-1.json' }],
  authority: {
    actor: 'alice',
    roles: ['steward'],
    permissions: ['submit-intent'],
  },
  traceability: [
    {
      cisRequirement: 'UL-VERB-001',
      referenceArchitecture: 'UL -> ISL -> ULX',
      conformanceTest: 'packages/ul-runtime/src/index.test.ts',
      evidenceArtifact: 'ul-evidence-1',
    },
  ],
} as const;

describe('ul-runtime', () => {
  it('normalizes verb commands deterministically', () => {
    const command = normalizeUlCommand({
      actor: ' alice ',
      verb: ' VERIFY ',
      target: ' sovereign/kernel ',
      purpose: ' release readiness ',
      context: { stage: ' prototype ' },
      evidence: defaults.evidence,
      authority: defaults.authority,
      traceability: defaults.traceability,
    });

    expect(command.actor).toBe('alice');
    expect(command.verb).toBe('verify');
    expect(command.target).toBe('sovereign/kernel');
    expect(command.purpose).toBe('release readiness');
    expect(command.id).toHaveLength(64);
    expect(validateUlCommand(command).valid).toBe(true);
  });

  it('parses operator verb phrases into structured UL commands', () => {
    const command = parseUlPhrase('verify sovereign/kernel for release readiness as nova with stage=verified, surface=governance', defaults);

    expect(command.actor).toBe('nova');
    expect(command.verb).toBe('verify');
    expect(command.target).toBe('sovereign/kernel');
    expect(command.purpose).toBe('release readiness');
    expect(command.context).toMatchObject({ stage: 'verified', surface: 'governance' });
  });

  it('compiles UL commands into ISL-compatible intent drafts', () => {
    const command = parseUlPhrase('build ul-runtime for verb language promotion as alice with surface=UL', defaults);
    const intent = compileUlToIslIntent(command);

    expect(intent.actor).toBe('alice');
    expect(intent.target).toBe('ul-runtime');
    expect(intent.purpose).toBe('build verb language promotion');
    expect(intent.context.ul).toMatchObject({
      verb: 'build',
      source: 'build ul-runtime for verb language promotion as alice with surface=UL',
    });
    expect(intent.evidence).toHaveLength(1);
    expect(intent.traceability[0]?.cisRequirement).toBe('UL-VERB-001');
  });

  it('rejects malformed or unauditable verb commands', () => {
    const result = validateUlCommand({
      actor: '',
      verb: 'Bad Verb',
      target: '',
      evidence: [],
      authority: { actor: '', roles: [], permissions: [] },
      traceability: [],
    });

    expect(result.valid).toBe(false);
    expect(result.issues.map((issue) => issue.field)).toEqual(
      expect.arrayContaining([
        'actor',
        'verb',
        'target',
        'evidence',
        'authority.actor',
        'authority.roles',
        'authority.permissions',
        'traceability',
      ]),
    );
  });

  it('tracks accepted and rejected command compilation', () => {
    const runtime = createUlRuntime();
    const accepted = runtime.compilePhrase('verify sovereign/kernel for release readiness as alice', defaults);
    const rejected = runtime.compile({
      actor: 'alice',
      verb: '',
      target: '',
      evidence: [],
      authority: { actor: 'alice', roles: [], permissions: [] },
      traceability: [],
    });

    expect(accepted.accepted).toBe(true);
    expect(rejected.accepted).toBe(false);
    expect(runtime.snapshot()).toMatchObject({
      packageName: '@aaes-os/ul-runtime',
      version: 'ul-v1',
      totalCommands: 2,
      acceptedCommands: 1,
      rejectedCommands: 1,
      lastCommandId: accepted.command.id,
    });
    expect(runtime.listCommands()).toHaveLength(1);
  });
});
