import { describe, expect, it } from 'vitest';

import {
  createCmlVossRuntime,
  normalizeCmlVossBinding,
  normalizeCmlVossFamily,
  summarizeCmlVossRuntime,
  validateCmlVossBinding,
  validateCmlVossFamily,
} from './index.js';

const traceability = [
  {
    cisRequirement: 'CML-VOSS-LIVE-001',
    referenceArchitecture: 'ULX Language Registry / CML Voss',
    conformanceTest: 'packages/cml-voss-runtime/src/index.test.ts',
    evidenceArtifact: 'cml-voss-runtime',
  },
] as const;

describe('cml-voss-runtime', () => {
  it('normalizes and hashes CML/CVM/Voss family records deterministically', () => {
    const family = normalizeCmlVossFamily({
      id: ' CML-2 ',
      name: ' CML-2 ',
      kind: 'constraint-language',
      purpose: ' governed meaning constraints ',
      canonicalSource: ' docs/specifications/README.md ',
      aliases: [' cml2 ', ' constitutional meaning language 2 '],
      traceability,
    });

    expect(family.id).toBe('CML-2');
    expect(family.hash).toHaveLength(64);
    expect(validateCmlVossFamily(family).valid).toBe(true);
  });

  it('exposes default live families and the Voss binding', () => {
    const runtime = createCmlVossRuntime();

    expect(runtime.findFamily('cml2')).toMatchObject({ id: 'CML-2' });
    expect(runtime.findFamily('cvm1')).toMatchObject({ id: 'CVM-1' });
    expect(runtime.findFamily('voss')).toMatchObject({ id: 'The Voss Binding' });
    expect(runtime.listBindings()[0]).toMatchObject({
      id: 'voss-cml2-cvm1',
      relation: 'binds-meaning-to-verification',
    });
    expect(runtime.snapshot()).toMatchObject({
      packageName: '@aaes-os/cml-voss-runtime',
      version: 'cml-voss-v1',
      totalFamilies: 3,
      totalBindings: 1,
      rejectedSubjects: 0,
    });
  });

  it('validates bindings and rejects missing traceability', () => {
    const binding = normalizeCmlVossBinding({
      id: 'voss-cml2-cvm1',
      fromFamily: 'CML-2',
      toFamily: 'CVM-1',
      relation: 'binds',
      invariant: 'meaning remains traceable to verification',
      traceability,
    });
    const invalid = validateCmlVossBinding({
      id: '',
      fromFamily: '',
      toFamily: '',
      relation: '',
      invariant: '',
      traceability: [],
    });

    expect(validateCmlVossBinding(binding).valid).toBe(true);
    expect(invalid.valid).toBe(false);
    expect(invalid.issues.map((issue) => issue.field)).toEqual(
      expect.arrayContaining(['id', 'fromFamily', 'toFamily', 'relation', 'invariant', 'traceability']),
    );
  });

  it('summarizes the live corpus surface', () => {
    expect(summarizeCmlVossRuntime()).toBe('@aaes-os/cml-voss-runtime exposes 3 live corpus families and 1 bindings');
  });
});
