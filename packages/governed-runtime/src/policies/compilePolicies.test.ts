import { describe, expect, it } from 'vitest';
import { compilePolicies, loadFreeCodingPolicyPack, loadPoliciesFromYaml } from './compilePolicies.js';
import { CodingRouter, governanceMatches } from '../router/CodingRouter.js';
import type { CodingBackend, GovernedChatRequest } from '../types.js';
import { PatternLedger } from '@aaes-os/aaes-governance';

const SAMPLE_YAML = `
- id: test.policy
  when:
    domain: coding
    risk: low
  then:
    routing:
      preferred_backends: ["groq-llama3-70b"]
`;

describe('compilePolicies', () => {
  it('loads YAML with snake_case keys', () => {
    const policies = loadPoliciesFromYaml(SAMPLE_YAML);
    expect(policies).toHaveLength(1);
    expect(policies[0]?.id).toBe('test.policy');
    expect(policies[0]?.routing.preferredBackends).toEqual(['groq-llama3-70b']);
  });

  it('matches governance context', () => {
    const [policy] = loadPoliciesFromYaml(SAMPLE_YAML);
    expect(policy?.matches({ domain: 'coding', risk: 'low' })).toBe(true);
    expect(policy?.matches({ domain: 'coding', risk: 'high' })).toBe(false);
  });

  it('loads free coding policy pack', () => {
    const policies = loadFreeCodingPolicyPack();
    expect(policies.length).toBeGreaterThan(0);
    expect(policies.some((p) => p.id === 'coding.free.general')).toBe(true);
    const general = policies.find((p) => p.id === 'coding.free.general');
    expect(general?.routing.preferredBackends).toContain('ollama');
  });
});

describe('governanceMatches', () => {
  it('requires all tags when specified', () => {
    expect(
      governanceMatches({ domain: 'coding', tags: ['agentic', 'tool-use'] }, {
        domain: 'coding',
        risk: 'medium',
        tags: ['agentic', 'tool-use'],
      }),
    ).toBe(true);

    expect(
      governanceMatches({ domain: 'coding', tags: ['agentic', 'tool-use'] }, {
        domain: 'coding',
        risk: 'medium',
        tags: ['agentic'],
      }),
    ).toBe(false);
  });
});

describe('CodingRouter', () => {
  const mockBackend = (name: string, text: string): CodingBackend => ({
    name,
    supports: { chat: true, code: true },
    chat: async (req) => ({
      intentId: req.intent.id,
      backendName: name,
      trace: req.trace,
      output: { text, tokensIn: 1, tokensOut: 1, latencyMs: 0 },
      governance: { policyIds: [], violations: [] },
    }),
  });

  const baseRequest = (): GovernedChatRequest => ({
    intent: { id: 'intent-1', kind: 'coding', description: 'test' },
    identity: { actorId: 'jon', role: 'developer' },
    governance: { domain: 'coding', risk: 'low', tags: ['general'] },
    trace: {
      traceId: 'trace-1',
      intentId: 'intent-1',
      actorId: 'jon',
      policyIds: [],
      timestamps: { createdAt: Date.now() },
    },
    input: {
      systemPrompt: 'You are a coding assistant.',
      userContent: 'Hello',
    },
  });

  it('prefers backend from matched policy', async () => {
    const policies = compilePolicies([
      {
        id: 'prefer-groq',
        when: { domain: 'coding', risk: 'low' },
        then: { routing: { preferredBackends: ['groq-llama3-70b'] } },
      },
    ]);

    const router = new CodingRouter(
      [mockBackend('codex', 'codex'), mockBackend('groq-llama3-70b', 'groq')],
      policies,
      new PatternLedger(),
    );

    const result = await router.execute(baseRequest());
    expect(result.backendName).toBe('groq-llama3-70b');
    expect(result.output.text).toBe('groq');
    expect(result.governance.policyIds).toContain('prefer-groq');
  });

  it('restricts to allowed backends', async () => {
    const policies = compilePolicies([
      {
        id: 'only-cursor',
        when: { domain: 'coding', tags: ['local-project'] },
        then: { routing: { allowedBackends: ['cursor'] } },
      },
    ]);

    const router = new CodingRouter(
      [mockBackend('codex', 'codex'), mockBackend('cursor', 'cursor')],
      policies,
      new PatternLedger(),
    );

    const req = baseRequest();
    req.governance.tags = ['local-project'];

    const result = await router.execute(req);
    expect(result.backendName).toBe('cursor');
  });

  it('enforces identity role guardrails', async () => {
    const policies = compilePolicies([
      {
        id: 'dev-only',
        when: { domain: 'coding' },
        then: { guardrails: { requireIdentityRole: ['developer'] } },
      },
    ]);

    const router = new CodingRouter(
      [mockBackend('codex', 'ok')],
      policies,
      new PatternLedger(),
    );

    const req = baseRequest();
    req.identity.role = 'guest';

    await expect(router.execute(req)).rejects.toThrow(/requires identity role/);
  });
});
