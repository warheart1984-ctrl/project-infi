import { describe, expect, it } from 'vitest';

import {
  getCodingCapabilityPrimaryModel,
  getCodingCapabilityRouting,
  listAAISCodingCapabilities,
  resolveAAISCodingCapability,
} from './codingCapabilities.js';

describe('AAIS coding capabilities', () => {
  it('exposes the real coding agent catalog', () => {
    const names = listAAISCodingCapabilities().map((capability) => capability.name);

    expect(names).toEqual([
      'RefactorCode',
      'GenerateModule',
      'ExplainCode',
      'AddTests',
      'MigrateAPI',
      'DesignSchema',
    ]);
  });

  it('attaches routing hints and governance constraints to the catalog', () => {
    const refactor = resolveAAISCodingCapability('RefactorCode');
    const schema = resolveAAISCodingCapability('DesignSchema');

    expect(refactor?.routing.fastIteration?.preferredModel).toBe('qwen-3b');
    expect(refactor?.routing.deepReasoning?.preferredModel).toBe('qwen-7b');
    expect(schema?.governanceConstraints).toContain('must support provenance');
    expect(getCodingCapabilityPrimaryModel('DesignSchema')).toBe('qwen-7b');
    expect(getCodingCapabilityRouting('ExplainCode').smallPrompt?.preferredModel).toBe('qwen-3b');
  });
});
