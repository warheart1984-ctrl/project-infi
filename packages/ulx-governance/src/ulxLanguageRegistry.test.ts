import { describe, expect, it } from 'vitest';

import { ULXLanguageRegistry, ulxLanguageRegistry } from './index.js';

describe('ULX language registry', () => {
  it('includes the documented live and spec-layer language surfaces', () => {
    const names = ulxLanguageRegistry.list().map((entry) => entry.name);

    expect(names).toEqual([
      'UL',
      'ULX',
      'CSL',
      'ISL',
      'CIC',
      'CCC',
      'COE',
      'UGR',
      'UGQL',
      'UPL',
      'CRF',
      'Policy DSL',
      'Replay DSL',
      'CML-2',
      'CVM-1',
      'The Voss Binding',
      'CodaDoc',
      'CodaRuntime',
      'NovaCoda',
      'GCRE-SYSMIN-001',
    ]);
  });

  it('finds entries by name, id, and alias without case-sensitive drift', () => {
    expect(ulxLanguageRegistry.find('ulx')).toMatchObject({ id: 'ULX' });
    expect(ulxLanguageRegistry.find('intent specification layer')).toMatchObject({ id: 'ISL' });
    expect(ulxLanguageRegistry.find('replay-dsl')).toMatchObject({ id: 'Replay DSL' });
    expect(ulxLanguageRegistry.find('coda runtime')).toMatchObject({ id: 'CodaRuntime' });
    expect(ulxLanguageRegistry.find('gcre sysmin')).toMatchObject({ id: 'GCRE-SYSMIN-001' });
  });

  it('produces a deterministic manifest that can be consumed by docs or tooling', () => {
    const manifest = ulxLanguageRegistry.manifest();
    const firstListEntry = ulxLanguageRegistry.list()[0];

    expect(manifest.total).toBe(20);
    expect(manifest.entries[0]).toMatchObject({
      id: 'UL',
      name: 'UL',
      kind: 'verb-language',
      status: 'live',
    });
    expect(manifest.entries[1]).toMatchObject({
      id: 'ULX',
      name: 'ULX',
      kind: 'source-language',
      status: 'live',
    });
    expect(manifest.entries.find((entry) => entry.id === 'CSL')).toMatchObject({
      id: 'CSL',
      kind: 'constitutional-layer',
      status: 'live',
    });
    expect(manifest.entries.find((entry) => entry.id === 'CIC')).toMatchObject({
      id: 'CIC',
      kind: 'constitutional-layer',
      status: 'live',
    });
    expect(manifest.entries.find((entry) => entry.id === 'CCC')).toMatchObject({
      id: 'CCC',
      kind: 'constitutional-layer',
      status: 'live',
    });
    expect(manifest.entries.find((entry) => entry.id === 'COE')).toMatchObject({
      id: 'COE',
      kind: 'constitutional-layer',
      status: 'live',
    });
    expect(manifest.entries.find((entry) => entry.id === 'CML-2')).toMatchObject({
      id: 'CML-2',
      kind: 'spec-family',
      status: 'live',
    });
    expect(manifest.entries.find((entry) => entry.id === 'CVM-1')).toMatchObject({
      id: 'CVM-1',
      kind: 'spec-family',
      status: 'live',
    });
    expect(manifest.entries.find((entry) => entry.id === 'The Voss Binding')).toMatchObject({
      id: 'The Voss Binding',
      kind: 'spec-family',
      status: 'live',
    });
    expect(manifest.entries.find((entry) => entry.id === 'UGR')).toMatchObject({
      id: 'UGR',
      kind: 'runtime-surface',
      status: 'live',
    });
    expect(manifest.entries.find((entry) => entry.id === 'UGQL')).toMatchObject({
      id: 'UGQL',
      kind: 'query-language',
      status: 'live',
    });
    expect(manifest.entries.find((entry) => entry.id === 'UPL')).toMatchObject({
      id: 'UPL',
      kind: 'package-language',
      status: 'live',
    });
    expect(manifest.entries.find((entry) => entry.id === 'CRF')).toMatchObject({
      id: 'CRF',
      kind: 'replay-format',
      status: 'live',
    });
    expect(manifest.entries[manifest.entries.length - 1]).toMatchObject({
      id: 'GCRE-SYSMIN-001',
      name: 'GCRE-SYSMIN-001',
      kind: 'runtime-surface',
      status: 'live',
    });
    expect(manifest.entries[0]?.aliases).not.toBe(firstListEntry?.aliases);
  });

  it('allows custom registries for narrower ULX language subsets', () => {
    const registry = new ULXLanguageRegistry([
      {
        id: 'Demo',
        name: 'Demo',
        kind: 'dsl',
        status: 'spec-only',
        ulxRole: 'Demo surface.',
        source: 'docs/demo.md',
        aliases: ['demo language'],
      },
    ]);

    expect(registry.list()).toHaveLength(1);
    expect(registry.find('demo language')).toMatchObject({ id: 'Demo' });
  });
});
