import { beforeEach, describe, expect, it, vi } from 'vitest';

import {
  createJarvisSession,
  getSystemHealth,
  resolveIntegrationRoute,
  sendToJarvis,
  systemRoutingMap,
  writeJarvisMemory,
} from './jarvisContract';

describe('jarvis integration contract adapter', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    window.localStorage.clear();
  });

  it('resolves routes from the shared routing map', () => {
    expect(systemRoutingMap.routes.jarvis_chat).toBe('/api/jarvis');
    expect(resolveIntegrationRoute('jarvis_chat')).toBe(
      'http://127.0.0.1:8000/api/jarvis',
    );
  });

  it('sends one normalized Jarvis message through the compatibility endpoint', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        session_id: 'session-1',
        output: 'Ready.',
        trace: { provider_dispatch: {} },
        status: 'ok',
        runtime: {
          response: 'Ready.',
          response_trace: { provider_dispatch: {} },
        },
      }),
    });

    const response = await sendToJarvis({
      input: 'Test request',
      mode: 'normal',
      context: {
        persona_mode: 'builder',
      },
    });

    expect(response.output).toBe('Ready.');
    expect(response.status).toBe('ok');
    expect(response.session_id).toBe('session-1');
    expect(global.fetch).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/api/jarvis',
      expect.objectContaining({ method: 'POST' }),
    );
  });

  it('marks fallback or truncation evidence as degraded', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        session_id: 'session-2',
        response: 'Still usable.',
        provider_notice: 'Fallback applied',
        response_trace: {},
      }),
    });

    const response = await sendToJarvis({
      input: 'Use existing session',
      context: { session_id: 'session-2' },
    });

    expect(response.status).toBe('degraded');
  });

  it('writes Jarvis memory through the shared route map', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ id: 'memory-1', text: 'remember this' }),
    });

    const response = await writeJarvisMemory({ text: 'remember this' });

    expect(response.id).toBe('memory-1');
    expect(global.fetch).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/api/memory/write',
      expect.objectContaining({ method: 'POST' }),
    );
  });

  it('checks system health through the shared contract route', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ status: 'healthy' }),
    });

    const response = await getSystemHealth();

    expect(response.status).toBe('healthy');
    expect(global.fetch).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/health',
      expect.objectContaining({ method: 'GET' }),
    );
  });

  it('exposes session creation as a standalone adapter call', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ session_id: 'session-3' }),
    });

    const response = await createJarvisSession({ persona_mode: 'builder' });

    expect(response.session_id).toBe('session-3');
  });
});
