import { describe, expect, it } from 'vitest';

import { buildCodaRuntimeStatus, createCodaRuntime } from './index.js';

describe('coda-runtime facade', () => {
  it('summarizes the live and doc-forward split', () => {
    const status = buildCodaRuntimeStatus({
      transport: {
        async connect() {},
        async ping() {},
        disconnect() {},
      },
    });

    expect(status).toContain('@aaes-os/coda-runtime');
    expect(status).toContain('live surfaces');
    expect(status).toContain('doc-forward surfaces');
  });

  it('creates a snapshot with the corpus and substrate summary', async () => {
    const runtime = createCodaRuntime({
      transport: {
        async connect() {},
        async ping() {},
        disconnect() {},
      },
    });

    await runtime.connect();
    const snapshot = await runtime.ping();

    expect(snapshot.packageName).toBe('@aaes-os/coda-runtime');
    expect(snapshot.liveSurfaces).toEqual(expect.arrayContaining(['CodaDoc', 'CodaRuntime', 'NovaCoda']));
    expect(snapshot.liveSurfaces).toEqual(expect.arrayContaining(['ISL', 'GCRE-SYSMIN-001']));
    expect(snapshot.docForwardSurfaces).toEqual(expect.arrayContaining(['CML-2', 'CVM-1', 'The Voss Binding']));
    expect(snapshot.novaCoda.packageName).toBe('@aaes-os/nova-coda');
  });
});
