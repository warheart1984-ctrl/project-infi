import { describe, expect, it } from 'vitest';
import { SovereignXRouter } from '@aaes-os/sovereignx-router';
import { buildRequestPacket } from '../../tools/codex-handoff-core.js';
import { createCodexHandoffRouter, routeCodexHandoff } from '../../tools/codex-handoff-router.js';

describe('codex handoff sovereign router bridge', () => {
  it('selects the constitutional model from the packet size', () => {
    const router = createCodexHandoffRouter(new SovereignXRouter({ clock: () => 1_700_000_000_000 }));
    const request = buildRequestPacket(
      'ship slice',
      new Map<string, string[]>([
        ['current-state', ['ready']],
        ['done', ['schema']],
        ['next-action', ['route']],
        ['files', ['a.ts']],
        ['verification', ['ok']],
      ]),
    );
    const route = routeCodexHandoff(router, { request, hasReply: false });
    expect(route.selectedModel).toBe('qwen-3b');
    expect(route.requestId).toMatch(/^codex-/);
  });

  it('promotes longer packets to the larger model', () => {
    const router = createCodexHandoffRouter(new SovereignXRouter({ clock: () => 1_700_000_000_000 }));
    const request = buildRequestPacket(
      'route the full constitutional handoff and continuity bundle through the orchestration layer so the reply ledger and the evidence surface remain aligned with the selected reasoning engine',
      new Map<string, string[]>([
        ['current-state', ['request and reply packet tooling is already in place']],
        ['done', ['request schema exists', 'reply schema exists', 'smoke test exists']],
        ['next-action', ['wire the router into the orchestrator and record the route decision']],
        ['files', ['tools/codex-handoff-orchestrator.ts', 'tools/codex-handoff-router.ts']],
        ['verification', ['corepack pnpm codex-handoff-smoke']],
        ['blockers', ['none']],
      ]),
    );
    const route = routeCodexHandoff(router, { request, hasReply: true, replyPath: 'reply.json' });
    expect(route.selectedModel).toBe('qwen-7b');
    expect(route.backend === 'delay' || route.backend === 'drop' || route.backend === 'cpu' || route.backend === 'opencl' || route.backend === 'vulkan').toBe(true);
  });
});
