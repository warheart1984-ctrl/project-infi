import { describe, expect, it } from 'vitest';

import {
  ConstitutionalCompiler,
  ULXGovernanceRuntime,
  ULXTraceInvariant,
  ULXValidator,
} from './index.js';

describe('ULX governance', () => {
  it('compiles source into constitutional ULX bytecode', () => {
    const compiler = new ConstitutionalCompiler();

    expect(compiler.compile('  let   x =  1;  ')).toBe('ULX::let x = 1;');
  });

  it('validates only constitutional ULX bytecode', () => {
    const validator = new ULXValidator();

    expect(validator.validate('')).toMatchObject({
      passed: false,
      severity: 'error',
      message: 'ULX bytecode must not be empty',
    });
    expect(validator.validate('plain text')).toMatchObject({
      passed: false,
      severity: 'fatal',
      message: 'ULX bytecode must be constitutionalized before execution',
    });
    expect(validator.validate('ULX::let x = 1;')).toMatchObject({
      passed: true,
      severity: 'info',
      message: 'ULX bytecode is valid',
      canonicalBytecode: 'ULX::let x = 1;',
    });
  });

  it('executes ULX source and emits a traceable result', () => {
    const sentMessages: unknown[] = [];
    const runtime = new ULXGovernanceRuntime({
      bus: {
        async send(message: unknown) {
          sentMessages.push(message);
        },
      } as never,
    });

    const result = runtime.execute('   emit   governed   trace   ');

    expect(result).toMatchObject({
      source: '   emit   governed   trace   ',
      bytecode: 'ULX::emit governed trace',
      verified: true,
    });
    expect(sentMessages).toHaveLength(1);
    expect(sentMessages[0]).toMatchObject({
      from: 'runtime',
      to: 'governance',
      type: 'ULX_TRACE',
      payload: {
        source: '   emit   governed   trace   ',
        bytecode: 'ULX::emit governed trace',
        verified: true,
      },
    });
  });

  it('requires a trace artifact before ULX commit', () => {
    const passed = ULXTraceInvariant.check({
      payload: {
        traceId: 'trace-1',
      },
    });

    const failed = ULXTraceInvariant.check({
      payload: {},
    });

    expect(passed).toMatchObject({
      passed: true,
      severity: 'info',
      invariantId: 'I-ULX-001',
    });
    expect(failed).toMatchObject({
      passed: false,
      severity: 'fatal',
      invariantId: 'I-ULX-001',
    });
  });
});
