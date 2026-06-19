import { describe, expect, it } from 'vitest';

import {
  CANONICAL_INVARIANTS,
  compileInvariantDsl,
  createInvariantRegistry,
  getInvariant,
  registerInvariant,
} from './index.js';

describe('invariant registry and IDSL-1', () => {
  it('registers and retrieves canonical invariants with receipt metadata', () => {
    const registry = createInvariantRegistry(CANONICAL_INVARIANTS);
    const invariant = getInvariant(registry, 'INV-007');

    expect(invariant.name).toBe('Resource Floor');
    expect(invariant.measuredDimensions).toContain('continuity');
    expect(invariant.receiptMetadata.subsystem).toBe('constitutional-enforcement-node');
  });

  it('parses boolean IDSL and trigger bindings without eval', () => {
    const invariant = compileInvariantDsl(
      'WHEN governance < 70 AND confidence >= 80 THEN FREEZE IF VIOLATED THEN DENY',
    );
    const failed = invariant.evaluate({
      transitionId: 'idsl:freeze',
      transitionType: 'law_mutation',
      payload: {},
      requestedCapabilities: ['law:propose'],
      context: {
        actor: 'operator',
        mriSnapshot: { continuity: 72, governance: 68, memory: 75, coordination: 63, confidence: 81 },
        runtimeContext: { corridorId: 'law-evolution', capabilities: ['law:propose'] },
      },
    });

    expect(failed.passed).toBe(false);
    expect(failed.action).toBe('FREEZE');
  });

  it('keeps backward compatibility with require syntax and rejects unsupported syntax', () => {
    const registry = createInvariantRegistry();
    registerInvariant(registry, {
      id: 'INV-CUSTOM',
      name: 'Custom Confidence Floor',
      measuredDimensions: ['confidence'],
      threshold: 70,
      expression: 'require confidence >= 70',
      receiptMetadata: { subsystem: 'test', severity: 'medium' },
    });

    expect(compileInvariantDsl('require governance >= 70').invariantId).toBe('idsl:governance:min:70');
    expect(() => compileInvariantDsl('eval process.exit()')).toThrow(/unsupported IDSL/);
    expect(getInvariant(registry, 'INV-CUSTOM').threshold).toBe(70);
  });
});
