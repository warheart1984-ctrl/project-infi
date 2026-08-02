import { createServer, type Server } from 'node:http';
import { AddressInfo } from 'node:net';

import { describe, expect, it, afterEach } from 'vitest';

import { LOCAL_PROOF_SURFACE_CATALOG_URL } from './catalogConfig.js';
import { loadNovaStudioProofSurfaces } from './proofSurfaces.js';
import { DEFAULT_PROOF_SURFACE_CATALOG_URL } from './catalogConfig.js';

const servers: Server[] = [];

afterEach(() => {
  for (const server of servers) {
    server.close();
  }
  servers.length = 0;
});

function startServer(handler: (req: import('node:http').IncomingMessage, res: import('node:http').ServerResponse) => void): Promise<string> {
  const server = createServer(handler);
  servers.push(server);
  return new Promise((resolve) => {
    server.listen(0, '127.0.0.1', () => {
      const { port } = server.address() as AddressInfo;
      resolve(`http://127.0.0.1:${port}`);
    });
  });
}

describe('Nova Studio proof-surface catalog loader', () => {
  it('loads the local registry when catalogUrl is local-registry', async () => {
    const catalog = await loadNovaStudioProofSurfaces(LOCAL_PROOF_SURFACE_CATALOG_URL);

    expect(catalog.source).toBe('local-registry');
    expect(catalog.surfaces.length).toBeGreaterThan(0);
    expect(catalog.replayableSurfaces.length).toBeGreaterThan(0);
    expect(catalog.replayableSurfaces.some((s) => s.identity.id === '@aaes-os/sovereignx-router')).toBe(true);
    expect(catalog.graph.graphId).toBeTruthy();
  });

  it('loads a live catalog from the operator backend when reachable', async () => {
    const baseUrl = await startServer((req, res) => {
      if (req.url?.endsWith('/proof-surfaces')) {
        res.setHeader('content-type', 'application/json');
        res.end(JSON.stringify({ summaries: [{ identity: { id: 'remote-surface' }, proofLevel: 'P2', commercialReadiness: {} }] }));
        return;
      }
      if (req.url?.endsWith('/evidence-graph')) {
        res.setHeader('content-type', 'application/json');
        res.end(JSON.stringify({ summary: { graphId: 'ceg:remote', rootReceiptId: 'remote', claimCount: 0, unresolvedClaims: [] } }));
        return;
      }
      res.statusCode = 404;
      res.end('{}');
    });

    const catalog = await loadNovaStudioProofSurfaces(`${baseUrl}/proof-surfaces`);

    expect(catalog.source).toBe('operator-backend');
    expect(catalog.catalogUrl).toBe(`${baseUrl}/proof-surfaces`);
    expect(catalog.surfaces.some((s) => s.identity.id === 'remote-surface')).toBe(true);
  });

  it('falls back to the local registry when the operator backend is unreachable', async () => {
    const catalog = await loadNovaStudioProofSurfaces('http://127.0.0.1:1/proof-surfaces');

    expect(catalog.source).toBe('local-registry');
    expect(catalog.replayableSurfaces.length).toBeGreaterThan(0);
  });

  it('loads nested catalog.surfaces payloads from the operator backend', async () => {
    const baseUrl = await startServer((req, res) => {
      if (req.url?.endsWith('/proof-surfaces')) {
        res.setHeader('content-type', 'application/json');
        res.end(
          JSON.stringify({
            catalog: {
              surfaces: [{ surface: { identity: { id: 'nested-surface' }, proofLevel: 'P2', commercialReadiness: {} } }],
            },
          }),
        );
        return;
      }
      res.statusCode = 404;
      res.end('{}');
    });

    const catalog = await loadNovaStudioProofSurfaces(`${baseUrl}/proof-surfaces`);

    expect(catalog.source).toBe('operator-backend');
    expect(catalog.surfaces.some((s) => s.identity.id === 'nested-surface')).toBe(true);
  });

  it('uses the default operator catalog URL when no override is provided', async () => {
    const catalog = await loadNovaStudioProofSurfaces();
    expect(catalog.catalogUrl).toBe(DEFAULT_PROOF_SURFACE_CATALOG_URL);
  });
});
