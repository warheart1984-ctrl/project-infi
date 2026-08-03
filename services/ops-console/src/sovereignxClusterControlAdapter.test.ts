import { createServer, type Server } from 'node:http';
import { AddressInfo } from 'node:net';

import { describe, expect, it, vi } from 'vitest';

import { createSovereignXClusterControlAdapter } from './sovereignxClusterControlAdapter.js';
import { resetSovereignXClusterControlState } from './sovereignxClusterGovernance.js';

describe('sovereignxClusterControlAdapter', () => {
  it('applies membership control through the local backend and records an audit entry', async () => {
    const adapter = createSovereignXClusterControlAdapter();
    expect(adapter.backend).toBe('local');
    expect(adapter.controlUrl).toBeNull();

    const result = await adapter.applyControl(
      { action: 'quarantine', nodeId: 'cluster-gpu-a', reason: 'operator drill' },
      1_700_000_000_000,
    );

    expect(result.outcome).toBe('applied');
    expect(result.controlState.quarantinedNodeIds).toContain('cluster-gpu-a');
    expect(result.auditEntry.backend).toBe('local');
    expect(result.auditEntry.reason).toBe('operator drill');
    expect(adapter.auditTrail()).toHaveLength(1);
    expect(adapter.status().auditEntryCount).toBe(1);
  });

  it('reports noop when the control request does not change membership', async () => {
    const adapter = createSovereignXClusterControlAdapter();
    const steadyState = await adapter.applyControl({ action: 'steady_state' }, 1_700_000_000_000);
    expect(steadyState.outcome).toBe('noop');

    await adapter.applyControl({ action: 'quarantine', nodeId: 'cluster-gpu-a' }, 1_700_000_000_001);
    const repeatQuarantine = await adapter.applyControl(
      { action: 'quarantine', nodeId: 'cluster-gpu-a' },
      1_700_000_000_002,
    );
    expect(repeatQuarantine.outcome).toBe('noop');
  });

  it('forwards control to a real control-plane endpoint and adopts the returned state', async () => {
    let receivedBody: unknown = null;
    let server: Server;
    await new Promise<void>((resolve) => {
      server = createServer((req, res) => {
        let raw = '';
        req.on('data', (chunk) => {
          raw += chunk;
        });
        req.on('end', () => {
          receivedBody = JSON.parse(raw);
          res.writeHead(200, { 'content-type': 'application/json' });
          res.end(
            JSON.stringify({
              controlState: {
                desiredNodeCount: 4,
                quarantinedNodeIds: ['cluster-gpu-b'],
                preferredFailoverNodeId: 'cluster-mixed-a',
                lastAction: null,
              },
            }),
          );
        });
      });
      server.listen(0, '127.0.0.1', () => {
        resolve();
      });
    });

    try {
      const address = server.address() as AddressInfo;
      const adapter = createSovereignXClusterControlAdapter({
        controlUrl: `http://127.0.0.1:${address.port}`,
      });

      expect(adapter.backend).toBe('remote');
      expect(adapter.controlUrl).toBe(`http://127.0.0.1:${address.port}`);

      const result = await adapter.applyControl(
        { action: 'quarantine', nodeId: 'cluster-gpu-a' },
        1_700_000_000_000,
      );

      expect(receivedBody).toMatchObject({
        request: { action: 'quarantine', nodeId: 'cluster-gpu-a' },
        observedAtMs: 1_700_000_000_000,
      });
      expect(result.outcome).toBe('remote-applied');
      expect(result.controlState.quarantinedNodeIds).toContain('cluster-gpu-b');
      expect(result.controlState.desiredNodeCount).toBe(4);
      expect(result.auditEntry.backend).toBe('remote');
    } finally {
      await new Promise<void>((resolve, reject) => {
        server.close((error) => {
          if (error) {
            reject(error);
            return;
          }
          resolve();
        });
      });
      resetSovereignXClusterControlState();
    }
  });

  it('falls back to the local backend when the control plane is unreachable', async () => {
    const adapter = createSovereignXClusterControlAdapter({
      controlUrl: 'http://127.0.0.1:1',
      timeoutMs: 250,
    });

    const result = await adapter.applyControl(
      { action: 'quarantine', nodeId: 'cluster-gpu-c' },
      1_700_000_000_000,
    );

    expect(result.outcome).toBe('remote-fallback');
    expect(result.controlState.quarantinedNodeIds).toContain('cluster-gpu-c');
    expect(result.auditEntry.detail).toContain('fell back to in-process control');
  });

  it('rejects when the control plane returns a non-ok response', async () => {
    const fetchImpl = vi.fn(async () => {
      return new Response(JSON.stringify({ error: 'control denied' }), {
        status: 409,
        headers: { 'content-type': 'application/json' },
      });
    }) as unknown as typeof fetch;

    const adapter = createSovereignXClusterControlAdapter({
      controlUrl: 'http://control-plane.example',
      fetchImpl,
    });

    const result = await adapter.applyControl(
      { action: 'failover', nodeId: 'cluster-gpu-a' },
      1_700_000_000_000,
    );

    expect(result.outcome).toBe('rejected');
    expect(result.auditEntry.detail).toContain('HTTP 409');
    expect(adapter.auditTrail()).toHaveLength(1);
  });

  it('rejects when the control plane returns an invalid control state payload', async () => {
    const fetchImpl = vi.fn(async () => {
      return new Response(JSON.stringify({ controlState: { desiredNodeCount: 'four' } }), {
        status: 200,
        headers: { 'content-type': 'application/json' },
      });
    }) as unknown as typeof fetch;

    const adapter = createSovereignXClusterControlAdapter({
      controlUrl: 'http://control-plane.example',
      fetchImpl,
    });

    const result = await adapter.applyControl({ action: 'scale_up' }, 1_700_000_000_000);

    expect(result.outcome).toBe('rejected');
    expect(result.auditEntry.detail).toContain('invalid control state payload');
  });
});
