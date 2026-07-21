import { randomUUID } from 'node:crypto';
import type { CodingRouter, GovernedChatResponse, Identity } from '@aaes-os/governed-runtime';

export interface NovaShellOptions {
  systemPrompt?: string;
  defaultTags?: string[];
  defaultRisk?: 'low' | 'medium' | 'high' | 'critical';
}

export class NovaCodingShell {
  private readonly systemPrompt: string;
  private readonly defaultTags: string[];
  private readonly defaultRisk: NovaShellOptions['defaultRisk'];

  constructor(
    private readonly router: CodingRouter,
    private readonly identity: Identity,
    options: NovaShellOptions = {},
  ) {
    this.systemPrompt = options.systemPrompt ?? 'You are Nova, a governed coding shell.';
    this.defaultTags = options.defaultTags ?? ['general'];
    this.defaultRisk = options.defaultRisk ?? 'low';
  }

  async runCommand(input: string): Promise<GovernedChatResponse> {
    const intentId = randomUUID();
    const traceId = randomUUID();

    return this.router.execute({
      intent: {
        id: intentId,
        kind: 'coding',
        description: `Nova coding input: ${input.slice(0, 120)}`,
      },
      identity: this.identity,
      governance: {
        domain: 'coding',
        risk: this.defaultRisk ?? 'low',
        tags: this.defaultTags,
      },
      trace: {
        traceId,
        intentId,
        actorId: this.identity.actorId,
        policyIds: [],
        timestamps: { createdAt: Date.now() },
      },
      input: {
        systemPrompt: this.systemPrompt,
        userContent: input,
        context: '',
      },
    });
  }
}
