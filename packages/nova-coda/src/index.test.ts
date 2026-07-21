import { describe, expect, it } from 'vitest';

import { MAGIC, NovaCodaMessageType, createNovaCodaRuntime } from './index.js';

describe('nova-coda runtime', () => {
  it('exposes the substrate protocol constants', () => {
    expect(MAGIC).toEqual(Buffer.from([0xc0, 0xda]));
  });

  it('builds a runtime snapshot around an injected transport', async () => {
    const calls: string[] = [];
    const runtime = createNovaCodaRuntime({
      transport: {
        async connect() {
          calls.push('connect');
        },
        async ping() {
          calls.push('ping');
          return {
            ok: true,
            message: 'pong',
            protocol: 'NovaCoda',
            arenaCapacity: 1_048_576,
          };
        },
        disconnect() {
          calls.push('disconnect');
        },
        async request(msgType) {
          calls.push(`request:${msgType}`);
          return {
            version: 1,
            msgType: NovaCodaMessageType.Pong,
            body: Buffer.from(JSON.stringify({
              ok: true,
              message: 'pong',
              protocol: 'NovaCoda',
              arenaCapacity: 1_048_576,
            }), 'utf8'),
          };
        },
      },
    });

    await runtime.connect();
    const snapshot = await runtime.ping();
    runtime.disconnect();
    const disconnectedSnapshot = runtime.snapshot();

    expect(calls).toEqual(['connect', 'ping', 'disconnect']);
    expect(snapshot.packageName).toBe('@aaes-os/nova-coda');
    expect(snapshot.socketPath).toContain('/tmp/nova.sock');
    expect(snapshot.operations.ping).toBe(1);
    expect(snapshot.lastOperation).toBe('ping');
    expect(disconnectedSnapshot.lastOperation).toBe('disconnect');
  });

  it('falls back to the generic request surface when dedicated methods are absent', async () => {
    const calls: string[] = [];
    const runtime = createNovaCodaRuntime({
      transport: {
        async connect() {
          calls.push('connect');
        },
        async ping() {
          calls.push('ping');
          return {
            ok: true,
            message: 'pong',
            protocol: 'NovaCoda',
            arenaCapacity: 1_048_576,
          };
        },
        disconnect() {
          calls.push('disconnect');
        },
        async request(msgType, body) {
          calls.push(`request:${msgType}:${JSON.stringify(body)}`);
          return {
            version: 1,
            msgType: NovaCodaMessageType.ArenaHandle,
            body: Buffer.from(JSON.stringify({
              protocol: 'NovaCoda',
              arenaId: 'arena-1',
              requestedCapacity: 16,
              grantedCapacity: 16,
              remainingCapacity: 1_048_560,
            }), 'utf8'),
          };
        },
      },
    });

    const handle = await runtime.allocateArena({ capacity: 16, label: 'scratch' });

    expect(handle.arenaId).toBe('arena-1');
    expect(calls[0]).toBe('request:16:{"capacity":16,"label":"scratch"}');
  });
});
