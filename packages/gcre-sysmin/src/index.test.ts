import { describe, expect, it } from 'vitest';

import { buildGcreFamily, createGcreSysminRuntime, summarizeGcreFamily } from './index.js';

describe('gcre-sysmin', () => {
  it('exposes a live family registry and graph fingerprint', () => {
    const family = buildGcreFamily();
    expect(family.map((member) => member.displayName)).toEqual(
      expect.arrayContaining(['GCRE-SYSMIN-001', 'GCRE', 'CML-2', 'CVM-1', 'The Voss Binding']),
    );

    const runtime = createGcreSysminRuntime();
    expect(runtime.resolve('gcre')).toBeTruthy();
    expect(runtime.graph().fingerprint).toHaveLength(64);
  });

  it('summarizes live and doc-forward family members', () => {
    const snapshot = summarizeGcreFamily();

    expect(snapshot.packageName).toBe('@aaes-os/gcre-sysmin');
    expect(snapshot.rootFamily).toBe('GCRE-SYSMIN-001');
    expect(snapshot.liveMembers).toEqual(expect.arrayContaining(['GCRE-SYSMIN-001', 'GCRE']));
    expect(snapshot.docForwardMembers).toEqual(expect.arrayContaining(['CML-2', 'CVM-1', 'The Voss Binding']));
    expect(snapshot.total).toBe(5);
    expect(snapshot.live).toBe(2);
    expect(snapshot.docForward).toBe(3);
  });
});
